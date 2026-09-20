"""Fail-closed admission around the pinned host's session restore/save boundary.

The native task adapter did not serialize explicit conversations in the cloud
gate. A small Foundry State Store record owns each conversation until the host
has saved its AgentSession. No lease expiry, takeover, or operation retry exists.
"""

from dataclasses import dataclass

from azure.ai.agentserver.core.storage import (
    FoundryStorageConflictError, FoundryStoragePreconditionError,
)


class AdmissionRejected(RuntimeError):
    """The request must not restore a session or execute tools."""


@dataclass(frozen=True)
class Admission:
    key: str
    response_id: str
    etag: str
    previous_head: str | None


async def acquire(store, *, conversation_id, previous_response_id, response_id):
    """Atomically own a canonical conversation, independent of Python objects.

    Response aliases avoid deriving authority from routing/partition hints. Old
    previous-response chains without an admission record deliberately fail closed.
    """
    if conversation_id:
        key = "conversation:" + conversation_id
    elif previous_response_id:
        alias = await store.get_item("response:" + previous_response_id)
        if alias is None or not isinstance(alias.value.get("gate"), str):
            raise AdmissionRejected("continuation has no admission record")
        key = alias.value["gate"]
    else:
        key = "root:" + response_id

    prior = await store.get_item(key)
    head = None
    if prior is not None:
        value = prior.value
        if value.get("phase") != "IDLE" or value.get("version") != 1:
            raise AdmissionRejected("conversation is busy or requires reconciliation")
        head = value.get("head")
        if not head or (previous_response_id and head != previous_response_id):
            raise AdmissionRejected("stale continuation cannot obtain execution authority")
    elif previous_response_id:
        raise AdmissionRejected("continuation admission state is missing")

    value = {"version": 1, "phase": "BUSY", "owner": response_id, "head": head}
    try:
        if prior is None:
            owned = await store.create_item(key, value)
        else:
            owned = await store.set_item(key, value, if_match=prior.etag)
    except (FoundryStorageConflictError, FoundryStoragePreconditionError) as error:
        raise AdmissionRejected("another request owns this conversation") from error
    return Admission(key, response_id, owned.etag, head)


async def complete(store, admission):
    """Publish the new head only after the pinned host saved the full session."""
    # A failed/ambiguous alias or head write keeps the gate BUSY. In particular,
    # never delete a gate in finally: the operation may already have happened.
    await store.create_item("response:" + admission.response_id, {"gate": admission.key})
    await store.set_item(admission.key, {
        "version": 1, "phase": "IDLE", "head": admission.response_id,
    }, if_match=admission.etag)
