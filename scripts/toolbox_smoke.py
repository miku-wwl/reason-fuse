import asyncio
import json
import os
import sys
from pathlib import Path

from agent_framework.foundry import FoundryToolbox
from azure.identity import AzureCliCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import Evidence, Operations


async def main():
    evidence = Evidence("toolbox-smoke")
    counters = Operations(evidence)
    counters.reset()
    allowed_tools = ["operations___dns_resolution", "operations___restart_service"]
    if os.environ.get("FOUNDRY_IQ_MCP_ENDPOINT"):
        allowed_tools.extend(["foundry_iq___knowledge_base_retrieve", "knowledge_base_retrieve"])
    with AzureCliCredential() as credential:
        async with FoundryToolbox(
            credential, url=os.environ["TOOLBOX_ENDPOINT"],
            allowed_tools=allowed_tools,
            approval_mode={"always_require_approval": ["operations___restart_service"],
                           "never_require_approval": ["operations___dns_resolution"]},
        ) as toolbox:
            listed = await toolbox.session.list_tools()
            evidence.write("TOOLS_LIST", tools=[tool.model_dump(mode="json") for tool in listed.tools])
            modes = {f.name: f.approval_mode for f in toolbox.functions}
            evidence.write("LOCAL_FUNCTIONS", approval_modes=modes)
            print(json.dumps({"tool_names": [tool.name for tool in listed.tools], "approval_modes": modes}))
            assert "operations___dns_resolution" in [tool.name for tool in listed.tools]
            assert "operations___dns_resolution" in modes
            if os.environ.get("FOUNDRY_IQ_MCP_ENDPOINT"):
                iq_names = [tool.name for tool in listed.tools if "knowledge_base_retrieve" in tool.name]
                assert iq_names, "Native IQ MCP tool missing from the versioned toolbox"
                evidence.write("NATIVE_IQ_TOOL_LISTED", tool_names=iq_names)
            for name, mode in modes.items():
                if "restart_service" in name:
                    assert mode == "always_require", "R2 tool missing runtime approval enforcement"
            result = await toolbox.session.call_tool("operations___dns_resolution", {"body": {"hostname": "api.reasonfuse.local"}})
            evidence.write("DNS_RESULT", result=result.model_dump(mode="json"))
            assert not result.isError and "INCONCLUSIVE" in str(result)
            counters.assert_counts({"dns_resolution:api.reasonfuse.local": 1})
    evidence.write("RESULT", status="PASS", exit_code=0, evidence_layer="real_foundry_toolbox_and_operations_api")
    print(f"TOOLBOX_SMOKE_PASS {evidence.path}")


if __name__ == "__main__":
    asyncio.run(main())
