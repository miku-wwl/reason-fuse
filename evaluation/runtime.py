"""Bounded comparison using the real pinned host and explicitly scripted local model.

No policy substitutes, deployment, automatic retry or hidden model calls.
"""
import asyncio
from contextlib import asynccontextmanager
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

import httpx
from agent_framework import Content, tool
from azure.ai.agentserver.core.tasks import set_resilient_tasks_enabled
from azure.ai.agentserver.responses._id_generator import IdGenerator
from reasonfuse.main import ReasonFuseHostServer

ROOT = Path(__file__).resolve().parents[1]


def load_protocol():
    p = json.loads((ROOT / 'evaluation/protocol.json').read_text(encoding='utf-8'))
    assert len(p['scenarios']) == len({s['id'] for s in p['scenarios']}) == 15
    assert sum(s['maximum_requests'] for s in p['scenarios']) * 2 == 64
    return p


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def batches(s):
    """Declared behavior attempts, identical in both arms; not model statistics."""
    support = module('evaluation_transport', ROOT / 'tests/p0_support.py')
    call = support.call
    status = lambda i: [call(f'status-{i}', 'operations___service_status')]
    text = lambda v: [Content.from_text(json.dumps({'task_result': v}))]
    if s['flow'] == 'read_loop':
        return [status(i) for i in range(4)] + [text('NO_PROGRESS')]
    proposals = [call('restart-1')]
    if s['flow'] == 'duplicate':
        proposals.append(call('restart-2'))
    result = [proposals]
    if s['flow'] == 'denial':
        return result + [text('DENIED')]
    if s['script'] == 'verify':
        result.append(status(1))
    elif s['script'] == 'diagnostic':
        result.append([Content.from_function_call('diag', 'read_reasonfuse_state', arguments={})])
    # Honest negative prompts vs explicit adversarial success instructions.
    result.append(text({'E07': 'FAILED', 'E09': 'UNKNOWN', 'E12': 'FAILED'}.get(s['id'], 'SUCCESS')))
    if s['flow'] == 'reapproval':
        result.extend([[call('restart-again')], status(2), text('FAILED')])
    return result


@asynccontextmanager
async def local_driver(scenario, arm):
    state = module('eval_fixture', ROOT / 'cloud/operations-mcp/server.py').OperationsState()
    state.reset(scenario['mode'])
    support = module('eval_support', ROOT / 'tests/p0_support.py')
    entered, release = asyncio.Event(), asyncio.Event()
    if scenario['flow'] != 'concurrent':
        release.set()

    @tool(name='operations___restart_service', approval_mode='always_require')
    async def restart(service_name: str) -> str:
        """Submit a test restart; acceptance is not verified success."""
        entered.set()
        await release.wait()
        return json.dumps(state.restart_service(service_name))

    @tool(name='operations___service_status', approval_mode='never_require')
    async def status(service_name: str) -> str:
        """Read orders health and generation from the fixture."""
        return json.dumps(state.service_status(service_name))

    with tempfile.TemporaryDirectory(prefix='reasonfuse-eval-') as temp:
        with patch.dict(os.environ, {'AGENTSERVER_STATE_ROOT': temp,
            'FOUNDRY_PROJECT_ENDPOINT': 'https://test.invalid/api/projects/test',
            'AZURE_AI_PROJECT_ENDPOINT': 'https://test.invalid/api/projects/test',
            'AZURE_AI_MODEL_DEPLOYMENT_NAME': 'scripted-local-control',
            'REASONFUSE_PROFILE': 'evaluation', 'REASONFUSE_ENABLED': str(arm == 'ON').lower(),
            'TOOLBOX_NAME': ''}, clear=True):
            set_resilient_tasks_enabled(False)
            agent, model = support.make_agent(batches(scenario), [restart, status])
            host = ReasonFuseHostServer(agent, history_source='agent_server', configure_observability=None)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=host), base_url='http://localhost') as client:
                async def snapshot():
                    return state.snapshot()
                driver = Driver(client, '/responses', snapshot)
                driver.entered, driver.release, driver.model = entered, release, model
                driver.scenario = scenario
                try:
                    yield driver
                finally:
                    release.set()


class BudgetStop(RuntimeError):
    pass


class ResponseFailure(RuntimeError):
    pass


def is_admission_rejection(response):
    """Only the two known pre-dispatch concurrency rejections qualify."""
    error = response.get('error') or {}
    return (response.get('status') == 'failed' and response.get('output') == []
            and error.get('code') == 'server_error' and error.get('message') in {
                'ReasonFuse: conversation is busy or requires reconciliation',
                'ReasonFuse: another request owns this conversation'})


class RequestBudget:
    def __init__(self, requests, tokens):
        if requests < 1 or tokens < 1:
            raise ValueError('Positive explicit request/token limits required')
        self.maximum_requests, self.maximum_tokens = requests, tokens
        self.requests = self.reported_tokens = 0
        self.stopped = False

    def reserve(self):
        if self.stopped or self.requests >= self.maximum_requests:
            raise BudgetStop('Request/token limit reached or usage unavailable; no retry')
        self.requests += 1

    def observe(self, response):
        usage = response.get('usage')
        if not usage or usage.get('total_tokens') is None:
            self.stopped = True
            return
        self.reported_tokens += usage['total_tokens']
        self.stopped |= self.reported_tokens >= self.maximum_tokens


class Driver:
    def __init__(self, client, endpoint, snapshot, *, headers=None, budget=None, max_output_tokens=1000):
        self.client, self.endpoint, self.snapshot = client, endpoint, snapshot
        self.headers, self.budget, self.max_output_tokens = headers or {}, budget, max_output_tokens
        self.records = []
        self.entered = self.release = self.model = None
        self.scenario = None

    async def request(self, body, *, allow_admission_rejection=False):
        # Script the new user turn independently of whether enforcement ended
        # the preceding model loop early. Same rule and attempts in both arms.
        if self.model and self.scenario and body.get('input') == self.scenario.get('followup'):
            self.model.batches = batches(self.scenario)[-3:]
        record = {'request': {'store': True, 'max_output_tokens': self.max_output_tokens, **body},
            'backend_before': await self.snapshot(), 'first_output_seconds': None, 'text_observations': []}
        if self.budget:
            self.budget.reserve()
        self.records.append(record)
        started = time.perf_counter()
        try:
            if body.get('stream'):
                record['events'] = []
                async with self.client.stream('POST', self.endpoint, headers=self.headers, json=record['request']) as r:
                    record['http_status'] = r.status_code
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line.startswith('data:') or line[5:].strip() == '[DONE]':
                            continue
                        event = json.loads(line[5:].strip())
                        record['events'].append(event)
                        if event.get('type') == 'response.output_text.delta':
                            if record['first_output_seconds'] is None:
                                record['first_output_seconds'] = time.perf_counter() - started
                            record['text_observations'].append({'text': event.get('delta', ''), 'backend': await self.snapshot()})
                        if event.get('type') in {'response.completed', 'response.failed', 'response.incomplete'}:
                            record['response'] = event['response']
                if 'response' not in record:
                    raise RuntimeError('No terminal stream response')
            else:
                r = await self.client.post(self.endpoint, headers=self.headers, json=record['request'])
                record['http_status'] = r.status_code
                r.raise_for_status()
                record['response'] = r.json()
            if self.budget:
                self.budget.observe(record['response'])
            record['backend_after'] = await self.snapshot()
            if not body.get('stream'):
                record['text_observations'] = [{'text': output_text(record['response']), 'backend': record['backend_after']}]
            if record['response'].get('status') != 'completed' and not (
                    allow_admission_rejection and is_admission_rejection(record['response'])):
                raise ResponseFailure('Unexpected terminal response; preserve raw state and reconcile before reset')
            return record['response']
        except Exception as error:
            record['error'] = {'type': type(error).__name__, 'message': str(error)}
            if self.budget:
                self.budget.stopped = True
            raise
        finally:
            record['elapsed_seconds'] = time.perf_counter() - started
            record['completed_monotonic'] = time.perf_counter()


def output_text(response):
    return ''.join(c.get('text', '') for i in response.get('output', []) if i.get('type') == 'message'
                   for c in i.get('content', []) if isinstance(c, dict))


def continuation(s, response, conversation, value):
    body = {'input': value, 'stream': s['stream']}
    body['conversation' if s['continuation'] == 'explicit' else 'previous_response_id'] = (
        conversation if s['continuation'] == 'explicit' else response['id'])
    return body


def approval_input(response, approved=True):
    requests = [i for i in response.get('output', []) if i.get('type') == 'mcp_approval_request']
    if not requests:
        raise ValueError('Expected approval missing; retain model behavior, never retry')
    return [{'type': 'mcp_approval_response', 'approval_request_id': i['id'], 'approve': approved} for i in requests]


async def execute_scenario(d, s, protocol, conversation=None):
    conversation = conversation or IdGenerator.new_id('conv')
    body = {'input': s['prompt'] + ' ' + protocol['output_instruction'], 'stream': s['stream']}
    if s['continuation'] == 'explicit':
        body['conversation'] = conversation
    response = await d.request(body)
    if s['flow'] == 'read_loop':
        return
    follow = continuation(s, response, conversation, approval_input(response, s['flow'] != 'denial'))
    if s['flow'] == 'concurrent':
        if d.entered is None:
            # Drain both in-flight branches before recording failure or resetting.
            outcomes = await asyncio.gather(d.request(follow, allow_admission_rejection=True),
                                            d.request(follow, allow_admission_rejection=True), return_exceptions=True)
            for outcome in outcomes:
                if isinstance(outcome, BaseException):
                    raise outcome
        else:
            first = asyncio.create_task(d.request(follow, allow_admission_rejection=True))
            try:
                await asyncio.wait_for(d.entered.wait(), 10)
                await d.request(follow, allow_admission_rejection=True)
            finally:
                d.release.set()
                await first
        return
    response = await d.request(follow)
    if s['flow'] == 'reapproval':
        response = await d.request(continuation(s, response, conversation, s['followup']))
        await d.request(continuation(s, response, conversation, approval_input(response)))
