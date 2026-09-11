# ReasonFuse

ReasonFuse 使用 Foundry Hosted Agent、Microsoft Agent Framework、Foundry Toolbox
和 Azure API Management 构建 agent runtime。

仓库按功能组织为一个工程。历史阶段报告和 Prompt 已清理，当前以源码、轻量场景清单和
明确标注范围的一次性最终 Azure 审计报告为准。

Phase 1 的历史验收曾覆盖四项验证、clean-start 和部署路径；相关报告已清理，
不作为当前仓库证据。Phase 2 核心已实现，历史 construction 报告也已清理；核心代码位于 `src/reasonfuse/core/`；
`src/reasonfuse/validation/` 保留兼容性回归探针。Terraform 仍保留 Operations Web App
和 APIM 的基础设施声明，但当前仓库不包含配套的 `server.py` 服务源码；本地场景使用
明确标注的 fixture，不代表生产 restart 或 Foundry IQ 已验证。

Phase 3/4 的历史结论不再作为仓库资产；当前只保留一个按需人工执行的
[15 个场景清单](benchmark/15-scenarios.md)，不再维护自动 benchmark runner、
microbenchmark 或重复执行配置。Phase 4 的临时 Azure 环境已清理，当前默认命令不会重新部署 Azure；
历史结论不作为当前验证资产。Phase 5 的 root prompt 和历史报告也已清理。

最近一次最小 Azure E2E 审计已在本地完成：Hosted Agent 多轮会话和
`NO_PROGRESS → COMPLETE_AND_CONTAIN → BLOCK` 通过；Approval/Outcome 仅有本地
实现证据，云端仍未验证。详细 Azure 审计报告是本地-only 文件，已明确排除在 GitHub
仓库之外，不作为仓库提交资产或生产验证声明。

## 目录

```text
reason-fuse/
├── azure.yaml                    # 统一部署入口
├── pyproject.toml                # 工程依赖声明
├── uv.lock / requirements.txt    # 依赖锁与远程构建输入
├── ReasonFuse_v5.0.0_AGENT_A_THON_IMPLEMENTATION_FREEZE.md # 最终 hackathon 冻结说明
├── src/
│   ├── main.py                   # Hosted Agent 启动入口
│   └── reasonfuse/
│       ├── main.py
│       ├── agent.py
│       ├── core/                 # 状态、进展、检测器、预算、outcome 与 middleware
│       └── validation/           # 需要随 agent 部署的验证钩子
├── infra/                        # 同一个 Terraform root module
├── scripts/                      # 仅保留工具链检查与安全 Terraform plan 脚手架
├── tests/
│   ├── local_wiring.py
│   ├── local_history_audit.py
│   ├── unit/                     # Phase 2 核心与边界测试
```

## 本地使用

在仓库根目录运行。当前 Azure Hosted 环境已清理，仓库只保留两个最小维护脚本：

```powershell
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
$env:PYTHONPATH = (Join-Path $PWD 'src')
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe tests/local_wiring.py
.venv/Scripts/python.exe tests/local_history_audit.py
pwsh -File scripts/terraform_plan_safe.ps1
```

`terraform_plan_safe.ps1` 使用 `refresh=false`，只生成计划，不执行 apply，
不会改变 Azure 资源。需要进行功能回归时，按
`benchmark/15-scenarios.md` 由 Codex 逐项执行并另存结果报告，不再依赖自动 runner。
Phase 1–5 文档中的其他脚本命令属于历史施工/验证记录，不再作为当前部署入口；
当前没有保持运行的 ReasonFuse Hosted 环境。

## Azure Hosted Agent 部署（显式执行）

本项目采用混合部署边界：Terraform 创建和更新 Azure 基础设施，`azd` 根据
`azure.yaml` 打包并上传 `src/main.py`，然后发布两个 Foundry Hosted Agent。
Terraform 不负责上传 Hosted Agent 业务代码。

使用仓库固定的 `azd` 版本时，流程是：

```powershell
# 首次准备本地工具链；会安装固定版本 azd 及项目需要的扩展
pwsh -File scripts/bootstrap.ps1

$azd = ".tools/azd-1.33.0/azd-windows-amd64.exe"
$envName = "<azd-environment>"

# 登录 Azure
& $azd auth login

# 创建新环境；如果环境已存在，改用 azd env select
& $azd env new $envName
# & $azd env select $envName

# 保存到被 Git 忽略的 azd 环境，不要写入仓库
& $azd env set AZURE_SUBSCRIPTION_ID "<subscription-id>"
& $azd env set AZURE_LOCATION "australiaeast"
& $azd env set PUBLISHER_EMAIL "<publisher-email>"
& $azd env set OPERATIONS_ADMIN_KEY "<operations-admin-key>"

# 阶段 1：由 azd 调用 infra/ 中的 Terraform 创建基础设施
& $azd provision --environment $envName --no-prompt

# 阶段 2：由 azd 根据 azure.yaml 上传并发布 src/main.py
& $azd deploy stable --environment $envName --no-prompt
& $azd deploy candidate --environment $envName --no-prompt
```

`azd up` 可以把 provision 和 deploy 合并执行，但预算受限时建议分开，先确认
Terraform 资源计划，再明确执行 Hosted Agent 发布。只做本地检查或 Terraform
plan 时，不要运行 `azd provision`、`azd deploy` 或 `azd up`；这些命令会实际访问
Azure 并可能产生费用。部署完成后，Stable/Candidate 的路由仍由 APIM 和对应的
Terraform 配置管理。

`azd env new` 与 `azd env select` 二选一，不要连续执行。`PUBLISHER_EMAIL` 和
`OPERATIONS_ADMIN_KEY` 只作为示例变量名，实际值保存在被 Git 忽略的 azd 环境中；
不要把真实密钥写入 `azure.yaml`、README 或 Terraform 文件。

`.azure/` 保存本地环境和 Terraform state，`.venv/`、`.tools/` 保存本地依赖与工具，
这些目录均被 Git 忽略。在另一台机器复用已部署环境时，需要先恢复对应环境与 state。

## 项目记录

历史 Phase 报告、runbook 和阶段 Prompt 已删除；
`benchmark/15-scenarios.md` 仅作为按需人工场景清单保留；最终 Azure 审计报告只记录
本轮临时验证及其限制，并保持在本地，不进入 GitHub 仓库。
最终范围说明见 [v5.0.0 Agent-a-thon 冻结文档](ReasonFuse_v5.0.0_AGENT_A_THON_IMPLEMENTATION_FREEZE.md)。
