import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import HostedClient, output_text, run_case


def validate(evidence):
    assert os.environ["AZURE_LOCATION"] == "australiaeast"
    project = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    for role in ["stable", "candidate"]:
        client = HostedClient(evidence, base_url=f"{project}/agents/reasonfuse-phase1-{role}/endpoint/protocols/openai")
        try:
            result = client.turn("RF_RELEASE_PROBE")
            assert json.loads(output_text(result))["release_role"] == role
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
    def arm(path):
        response = httpx.get("https://management.azure.com" + apim_id + path,
                             headers={"Authorization": "Bearer " + arm_token, "Accept": "application/json"}, timeout=90)
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
    policy = arm("/apis/reasonfuse/policies/policy?api-version=2024-05-01&format=rawxml")["properties"]["value"]
    root = ET.fromstring(policy)
    forward = root.find("backend/forward-request")
    assert forward is not None and forward.get("buffer-response") == "false"
    assert root.find("inbound/set-backend-service").get("backend-id") == "reasonfuse-canary"
    assert not any("cache" in item.tag or item.tag in {"set-body", "validate-content", "base"} for item in root.iter())
    evidence.write("APIM_READBACK", pool=pool, diagnostics=diagnostics, policy=policy)


if __name__ == "__main__":
    run_case("preflight", validate)
