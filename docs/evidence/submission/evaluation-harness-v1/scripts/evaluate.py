"""One fixed 15-pair run, or explicit budget placeholders. Never deploys/retries."""
import argparse
import asyncio
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from evaluation.runtime import load_protocol, local_driver, execute_scenario, module
from evaluation.scoring import score


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_results(directory, payload):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    sanitizer = module('eval_sanitizer', ROOT / 'scripts/p0_foundry_cloud.py').sanitize
    payload = sanitizer(payload)
    (directory / 'results.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    scalar = {key for row in payload['results'] for key, value in row.items()
              if key not in {'records', 'error', 'concurrency_attribution'} and not isinstance(value, (dict, list))}
    with (directory / 'results.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['scenario', 'arm'] + sorted(scalar - {'scenario', 'arm'}), extrasaction='ignore')
        writer.writeheader()
        writer.writerows(payload['results'])
    manifest = {p.name: hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                for p in directory.iterdir() if p.is_file()}
    (directory / 'manifest.json').write_text(json.dumps({'algorithm': 'SHA256, LF normalized', 'files': manifest}, indent=2) + '\n', encoding='utf-8')


def metadata(lane):
    names = ['agent-framework-core', 'agent-framework-foundry', 'agent-framework-foundry-hosting',
             'azure-ai-projects', 'azure-ai-agentserver-responses', 'azure-ai-agentserver-core']
    return {'started_utc': utc(), 'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'lane': lane, 'scenario_count': 15, 'protocol_sha256': hashlib.sha256((ROOT/'evaluation/protocol.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'harness_source_hashes': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                                 for p in sorted((ROOT/'evaluation').glob('*.py')) + [Path(__file__).resolve()]},
        'runtime_source_identity': 'docs/evidence/p0-foundry/hosted-concurrency/V10-source-identity.json',
        'python': sys.version.split()[0], 'versions': {name: version(name) for name in names},
        'azure_resources_created': 0, 'azure_resources_deleted': 0, 'automatic_retries': 0,
        'cleanup': 'Local ephemeral State Store and in-memory fixture disposed per execution; no Azure resources created.'}


async def local_run():
    protocol = load_protocol()
    payload = metadata('local-scripted')
    payload['model_network_calls'] = 0
    payload['results'] = []
    for scenario in protocol['scenarios']:
        for arm in protocol['arms']:
            started, error = time.perf_counter(), None
            async with local_driver(scenario, arm) as driver:
                try:
                    await execute_scenario(driver, scenario, protocol)
                except Exception as exc:
                    error = {'type': type(exc).__name__, 'message': str(exc)}
                row = score(scenario, arm, driver.records, lane='local-scripted', elapsed=time.perf_counter()-started,
                            scripted_requests=len(driver.model.requests), error=error)
                payload['results'].append(row)
                print(f"{scenario['id']} {arm}: {row['execution_status']}; unsupported={row['unsupported_success_claims']}; attempts={row['side_effect_attempt_count']}")
    payload['completed_utc'] = utc()
    return payload


def budget_rows(reason):
    payload = metadata('cloud-not-run')
    payload.update({'model_network_calls': 0, 'responses_request_count': 0, 'budget_reason': reason,
                    'cleanup': 'No cloud actions performed; no cleanup necessary.'})
    payload['results'] = [{'scenario': s['id'], 'arm': arm, 'execution_status': 'NOT RUN — BUDGET CONSTRAINT',
        'lane': 'cloud-not-run', 'model_network_calls': 0, 'responses_request_count': 0,
        'reported_input_tokens': None, 'reported_output_tokens': None, 'total_reported_tokens': None}
        for s in load_protocol()['scenarios'] for arm in ['ON', 'OFF']]
    payload['completed_utc'] = utc()
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane', choices=['local', 'budget-record'], required=True)
    parser.add_argument('--output', required=True, help='New directory; existing evidence is never overwritten')
    parser.add_argument('--budget-reason', default='No numeric Azure/model spending ceiling supplied; do not infer available credit.')
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error('output directory already exists; evidence is immutable')
    payload = asyncio.run(local_run()) if args.lane == 'local' else budget_rows(args.budget_reason)
    write_results(args.output, payload)
    print('RESULTS=' + args.output)
    if any(row['execution_status'] == 'ERROR' for row in payload['results']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
