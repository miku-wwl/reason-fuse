"""Capture deployed configuration with a strict whitelist of nonsecret fields."""

import json
import os
import platform
import subprocess
import shutil
import hashlib
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import EVIDENCE_ROOT, Evidence


def main(evidence):
    azd = ROOT / ".tools" / "azd-1.33.0" / "azd-windows-amd64.exe"
    def command(argv):
        output = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
        return output.strip()
    packages = ["agent-framework-core", "agent-framework-foundry", "agent-framework-foundry-hosting",
                "azure-ai-projects", "azure-identity", "azure-ai-agentserver-responses"]
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "region": os.environ["AZURE_LOCATION"], "python_local": platform.python_version(),
        "packages": {name: version(name) for name in packages},
        "terraform": json.loads(command(["terraform", "-chdir=infra", "version", "-json"])),
        "azd": command([str(azd), "version"]),
        "extensions": json.loads(command([str(azd), "ext", "list", "--output", "json"])),
        "uv": command(["uv", "--version"]),
        "dependency_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                              ["pyproject.toml", "uv.lock", "requirements.txt", "scripts/bootstrap.ps1", "infra/.terraform.lock.hcl"]},
        "subscription_id": command([shutil.which("az"), "account", "show", "--query", "id", "-o", "tsv"]),
        "model": json.loads(command([shutil.which("az"), "cognitiveservices", "account", "deployment", "show",
                                     "-g", os.environ["AZURE_RESOURCE_GROUP"], "-n", "cog-cce5b59dd73ad",
                                     "--deployment-name", "gpt-5-mini", "--query", "{name:name,sku:sku,model:properties.model,state:properties.provisioningState}", "-o", "json"])),
        "agents": [],
    }
    exported = command(["uv", "export", "--frozen", "--no-dev", "--no-emit-project", "--no-hashes"])
    def pins(text):
        return sorted(line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#"))
    assert pins(exported) == pins((ROOT / "requirements.txt").read_text()), "Frozen dependency export mismatch"
    result["frozen_export_matches"] = True
    assert result["subscription_id"] == "7c73b89d-485e-43a9-8d66-b12b766d567f"
    assert result["terraform"]["terraform_version"] == "1.14.0"
    assert result["terraform"]["provider_selections"] == {
        "registry.terraform.io/azure/azapi": "2.12.0", "registry.terraform.io/hashicorp/azurerm": "5.4.0"}
    assert result["uv"].startswith("uv 0.11.16 ") and "azd version 1.33.0 " in result["azd"]
    extensions = {item["id"]: item["installedVersion"] for item in result["extensions"]}
    for name, pin in {"azure.ai.agents": "1.0.0-beta.13", "azure.ai.projects": "1.0.0-beta.9", "azure.ai.toolboxes": "1.0.0-beta.6"}.items():
        assert extensions[name] == pin
    assert result["model"]["model"]["version"] == "2025-08-07"
    assert result["model"]["model"]["name"] == "gpt-5-mini"
    assert result["model"]["sku"]["name"] == "GlobalStandard" and result["model"]["sku"]["capacity"] == 10
    result["resources"] = json.loads(command([shutil.which("az"), "resource", "list", "-g", os.environ["AZURE_RESOURCE_GROUP"],
                                             "--query", "[].{name:name,type:type,location:location,sku:sku.name}", "-o", "json"]))
    assert all(item["location"] in {"australiaeast", "global"} for item in result["resources"])
    for role in ["stable", "candidate"]:
        response = subprocess.run([str(azd), "ai", "agent", "show", role, "--output", "json"],
                                  cwd=ROOT, capture_output=True, text=True)
        if response.returncode:
            evidence.write("RESULT", status="FAIL", role=role, exit_code=response.returncode)
            raise RuntimeError(f"Cannot resolve {role}")
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
    assert all(agent["status"] == "active" for agent in result["agents"])
    assert len({agent["code_configuration"]["content_hash"] for agent in result["agents"]}) == 1
    identity = json.loads((ROOT / "src/reasonfuse/validation/build_identity.json").read_text())
    manifests = []
    for path in sorted((EVIDENCE_ROOT / "runs").rglob("*-source-identity.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry["event"] == "PACKAGE_MANIFEST" and entry["build"] == identity:
                manifests.append((path, entry))
    assert manifests, "No audited native package for this build"
    package_path, package = manifests[-1]
    assert all(agent["code_configuration"]["content_hash"] == package["sha256"] for agent in result["agents"]), "Hosted hash differs from audited ZIP SHA-256"
    evidence.write("EXACT_DEPLOYED_PACKAGE", manifest_evidence=str(package_path), zip_sha256=package["sha256"],
                   source_manifest_sha256=identity["source_manifest_sha256"], roles=["stable", "candidate"])
    evidence.write("RESULT", status="PASS", exit_code=0)
    (EVIDENCE_ROOT / "environment-current.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"ENVIRONMENT_CAPTURED {evidence.path}")


if __name__ == "__main__":
    evidence = Evidence("environment")
    try:
        main(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error), exit_code=1)
        raise
