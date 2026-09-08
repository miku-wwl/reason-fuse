"""One fixed, sequential acceptance batch, stopping at the first failed command."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import Evidence


def main():
    label = sys.argv[1]
    evidence = Evidence("batch-" + label)
    python = str(ROOT / ".venv/Scripts/python.exe")
    commands = [
        ["pwsh", "-File", "scripts/preflight.ps1"],
        [python, "scripts/capture_environment.py"],
        [python, "tests/integration/history_session.py"],
        *[[python, "tests/integration/toolbox_interception.py", case] for case in ["allow", "block", "allow", "block"]],
        *[[python, "tests/integration/approval.py", case] for case in ["approve", "deny", "binding"]],
        [python, "tests/integration/apim.py", "affinity"],
        [python, "tests/integration/apim.py", "new_session_control", "--samples", "60"],
        [python, "tests/integration/apim.py", "sse"],
        [python, "scripts/capture_telemetry.py"],
    ]
    evidence.write("FIXED_BATCH", label=label, commands=commands, fresh_client_cohort_size=60,
                   retry_policy="none; stop and retain failures")
    for index, command in enumerate(commands):
        status = subprocess.call([python, "scripts/verification_command.py", f"{label}-{index:02}", "--", *command], cwd=ROOT)
        evidence.write("COMMAND_RESULT", index=index, argv=command, exit_code=status)
        if status:
            evidence.write("RESULT", status="FAIL", exit_code=status)
            raise SystemExit(status)
    evidence.write("RESULT", status="PASS", exit_code=0)
    print(f"BATCH_PASS {label} {evidence.path}")


if __name__ == "__main__":
    main()
