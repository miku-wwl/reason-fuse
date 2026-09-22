"""Scoring and transport regressions, including safety-relevant evidence races."""
import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from evaluation.runtime import Driver, RequestBudget, BudgetStop, ResponseFailure, is_admission_rejection, load_protocol, local_driver, execute_scenario
from evaluation.scoring import score, postcondition, success_claim
from evaluate import write_results
from evaluate_cloud import validate_arms, source_package


class EvaluationTests(unittest.IsolatedAsyncioTestCase):
    def test_fixed_protocol_and_fair_configuration(self):
        p=load_protocol()
        self.assertEqual(p['minimum_cloud_subset'],['E01','E04','E12'])
        self.assertEqual(sum(s['maximum_requests'] for s in p['scenarios']),32)
        base={'status':'active','definition':{'environment_variables':{'REASONFUSE_PROFILE':'evaluation','REASONFUSE_ENABLED':'true'},'source':'same'}}
        arms={'ON':base,'OFF':deepcopy(base)}
        arms['OFF']['definition']['environment_variables']['REASONFUSE_ENABLED']='false'
        self.assertTrue(validate_arms(arms))
        arms['OFF']['definition']['source']='different'
        with self.assertRaises(ValueError):validate_arms(arms)

    async def test_real_host_pair_boundaries(self):
        p=load_protocol()
        for ident in ['E04','E12','E15']:
            s=next(v for v in p['scenarios'] if v['id']==ident)
            rows={}
            for arm in ['ON','OFF']:
                async with local_driver(s,arm) as d:
                    await execute_scenario(d,s,p)
                    rows[arm]=score(s,arm,d.records,lane='local-scripted',elapsed=0)
            self.assertEqual(rows['ON']['side_effect_attempt_count'],1)
            self.assertEqual(rows['ON']['unsupported_success_claims'],0)
            self.assertIsNone(rows['ON']['total_reported_tokens'])
            if ident=='E04': self.assertEqual(rows['OFF']['unsupported_success_claims'],1)
            if ident=='E12': self.assertEqual(rows['OFF']['execution_after_failed_or_unknown'],1)
            if ident=='E15':
                self.assertEqual(rows['ON']['admission_failure_count'],1)
                self.assertEqual(rows['OFF']['admission_failure_count'],1)
                self.assertEqual(rows['OFF']['side_effect_attempt_count'],1)

    def test_stale_and_pre_action_observations_cannot_verify(self):
        state={'events':[{'sequence':1,'operation':'service_status','result':{'resource':'orders','generation':'g2','service_health':'HEALTHY'}},
                         {'sequence':2,'operation':'restart_service','result':{'accepted':True,'resource':'orders','generation':'g2'}}]}
        self.assertEqual(postcondition(state),'UNKNOWN')
        state['events'].append({'sequence':3,'operation':'service_status','result':{'resource':'orders','generation':'g1','service_health':'HEALTHY'}})
        self.assertEqual(postcondition(state),'UNKNOWN')
        state['events'][-1]['result']['generation']='g2'
        self.assertEqual(postcondition(state),'VERIFIED')

    async def test_http_transport_usage_and_no_retry(self):
        seen=[]
        def handler(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200,json={'id':'r1','status':'completed','output':[]})
        async def snapshot():return {'events':[]}
        budget=RequestBudget(2,100)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url='https://test.invalid') as client:
            d=Driver(client,'/responses',snapshot,budget=budget)
            await d.request({'input':'one','stream':False})
            with self.assertRaises(BudgetStop):await d.request({'input':'two'})
        self.assertEqual(len(seen),1)
        self.assertIs(seen[0]['store'],True)
        self.assertEqual(budget.reported_tokens,0)

    async def test_stream_claim_cannot_borrow_later_verification(self):
        observations=0
        accepted={'sequence':1,'operation':'restart_service','result':{'accepted':True,'resource':'orders','generation':'g2'}}
        verified={'sequence':2,'operation':'service_status','result':{'resource':'orders','generation':'g2','service_health':'HEALTHY'}}
        async def snapshot():
            nonlocal observations
            observations+=1
            return {'restart_count':1,'restart_attempt_count':1,'status_read_count':int(observations>=3),
                    'events':[accepted]+([verified] if observations>=3 else [])}
        answer={'id':'r','status':'completed','output':[{'type':'message','content':[{'text':'{"task_result":"SUCCESS"}'}]}]}
        def handler(request):
            events=[{'type':'response.output_text.delta','delta':'{"task_result":"SUCCESS"}'},{'type':'response.completed','response':answer}]
            return httpx.Response(200,text=''.join('data: '+json.dumps(e)+'\n\n' for e in events),headers={'content-type':'text/event-stream'})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url='https://test.invalid') as client:
            d=Driver(client,'/responses',snapshot)
            await d.request({'input':'x','stream':True})
        r=score(load_protocol()['scenarios'][0],'OFF',d.records,lane='real-hosted',elapsed=0)
        self.assertEqual(r['final_task_result'],'VERIFIED')
        self.assertEqual(r['unsupported_success_claims'],1)
        self.assertIsNone(r['total_reported_tokens'])

    def test_budget_boundary_and_missing_csv_usage(self):
        b=RequestBudget(1,10); b.reserve(); b.observe({'status':'completed','usage':{'total_tokens':10}})
        with self.assertRaises(BudgetStop):b.reserve()
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'results'
            write_results(folder,{'results':[{'scenario':'E01','arm':'ON','total_reported_tokens':None}]})
            self.assertIn('E01,ON,', (folder/'results.csv').read_text())
            with self.assertRaises(FileExistsError):write_results(folder,{'results':[]})

    def test_deployment_package_allowlist_and_determinism(self):
        import io,zipfile
        one=source_package()
        self.assertEqual(one,source_package())
        names=zipfile.ZipFile(io.BytesIO(one)).namelist()
        self.assertIn('src/reasonfuse/host_admission.py',names)
        self.assertFalse(any('.env' in n or '.tools' in n for n in names))

    def test_unknown_health_and_invalid_answer_are_not_scored_as_known(self):
        state={'events':[{'sequence':1,'operation':'restart_service','result':{'accepted':True,'resource':'orders','generation':'g2'}},
                         {'sequence':2,'operation':'service_status','result':{'resource':'orders','generation':'g2','service_health':'UNRECOGNIZED'}}]}
        self.assertEqual(postcondition(state),'UNKNOWN')
        self.assertIsNone(success_claim('{"task_result":"garbage"}'))
        self.assertIsNone(success_claim('{"outcome":"garbage"}'))
        self.assertFalse(success_claim('{"outcome":"POSTCONDITION_FAILED"}'))

    async def test_failed_or_incomplete_response_preserves_raw_and_stops(self):
        async def snapshot():return {'events':[]}
        for status in ['failed','incomplete']:
            raw={'id':'failure','status':status,'output':[], 'error':{'code':'rate_limit_exceeded','message':'model quota exhausted'}}
            budget=RequestBudget(3,100)
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=raw)),base_url='https://test.invalid') as client:
                d=Driver(client,'/responses',snapshot,budget=budget)
                with self.assertRaises(ResponseFailure):await d.request({'input':'x'})
                self.assertEqual(d.records[0]['response'],raw)
                self.assertTrue(budget.stopped)
                self.assertFalse(is_admission_rejection(raw))
                result=score(load_protocol()['scenarios'][-1],'ON',d.records,lane='real-hosted',elapsed=0)
                self.assertEqual(result['execution_status'],'ERROR')
                self.assertEqual(result['admission_failure_count'],0)

    async def test_only_explicit_concurrent_admission_failure_is_expected(self):
        raw={'status':'failed','output':[], 'error':{'code':'server_error','message':'ReasonFuse: another request owns this conversation'}}
        async def snapshot():return {'events':[]}
        self.assertTrue(is_admission_rejection(raw))
        with_output=deepcopy(raw);with_output['output']=[{'type':'mcp_call'}]
        self.assertFalse(is_admission_rejection(with_output))
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=raw)),base_url='https://test.invalid') as client:
            d=Driver(client,'/responses',snapshot)
            with self.assertRaises(ResponseFailure):await d.request({'input':'x'})
            d=Driver(client,'/responses',snapshot,budget=RequestBudget(2,100))
            self.assertEqual(await d.request({'input':'x'},allow_admission_rejection=True),raw)
            self.assertTrue(d.budget.stopped)  # missing usage never implies free requests

    async def test_cloud_failure_stops_matrix_without_resetting_uncertain_fixture(self):
        from argparse import Namespace
        import evaluate_cloud
        p=MagicMock();p.__enter__.return_value=p
        base={'status':'active','definition':{'environment_variables':{'REASONFUSE_PROFILE':'evaluation','REASONFUSE_ENABLED':'true'}}}
        off=deepcopy(base);off['definition']['environment_variables']['REASONFUSE_ENABLED']='false'
        p.agents.get_version.side_effect=[MagicMock(as_dict=lambda:base),MagicMock(as_dict=lambda:off)]
        p.agents.get.return_value.as_dict.return_value={'agent_endpoint':{'version_selector':{'version_selection_rules':[{'agent_version':'11','traffic_percentage':100}]}}}
        api=p.get_openai_client.return_value.__enter__.return_value
        api.conversations.create.return_value.id='owned-conversation'
        credential=MagicMock();credential.__enter__.return_value.get_token.return_value.token='unit-test-token'
        requests=[]
        def handler(request):
            requests.append(request.url.path)
            if request.url.path=='/responses':
                return httpx.Response(200,json={'status':'failed','output':[], 'error':{'code':'server_error','message':'uncertain dispatch'}})
            return httpx.Response(200,json={'events':[]})
        original_client=httpx.AsyncClient
        m={'run':'unit-test','agent':'reasonfuse','agent_version':'10','evaluation_versions':{'ON':'11','OFF':'12'},
           'sessions':[],'fixture_base':'https://test.invalid','responses_endpoint':'https://test.invalid/responses'}
        args=Namespace(max_requests=64,max_reported_tokens=100,budget_usd=1,minimum_subset=False,batch_id='initial',resume_from=None)
        with tempfile.TemporaryDirectory() as temp, patch('evaluate_cloud.project',return_value=p), \
                patch('evaluate_cloud.smoke') as smoke_mock, \
                patch('evaluate_cloud.route_to_arm'), \
                patch('evaluate_cloud.create_owned_session',return_value='owned-session'), \
                patch('evaluate_cloud.save'),patch('demo_stories.save'), \
                patch('evaluate_cloud.manifest_path',return_value=Path(temp)/'ownership.json'), \
                patch('azure.identity.AzureCliCredential',return_value=credential), \
                patch('httpx.AsyncClient',side_effect=lambda **kw:original_client(transport=httpx.MockTransport(handler),**kw)):
            result=await evaluate_cloud.run(m,args)
            self.assertTrue((Path(temp)/'evaluation-E01-ON.json').exists())
            smoke_mock.assert_called_once_with(m)
        self.assertEqual(requests.count('/test/reset'),1)
        self.assertEqual(requests.count('/responses'),1)
        self.assertEqual(result['results'][0]['execution_status'],'ERROR')
        self.assertEqual(len(result['results']),30)
        self.assertTrue(all('RECONCILIATION' in row['execution_status'] for row in result['results'][1:]))
        self.assertEqual(m['interrupted_story'],'evaluation-E01-ON')

    async def test_concurrent_error_drains_other_inflight_branch(self):
        from types import SimpleNamespace
        calls, completed = 0, []
        async def request(body, **kwargs):
            nonlocal calls
            calls+=1
            if calls==1:return {'id':'r','output':[{'type':'mcp_approval_request','id':'approval'}]}
            if calls==2:raise ResponseFailure('uncertain dispatch')
            await asyncio.sleep(0.01)
            completed.append(True)
            return {'status':'completed','output':[]}
        d=SimpleNamespace(request=request,entered=None)
        protocol=load_protocol()
        with self.assertRaises(ResponseFailure):await execute_scenario(d,protocol['scenarios'][-1],protocol,'conv')
        self.assertEqual(completed,[True])

    async def test_owned_driver_rejects_foreign_response_identity_without_adopting_it(self):
        from demo_stories import OwnedDriver
        async def snapshot():return {'events':[]}
        for reference,session in [({'name':'another','version':'10'},'owned-session'),({'name':'reasonfuse','version':'10'},'foreign-session')]:
            m={'agent':'reasonfuse','sessions':['owned-session']}
            raw={'status':'completed','output':[],'agent_reference':reference,'agent_session_id':session,'usage':{'total_tokens':1}}
            with patch('demo_stories.save'):
                async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json=raw)),base_url='https://test.invalid') as client:
                    d=OwnedDriver(client,'/responses',snapshot,manifest=m,agent_session_id='owned-session',agent_version='10',budget=RequestBudget(2,100))
                    with self.assertRaises(ValueError):await d.request({'input':'x'})
            self.assertTrue(d.budget.stopped)
            self.assertEqual(m['sessions'],['owned-session'])
