import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import HostedClient, output_text, run_case
from scripts.source_identity import IDENTITY


def validate(evidence):
    assert os.environ["AZURE_LOCATION"] == "australiaeast"
    project = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    expected_build = {k: v for k, v in json.loads(IDENTITY.read_text()).items() if k != "files"}
    releases = {}
    for role in ["stable", "candidate"]:
        client = HostedClient(evidence, base_url=f"{project}/agents/reasonfuse-phase1-{role}/endpoint/protocols/openai")
        try:
            result = client.turn("RF_RELEASE_PROBE")
            probe = json.loads(output_text(result))
            assert probe["release_role"] == role
            assert probe["build_identity"] == expected_build
            releases[role] = {"probe": probe, "response_id": result["id"],
                              "agent": result.get("agent"), "agent_session_id": result["agent_session_id"]}
        finally:
            client.close()
    client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    try:
        assert json.loads(output_text(client.turn("RF_RELEASE_PROBE")))["release_role"] in {"stable", "candidate"}
    finally:
        client.close()
    apim_id = (f"/subscriptions/{os.environ['AZURE_SUBSCRIPTION_ID']}/resourceGroups/"
               f"{os.environ['AZURE_RESOURCE_GROUP']}/providers/Microsoft.ApiManagement/service/{os.environ['APIM_NAME']}")
    with AzureCliCredential(process_timeout=60) as credential:
        arm_token = credential.get_token("https://management.azure.com/.default").token
    def arm(path, optional=False):
        response = httpx.get("https://management.azure.com" + apim_id + path,
                             headers={"Authorization": "Bearer " + arm_token, "Accept": "application/json"}, timeout=90)
        if optional and response.status_code == 404:
            return None
        response.raise_for_status()
        # Request the JSON policy envelope explicitly (the API also offers XML)
        # and tolerate the UTF-8 BOM returned by APIM on Windows CLI readback.
        return json.loads(response.content.decode("utf-8-sig"))
    pool = arm("/backends/reasonfuse-canary?api-version=2025-03-01-preview")["properties"]["pool"]
    assert {item["id"].rsplit("/", 1)[-1]: item["weight"] for item in pool["services"]} == {"stable": 95, "candidate": 5}
    assert all(item["priority"] == 1 for item in pool["services"])
    affinity = pool["sessionAffinity"]["sessionId"]
    assert affinity["name"] == "ReasonFuseAffinity" and affinity["source"].lower() == "cookie"
    diagnostics = arm("/apis/reasonfuse/diagnostics/applicationinsights?api-version=2024-05-01")["properties"]
    assert diagnostics["sampling"]["percentage"] == 100
    assert diagnostics["loggerId"].endswith("/loggers/phase1-metadata")
    for side in ["frontend", "backend"]:
        for direction in ["request", "response"]:
            assert diagnostics[side][direction].get("body", {}).get("bytes", 0) == 0
            assert diagnostics[side][direction].get("headers", []) == []
    policy = arm("/apis/reasonfuse/policies/policy?api-version=2024-05-01&format=rawxml")["properties"]["value"]
    root = ET.fromstring(policy)
    forward = root.find("backend/forward-request")
    assert forward is not None and forward.get("buffer-response") == "false"
    assert root.find("inbound/set-backend-service").get("backend-id") == "reasonfuse-canary"
    assert not any("cache" in item.tag or item.tag in {"set-body", "validate-content", "base"} for item in root.iter())
    mappings = {}
    for role, weight in [("stable", 95), ("candidate", 5)]:
        backend = arm(f"/backends/{role}?api-version=2024-05-01")["properties"]
        expected_url = f"{project}/agents/reasonfuse-phase1-{role}/endpoint/protocols/openai"
        assert backend["url"].rstrip("/") == expected_url.rstrip("/")
        mappings[role] = {"url": backend["url"], "weight": weight, "live_release": releases[role]}
    operations = arm("/apis/reasonfuse/operations?api-version=2024-05-01")
    assert not operations.get("nextLink"), "Handle additional operation pages before acceptance"
    operation_policies = {}
    for operation in operations["value"]:
        name = operation["name"]
        effective = arm(f"/apis/reasonfuse/operations/{name}/policies/policy?api-version=2024-05-01&format=rawxml", optional=True)
        value = effective["properties"]["value"] if effective else None
        # No operation override means the API's non-inheriting policy is effective.
        if value:
            parsed = ET.fromstring(value)
            assert all(node.tag in {"policies", "inbound", "backend", "outbound", "on-error", "base"} for node in parsed.iter()), "Unexpected operation override"
            for section in ["inbound", "backend", "outbound", "on-error"]:
                assert parsed.find(section + "/base") is not None
        operation_policies[name] = value
    evidence.write("APIM_READBACK", pool=pool, diagnostics=diagnostics, policy=policy,
                   release_mapping=mappings, operation_policies=operation_policies,
                   inheritance="API has no base; global/product policies are not inherited; operations absent or base-only")


if __name__ == "__main__":
    run_case("preflight", validate)
