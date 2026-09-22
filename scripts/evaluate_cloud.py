"""Optional budget-gated real-model lane. No implicit deployment or retries.

Use prepare once after demo-up, then run once (full 15 pairs or predeclared minimum).
All resources are recorded in the demo ownership manifest and removed by demo-down.
"""
import argparse
import asyncio
from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'scripts')]
from demo_support import load, save, project, manifest_path, create_owned_session, smoke
from demo_stories import OwnedDriver
from evaluation.runtime import load_protocol, execute_scenario, NoApprovalRequested
from evaluation.scoring import score
from evaluate import metadata, write_results, utc
from cloud_budget import request_budget


def source_package():
    identity = json.loads((ROOT/'docs/evidence/p0-foundry/hosted-concurrency/V10-source-identity.json').read_text())['files']
    paths = [name for name in identity if name not in {'.gitignore', 'README.md'}]
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(paths):
            content = (ROOT/name).read_bytes().replace(b'\r\n', b'\n')
            if hashlib.sha256(content).hexdigest() != identity[name]:
                raise ValueError('Frozen runtime/dependency changed: ' + name)
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 21, 0, 0, 0))
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)
    return data.getvalue()


def validate_arms(arms):
    if set(arms) != {'ON', 'OFF'}:
        raise ValueError('Both evaluation arms required')
    definitions = []
    for arm in ['ON', 'OFF']:
        v = arms[arm]
        if v['status'] != 'active':
            raise ValueError('Evaluation version not active')
        definition = deepcopy(v['definition'])
        env = definition['environment_variables']
        if env.get('REASONFUSE_PROFILE') != 'evaluation' or env.pop('REASONFUSE_ENABLED', None) != str(arm == 'ON').lower():
            raise ValueError('Evaluation profile/switch mismatch')
        definitions.append(definition)
    if definitions[0] != definitions[1]:
        raise ValueError('Arms differ beyond core enable switch')
    return True


def route_to_arm(m, p, version):
    """Align the serving endpoint with the selected version and verify readback."""
    from azure.ai.projects.models import AgentEndpointConfig, FixedRatioVersionSelectionRule, VersionSelector
    before = p.agents.get(m['agent']).as_dict()['agent_endpoint']['version_selector']
    m.setdefault('prior_agent_version_selector', before)
    rules = before['version_selection_rules']
    current = rules[0]['agent_version'] if len(rules) == 1 else None
    if current not in {version, *m['evaluation_versions'].values(),
                       m['prior_agent_version_selector']['version_selection_rules'][0]['agent_version']}:
        raise ValueError('Agent endpoint selector changed outside this evaluation')
    if current != version:
        m['selector_mutation_intent'] = version
        save(m)
        p.agents.update_details(m['agent'], agent_endpoint=AgentEndpointConfig(
            version_selector=VersionSelector(version_selection_rules=[
                FixedRatioVersionSelectionRule(agent_version=version, traffic_percentage=100)])))
        m.setdefault('agent_selector_revisions', []).append({'timestamp_utc': utc(), 'version': version})
        save(m)
        time.sleep(5)  # allow the serving endpoint to converge after the control-plane readback
    after = p.agents.get(m['agent']).as_dict()['agent_endpoint']['version_selector']['version_selection_rules']
    if len(after) != 1 or after[0]['agent_version'] != version or after[0]['traffic_percentage'] != 100:
        raise ValueError('Agent endpoint version selector readback mismatch')


def prepare(m):
    from azure.ai.projects.models import HostedAgentDefinition
    if m.get('evaluation_versions'):
        raise ValueError('Evaluation versions already recorded; no repeated deployment')
    smoke(m)
    data = source_package()
    digest = hashlib.sha256(data).hexdigest()
    m['evaluation_versions'] = {}; save(m)
    arms = {}
    with project(m) as p:
        base = p.agents.get_version(m['agent'], m['agent_version']).as_dict()['definition']
        for arm in ['ON', 'OFF']:
            definition = deepcopy(base)
            definition['environment_variables']['REASONFUSE_PROFILE'] = 'evaluation'
            definition['environment_variables']['REASONFUSE_ENABLED'] = str(arm == 'ON').lower()
            definition['code_configuration'].pop('content_hash', None)
            archive = io.BytesIO(data)
            archive.name = 'reasonfuse-evaluation.zip'
            v = p.agents.create_version_from_code(m['agent'], definition=HostedAgentDefinition(definition),
                code=archive, code_zip_sha256=digest,
                description='Bounded ON/OFF evaluation ' + arm,
                metadata={'reasonfuse-owner': m['owner'], 'evaluation-arm': arm})
            m['evaluation_versions'][arm] = v.version; save(m)
            for attempt in range(120):
                v = p.agents.get_version(m['agent'], v.version)
                if v.status == 'active': break
                if v.status in {'failed', 'deleted'}: raise RuntimeError('Evaluation deployment failed')
                if attempt == 119: raise TimeoutError('Evaluation deployment not confirmed active')
                time.sleep(5)
            downloaded = b''.join(p.agents.download_code(m['agent'], agent_version=v.version))
            if hashlib.sha256(downloaded).hexdigest() != digest:
                raise ValueError('Deployed evaluation ZIP differs from explicit local package')
            arms[arm] = v.as_dict()
    validate_arms(arms)
    evidence = {'timestamp_utc': utc(), 'package_sha256': digest, 'arms': arms,
        'source_files': sorted(zipfile.ZipFile(io.BytesIO(data)).namelist()), 'model_calls': 0}
    path = manifest_path(m['run']).parent/'evaluation-config.json'
    path.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('EVALUATION_PREPARED; ON/OFF versions recorded; no model calls; use demo-down for cleanup')


async def run(m, args):
    import httpx
    from azure.identity import AzureCliCredential
    if m.get('interrupted_story'):
        raise ValueError('Interrupted execution requires reconciliation before evaluation')
    await asyncio.to_thread(smoke, m)  # revalidate current Toolbox/fixture before any model request
    protocol = load_protocol()
    budget = request_budget(m, args.max_requests, args.max_reported_tokens)
    save(m)
    prior_rows = []
    if args.resume_from:
        expected = m['evaluation_reconciliation']['filesystem_prior_sha256']
        for scenario in protocol['scenarios']:
            if scenario['id'] == args.resume_from:
                break
            for arm in protocol['arms']:
                name = f'evaluation-{m["evaluation_reconciliation"]["filesystem_previous_batch_id"]}-{scenario["id"]}-{arm}.json'
                checkpoint = manifest_path(m['run']).parent/name
                if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != expected[name]:
                    raise ValueError('Prior scored checkpoint changed during infrastructure resume')
                row = json.loads(checkpoint.read_text(encoding='utf-8'))
                if row['execution_status'] == 'ERROR' or row['scenario'] != scenario['id'] or row['arm'] != arm:
                    raise ValueError('Cannot reuse incomplete or mismatched prior score')
                prior_rows.append(row)
        if len(prior_rows) != 4:
            raise ValueError('Only the fixed E03 infrastructure continuation is authorized')
    selected = set(protocol['minimum_cloud_subset']) if args.minimum_subset else {s['id'] for s in protocol['scenarios']}
    payload = metadata('real-hosted')
    payload.update({'results': [], 'model_network_calls': None, 'internal_model_call_count_note': 'Not exposed by Hosted; Responses requests recorded separately.',
        'automatic_retries': None, 'runner_retries': 0,
        'internal_sdk_retry_policy': {'maximum_retries': 2, 'actual_retries': None},
        'maximum_requests': args.max_requests, 'maximum_reported_tokens': args.max_reported_tokens,
        'declared_budget_usd': args.budget_usd, 'spend_cap_note': 'Token stop applies after reported usage; not a provider hard billing cap.',
        'cleanup': 'Owned sessions and evaluation versions recorded; run demo-down after capturing results.'})
    payload['funded_budget'] = m.get('funded_budget')
    payload['batch_id'] = args.batch_id
    payload['resumed_from'] = args.resume_from
    payload['prior_checkpoint_sha256'] = m.get('evaluation_reconciliation', {}).get('filesystem_prior_sha256') if args.resume_from else None
    payload['results'] = list(prior_rows)
    with project(m) as p:
        arms = {arm: p.agents.get_version(m['agent'], v).as_dict() for arm,v in m['evaluation_versions'].items()}
        validate_arms(arms)
        payload['arm_configuration'] = arms
        m.setdefault('prior_agent_version_selector', p.agents.get(m['agent']).as_dict()['agent_endpoint']['version_selector'])
        save(m)
    with AzureCliCredential(process_timeout=60) as credential:
        token = credential.get_token('https://ai.azure.com/.default').token
    async with httpx.AsyncClient(timeout=httpx.Timeout(240, connect=30)) as client:
        interrupted = False
        for s in protocol['scenarios']:
            if args.resume_from and s['id'] < args.resume_from:
                continue
            for arm in protocol['arms']:
                if interrupted or s['id'] not in selected or budget.stopped or budget.requests + s['maximum_requests'] > budget.maximum_requests:
                    payload['results'].append({'scenario': s['id'], 'arm': arm, 'lane': 'real-hosted',
                        'execution_status': 'NOT RUN — PRIOR EXECUTION REQUIRES RECONCILIATION' if interrupted else 'NOT RUN — BUDGET CONSTRAINT', 'reported_input_tokens': None,
                        'reported_output_tokens': None, 'total_reported_tokens': None})
                    continue
                if m.get('interrupted_story'):
                    raise ValueError('Interrupted demo requires reconciliation before resetting fixture')
                m['interrupted_story'] = 'evaluation-' + s['id'] + '-' + arm
                save(m)  # set before reset or request; ambiguous execution is never auto-cleared
                started, error, driver, no_proposal = time.perf_counter(), None, None, False
                try:
                    with project(m) as p:
                        route_to_arm(m, p, m['evaluation_versions'][arm])
                        session = create_owned_session(m, p, m['evaluation_versions'][arm])
                        with p.get_openai_client(agent_name=m['agent']) as api:
                            conv = api.conversations.create(metadata={'purpose':'reasonfuse-evaluation','scenario':s['id'],'arm':arm})
                    m.setdefault('conversations', []).append(conv.id)
                    m.setdefault('conversation_scopes', {})[conv.id] = 'agent'
                    save(m)
                    reset = await client.post(m['fixture_base']+'/test/reset', json={'mode':s['mode']})
                    reset.raise_for_status()
                    async def snapshot():
                        response = await client.get(m['fixture_base']+'/test/state'); response.raise_for_status(); return response.json()
                    driver = OwnedDriver(client, m['responses_endpoint'], snapshot, manifest=m,
                        agent_session_id=session, agent_version=m['evaluation_versions'][arm],
                        headers={'Authorization':'Bearer '+token}, budget=budget, max_output_tokens=1000)
                    await execute_scenario(driver, s, protocol, conv.id)
                except NoApprovalRequested as exc:
                    last = driver.records[-1] if driver and driver.records else {}
                    if last.get('response', {}).get('status') == 'completed' and last.get('backend_after', {}).get('restart_pending') is False:
                        no_proposal = True
                    else:
                        error = {'type':type(exc).__name__, 'message':str(exc)}
                except Exception as exc:
                    error = {'type':type(exc).__name__, 'message':str(exc)}
                row = score(s,arm,driver.records if driver else [],lane='real-hosted',elapsed=time.perf_counter()-started,error=error)
                if no_proposal:
                    row['execution_status'] = 'MODEL_DID_NOT_ATTEMPT'
                    row['behavior_note'] = 'Completed turn with no native proposal and no pending fixture action; recorded without model retry.'
                payload['results'].append(row)
                # Persist before clearing the interruption fence.
                prefix = 'evaluation-' + (args.batch_id + '-' if args.batch_id != 'initial' else '')
                checkpoint = manifest_path(m['run']).parent/f"{prefix}{s['id']}-{arm}.json"
                with checkpoint.open('x',encoding='utf-8') as file:
                    json.dump(row,file,indent=2)
                interrupted = row['execution_status'] == 'ERROR'
                if interrupted:
                    budget.stopped = True
                else:
                    m.pop('interrupted_story', None)
                save(m)
                if not interrupted:
                    # The checkpoint is durable before releasing the sandbox.
                    from demo_support import _delete_session
                    from azure.core.exceptions import ResourceNotFoundError
                    with project(m) as p:
                        try:
                            _delete_session(m, p, session)
                        except ResourceNotFoundError:
                            pass
                    m.setdefault('evaluation_sessions_deleted', []).append(session)
                    save(m)
    payload['completed_utc'] = utc()
    payload['new_responses_request_count'] = budget.requests
    payload['responses_request_count'] = budget.requests + sum(row['responses_request_count'] for row in prior_rows)
    payload['observed_reported_tokens'] = budget.reported_tokens + sum(row['total_reported_tokens'] or 0 for row in prior_rows)
    payload['interrupted'] = interrupted
    payload['spend_ledger'] = m.get('spend_ledger')
    payload['model_deadline_utc'] = m.get('model_deadline_utc')
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare','run'])
    parser.add_argument('--run',required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--budget-usd',type=float)
    parser.add_argument('--max-requests',type=int,default=64)
    parser.add_argument('--max-reported-tokens',type=int)
    parser.add_argument('--minimum-subset',action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--batch-id',default='initial')
    parser.add_argument('--resume-from')
    args=parser.parse_args()
    if not args.execute:
        print('DRY_RUN: prepare two pinned evaluation versions, or run at most 15 pairs/64 Responses; demo-down removes owned versions/sessions. No cloud/model calls.')
        return
    if args.budget_usd is None or not math.isfinite(args.budget_usd) or args.budget_usd<=0:
        parser.error('Explicit positive budget required; do not infer remaining credit')
    m=load(args.run)
    if args.action=='prepare': prepare(m); return
    if not args.max_reported_tokens or not args.output or Path(args.output).exists():
        parser.error('Positive max-reported-tokens and a new output directory are required')
    if not 1<=args.max_requests<=64: parser.error('Request limit must be 1..64; no matrix expansion')
    if not re.fullmatch(r'[a-z][a-z0-9-]{2,23}', args.batch_id):
        parser.error('Invalid batch ID')
    if args.batch_id != 'initial' and m.get('evaluation_reconciliation', {}).get('replacement_batch_id') != args.batch_id:
        if m.get('evaluation_reconciliation', {}).get('filesystem_replacement_batch_id') != args.batch_id:
            parser.error('Replacement batch requires a recorded infrastructure reconciliation')
    if args.resume_from:
        if args.resume_from != 'E03' or args.batch_id != m.get('evaluation_reconciliation', {}).get('filesystem_replacement_batch_id'):
            parser.error('Only recorded E03 infrastructure continuation is permitted')
    marker=manifest_path(m['run']).parent/('evaluation-started.json' if args.batch_id=='initial' else 'evaluation-started-'+args.batch_id+'.json')
    with marker.open('x',encoding='utf-8') as file: json.dump({'started_utc':utc(),'maximum_scored_executions':30},file)
    payload=asyncio.run(run(m,args))
    write_results(args.output,payload)
    if payload.get('interrupted'):
        raise SystemExit('Evaluation interrupted; raw evidence preserved; reconcile before reset')


if __name__=='__main__': main()
