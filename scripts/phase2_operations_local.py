"""Exercise the Phase 2 deterministic Operations API locally."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "tests" / "support" / "operations_api"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Evidence:
    def __init__(self):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        batch = "local-" + datetime.now(timezone.utc).strftime("%Y%m%d")
        self.path = ROOT / "evidence" / "phase-02-core" / batch / f"{stamp}-operations-api.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event, **fields):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                                     "event": event, **fields}, default=str) + "\n")


def main():
    port = free_port()
    key = uuid.uuid4().hex
    process_env = {**os.environ, "OPERATIONS_ADMIN_KEY": key, "PORT": str(port)}
    evidence = Evidence()
    process = subprocess.Popen([sys.executable, "server.py"], cwd=API_DIR, env=process_env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    base = f"http://127.0.0.1:{port}"
    admin = {"X-Validation-Key": key}
    try:
        for _ in range(50):
            try:
                if httpx.get(base + "/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(.1)
        else:
            raise RuntimeError("Operations API did not become healthy")
        evidence.write("START", endpoint="local_loopback", scenarios=["outcome_failure", "useful_recheck", "retrieval_churn"])
        reset = httpx.post(base + "/reset", headers=admin, timeout=5).json()
        evidence.write("RESET", epoch=reset["epoch"], counts=reset["counts"])

        httpx.post(base + "/scenario", headers=admin, json={"scenario": "outcome_failure"}, timeout=5).raise_for_status()
        failure = httpx.post(base + "/restart-service", json={"service_name": "orders"}, timeout=5).json()
        unhealthy = httpx.post(base + "/service-status", json={"service_name": "orders"}, timeout=5).json()
        assert failure["accepted"] is True and failure["status_code"] == 202
        assert unhealthy["service_health"] == "UNHEALTHY"
        evidence.write("OUTCOME_FAILURE", accepted_status= failure["status_code"], service_health=unhealthy["service_health"])

        httpx.post(base + "/scenario", headers=admin, json={"scenario": "useful_recheck"}, timeout=5).raise_for_status()
        healthy_restart = httpx.post(base + "/restart-service", json={"service_name": "orders"}, timeout=5).json()
        healthy = httpx.post(base + "/service-status", json={"service_name": "orders"}, timeout=5).json()
        assert healthy_restart["accepted"] is True and healthy["service_health"] == "HEALTHY"
        evidence.write("USEFUL_RECHECK", accepted_status=healthy_restart["status_code"], service_health=healthy["service_health"])

        httpx.post(base + "/scenario", headers=admin, json={"scenario": "retrieval_churn"}, timeout=5).raise_for_status()
        retrieval = [httpx.post(base + "/retrieval-fixture", json={"query": query}, timeout=5).json()
                     for query in ["database failure", "db connectivity", "database issue"]]
        assert all(item["retrieval"]["source_keys"] == ["fixture-A", "fixture-B"] for item in retrieval)
        evidence.write("RETRIEVAL_FIXTURE", queries=[item["query"] for item in retrieval],
                       source_keys=retrieval[0]["retrieval"]["source_keys"], foundry_iq="NOT VERIFIED")

        counters = httpx.get(base + "/counters", headers=admin, timeout=5).json()
        assert counters["epoch"] == reset["epoch"] and counters["counts"]
        next_reset = httpx.post(base + "/reset", headers=admin, timeout=5).json()
        assert next_reset["epoch"] != reset["epoch"] and next_reset["counts"] == {}
        evidence.write("ASSERTIONS", first_epoch=reset["epoch"], second_epoch=next_reset["epoch"],
                       reset_counts=next_reset["counts"], admin_key_recorded=False)
        evidence.write("RESULT", status="PASS", exit_code=0, evidence_layer="LOCAL_OPERATIONS_API")
        print(f"PHASE2_OPERATIONS_LOCAL_PASS {evidence.path}")
    except Exception as error:
        evidence.write("RESULT", status="FAIL", exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
