"""Process-local coordination; none of these objects enter serialized state."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any
from weakref import WeakKeyDictionary


@dataclass
class SessionLocks:
    loop: asyncio.AbstractEventLoop
    run: asyncio.Lock = field(default_factory=asyncio.Lock)
    dispatch: asyncio.Lock = field(default_factory=asyncio.Lock)


_LOCKS: WeakKeyDictionary = WeakKeyDictionary()


def session_locks(session) -> SessionLocks:
    """One live AgentSession, one process/event loop; reject cross-loop use."""
    if session is None:
        raise RuntimeError("ReasonFuse requires an AgentSession")
    loop = asyncio.get_running_loop()
    locks = _LOCKS.get(session)
    if locks is None:
        locks = SessionLocks(loop)
        _LOCKS[session] = locks
    elif locks.loop is not loop:
        raise RuntimeError("A live ReasonFuse session must stay on one event loop")
    return locks


@dataclass
class RuntimeTurn:
    tools: dict[str, Any] = field(default_factory=dict)


CURRENT_TURN: ContextVar[RuntimeTurn | None] = ContextVar("reasonfuse_turn", default=None)
