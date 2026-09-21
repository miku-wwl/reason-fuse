"""Deletion ownership and configuration fail-closed; no Azure/model traffic."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
from demo_support import (validate_owned_inventory, verify_toolbox, APPROVAL, manifest_path,
                         plan, command, validate_endpoints, check_binding, down)
from demo_stories import assertions
from check_submission import secret_findings


class DemoSafetyTests(unittest.TestCase):
    def test_exact_owned_inventory_only(self):
        m={'owner':'run-owner','expected_resources':['/subscriptions/s/resourceGroups/rg/providers/Microsoft.App/containerApps/test']}
        group={'tags':{'reasonfuse-owner':'run-owner'}}
        items=[{'id':m['expected_resources'][0],'tags':group['tags']}]
        validate_owned_inventory(m,group,items)
        with self.assertRaises(ValueError):validate_owned_inventory(m,{'tags':{}},items)
        with self.assertRaises(ValueError):validate_owned_inventory(m,group,items+[{'id':'/unrelated','tags':group['tags']}])
        with self.assertRaises(ValueError):validate_owned_inventory(m,group,[{'id':items[0]['id'],'tags':{}}])

    def test_toolbox_endpoint_and_approval_are_both_required(self):
        value={'tools':[{'type':'mcp','server_label':'reasonfuse-operations','server_url':'https://fixture.invalid/mcp','require_approval':APPROVAL}]}
        verify_toolbox(value,'https://fixture.invalid/mcp')
        with self.assertRaises(ValueError):verify_toolbox(value,'https://different.invalid/mcp')
        altered=deepcopy(value);altered['tools'][0]['require_approval']={'never':['operations___restart_service']}
        with self.assertRaises(ValueError):verify_toolbox(altered,'https://fixture.invalid/mcp')
        altered=deepcopy(value);altered['tools'].append({'name':'reset'})
        with self.assertRaises(ValueError):verify_toolbox(altered,'https://fixture.invalid/mcp')

    def test_run_path_does_not_escape_workspace(self):
        self.assertTrue(manifest_path('test-demo').is_relative_to(ROOT/'.tools/demo'))
        for value in ['../escape','C:/temp','x','UPPER','*']:
            with self.assertRaises(ValueError):manifest_path(value)

    def test_dry_run_has_no_command_side_effect(self):
        from argparse import Namespace
        with patch('demo_support.command',side_effect=AssertionError('must not execute')):
            plan(Namespace(run='dry-check',action='up'))

    def test_concurrency_story_does_not_accept_backend_dedup_as_admission(self):
        value={'execution_status':'COMPLETED','unsupported_success_claims':0,'side_effect_attempt_count':2,
               'accepted_side_effect_count':1,'final_task_result':'VERIFIED','admission_failure_count':0,'records':[]}
        with self.assertRaises(AssertionError):assertions('C',value)
        value.update(side_effect_attempt_count=1,admission_failure_count=1)
        with self.assertRaises(AssertionError):assertions('C',value)
        completed={'response':{'status':'completed','output':[{'type':'message','content':[{'text':'{"outcome":"OUTCOME_VERIFIED"}'}]}]}}
        rejected={'response':{'status':'failed','output':[], 'error':{'code':'server_error','message':'ReasonFuse: another request owns this conversation'}}}
        value['records']=[completed,rejected]
        assertions('C',value)
        value['records'][-1]={'response':{'status':'failed','output':[], 'error':{'code':'rate_limit_exceeded','message':'model quota exhausted'}}}
        with self.assertRaises(AssertionError):assertions('C',value)

    def test_secret_scan_does_not_echo_secret(self):
        fake='gh'+'p_'+'x'*36
        results=secret_findings('test.txt',fake)
        self.assertEqual(results,[{'file':'test.txt','rule':'github-token'}])
        self.assertNotIn(fake,str(results))

    def test_windows_cli_resolves_executable_without_shell_interpolation(self):
        from types import SimpleNamespace
        with patch('demo_support.shutil.which',return_value='C:/Azure/az.cmd'), patch('demo_support.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='false')) as run:
            self.assertIs(command(['az','group','exists','--name','rg-owned']),False)
        self.assertEqual(run.call_args.args[0][0],'C:/Azure/az.cmd')
        self.assertNotIn('shell',run.call_args.kwargs)

    def test_command_failure_never_prints_captured_credentials(self):
        from types import SimpleNamespace
        with patch('demo_support.shutil.which',return_value='docker'), patch('demo_support.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='private-value',stderr='private-value')):
            with self.assertRaisesRegex(RuntimeError,'credentials not printed') as error:
                command(['docker','login'])
        self.assertNotIn('private-value',str(error.exception))


class DemoCleanupTests(unittest.TestCase):
    """Actual cleanup control flow with in-memory SDK/CLI doubles only."""

    def manifest(self):
        return {'run':'owned-demo', 'owner':'exact-owner', 'agent':'reasonfuse', 'agent_version':'10',
                'toolbox':'operations-tools', 'prior_toolbox_version':'5', 'sessions':[],
                'resource_group':'rg-reasonfuse-demo-owned-demo',
                'expected_resources':['/owned/fixture'], 'status':'READY_FOR_MANUAL_DEMO'}

    def project(self):
        p=MagicMock()
        p.__enter__.return_value=p
        p.toolboxes.list_versions.return_value=[]
        p.agents.list_versions.return_value=[]
        return p

    def cli(self, m, calls, *, unexpected=False):
        exists=True
        def fake(_manifest, *args):
            nonlocal exists
            calls.append(args)
            if args[:2] == ('group','exists'): return exists
            if args[:2] == ('group','show'): return {'tags':{'reasonfuse-owner':m['owner']}}
            if args[:2] == ('resource','list'):
                return [{'id':'/unrelated' if unexpected else '/owned/fixture',
                         'tags':{'reasonfuse-owner':m['owner']}}]
            if args[:2] == ('group','delete'):
                exists=False
                return None
            raise AssertionError('Unexpected CLI command: '+str(args))
        return fake

    def test_endpoint_validation_rejects_mixed_project_agent_or_authority(self):
        m={'agent':'reasonfuse', 'project_endpoint':'https://account.services.ai.azure.com/api/projects/demo',
           'responses_endpoint':'https://account.services.ai.azure.com/api/projects/demo/agents/reasonfuse/endpoint/protocols/openai/responses?api-version=v1'}
        validate_endpoints(m)
        for endpoint in [m['responses_endpoint'].replace('/projects/demo/', '/projects/other/'),
                         m['responses_endpoint'].replace('/agents/reasonfuse/', '/agents/other/'),
                         m['responses_endpoint'].replace('account.services.', 'other.services.'),
                         m['responses_endpoint'].replace('https://', 'https://user:pass@'),
                         m['responses_endpoint']+'&api-version=v2', m['responses_endpoint']+'#fragment']:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                validate_endpoints({**m,'responses_endpoint':endpoint})

    def test_binding_rejects_explicit_toolbox_override(self):
        m={'agent':'reasonfuse','agent_version':'10','toolbox':'operations-tools',
           'project_endpoint':'https://account.services.ai.azure.com/api/projects/demo',
           'responses_endpoint':'https://account.services.ai.azure.com/api/projects/demo/agents/reasonfuse/endpoint/protocols/openai/responses'}
        p=self.project()
        p.agents.get_version.return_value.as_dict.return_value={
            'name':'reasonfuse','version':'10','status':'active','definition':{'environment_variables':{
                'TOOLBOX_NAME':'operations-tools','TOOLBOX_ENDPOINT':'https://elsewhere.invalid/mcp'}}}
        with self.assertRaisesRegex(ValueError,'overrides name binding'):
            check_binding(m,p)

    def test_foundry_connection_failure_does_not_skip_owned_group_cleanup(self):
        m=self.manifest(); calls=[]
        with (patch('demo_support.project',side_effect=RuntimeError('unavailable')),
              patch('demo_support.az',side_effect=self.cli(m,calls)), patch('demo_support.save')):
            with self.assertRaisesRegex(RuntimeError,'foundry-client'): down(m)
        self.assertTrue(any(c[:2]==('group','delete') for c in calls))
        self.assertFalse(m['resource_group_exists'])
        self.assertEqual(m['cleanup_result'],'PARTIAL')
        self.assertEqual(m['status'],'CLEANUP_PARTIAL')

    def test_one_failed_session_does_not_prevent_other_session_or_group_cleanup(self):
        m=self.manifest(); m['sessions']=['bad','good']; p=self.project(); calls=[]
        deleted=set()
        def get(_agent, identifier):
            if identifier=='bad': raise RuntimeError('session unavailable')
            return SimpleNamespace(status='deleted' if identifier in deleted else 'idle',
                                   version_indicator=SimpleNamespace(agent_version='10'))
        p.agents.get_session.side_effect=get
        p.agents.delete_session.side_effect=lambda _agent, identifier: deleted.add(identifier)
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            with self.assertRaisesRegex(RuntimeError,'session:bad'): down(m)
        self.assertEqual(deleted,{'good'})
        self.assertFalse(m['resource_group_exists'])
        self.assertEqual(m['cleanup_result'],'PARTIAL')

    def test_deleted_project_allows_absent_resources_and_owned_group_cleanup(self):
        from azure.core.exceptions import ResourceNotFoundError
        m=self.manifest(); m['toolbox_version']='6'; m['sessions']=['gone']; p=self.project(); calls=[]
        for method in [p.toolboxes.list_versions,p.agents.list_versions,p.toolboxes.get,
                       p.toolboxes.get_version,p.agents.get_session]:
            method.side_effect=ResourceNotFoundError('gone')
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            down(m)
        self.assertEqual(m['cleanup_result'],'PASS')
        self.assertEqual(m['status'],'DELETED')
        self.assertTrue(any(s['result']=='ALREADY_ABSENT' for s in m['cleanup_steps']))

    def test_lost_create_replies_discover_only_exact_owner_in_named_scopes(self):
        from azure.core.exceptions import ResourceNotFoundError
        m=self.manifest(); p=self.project(); calls=[]; deleted=[]
        toolbox=SimpleNamespace(name=m['toolbox'],version='6',metadata={'reasonfuse-owner':m['owner']})
        evaluation=SimpleNamespace(name=m['agent'],version='11',metadata={'reasonfuse-owner':m['owner'],'evaluation-arm':'ON'})
        unrelated=SimpleNamespace(name=m['agent'],version='12',metadata={'reasonfuse-owner':'another-run','evaluation-arm':'OFF'})
        p.toolboxes.list_versions.return_value=[toolbox]
        p.agents.list_versions.return_value=[evaluation,unrelated]
        current=['6']
        p.toolboxes.get.side_effect=lambda _name: SimpleNamespace(default_version=current[0])
        p.toolboxes.update.side_effect=lambda _name,default_version: current.__setitem__(0,default_version)
        def get(kind,value):
            def lookup(_name,version):
                if (kind,version) in deleted: raise ResourceNotFoundError('deleted')
                self.assertEqual(version,value.version)
                return value
            return lookup
        p.toolboxes.get_version.side_effect=get('toolbox',toolbox)
        p.agents.get_version.side_effect=get('evaluation',evaluation)
        p.toolboxes.delete_version.side_effect=lambda _name,version: deleted.append(('toolbox',version))
        p.agents.delete_version.side_effect=lambda _name,version: deleted.append(('evaluation',version))
        with (patch('demo_support.project',return_value=p), patch('demo_support.save') as save_mock,
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            down(m)
        p.toolboxes.list_versions.assert_called_once_with('operations-tools')
        p.agents.list_versions.assert_called_once_with('reasonfuse',include_drafts=True)
        self.assertEqual(m['owned_toolbox_versions'],['6'])
        self.assertEqual(m['owned_evaluation_versions'],['11'])
        self.assertEqual(deleted,[('toolbox','6'),('evaluation','11')])
        self.assertEqual(current,['5'])
        self.assertEqual(m['cleanup_result'],'PASS')
        self.assertGreater(save_mock.call_count,4)

    def test_failed_discovery_is_partial_even_when_owned_group_was_removed(self):
        m=self.manifest(); p=self.project(); calls=[]
        p.agents.list_versions.side_effect=RuntimeError('read unavailable')
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            with self.assertRaisesRegex(RuntimeError,'discover-evaluation-versions'): down(m)
        self.assertEqual(m['cleanup_result'],'PARTIAL')
        self.assertFalse(m['resource_group_exists'])

    def test_unknown_group_resource_is_never_deleted(self):
        m=self.manifest(); p=self.project(); calls=[]
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls,unexpected=True))):
            with self.assertRaisesRegex(RuntimeError,'resource-group'): down(m)
        self.assertFalse(any(c[:2]==('group','delete') for c in calls))
        self.assertNotEqual(m['cleanup_result'],'PASS')

    def test_unowned_recorded_version_is_refused_without_blocking_group_cleanup(self):
        m=self.manifest(); m['evaluation_versions']={'ON':'11'}; p=self.project(); calls=[]
        p.agents.get_version.return_value=SimpleNamespace(metadata={'reasonfuse-owner':'other','evaluation-arm':'ON'})
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            with self.assertRaisesRegex(RuntimeError,'evaluation-version:11'): down(m)
        p.agents.delete_version.assert_not_called()
        self.assertFalse(m['resource_group_exists'])

    def test_changed_toolbox_default_is_preserved_but_owned_group_still_cleans(self):
        m=self.manifest(); m['toolbox_version']='6'; p=self.project(); calls=[]
        p.toolboxes.get.return_value=SimpleNamespace(default_version='another-operators-version')
        with (patch('demo_support.project',return_value=p), patch('demo_support.save'),
              patch('demo_support.az',side_effect=self.cli(m,calls))):
            with self.assertRaisesRegex(RuntimeError,'restore-toolbox-default'): down(m)
        p.toolboxes.update.assert_not_called()
        p.toolboxes.delete_version.assert_not_called()
        self.assertFalse(m['resource_group_exists'])
        self.assertEqual(m['cleanup_result'],'PARTIAL')
