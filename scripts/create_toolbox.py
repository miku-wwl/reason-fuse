"""Provision a real Foundry Toolbox; initially expose only dns_resolution."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    MCPToolboxTool,
    OpenApiToolboxTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,
)
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import Evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-restart", action="store_true")
    args = parser.parse_args()
    config_path = ROOT / "config" / "toolbox" / "operations.yaml"
    config = yaml.safe_load(config_path.read_text())
    spec = yaml.safe_load((config_path.parent / config["spec_file"]).read_text())
    spec["servers"] = [{"url": os.environ["OPERATIONS_ENDPOINT"]}]
    if not args.include_restart:
        del spec["paths"]["/restart-service"]
    evidence = Evidence("toolbox-provision")
    with AzureCliCredential() as credential, AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential
    ) as project:
        tools = [OpenApiToolboxTool(
            openapi=OpenApiFunctionDefinition(
                name=config["openapi_name"], spec=spec, auth=OpenApiAnonymousAuthDetails()
            ),
            tool_configs=config["tool_configs"],
        )]
        iq_endpoint = os.environ.get("FOUNDRY_IQ_MCP_ENDPOINT")
        iq_connection = os.environ.get("FOUNDRY_IQ_CONNECTION", "reasonfuse-phase4-iq")
        if iq_endpoint:
            tools.append(MCPToolboxTool(
                name="foundry-iq",
                server_label="foundry_iq",
                server_url=iq_endpoint,
                project_connection_id=iq_connection,
                allowed_tools=["knowledge_base_retrieve"],
                require_approval="never",
                server_description=(
                    "Native Azure AI Search Knowledge Base MCP retrieval for the "
                    "version-pinned ReasonFuse Phase 4 source."
                ),
            ))
        toolbox = project.toolboxes.create_version(
            name=config["name"], description=config["description"],
            tools=tools,
        )
        endpoint = (f"{os.environ['FOUNDRY_PROJECT_ENDPOINT']}/toolboxes/{toolbox.name}"
                    f"/versions/{toolbox.version}/mcp?api-version=v1")
        evidence.write("CREATED", name=toolbox.name, version=toolbox.version,
                        endpoint=endpoint, openapi_spec=spec,
                        native_iq_mcp=bool(iq_endpoint),
                        iq_connection=iq_connection if iq_endpoint else None,
                        exit_code=0)
    azd = ROOT / ".tools" / "azd-1.33.0" / "azd-windows-amd64.exe"
    azd_command = str(azd) if azd.exists() else "azd"
    environment = os.environ.get("AZURE_ENV_NAME")
    if not environment:
        environment = subprocess.run(
            [azd_command, "env", "get-value", "AZURE_ENV_NAME"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    subprocess.run(
        [azd_command, "env", "set", "--environment", environment, "TOOLBOX_ENDPOINT", endpoint],
        cwd=ROOT, check=True,
    )
    print(json.dumps({"toolbox": config["name"], "endpoint": endpoint, "evidence": str(evidence.path)}))


if __name__ == "__main__":
    main()
