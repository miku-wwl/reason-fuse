"""Reset only the deterministic API and hosted sessions recorded by these validators."""

import json
import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import EVIDENCE_ROOT, Evidence, Operations


def reset(evidence):
    operations = Operations(evidence)
    operations.reset()
    operations.assert_counts({})
    recorded = set()
    for path in EVIDENCE_ROOT.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            body = entry.get("body", {})
            if entry.get("event") == "RESPONSE" and isinstance(body, dict) and body.get("agent_session_id"):
                recorded.add(body["agent_session_id"])
            if entry.get("event") == "SSE_EVENT" and isinstance(body, dict):
                session = body.get("response", {}).get("agent_session_id")
                if session:
                    recorded.add(session)
    deleted = []
    already_deleted = 0
    with AzureCliCredential(process_timeout=60) as credential, AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential
    ) as project:
        for agent in ["reasonfuse-phase1-stable", "reasonfuse-phase1-candidate"]:
            # Read all pages before deleting; do not remove a pagination cursor.
            sessions = list(project.agents.list_sessions(agent_name=agent))
            for session in sessions:
                if session.agent_session_id in recorded:
                    if session.status == "deleted":
                        already_deleted += 1
                        continue
                    project.agents.delete_session(agent_name=agent, session_id=session.agent_session_id)
                    deleted.append(session.agent_session_id)
                    evidence.write("DELETED_TEST_SESSION", agent=agent, session_id=session.agent_session_id)
            remaining = [{"session_id": session.agent_session_id, "status": session.status}
                         for session in project.agents.list_sessions(agent_name=agent)
                         if session.agent_session_id in recorded]
            # The native API can retain metadata rows with terminal status deleted.
            # Absence or explicit deleted status is success; every other status fails.
            evidence.write("SESSION_RESET_READBACK", agent=agent, recorded_sessions_still_listed=remaining)
            assert all(session["status"] == "deleted" for session in remaining), f"Non-deleted recorded test sessions remain for {agent}"
    # Evidence is retained. The next test creates fresh native conversation/provider/
    # approval state. There is no separate fault state or custom approval database.
    artifact = ROOT / ".azure" / "rf-phase1-aue" / "validation-last-run.json"
    artifact.unlink(missing_ok=True)
    operations.assert_counts({})
    evidence.write("ASSERTIONS", recorded_sessions=len(recorded), deleted_sessions=len(deleted),
                   already_deleted_sessions=already_deleted,
                   recorded_non_deleted_sessions_remaining=0, external_counts={},
                   local_artifact_absent=not artifact.exists())
    evidence.write("RESULT", status="RESET_COMPLETE", exit_code=0)
    print(f"RESET_COMPLETE {evidence.path}")


if __name__ == "__main__":
    evidence = Evidence("reset")
    try:
        reset(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error), exit_code=1)
        raise
