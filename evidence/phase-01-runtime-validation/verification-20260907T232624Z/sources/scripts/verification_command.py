"""Durable sanitized command capture; no automatic retry or hidden success."""
import argparse
import os
import re
import subprocess
import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import Evidence


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[0] == "--":
        command = command[1:]
    evidence = Evidence(args.label)
    evidence.write("COMMAND", argv=command)
    sources = [p for folder in ["src", "scripts", "tests"] for p in Path(folder).rglob("*")
               if p.is_file() and p.suffix in {".py", ".ps1", ".json"} and "__pycache__" not in p.parts]
    evidence.write("EXECUTION_SOURCE_HASHES", sha256={p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    secrets = [v for k, v in os.environ.items() if any(s in k.upper() for s in
               ("SECRET", "TOKEN", "PASSWORD", "CONNECTION_STRING", "ADMIN_KEY")) and len(v) > 8]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    for line in process.stdout:
        for secret in secrets:
            line = line.replace(secret, "[REDACTED]")
        line = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line).rstrip()
        evidence.write("OUTPUT", text=line)
        print(line, flush=True)
    status = process.wait()
    evidence.write("RESULT", status="PASS" if status == 0 else "FAIL", exit_code=status)
    print(f"COMMAND_EVIDENCE {evidence.path}", flush=True)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
