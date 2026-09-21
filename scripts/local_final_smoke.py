"""One optional real LOCAL model smoke, using an already-loaded model only."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import httpx
from agent_framework import AgentSession,Message
from reasonfuse.local_runtime import LocalOperationsServer,build_local_agent,configure_foundry_local_sdk_compat,reset_operations_fixture


async def run(model):
    configure_foundry_local_sdk_compat()
    calls=0
    original=httpx.AsyncClient.send
    async def local_only(client,request,*args,**kwargs):
        nonlocal calls
        if request.url.host not in {'127.0.0.1','localhost','::1'}:
            raise RuntimeError('This smoke permits only loopback HTTP')
        if request.url.path.endswith('/chat/completions'):
            calls+=1
        return await original(client,request,*args,**kwargs)
    result={'started_utc':datetime.now(timezone.utc).isoformat(),'model':model,
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'azure_model_calls':0,'azure_resources_created':0,'scope':'one real local model happy-path smoke; not Hosted proof'}
    with patch.object(httpx.AsyncClient,'send',local_only),LocalOperationsServer() as fixture:
        reset_operations_fixture(fixture.base_url,mode='verified')
        try:
            bundle=build_local_agent(fixture.base_url,model=model,bootstrap=False,prepare_model=False)
            session=AgentSession()
            first=await asyncio.wait_for(bundle.agent.run('Submit operations___restart_service for service_name exactly orders. Wait for native approval.',
                session=session,options={'tool_choice':{'mode':'required','required_function_name':'operations___restart_service'},'temperature':0,'max_tokens':120}),60)
            approvals=[c for m in first.messages for c in m.contents if c.type=='function_approval_request']
            result['approval_count']=len(approvals)
            if len(approvals)!=1:raise RuntimeError('Expected exactly one native approval')
            result['side_effect_count_before_approval']=session.state.get('reasonfuse_core_v1',{}).get('side_effect_count',0)
            final=await asyncio.wait_for(bundle.agent.run(Message('user',[approvals[0].to_function_approval_response(approved=True)]),
                session=session,options={'temperature':0,'max_tokens':120}),60)
            core=session.state.get('reasonfuse_core_v1',{})
            result['final_text']=final.text
            result['outcome']=core.get('last_postcondition_result')
            result['side_effect_count']=core.get('side_effect_count')
            result['lifecycle']=core.get('action_lifecycle')
            result['status']='PASS' if result['side_effect_count_before_approval']==0 and core.get('side_effect_count')==1 and (core.get('last_postcondition_result') or {}).get('outcome')=='OUTCOME_VERIFIED' else 'FAIL'
        except Exception as error:
            result.update(status='BLOCKED',error={'type':type(error).__name__,'message':str(error)})
    result.update(observed_async_httpx_inference_requests=calls,actual_local_model_call_count=None,
                  instrumentation_limit='Async httpx hook does not cover every transport used by the local SDK; never interpret an observed zero as zero model inference.',
                  completed_utc=datetime.now(timezone.utc).isoformat(),
                  reported_usage=None,cleanup='Ephemeral local HTTP fixture stopped; pre-existing model and daemon retained.')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    target=Path(args.output)
    if target.exists():parser.error('Evidence already exists')
    models=json.loads(subprocess.check_output(['foundry','model','list','--loaded','--output','json'],text=True))['models']
    available=[m for m in models if m.get('supportsToolCalling')]
    if not available:
        result={'status':'NOT RUN','reason':'No already-loaded tool-capable model; no download/load performed','local_inference_http_requests':0,'azure_model_calls':0}
    else:result=asyncio.run(run(available[0]['id']))
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
