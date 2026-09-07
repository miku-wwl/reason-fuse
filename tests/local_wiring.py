"""Verify local wiring only; never use this result as hosted integration PASS."""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_framework import AgentContext, AgentSession, Content, FunctionInvocationContext, Message, tool
from reasonfuse.validation.middleware import StreamingProbeMiddleware, ValidationMiddleware


async def check():
    calls = 0

    @tool
    def operations___dns_resolution(hostname: str) -> str:
        return hostname

    async def execute():
        nonlocal calls
        calls += 1
        context.result = [Content.from_text('{"status":"INCONCLUSIVE"}')]

    session = AgentSession()
    context = FunctionInvocationContext(operations___dns_resolution,
        {"body": {"hostname": "blocked.reasonfuse.local"}}, session=session)
    await ValidationMiddleware().process(context, execute)
    assert calls == 0 and context.result["status"] == "BLOCKED"
    context = FunctionInvocationContext(operations___dns_resolution,
        {"body": {"hostname": "api.reasonfuse.local"}}, session=session)
    await ValidationMiddleware().process(context, execute)
    assert calls == 1
    assert "INCONCLUSIVE" in session.state["reasonfuse"]["middleware_events"][-1]["result"]
    os.environ["RELEASE_ROLE"] = "stable"
    probe = AgentContext(agent=None, messages=[Message("user", ["RF_RELEASE_PROBE"])], stream=True)
    async def forbidden():
        raise AssertionError("Deterministic probe reached model execution")
    await StreamingProbeMiddleware().process(probe, forbidden)
    chunks = [update.text async for update in probe.result]
    assert chunks == ['{"release_role": "stable"}']
    print("LOCAL_WIRING_PASS (not hosted integration validation)")


if __name__ == "__main__":
    asyncio.run(check())
