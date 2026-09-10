"""Provision the bounded Native Foundry IQ MCP path before agent deployment.

This is intentionally separate from ``phase4_cloud_verify.py`` so a clean-start
run can create the Search/Knowledge Base/Foundry connection first, publish the
MCP endpoint into the azd environment, and only then deploy Stable/Candidate.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AZ = shutil.which("az.cmd") or shutil.which("az") or "az"

from scripts.support.validation import Evidence  # noqa: E402


def checked(args: list[str], *, json_output: bool = False) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def azd_path() -> str:
    local = ROOT / ".tools" / "azd-1.33.0" / "azd-windows-amd64.exe"
    return str(local) if local.exists() else "azd"


def set_azd(name: str, value: str) -> None:
    environment = os.environ.get("AZURE_ENV_NAME")
    if not environment:
        probe = subprocess.run(
            [azd_path(), "env", "get-value", "AZURE_ENV_NAME"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        environment = probe.stdout.strip()
    command = [azd_path(), "env", "set", "--environment", environment, name, value]
    subprocess.run(command, cwd=ROOT, check=True)


def ensure_role(principal_id: str, principal_type: str, role: str, scope: str) -> None:
    existing = subprocess.run(
        [
                AZ, "role", "assignment", "list", "--assignee-object-id", principal_id,
            "--scope", scope, "--role", role, "--query", "[0].id", "-o", "tsv",
        ], cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not existing:
        subprocess.run(
            [
                AZ, "role", "assignment", "create", "--assignee-object-id", principal_id,
                "--assignee-principal-type", principal_type, "--role", role, "--scope", scope,
            ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-service-name", required=True)
    parser.add_argument("--search-sku", default="basic", choices=["basic", "standard"])
    args = parser.parse_args()

    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    project_id = os.environ["AZURE_AI_PROJECT_ID"]
    subscription = os.environ["AZURE_SUBSCRIPTION_ID"]
    service_id = ""
    found = subprocess.run(
        [AZ, "search", "service", "show", "--resource-group", resource_group,
         "--name", args.search_service_name, "--query", "id", "-o", "tsv"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if found.returncode != 0 or not found.stdout.strip():
        subprocess.run(
            [
                AZ, "search", "service", "create", "--resource-group", resource_group,
                "--name", args.search_service_name, "--location", "australiaeast",
                "--sku", args.search_sku, "--replica-count", "1", "--partition-count", "1",
                "--identity-type", "SystemAssigned", "--auth-options", "aadOrApiKey",
                "--aad-auth-failure-mode", "http401WithBearerChallenge",
                "--public-network-access", "enabled", "--semantic-search", "free",
            ], cwd=ROOT, check=True,
        )
    service_json = json.loads(checked([
        AZ, "search", "service", "show", "--resource-group", resource_group,
        "--name", args.search_service_name, "-o", "json",
    ]))
    service_id = service_json["id"]
    endpoint = service_json["endpoint"].rstrip("/")

    principal = checked([AZ, "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"])
    ensure_role(principal, "User", "Search Index Data Contributor", service_id)
    project_principal = checked([AZ, "resource", "show", "--ids", project_id,
                                 "--query", "identity.principalId", "-o", "tsv"])
    if project_principal:
        ensure_role(project_principal, "ServicePrincipal", "Search Index Data Reader", service_id)

    set_azd("SEARCH_SERVICE_NAME", args.search_service_name)
    set_azd("SEARCH_ENDPOINT", endpoint)
    set_azd("SEARCH_INDEX", "reasonfuse-phase4-index")
    set_azd("KNOWLEDGE_SOURCE", "reasonfuse-phase4-ks")
    set_azd("KNOWLEDGE_BASE", "reasonfuse-phase4-kb")

    # Import only after SEARCH_ENDPOINT exists because the verification module
    # deliberately reads its required cloud coordinates at import time.
    os.environ.update({
        "SEARCH_ENDPOINT": endpoint,
        "SEARCH_SERVICE_NAME": args.search_service_name,
        "SEARCH_INDEX": "reasonfuse-phase4-index",
        "KNOWLEDGE_SOURCE": "reasonfuse-phase4-ks",
        "KNOWLEDGE_BASE": "reasonfuse-phase4-kb",
    })
    from scripts.phase4_cloud_verify import create_project_connection, native_iq  # noqa: E402

    evidence = Evidence("phase4_native_iq_setup")
    iq = native_iq(evidence)
    connection = create_project_connection(evidence)
    set_azd("FOUNDRY_IQ_MCP_ENDPOINT", connection["target"])
    result = {
        "status": "PASS",
        "search_service": args.search_service_name,
        "search_endpoint": endpoint,
        "search_service_id": service_id,
        "native_iq": iq,
        "foundry_project_connection": connection,
        "mcp_endpoint_published_to_azd": True,
        "evidence": str(evidence.path),
    }
    evidence.write("RESULT", **result)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
