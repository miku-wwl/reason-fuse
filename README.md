# ReasonFuse

ReasonFuse is a deterministic reliability layer for AI agents. It detects
non-progress, contains unsafe or repeated execution, and verifies that an
accepted action actually changed the external world before the agent claims
success.

## The problem

Agents can appear busy without making progress:

- `Todo != objective progress`. A changed plan is not evidence that the real
  system changed.
- `HTTP 202` or `accepted=true != successful outcome`. Acceptance only means
  that an operation was accepted for processing.
- An agent must obtain fresh external evidence before claiming success.
- Repeated non-progress must eventually be contained so another operational
  dispatch is blocked.

ReasonFuse makes those boundaries explicit and fail-closed.

## Architecture

```text
Microsoft Foundry Hosted Agent
        ↓
Microsoft Agent Framework
        ↓
ReasonFuse
        ↓
Foundry Toolbox / MCP
        ↓
External Operations State
```

The Hosted Agent is the competition deployment runtime. ReasonFuse owns the
progress, containment, approval-boundary, and outcome-verification decisions;
the model and tool platform provide proposals, execution, and observations.

Foundry Local is an additional low-cost validation path using the same
ReasonFuse core. It is not the competition deployment runtime and does not
prove Microsoft Foundry cloud infrastructure.

The final lean scope does not include APIM/canary infrastructure, an
Operations App Service, Terraform, or a custom Azure Monitor exporter.

`server.py` is a local in-memory fixture. The bounded cloud Operations MCP
fixture lives under `cloud/operations-mcp/`; neither is a production
Operations backend.

## 目录

```text
reason-fuse/
├── azure.yaml                    # 唯一的 Foundry/azd 部署入口
├── pyproject.toml                # 工程依赖声明
├── uv.lock / requirements.txt    # 依赖锁与远程构建输入
├── server.py                     # 本地 deterministic Operations fixture
├── docs/evidence/                # 精简的本地/云端证据索引
├── cloud/operations-mcp/         # 可复现的 bounded MCP fixture
├── src/
│   ├── main.py                   # Hosted Agent 启动入口
│   └── reasonfuse/
│       ├── main.py
│       ├── agent.py
│       ├── core/                 # 冻结的 progress/containment/outcome 核心
│       └── validation/           # AgentSession 与本地 wiring 钩子
├── scripts/bootstrap.ps1         # 固定 azd/扩展工具链准备
└── tests/                        # 本地 unit、wiring、history audit
```

## 本地检查

在仓库根目录运行；这些命令不访问 Azure：

```powershell
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
$env:PYTHONPATH = (Join-Path $PWD 'src')
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe tests/local_wiring.py
.venv/Scripts/python.exe tests/local_history_audit.py
python -m compileall src tests
uv lock --check
git diff --check
```

仓库不维护 300-run benchmark、10k microbenchmark 或自动重复 runner。

本地 fixture 可用于低成本 outcome 验证：

```powershell
$env:PORT = "8000"
.venv/Scripts/python.exe server.py
```

`restart_service` 返回 accepted 后必须重新读取 `service_status`，才能得到
verified/failed/unknown 结果。

## Foundry Local validation — LOCAL ONLY

仓库还提供一个可选的本地模型审计路径。它使用官方
`agent-framework-foundry-local` 客户端、同一组 ReasonFuse providers/middleware，以及
`server.py` 的 HTTP fixture；不会访问 Azure，也不会运行大规模 benchmark。
Foundry Local 运行时本身必须由本机按 Microsoft 文档安装并启动，Python 依赖已经锁定在
`pyproject.toml`/`uv.lock` 中。

已保存的本地证据使用 Foundry Local CLI `0.10.3` 和模型 `phi-4-mini`，见
[`docs/evidence/foundry-local-e2e.json`](docs/evidence/foundry-local-e2e.json)。其中真实 function calling、native
approval、`OUTCOME_VERIFIED`、`POSTCONDITION_FAILED`、`OUTCOME_UNKNOWN`、containment、
blocked-host validation 和 no-replay 均为 `PASS`。

```powershell
uv sync --frozen --python 3.13
$env:PYTHONPATH = (Join-Path $PWD 'src')
$env:FOUNDRY_LOCAL_MODEL = "phi-4-mini"
.venv/Scripts/python.exe scripts/foundry_local_e2e.py --report docs/evidence/foundry-local-e2e.json
```

首次使用 Windows CLI 时可先检查 daemon 和模型目录：

```powershell
foundry server start
foundry server status
foundry model list --type chat
foundry model download phi-4-mini
foundry model load phi-4-mini
```

本地适配层只在这个审计入口内兼容当前 CLI 的 `server`/catalog 接口与 Python SDK
旧版探测方式；它不改变 Hosted Agent 的部署代码。

该审计执行有界的本地场景：正常多轮会话、真实 read-only function call、native approval、
accepted-but-not-success 后的 VERIFIED/FAILED/UNKNOWN fresh postcondition、no-progress
containment、blocked-hostname validation，以及 verified restart 后的 no-replay。它还会通过
`FoundryLocalClient.manager` 检查选定模型是否支持 tool calling；Foundry Local CLI/服务未
安装或未启动时，它会诚实报告 `BLOCKED`，不会把 Hosted Agent 的
`history_source="agent_server"` 伪称为本地等价物。

这些本地检查可以证明 Foundry Local 推理、function calling、Agent Framework approval、
ReasonFuse middleware/core、本地 HTTP fixture、outcome verification、containment 和
no-replay；不能证明 Microsoft Foundry Hosted Agent infrastructure、Azure RBAC、Hosted
Responses endpoint、Foundry IQ、Foundry Toolbox、Application Insights 或 cloud tracing。
本地多轮记录使用 local `AgentSession`，不把它改称为
`history_source="agent_server"`。云端证据见
[`docs/evidence/cloud-e2e.md`](docs/evidence/cloud-e2e.md)。

## Proven bounded cloud E2E

The bounded Hosted Agent behavioral path is **PASS**. The temporary Operations
MCP resources used for that audit were deleted after evidence capture; the
detailed raw Azure reports are local-only and are not part of this repository.

Observed deployment and protocol:

- Hosted Agent: `reasonfuse:6`
- Responses protocol: `2.0.0`
- Model: `gpt-5-mini`
- Normal multi-turn Hosted Agent behavior: `PASS`
- Normal request contract: `history_source="agent_server"`, `store=False`

```text
BEFORE: UNHEALTHY / g1
  → native MCP approval request
  → no execution before approval
  → approved restart
  → accepted=true / status_code=202
  → execution_count=1 / side_effect_count=1
  → fresh service_status
  → HEALTHY / g2
  → OUTCOME_VERIFIED
```

Repeated no-progress then produced `NO_PROGRESS` containment; a subsequent
restart was `BLOCKED` and `side_effect_count` remained `1`. No accidental
replay: **PASS**. The detailed identifiers and runtime state are in
[`docs/evidence/cloud-e2e.md`](docs/evidence/cloud-e2e.md).

The approval continuation temporarily used `store=True` because a
`previous_response_id` continuation with `store=False` does not persist the
server-side response state required by that continuation. The normal frozen
Hosted request remains `store=False`; no `store=False` approval-continuation
PASS is claimed.

## Azure Hosted Agent 部署（显式执行）

标准资源由 `azure.yaml` 中的 `azure.ai.project` 和 `azure.ai.agent` hosts 交给
`azd` 管理。部署前需要 Azure 登录、目标订阅/区域，以及 Foundry project/model 和
Hosted Agent 所需权限。不要把平台注入的 `FOUNDRY_PROJECT_ENDPOINT` 或
`APPLICATIONINSIGHTS_CONNECTION_STRING` 写进 `azure.yaml`。当前提交没有配置
Application Insights 或自定义云 tracing，因此不要把它们描述成已验证能力。

```powershell
pwsh -File scripts/bootstrap.ps1
$azd = ".tools/azd-1.33.0/azd-windows-amd64.exe"

& $azd auth login
& $azd env new <azd-environment>
& $azd env set AZURE_SUBSCRIPTION_ID "<subscription-id>"
& $azd env set AZURE_LOCATION "australiaeast"
& $azd env set REASONFUSE_ENABLED "true"
& $azd env set REASONFUSE_CONTRACT_JSON "{}"

# provision + deploy；会真实访问 Azure 并可能产生费用
& $azd up --no-prompt
```

也可以把 `azd up` 拆成 `azd provision` 和 `azd deploy reasonfuse`，以便在资源
创建前单独检查环境。当前仓库禁止在本地审计中自动执行这些命令。按需部署前应先
确认 Foundry 配额、区域可用性和费用；本项目默认不创建 APIM、Operations Web App
或额外的 canary 基础设施。

可选的外部 Toolbox/IQ 接线不属于默认 `azure.yaml` 资源图。若部署环境提供对应
endpoint，agent 仍可通过环境变量加载它们；仓库不把这类外部后端误报为已部署或已验证。

## Submission boundaries

`src/reasonfuse/core/` 保持以下语义：planning changed 不等于 reality changed、Todo
不等于 objective progress、accepted 不等于 verified success、fresh postcondition
verification、重复 non-progress fuse，以及 containment 后禁止继续执行 operational
tools。Foundry 观察执行；ReasonFuse 验证进展和结果。

Current limitations are explicit:

- Application Insights / cloud custom tracing: **NOT CONFIGURED**
- Foundry IQ native retrieval: **NOT VALIDATED**
- APIM/canary: **REMOVED FROM FINAL SCOPE**
- The bounded Operations MCP service is a deterministic fixture, not a
  production backend.
- The final video is **PENDING**.
- Large benchmarks and repeated model runs are **OUT OF SCOPE**.

No cloud `REASONFUSE_FUSE_TRIPPED` telemetry event is claimed. The containment
claim above is based on observed Hosted Agent behavior and runtime state, not on
Application Insights evidence.

Evidence index:

- [`docs/evidence/validation-summary.md`](docs/evidence/validation-summary.md)
- [`docs/evidence/cloud-e2e.md`](docs/evidence/cloud-e2e.md)
- [`docs/evidence/foundry-local-e2e.json`](docs/evidence/foundry-local-e2e.json)
