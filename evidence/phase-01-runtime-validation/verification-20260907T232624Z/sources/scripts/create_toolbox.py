"""Provision a real Foundry Toolbox; initially expose only dns_resolution."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiToolboxTool, OpenApiFunctionDefinition, OpenApiAnonymousAuthDetails
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
        toolbox = project.toolboxes.create_version(
            name=config["name"], description=config["description"],
            tools=[OpenApiToolboxTool(
                openapi=OpenApiFunctionDefinition(
                    name=config["openapi_name"], spec=spec, auth=OpenApiAnonymousAuthDetails()
                ),
                tool_configs=config["tool_configs"],
            )],
        )
        endpoint = (f"{os.environ['FOUNDRY_PROJECT_ENDPOINT']}/toolboxes/{toolbox.name}"
                    f"/versions/{toolbox.version}/mcp?api-version=v1")
        evidence.write("CREATED", name=toolbox.name, version=toolbox.version,
                        endpoint=endpoint, openapi_spec=spec, exit_code=0)
    azd = ROOT / ".tools" / "azd-1.33.0" / "azd-windows-amd64.exe"
    subprocess.run([str(azd) if azd.exists() else "azd", "env", "set", "TOOLBOX_ENDPOINT", endpoint],
                   cwd=ROOT, check=True)
    print(json.dumps({"toolbox": config["name"], "endpoint": endpoint, "evidence": str(evidence.path)}))


if __name__ == "__main__":
    main()
