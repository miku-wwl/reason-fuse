"""Observation-only unit checks. These cannot establish hosted acceptance."""
import asyncio
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_framework import AgentSession, ChatContext, Message
from reasonfuse.validation.middleware import HistoryAuditMiddleware
from reasonfuse.validation.session_state import message_summary


async def main():
    session = AgentSession()
    session.state["reasonfuse"] = {"history_audit": True}
    messages = [Message("user", ["RF-HISTORY-abc-T1 hello"])]
    options = {"store": False}
    context = ChatContext(client=None, messages=messages, options=options, session=session)
    before = copy.deepcopy(messages[0].to_dict())
    calls = 0
    async def next_call():
        nonlocal calls
        calls += 1
    await HistoryAuditMiddleware().process(context, next_call)
    assert calls == 1
    assert context.messages is messages and messages[0].to_dict() == before
    assert options == {"store": False} and context.options is options
    event = session.state["reasonfuse"]["chat_requests"][0]
    assert event["store"] is False and event["messages"][0]["markers"] == ["RF-HISTORY-abc-T1"]
    assert "hello" not in str(event), "Raw transcript leaked into audit metadata"
    assert message_summary(Message("assistant", ["RF-HISTORY-abc-T1"]))["markers"] == []
    session.state["reasonfuse"] = {"history_audit": False}
    await HistoryAuditMiddleware().process(context, next_call)
    assert calls == 2 and "chat_requests" not in session.state["reasonfuse"]
    print("LOCAL_HISTORY_AUDIT_PASS (observation-only; not hosted acceptance)")


if __name__ == "__main__":
    asyncio.run(main())
