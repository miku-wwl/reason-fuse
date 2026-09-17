# ReasonFuse

ReasonFuse 是一个精简的 Microsoft Foundry Hosted Agent submission。Microsoft Foundry
负责 Hosted Agent、身份、模型调用和平台 tracing；ReasonFuse 负责确定性的 progress
判断、containment 和 outcome verification。

## 当前边界

```text
User
  ↓
Microsoft Foundry Hosted Agent (one agent)
  ↓
Microsoft Agent Framework
  ↓
ReasonFuse Function Middleware
  ↓
Tool / server.py local deterministic fixture

Observability:
Foundry native tracing → Application Insights
ReasonFuse → custom OpenTelemetry span attributes/events + JSON application logs
```

当前 lean build 明确不包含 APIM/canary、Operations App Service、Terraform root 或
自定义 Azure Monitor exporter。`azure.yaml` 是标准 Foundry project/model/Hosted Agent
部署入口；没有第二个 stable/candidate agent，也没有 release-probe middleware。

`server.py` 仅是本地、内存中的 deterministic Operations/outcome fixture，不是生产
Operations 后端，也不代表 Foundry IQ/Toolbox 已经部署或验证。

## 目录

```text
reason-fuse/
├── azure.yaml                    # 唯一的 Foundry/azd 部署入口
├── pyproject.toml                # 工程依赖声明
├── uv.lock / requirements.txt    # 依赖锁与远程构建输入
├── ReasonFuse_v5.0.0_AGENT_A_THON_IMPLEMENTATION_FREEZE.md
├── benchmark/15-scenarios.md     # 按需人工场景清单
├── server.py                     # 本地 deterministic Operations fixture
├── docs/phase6/                  # 竞赛说明材料
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

`benchmark/15-scenarios.md` 只是低成本、按需执行的故障场景清单；仓库不再维护
300-run benchmark、10k microbenchmark 或自动重复 runner。

本地 fixture 可用于低成本 outcome 验证：

```powershell
$env:PORT = "8000"
.venv/Scripts/python.exe server.py
```

`restart_service` 返回 accepted 后必须重新读取 `service_status`，才能得到
verified/failed/unknown 结果。

## Azure Hosted Agent 部署（显式执行）

标准资源由 `azure.yaml` 中的 `azure.ai.project` 和 `azure.ai.agent` hosts 交给
`azd` 管理。部署前需要 Azure 登录、目标订阅/区域，以及 Foundry project/model 和
Hosted Agent 所需权限。Hosted Agent 的专用 Entra identity、平台 tracing 和
Application Insights 接线由 Microsoft Foundry 负责；不要把平台注入的
`FOUNDRY_PROJECT_ENDPOINT` 或 `APPLICATIONINSIGHTS_CONNECTION_STRING` 写进
`azure.yaml`。

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

## 证据边界

`src/reasonfuse/core/` 保持以下语义：planning changed 不等于 reality changed、Todo
不等于 objective progress、accepted 不等于 verified success、fresh postcondition
verification、重复 non-progress fuse，以及 containment 后禁止继续执行 operational
tools。Foundry 观察执行；ReasonFuse 验证进展和结果。

历史 Phase 6/7 计划和证据材料保留为竞赛记录，不是当前部署入口。最终范围说明见
[v5.0.0 Agent-a-thon 冻结文档](ReasonFuse_v5.0.0_AGENT_A_THON_IMPLEMENTATION_FREEZE.md)。
