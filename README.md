# ReasonFuse

ReasonFuse 使用 Foundry Hosted Agent、Microsoft Agent Framework、Foundry Toolbox
和 Azure API Management 构建 agent runtime。

仓库按功能组织为一个工程。Phase 是建设与验收里程碑；历史阶段报告已清理，
当前以根目录的任务 prompt、源码和轻量场景清单为准。

Phase 1 独立验收已通过：四项验证、完整 clean-start 及部署源码身份均有实跑证据；
历史报告已清理。Phase 2 核心已实现，历史 construction 报告也已清理；核心代码位于 `src/reasonfuse/core/`；
`src/reasonfuse/validation/` 保留兼容性回归探针。Operations API 是可部署的模拟测试服务，
retrieval 使用明确标注的 fixture，不代表生产 restart 或 Foundry IQ 已验证。
下一步是单独执行 Phase 2 独立验收，不能复用 construction PASS 代替它。

Phase 3/4 的历史结论保留在根目录 prompt 中；当前只保留一个按需人工执行的
[15 个场景清单](benchmark/15-scenarios.md)，不再维护自动 benchmark runner、
microbenchmark 或重复执行配置。Phase 4 的 bounded P0 Hosted 验证已完成并保留报告；临时 Azure
环境已清理，当前默认命令不会重新部署 Azure。Phase 5 的 root prompt 仍保留，
但不再保留单独的报告目录。

## 目录

```text
reason-fuse/
├── azure.yaml                    # 统一部署入口
├── pyproject.toml                # 工程依赖声明
├── uv.lock / requirements.txt    # 依赖锁与远程构建输入
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
.venv/Scripts/python.exe tests/local_wiring.py
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

历史 Phase 报告、runbook 和根目录 Phase prompt 已删除；
`benchmark/15-scenarios.md` 仅作为按需人工场景清单保留。
