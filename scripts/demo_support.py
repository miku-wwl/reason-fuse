"""Owned, bounded demo lifecycle. Dry-run is default; no Agent redeployment.

Credentials remain in memory; ownership and raw responses stay in .tools/demo.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
EXPECTED_TOOLS = {'operations___restart_service', 'operations___service_status'}
APPROVAL = {'always': ['operations___restart_service'], 'never': ['operations___service_status']}


def utc():
    return datetime.now(timezone.utc).isoformat()


def manifest_path(run):
    if not re.fullmatch(r'[a-z][a-z0-9-]{2,23}', run):
        raise ValueError('RunId must be 3..24 lowercase letters/digits/hyphens, starting with a letter')
    return ROOT/'.tools/demo'/run/'ownership.json'


def save(m):
    path = manifest_path(m['run'])
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
    try:
        for attempt in range(20):
            try:
                temp.replace(path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.1)
    finally:
        temp.unlink(missing_ok=True)


def load(run):
    value = json.loads(manifest_path(run).read_text(encoding='utf-8'))
    if value.get('run') != run or value.get('schema') != 'reasonfuse-demo-v1':
        raise ValueError('Unexpected ownership manifest')
    if value.get('resource_group') != 'rg-reasonfuse-demo-' + run:
        raise ValueError('Refusing a resource group outside this demo naming boundary')
    return value


def command(args, *, json_output=True, input_text=None):
    executable = shutil.which(args[0])
    if not executable:
        raise FileNotFoundError('Required command missing: ' + args[0])
    result = subprocess.run([executable, *args[1:]], cwd=ROOT, text=True, input=input_text, capture_output=True)
    if result.returncode:
        # Do not echo CLI stdout/stderr: registry login output may contain tokens.
        raise RuntimeError(f'{Path(args[0]).name} {args[1]} failed (exit {result.returncode}); credentials not printed')
    return json.loads(result.stdout) if json_output and result.stdout.strip() else result.stdout


def az(m, *args):
    return command(['az', *args, '--subscription', m['subscription'], '--only-show-errors', '--output', 'json'])


def settings(args):
    from dotenv import dotenv_values
    env = dotenv_values(ROOT/'.azure/reason-fuse/.env')
    values = {
        'subscription': args.subscription or env.get('AZURE_SUBSCRIPTION_ID'),
        'project_endpoint': args.project_endpoint or env.get('FOUNDRY_PROJECT_ENDPOINT') or env.get('AZURE_AI_PROJECT_ENDPOINT'),
        'responses_endpoint': args.responses_endpoint or env.get('AGENT_REASONFUSE_RESPONSES_ENDPOINT'),
        'agent': 'reasonfuse', 'agent_version': getattr(args, 'agent_version', None) or '10', 'toolbox': 'operations-tools',
    }
    for key in ['subscription', 'project_endpoint', 'responses_endpoint']:
        if not values[key]:
            raise ValueError(f'Missing {key}; supply explicit command parameter or existing .azure environment')
    validate_endpoints(values)
    if not re.fullmatch(r'[1-9][0-9]*', values['agent_version']):
        raise ValueError('A concrete positive Agent version is required')
    return values


def validate_endpoints(m):
    """Bind the invoked endpoint to the exact project/agent inspected by SDK."""
    project_url = urlsplit(m['project_endpoint'])
    responses_url = urlsplit(m['responses_endpoint'])
    for value in (project_url, responses_url):
        if value.scheme != 'https' or not value.hostname or value.username or value.password or value.fragment:
            raise ValueError('Cloud endpoints must be HTTPS without credentials or fragments')
    if not re.fullmatch(r'/api/projects/[A-Za-z0-9_.-]+/?', project_url.path) or project_url.query:
        raise ValueError('Expected a Foundry /api/projects/<project> endpoint')
    expected_path = project_url.path.rstrip('/') + '/agents/' + m['agent'] + '/endpoint/protocols/openai/responses'
    if (responses_url.hostname.lower(), responses_url.port or 443, responses_url.path) != (
            project_url.hostname.lower(), project_url.port or 443, expected_path):
        raise ValueError('Responses endpoint must identify the same account, project and agent as ProjectEndpoint')
    query = parse_qsl(responses_url.query, keep_blank_values=True)
    if query not in ([], [('api-version', 'v1')]):
        raise ValueError('Responses endpoint only permits the optional api-version=v1 query')


def project(m):
    from azure.ai.projects import AIProjectClient
    from azure.identity import AzureCliCredential
    return AIProjectClient(endpoint=m['project_endpoint'], credential=AzureCliCredential(process_timeout=60))


def check_binding(m, p):
    validate_endpoints(m)
    v = p.agents.get_version(m['agent'], m['agent_version']).as_dict()
    env = v['definition']['environment_variables']
    if v.get('name') != m['agent'] or str(v.get('version')) != m['agent_version']:
        raise ValueError('Inspected Agent identity differs from the requested binding')
    if v['status'] != 'active' or env.get('TOOLBOX_NAME') != m['toolbox']:
        raise ValueError('Configured Agent version must be active and bound by Toolbox name')
    if env.get('TOOLBOX_ENDPOINT'):
        raise ValueError('TOOLBOX_ENDPOINT overrides name binding; refusing an unverified alternate Toolbox')
    if env.get('REASONFUSE_PROFILE') != 'runtime' or env.get('REASONFUSE_ENABLED') != 'true':
        raise ValueError('Demo must retain runtime/ON settings')
    expected = json.loads((ROOT/'docs/evidence/p0-foundry/hosted-concurrency/V10-package.json').read_text())['sha256']
    if v['definition']['code_configuration']['content_hash'] != expected:
        raise ValueError('Agent source is not the known v10 package')
    return v


async def mcp_inventory(endpoint):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(endpoint) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return {t.name for t in result.tools}


def verify_toolbox(version, endpoint):
    tools = version['tools']
    if len(tools) != 1 or tools[0].get('type') != 'mcp':
        raise ValueError('Unexpected Toolbox tool definition')
    t = tools[0]
    if t.get('server_url') != endpoint or t.get('require_approval') != APPROVAL or t.get('server_label') != 'reasonfuse-operations':
        raise ValueError('Toolbox endpoint/approval/server label mismatch')


def create_owned_session(m, p, version):
    from azure.ai.projects.models import VersionRefIndicator
    identifier = uuid.uuid4().hex + uuid.uuid4().hex
    m['sessions'].append(identifier)
    m.setdefault('session_versions', {})[identifier] = version
    save(m)  # intent survives an ambiguous create reply
    session = p.agents.create_session(m['agent'], agent_session_id=identifier,
        version_indicator=VersionRefIndicator(agent_version=version))
    if session.agent_session_id != identifier:
        m['sessions'].append(session.agent_session_id)
        m['session_versions'][session.agent_session_id] = version
        save(m)
        raise ValueError('Session ID differs from explicitly requested ID; cleanup required')
    for attempt in range(120):
        if session.status in {'active', 'idle'}:
            if session.version_indicator.agent_version != version:
                raise ValueError('Session readback is not pinned to the requested concrete version')
            return identifier
        if session.status in {'failed', 'deleted', 'expired'}:
            raise RuntimeError('Pinned session is not runnable: ' + str(session.status))
        time.sleep(5)
        session = p.agents.get_session(m['agent'], identifier)
    raise TimeoutError('Pinned session startup not confirmed; do not invoke')


def smoke(m):
    import httpx
    with project(m) as p:
        check_binding(m, p)
        box = p.toolboxes.get(m['toolbox']).as_dict()
        if box['default_version'] != m['toolbox_version']:
            raise ValueError('Published default is not this run\'s Toolbox version')
        verify_toolbox(p.toolboxes.get_version(m['toolbox'], box['default_version']).as_dict(), m['mcp_endpoint'])
    with httpx.Client(timeout=30) as client:
        h = client.get(m['fixture_base'] + '/healthz'); h.raise_for_status()
        s = client.get(m['fixture_base'] + '/test/state'); s.raise_for_status()
        snapshot = s.json()
        if snapshot['service_name'] != 'orders':
            raise ValueError('Unexpected fixture')
    if asyncio.run(mcp_inventory(m['mcp_endpoint'])) != EXPECTED_TOOLS:
        raise ValueError('Unexpected MCP inventory (reset/admin must not be tools)')
    m['smoke'] = {'checked_utc': utc(), 'result': 'PASS', 'model_calls': 0, 'snapshot': snapshot}
    save(m)
    print('DEMO_CONFIG_SMOKE=PASS; model_calls=0; end-to-end behavior is exercised by demo-run')


def up(args):
    path = manifest_path(args.run)
    if path.exists():
        raise FileExistsError('Run already exists; use smoke/down or a new RunId, never overwrite ownership')
    m = {'schema': 'reasonfuse-demo-v1', 'run': args.run, 'owner': uuid.uuid4().hex, 'created_utc': utc(),
         'source_commit': command(['git', 'rev-parse', 'HEAD'], json_output=False).strip(),
         'resource_group': 'rg-reasonfuse-demo-' + args.run, 'location': 'australiaeast',
         'sessions': [], 'expected_resources': [], 'status': 'PREPARING', **settings(args)}
    # Validate local Docker and existing Foundry wiring before creating paid resources.
    command(['docker', 'version', '--format', '{{.Server.Version}}'], json_output=False)
    with project(m) as p:
        check_binding(m, p)
        m['prior_toolbox_version'] = p.toolboxes.get(m['toolbox']).default_version
    if az(m, 'group', 'exists', '--name', m['resource_group']):
        raise ValueError('Resource group already exists; no adoption or deletion permitted')
    prefix = f"/subscriptions/{m['subscription']}/resourceGroups/{m['resource_group']}/providers/"
    suffix = hashlib.sha256(m['owner'].encode()).hexdigest()[:12]
    m.update({'acr': 'rfdemo' + suffix, 'environment': 'reasonfuse-demo-env',
              'identity': 'reasonfuse-demo-pull', 'app': 'reasonfuse-demo-operations'})
    for provider, name in [('Microsoft.ContainerRegistry/registries', m['acr']),
                           ('Microsoft.App/managedEnvironments', m['environment']),
                           ('Microsoft.ManagedIdentity/userAssignedIdentities', m['identity']),
                           ('Microsoft.App/containerApps', m['app'])]:
        m['expected_resources'].append(prefix + provider + '/' + name)
    save(m)  # Persist intent before the first mutation, including ambiguous CLI failures.
    tags = ['reasonfuse-owner=' + m['owner'], 'reasonfuse-purpose=demo']
    try:
        az(m, 'group', 'create', '--name', m['resource_group'], '--location', m['location'], '--tags', *tags)
        print('Creating one owned ACR, identity and consumption Container Apps fixture...')
        acr = az(m, 'acr', 'create', '--name', m['acr'], '--resource-group', m['resource_group'], '--sku', 'Basic', '--admin-enabled', 'false', '--tags', *tags)
        login = az(m, 'acr', 'login', '--name', m['acr'], '--expose-token')
        command(['docker', 'login', login['loginServer'], '--username', '00000000-0000-0000-0000-000000000000', '--password-stdin'], json_output=False, input_text=login['accessToken'])
        m['image'] = login['loginServer'] + '/reasonfuse-operations:' + m['run']; save(m)
        try:
            command(['docker', 'build', '--platform', 'linux/amd64', '--tag', m['image'], str(ROOT/'cloud/operations-mcp')], json_output=False)
            command(['docker', 'push', m['image']], json_output=False)
        finally:
            command(['docker', 'logout', login['loginServer']], json_output=False)
        m['image_digest'] = az(m, 'acr', 'repository', 'show', '--name', m['acr'],
                              '--image', 'reasonfuse-operations:' + m['run'], '--query', 'digest')
        m['image'] = login['loginServer'] + '/reasonfuse-operations@' + m['image_digest']
        save(m)
        identity = az(m, 'identity', 'create', '--name', m['identity'], '--resource-group', m['resource_group'], '--tags', *tags)
        role = az(m, 'role', 'assignment', 'create', '--assignee-object-id', identity['principalId'], '--assignee-principal-type', 'ServicePrincipal', '--role', 'AcrPull', '--scope', acr['id'])
        m['role_assignment'] = role['id']; save(m)
        env = az(m, 'containerapp', 'env', 'create', '--name', m['environment'], '--resource-group', m['resource_group'], '--location', m['location'], '--logs-destination', 'none', '--tags', *tags)
        domain = env['properties']['defaultDomain']
        fqdn = m['app'] + '.' + domain
        allowed = fqdn + ',' + fqdn + ':*,127.0.0.1:*,localhost:*'
        app = az(m, 'containerapp', 'create', '--name', m['app'], '--resource-group', m['resource_group'],
                 '--environment', env['id'], '--image', m['image'], '--user-assigned', identity['id'],
                 '--registry-server', login['loginServer'], '--registry-identity', identity['id'],
                 '--ingress', 'external', '--target-port', '8080', '--transport', 'http', '--cpu', '0.25',
                 '--memory', '0.5Gi', '--min-replicas', '1', '--max-replicas', '1', '--env-vars', 'MCP_ALLOWED_HOSTS=' + allowed,
                 '--tags', *tags)
        actual = app['properties']['configuration']['ingress']['fqdn']
        if actual != fqdn:
            raise ValueError('Unexpected FQDN; do not publish a mismatched host allowlist')
        m['fixture_base'] = 'https://' + fqdn; m['mcp_endpoint'] = m['fixture_base'] + '/mcp'; save(m)
        import httpx
        for attempt in range(24):
            try:
                r = httpx.get(m['fixture_base'] + '/healthz', timeout=10)
                r.raise_for_status(); break
            except httpx.HTTPError:
                if attempt == 23: raise
                time.sleep(5)
        with project(m) as p:
            # A new version and explicit publication are separate operations.
            v = p.toolboxes.create_version(m['toolbox'], tools=[{'type': 'mcp', 'server_label': 'reasonfuse-operations',
                'server_url': m['mcp_endpoint'], 'require_approval': APPROVAL}],
                description='Owned bounded ReasonFuse demo ' + m['run'], metadata={'reasonfuse-owner': m['owner']})
            m['toolbox_version'] = v.version; save(m)
            p.toolboxes.update(m['toolbox'], default_version=v.version)
        smoke(m)
        m['status'] = 'READY_FOR_MANUAL_DEMO'; save(m)
        print(json.dumps({k: m[k] for k in ['resource_group', 'mcp_endpoint', 'agent', 'agent_version', 'toolbox_version']}, indent=2))
    except BaseException:
        m['status'] = 'UP_FAILED_CLEANUP_REQUIRED'; save(m)
        print('Preserved ownership. Run demo-down for RunId ' + m['run'], file=sys.stderr)
        raise


def validate_owned_inventory(m, group, resources):
    if group.get('tags', {}).get('reasonfuse-owner') != m['owner']:
        raise ValueError('Group ownership tag mismatch; refusing deletion')
    expected = {s.lower() for s in m['expected_resources']}
    unknown = [r['id'] for r in resources if r['id'].lower() not in expected]
    if unknown:
        raise ValueError('Unexpected resource inside group; stop without deleting: ' + ', '.join(unknown))
    for resource in resources:
        if resource.get('tags', {}).get('reasonfuse-owner') != m['owner']:
            raise ValueError('Resource ownership tag mismatch; refusing deletion')


def discover_owned_versions(m, operations, name, kind):
    """Recover lost create replies using exact owner metadata in one named scope."""
    key = 'owned_' + kind + '_versions'
    discovered = m.setdefault(key, [])
    options = {'include_drafts': True} if kind == 'evaluation' else {}
    for value in operations.list_versions(name, **options):
        metadata = value.metadata or {}
        if metadata.get('reasonfuse-owner') != m['owner']:
            continue
        if value.name != name:
            raise ValueError('Version discovery returned an unexpected named resource')
        version = str(value.version)
        protected = m['agent_version'] if kind == 'evaluation' else m.get('prior_toolbox_version')
        if version == protected:
            raise ValueError('Owner discovery must never adopt a protected baseline version')
        if kind == 'evaluation' and metadata.get('evaluation-arm') not in {'ON', 'OFF'}:
            raise ValueError('Owned Agent version lacks the evaluation-arm marker; reconcile manually')
        if version not in discovered:
            discovered.append(version)
            save(m)  # Persist each discovered identity before any cleanup mutation.


def _delete_version(m, operations, name, version, *, evaluation=False):
    """Recheck ownership immediately before delete and confirm removal afterward."""
    from azure.core.exceptions import ResourceNotFoundError
    value = operations.get_version(name, version)
    metadata = value.metadata or {}
    protected = m['agent_version'] if evaluation else m.get('prior_toolbox_version')
    if version == protected or metadata.get('reasonfuse-owner') != m['owner']:
        raise ValueError('Version ownership mismatch or protected baseline; refusing deletion')
    if evaluation and metadata.get('evaluation-arm') not in {'ON', 'OFF'}:
        raise ValueError('Agent version is not a marked evaluation version')
    operations.delete_version(name, version)
    for attempt in range(24):
        try:
            value = operations.get_version(name, version)
        except ResourceNotFoundError:
            return
        if getattr(value, 'status', None) == 'deleted':
            return
        if attempt == 23:
            raise RuntimeError('Version deletion not confirmed')
        time.sleep(5)


def _delete_session(m, p, identifier):
    session = p.agents.get_session(m['agent'], identifier)
    if session.version_indicator.agent_version != m.get('session_versions', {}).get(identifier, m['agent_version']):
        raise ValueError('Recorded session belongs to another agent version')
    if session.status != 'deleted':
        p.agents.delete_session(m['agent'], identifier)
    for attempt in range(24):
        if p.agents.get_session(m['agent'], identifier).status == 'deleted':
            return
        if attempt == 23:
            raise RuntimeError('Session deletion not confirmed')
        time.sleep(5)


def _delete_group(m):
    if az(m, 'group', 'exists', '--name', m['resource_group']):
        group = az(m, 'group', 'show', '--name', m['resource_group'])
        inventory = az(m, 'resource', 'list', '--resource-group', m['resource_group'])
        validate_owned_inventory(m, group, inventory)
        m['cleanup_inventory'] = inventory; save(m)
        az(m, 'group', 'delete', '--name', m['resource_group'], '--yes', '--no-wait')
        for attempt in range(120):
            if not az(m, 'group', 'exists', '--name', m['resource_group']):
                break
            if attempt == 119:
                raise RuntimeError('Group deletion not yet confirmed; rerun down to read status')
            time.sleep(5)
    m['resource_group_exists'] = False


def down(m):
    """Finish independent safe cleanup even if another service is unavailable."""
    from azure.core.exceptions import ResourceNotFoundError
    steps = []

    def attempt(label, action, *, absent=(ResourceNotFoundError,)):
        try:
            action()
            result = {'step': label, 'result': 'PASS'}
        except absent:
            result = {'step': label, 'result': 'ALREADY_ABSENT'}
        except Exception as error:
            # Error messages can contain service URLs or request details. Persist
            # only the exception class; stage names identify the failed action.
            result = {'step': label, 'result': 'FAIL', 'error_type': type(error).__name__}
        steps.append(result)
        m['cleanup_steps'] = steps
        save(m)
        return result['result'] != 'FAIL'

    def cleanup_foundry():
        with project(m) as p:
            attempt('discover-toolbox-versions', lambda: discover_owned_versions(m, p.toolboxes, m['toolbox'], 'toolbox'))
            attempt('discover-evaluation-versions', lambda: discover_owned_versions(m, p.agents, m['agent'], 'evaluation'))
            toolbox_versions = set(m.get('owned_toolbox_versions', []))
            if m.get('toolbox_version'):
                toolbox_versions.add(m['toolbox_version'])

            def restore_default():
                current = p.toolboxes.get(m['toolbox']).default_version
                if current not in toolbox_versions | {m['prior_toolbox_version']}:
                    raise ValueError('Toolbox default changed outside this run; reconcile its binding manually')
                if current in toolbox_versions:
                    value = p.toolboxes.get_version(m['toolbox'], current)
                    if (value.metadata or {}).get('reasonfuse-owner') != m['owner']:
                        raise ValueError('Active Toolbox version ownership mismatch')
                    p.toolboxes.update(m['toolbox'], default_version=m['prior_toolbox_version'])
                if p.toolboxes.get(m['toolbox']).default_version != m['prior_toolbox_version']:
                    raise ValueError('Toolbox restore readback failed')

            restored = attempt('restore-toolbox-default', restore_default) if toolbox_versions else True

            if m.get('prior_agent_version_selector'):
                def restore_agent_selector():
                    from azure.ai.projects.models import AgentEndpointConfig, FixedRatioVersionSelectionRule, VersionSelector
                    previous = m['prior_agent_version_selector']['version_selection_rules']
                    if len(previous) != 1 or previous[0]['traffic_percentage'] != 100:
                        raise ValueError('Unexpected original Agent version selector')
                    wanted = previous[0]['agent_version']
                    current = p.agents.get(m['agent']).as_dict()['agent_endpoint']['version_selector']['version_selection_rules']
                    if len(current) != 1 or current[0]['agent_version'] not in ({wanted} | set(m.get('evaluation_versions', {}).values())):
                        raise ValueError('Agent selector changed outside this run')
                    if current[0]['agent_version'] != wanted:
                        p.agents.update_details(m['agent'], agent_endpoint=AgentEndpointConfig(
                            version_selector=VersionSelector(version_selection_rules=[
                                FixedRatioVersionSelectionRule(agent_version=wanted, traffic_percentage=100)])))
                    actual = p.agents.get(m['agent']).as_dict()['agent_endpoint']['version_selector']['version_selection_rules']
                    if len(actual) != 1 or actual[0]['agent_version'] != wanted:
                        raise ValueError('Original Agent selector restore readback failed')
                attempt('restore-agent-selector', restore_agent_selector)
            if restored:
                deleted = [attempt('toolbox-version:' + version, lambda v=version:
                    _delete_version(m, p.toolboxes, m['toolbox'], v)) for version in sorted(toolbox_versions)]
                m['toolbox_removed'] = all(deleted)
            for identifier in m['sessions']:
                attempt('session:' + identifier, lambda i=identifier: _delete_session(m, p, i))
            if m.get('conversations'):
                import openai

                def cleanup_conversations():
                    def delete_conversation(identifier):
                        scope = m.get('conversation_scopes', {}).get(identifier, 'project')
                        if scope not in {'project', 'agent'}:
                            raise ValueError('Unknown conversation scope')
                        with p.get_openai_client(agent_name=m['agent'] if scope == 'agent' else None) as client:
                            client.conversations.delete(identifier)
                            try:
                                client.conversations.retrieve(identifier)
                            except openai.NotFoundError:
                                return
                            raise RuntimeError('Conversation deletion not confirmed')
                    for identifier in m['conversations']:
                        attempt('conversation:' + identifier, lambda i=identifier: delete_conversation(i),
                            absent=(openai.NotFoundError,))
                attempt('conversation-client', cleanup_conversations)
            versions = set(m.get('owned_evaluation_versions', [])) | set(m.get('evaluation_versions', {}).values())
            for version in sorted(versions):
                attempt('evaluation-version:' + version, lambda v=version:
                    _delete_version(m, p.agents, m['agent'], v, evaluation=True))

    # A missing/unreachable Foundry project does not prevent owner/tag-checked
    # deletion of the independently owned billable fixture resources.
    attempt('foundry-client', cleanup_foundry, absent=())
    attempt('resource-group', lambda: _delete_group(m), absent=())
    failed = [item for item in steps if item['result'] == 'FAIL']
    m['cleanup_result'] = 'PARTIAL' if failed and any(item['result'] != 'FAIL' for item in steps) else 'FAIL' if failed else 'PASS'
    m['status'] = 'CLEANUP_' + m['cleanup_result'] if failed else 'DELETED'
    m['cleanup_utc'] = utc()
    m.setdefault('cleanup_history', []).append({'timestamp_utc': m['cleanup_utc'], 'result': m['cleanup_result'], 'steps': steps})
    save(m)
    print('DEMO_CLEANUP=' + m['cleanup_result'] + '; consult ownership.json cleanup_steps for per-resource readback')
    if failed:
        raise RuntimeError('Cleanup incomplete: ' + ', '.join(item['step'] for item in failed))


def plan(args):
    manifest_path(args.run)
    print(json.dumps({'mode': 'DRY_RUN', 'action': args.action, 'run': args.run,
        'resource_group': 'rg-reasonfuse-demo-' + args.run, 'owned_resources': ['ACR Basic', 'managed identity', 'Container Apps environment (no logs workspace)', 'Container App 1..1 replicas until demo-down'],
        'reused': ['reason-fuse project', 'gpt-5-mini', 'reasonfuse v' + getattr(args, 'agent_version', '10'), 'operations-tools'],
        'cloud_calls': 0, 'model_calls': 0, 'cleanup': 'Restore prior Toolbox and Agent selector; delete exact recorded sessions; verify owner tags/inventory then delete exact owned group and read back.',
        'execute': 'Explicit --execute required; cloud execution incurs charges.'}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['up', 'smoke', 'run', 'down'])
    parser.add_argument('--run', required=True)
    parser.add_argument('--story', choices=['A', 'B', 'C'], default='A')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--subscription'); parser.add_argument('--project-endpoint'); parser.add_argument('--responses-endpoint')
    parser.add_argument('--agent-version', default='10', help='Concrete runtime version; must retain verified v10 package hash')
    args = parser.parse_args()
    if not args.execute:
        plan(args); return
    if args.action == 'up': up(args)
    elif args.action == 'smoke': smoke(load(args.run))
    elif args.action == 'down': down(load(args.run))
    else:
        from demo_stories import run_story
        asyncio.run(run_story(load(args.run), args.story))


if __name__ == '__main__':
    main()
