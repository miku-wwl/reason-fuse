"""Pinned native coordination regressions for the demonstrated cloud fork."""

import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from azure.ai.agentserver.core import AgentConfig
from azure.ai.agentserver.core.tasks import LastInputIdPreconditionFailed, TaskContext, multi_turn_task
from azure.ai.agentserver.core.tasks._local_provider import LocalFileTaskProvider
from azure.ai.agentserver.core.tasks._manager import TaskManager, set_task_manager

from reasonfuse.main import ReasonFuseHostServer


class CloudHostingTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_chain_rejects_two_continuations_from_same_head(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(AgentConfig.from_env(), provider=LocalFileTaskProvider(Path(directory)))
            set_task_manager(manager)
            entered, release = asyncio.Event(), asyncio.Event()
            dispatched = []

            @multi_turn_task(name="reasonfuse-cloud-fork-regression", steerable=True)
            async def turn(ctx: TaskContext[str]) -> str:
                if ctx.input != "initial":
                    dispatched.append(ctx.input)
                    entered.set()
                    await release.wait()
                return ctx.input

            try:
                initial = await turn.start(task_id="same-chain", input="initial", input_id="head")
                await initial.result()
                outcomes = await asyncio.gather(*[
                    turn.start(task_id="same-chain", input=label, input_id=label, if_last_input_id="head")
                    for label in ("a", "b")
                ], return_exceptions=True)
                await asyncio.wait_for(entered.wait(), 2)
                self.assertEqual(len(dispatched), 1)
                self.assertEqual(sum(isinstance(value, LastInputIdPreconditionFailed) for value in outcomes), 1)
                release.set()
                for value in outcomes:
                    if not isinstance(value, BaseException):
                        await value.result()
                with self.assertRaises(LastInputIdPreconditionFailed):
                    await turn.start(task_id="same-chain", input="replay", input_id="replay", if_last_input_id="head")
                self.assertEqual(len(dispatched), 1)
            finally:
                release.set()
                await manager.shutdown()
                set_task_manager(None)

    async def test_store_false_cannot_bypass_native_coordination(self):
        host = object.__new__(ReasonFuseHostServer)
        with patch("agent_framework_foundry_hosting.ResponsesHostServer._handle_response") as parent:
            with self.assertRaisesRegex(ValueError, "requires store=true"):
                await anext(host._handle_response({"store": False}, None, asyncio.Event()))
            parent.assert_not_called()
