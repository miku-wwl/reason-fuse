"""Merge successful low-rate-limit retries into a full Phase 3 model run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--retry", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    retry = json.loads(Path(args.retry).read_text(encoding="utf-8"))
    original_error_count = base.get("errors")
    retry_by_key = {
        (row["scenario_id"], row["repetition"]): row
        for row in retry["results"]
        if row.get("status") == "completed" and not row.get("error_message")
    }

    results = []
    recovered = []
    for original in base["results"]:
        key = (original["scenario_id"], original["repetition"])
        replacement = retry_by_key.get(key) if original.get("status") != "completed" else None
        if replacement is not None:
            recovered.append({"original": original, "replacement": replacement})
            results.append(replacement)
        else:
            results.append(original)

    completed = [row for row in results if row.get("status") == "completed" and not row.get("error_message")]
    errors = [row for row in results if row.get("status") != "completed" or row.get("error_message")]
    base["results"] = results
    base["completed"] = len(completed)
    base["errors"] = len(errors)
    base["threshold_passed"] = sum(bool(row.get("passed")) for row in results)
    base["status"] = "PASS" if len(results) == 300 and not errors else "PARTIAL"
    base["full_300_run"] = "RUN" if len(results) == 300 else base.get("full_300_run")
    base["recovery"] = {
        "method": "low_concurrency_retry_merge",
        "base_status": "PARTIAL",
        "base_errors": original_error_count,
        "retry_source": str(Path(args.retry)),
        "recovered_error_count": len(recovered),
        "recovered": recovered,
    }
    Path(args.output).write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": base["status"], "completed": base["completed"], "errors": base["errors"],
                      "threshold_passed": base["threshold_passed"], "recovered": len(recovered)}))
    return 0 if base["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
