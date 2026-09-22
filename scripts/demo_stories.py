"""Three real Hosted demo stories; no retry and no inference during import."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import re
import time

import httpx
from azure.identity import AzureCliCredential
from evaluation.runtime import Driver, RequestBudget, execute_scenario, load_protocol, output_text, is_admission_rejection
from evaluation.scoring import score
from demo_support import project, save, smoke, utc, manifest_path, create_owned_session
from cloud_budget import request_budget


class OwnedDriver(Driver):
    def __init__(self, *args, manifest, agent_session_id, agent_version, verbose=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest = manifest
        self.agent_session_id, self.agent_version = agent_session_id, agent_version
        self.verbose = verbose

    async def request(self, body, *, allow_admission_rejection=False):
        try:
            if self.verbose and isinstance(body.get('input'), list):
                print('NATIVE_APPROVAL_RESPONSE: runner sends the protocol response; prose is not authorization.')
            response = await super().request({'agent_session_id': self.agent_session_id, **body},
                                             allow_admission_rejection=allow_admission_rejection)
            reference = response.get('agent_reference', {})
            if reference.get('version') != self.agent_version or reference.get('name') != self.manifest['agent']:
                if self.budget: self.budget.stopped = True
                raise ValueError('Served Agent name/version differs from pinned evaluation/demo target')
            if response.get('agent_session_id') != self.agent_session_id:
                if self.budget: self.budget.stopped = True
                raise ValueError('Served session differs from the owned pinned session')
            if self.verbose:
                print('RESPONSE', response.get('status'), 'NATIVE_APPROVAL_REQUESTS', sum(i.get('type') == 'mcp_approval_request' for i in response.get('output', [])))
                print('AUTHORITATIVE_OUTPUT', output_text(response))
                print('BACKEND', json.dumps(await self.snapshot()))
            return response
        finally:
            # Ownership comes from explicit creation, never from an unexpected
            # response identity. Raw response identifiers remain in evidence.
            if self.budget and hasattr(self.budget, 'snapshot'):
                self.manifest['spend_ledger'] = self.budget.snapshot()
            save(self.manifest)


def assertions(story, result):
    if result['execution_status'] != 'COMPLETED' or result['unsupported_success_claims']:
        raise AssertionError('Unexpected response or unsupported success; preserve failure, do not retry')
    if result['side_effect_attempt_count'] != 1 or result['accepted_side_effect_count'] != 1:
        raise AssertionError('Expected exactly one attempt/accepted execution in this bounded story')
    texts = [output_text(r.get('response', {})) for r in result['records']]
    if story in {'A', 'C'} and result['final_task_result'] != 'VERIFIED':
        raise AssertionError('Missing independent fresh verified outcome')
    if story == 'A' and not any('OUTCOME_VERIFIED' in t for t in texts):
        raise AssertionError('Runtime VERIFIED output missing')
    if story == 'B' and (result['final_task_result'] != 'FAILED' or not any('BLOCKED' in t for t in texts)):
        raise AssertionError('Expected FAILED followed by BLOCKED')
    if story == 'C':
        branches = result['records'][-2:]
        rejected = [r for r in branches if is_admission_rejection(r.get('response', {}))]
        completed = [r for r in branches if r.get('response', {}).get('status') == 'completed'
                     and 'OUTCOME_VERIFIED' in output_text(r['response'])]
        if result['admission_failure_count'] != 1 or len(rejected) != 1 or len(completed) != 1:
            raise AssertionError('Expected a pre-dispatch admission rejection and a completed VERIFIED branch')


async def run_story(m, story, *, evidence_suffix=None):
    if m['status'] != 'READY_FOR_MANUAL_DEMO':
        raise ValueError('Run demo-up/smoke before executing stories')
    if m.get('interrupted_story'):
        raise ValueError('Prior story interrupted; preserve evidence and reconcile before another reset')
    directory = manifest_path(m['run']).parent
    if evidence_suffix is not None:
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,23}', evidence_suffix):
            raise ValueError('Invalid infrastructure retry evidence suffix')
        if m.get('reconciled_infrastructure_attempts', {}).get(story) != evidence_suffix:
            raise ValueError('Infrastructure retry requires an explicit recorded reconciliation')
    target = directory / ('story-' + story + ('-' + evidence_suffix if evidence_suffix else '') + '.json')
    if target.exists():
        raise FileExistsError('Story evidence exists; do not overwrite or retry for prettier behavior')
    # smoke is synchronous; no model requests and outside the active event loop.
    await asyncio.to_thread(smoke, m)
    protocol = load_protocol()
    s = deepcopy(next(x for x in protocol['scenarios'] if x['id'] == {'A':'E01','B':'E12','C':'E15'}[story]))
    m['interrupted_story'] = story
    save(m)
    error, driver = None, None
    started = time.perf_counter()
    try:
        with project(m) as p:
            pinned_session = create_owned_session(m, p, m['agent_version'])
            with p.get_openai_client(agent_name=m['agent']) as api:
                conv = api.conversations.create(metadata={'purpose': 'reasonfuse-demo', 'run': m['run'], 'story': story})
        m.setdefault('conversations', []).append(conv.id)
        m.setdefault('conversation_scopes', {})[conv.id] = 'agent'
        save(m)
        with AzureCliCredential(process_timeout=60) as credential:
            token = credential.get_token('https://ai.azure.com/.default').token
        async with httpx.AsyncClient(timeout=httpx.Timeout(240, connect=30)) as client:
            reset = await client.post(m['fixture_base'] + '/test/reset', json={'mode': s['mode']})
            reset.raise_for_status()
            async def snapshot():
                r = await client.get(m['fixture_base'] + '/test/state'); r.raise_for_status(); return r.json()
            driver = OwnedDriver(client, m['responses_endpoint'], snapshot, manifest=m,
                agent_session_id=pinned_session, agent_version=m['agent_version'], verbose=True,
                headers={'Authorization': 'Bearer ' + token}, budget=request_budget(m, s['maximum_requests'], 40000), max_output_tokens=1500)
            await execute_scenario(driver, s, protocol, conv.id)
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    result = score(s, 'ON', driver.records if driver else [], lane='real-hosted-demo', elapsed=time.perf_counter()-started, error=error)
    result.update({'story': story, 'timestamp_utc': utc(), 'agent_version': m['agent_version'],
                   'source_commit': m['source_commit'], 'internal_model_call_count': None,
                   'model_call_count_note': 'Hosted response count is known; internal inference count is not exposed.'})
    if evidence_suffix:
        result['infrastructure_retry_suffix'] = evidence_suffix
    try:
        assertions(story, result)
        result['demo_assertions'] = 'PASS'
    except Exception as exc:
        result['demo_assertions'] = 'FAIL'
        result['assertion_error'] = str(exc)
    with target.open('x', encoding='utf-8') as file:
        file.write(json.dumps(result, indent=2) + '\n')
    if result['demo_assertions'] == 'PASS':
        m.pop('interrupted_story', None)
    save(m)
    print(json.dumps({k:v for k,v in result.items() if k not in {'records','error'}}, indent=2))
    if result['demo_assertions'] != 'PASS':
        raise RuntimeError('Demo assertion failed; raw evidence preserved; no automatic retry')
