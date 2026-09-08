import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path
from azure.identity import AzureCliCredential, get_bearer_token_provider

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, output_text, run_case, safe_headers


def probe(client, conversation=None):
    result = client.turn("RF_RELEASE_PROBE", conversation=conversation)
    role = json.loads(output_text(result))["release_role"]
    assert role in {"stable", "candidate"}
    return role, result


def affinity(evidence):
    client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    try:
        conversation = client.conversation()
        roles = []
        sessions = []
        for _ in range(8):
            role, response = probe(client, conversation)
            roles.append(role)
            sessions.append(response["agent_session_id"])
        assert any(cookie.name == "ReasonFuseAffinity" for cookie in client.http.cookies.jar), "APIM affinity cookie missing"
        assert len(set(roles)) == 1, roles
        assert len(set(sessions)) == 1, sessions
        evidence.write("ASSERTIONS", conversation_id=conversation, roles=roles, platform_sessions=sessions)
    finally:
        client.close()


def new_session_control(evidence, samples):
    # A fresh HTTP client means a fresh cookie jar, so the old affinity is absent.
    # Sequential requests keep the experimental load and spending bounded.
    counts = Counter()
    # Share authentication only, not a connection or cookie jar. Azure's provider
    # caches tokens until refresh is needed, avoiding 60 identical CLI logins.
    credential = AzureCliCredential(process_timeout=60)
    token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
    evidence.write("COHORT_POLICY", samples=samples, sequential=True, fresh_cookie_jar_per_sample=True,
                   shared_authentication_only=True)
    for index in range(samples):
        client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"], token_provider=token_provider)
        try:
            assert not list(client.http.cookies.jar)
            role, _ = probe(client)
            counts[role] += 1
        finally:
            client.close()
        print(f"New session {index + 1}/{samples}: {dict(counts)}", flush=True)
    credential.close()
    assert counts["stable"] > 0 and counts["candidate"] > 0, "Both backends must be observed"
    # Check consistency with 5% using a 99% Wilson interval; this is not a precise
    # ratio estimate. Native pool readback separately checks the configured 95/5.
    p = counts["candidate"] / samples
    z = 2.576
    divisor = 1 + z * z / samples
    center = (p + z * z / (2 * samples)) / divisor
    radius = z * math.sqrt(p * (1 - p) / samples + z * z / (4 * samples * samples)) / divisor
    interval = [center - radius, center + radius]
    assert interval[0] <= 0.05 <= interval[1], f"Observed canary rate inconsistent with 5%: {counts}, 99% CI {interval}"
    evidence.write("ASSERTIONS", observed_counts=dict(counts), samples=samples,
                    candidate_fraction=p, wilson_99_percent_interval=interval,
                    interpretation="fresh-cookie routing control; 5% consistency check, not a precise ratio estimate")


def sse(evidence):
    client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    try:
        conversation = client.conversation()
        deltas = []
        done = False
        completed_at = None
        started = time.monotonic()
        body = {"input": "RF_SSE_PROBE", "conversation": conversation, "stream": True, "store": True}
        evidence.write("REQUEST", url=client.base + "/responses", body=body)
        with client.http.stream("POST", client.base + "/responses", params={"api-version": "v1"},
                                json=body, headers=client.headers()) as response:
            evidence.write("STREAM_HEADERS", status_code=response.status_code, headers=safe_headers(response.headers))
            response.raise_for_status()
            assert "text/event-stream" in response.headers.get("content-type", "")
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    continue
                event = json.loads(raw)
                arrived = time.monotonic() - started
                evidence.write("SSE_EVENT", arrival_seconds=arrived, body=event)
                if event.get("type") == "response.output_text.delta":
                    assert not done, "Text delta arrived after completion"
                    deltas.append((arrived, event["delta"]))
                if event.get("type") == "response.completed":
                    done = True
                    completed_at = arrived
                assert event.get("type") not in {"error", "response.failed"}, event
        assert done, "No terminal response.completed event"
        assert len(deltas) == 4, deltas
        assert [text.split(":", 1)[1].strip() for _, text in deltas] == [f"chunk-{n}" for n in range(1, 5)]
        assert deltas[-1][0] - deltas[0][0] >= 1.5, "SSE arrived as a buffered burst"
        assert all(deltas[i + 1][0] - deltas[i][0] >= 0.35 for i in range(3)), "Adjacent chunks were buffered"
        assert all(arrival < completed_at for arrival, _ in deltas[:3])
        evidence.write("ASSERTIONS", conversation_id=conversation, delta_arrivals=deltas, completed_at=completed_at)
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["affinity", "new_session_control", "sse"])
    parser.add_argument("--samples", type=int, default=60)
    args = parser.parse_args()
    functions = {"affinity": affinity, "new_session_control": lambda e: new_session_control(e, args.samples), "sse": sse}
    run_case("spike04_" + args.case, functions[args.case])
