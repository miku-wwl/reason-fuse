"""Capture deployed configuration with a strict whitelist of nonsecret fields."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import EVIDENCE_ROOT, Evidence


def main():
    evidence = Evidence("environment")
    azd = ROOT / ".tools" / "azd-1.33.0" / "azd-windows-amd64.exe"
    packages = ["agent-framework-core", "agent-framework-foundry", "agent-framework-foundry-hosting",
                "azure-ai-projects", "azure-identity", "azure-ai-agentserver-responses"]
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "region": os.environ["AZURE_LOCATION"], "python_local": platform.python_version(),
        "packages": {name: version(name) for name in packages},
        "terraform": "1.14.0", "azurerm": "5.4.0", "azapi": "2.12.0", "azd": "1.33.0",
        "agents": [],
    }
    for role in ["stable", "candidate"]:
        response = subprocess.run([str(azd), "ai", "agent", "show", role, "--output", "json"],
                                  cwd=ROOT, capture_output=True, text=True)
        if response.returncode:
            result["agents"].append({"role": role, "status": "NOT VERIFIED", "exit_code": response.returncode})
            continue
        raw = json.loads(response.stdout)
        definition = raw["definition"]
        result["agents"].append({
            "name": raw["name"], "version": raw["version"], "status": raw["status"],
            "protocols": definition.get("protocol_versions"),
            "code_configuration": definition.get("code_configuration"),
            "env": {key: value for key, value in definition.get("environment_variables", {}).items()
                    if key in {"RELEASE_ROLE", "AZURE_AI_MODEL_DEPLOYMENT_NAME", "TOOLBOX_ENDPOINT",
                               "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"}},
            "endpoint": raw.get("agent_endpoints", {}).get("responses"),
        })
    evidence.write("ENVIRONMENT", **result)
    (EVIDENCE_ROOT / "environment-current.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"ENVIRONMENT_CAPTURED {evidence.path}")


if __name__ == "__main__":
    main()
