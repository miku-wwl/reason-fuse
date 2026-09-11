# ReasonFuse

ReasonFuse 使用 Foundry Hosted Agent、Microsoft Agent Framework、Foundry Toolbox
和 Azure API Management 构建 agent runtime。

仓库按功能组织为一个工程。Phase 是建设与验收里程碑，阶段记录放在 `docs/phases/`
和各阶段报告；后续阶段继续演进同一套源码、依赖和部署配置。

Phase 1 独立验收已通过：四项验证、完整 clean-start
及部署源码身份均有实跑证据，见 [最终报告](docs/phases/phase-01-runtime-validation/verification-report.md)。
Phase 2 核心已实现，当前 construction 结果与实际证据见
[Phase 2 报告](docs/phases/phase-02-core/report.md)。核心代码位于 `src/reasonfuse/core/`；
`src/reasonfuse/validation/` 保留兼容性回归探针。Operations API 是可部署的模拟测试服务，
retrieval 使用明确标注的 fixture，不代表生产 restart 或 Foundry IQ 已验证。
下一步是单独执行 Phase 2 独立验收，不能复用 construction PASS 代替它。

Phase 3 已冻结为本地 15 场景 Agentathon profile（`15 × 1`）。Phase 4 的 bounded P0
Hosted 验证已完成并保留报告；临时 Azure
环境已清理，当前默认命令不会重新部署 Azure。Phase 5 施工产物位于
[Pre-Competition Freeze](docs/phases/phase-05-pre-competition-freeze/)，目标是生成可复现、可恢复的 Competition RC1，而不是继续扩展架构。

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
├── config/toolbox/               # Toolbox OpenAPI 配置
├── scripts/                      # 仅保留最小维护、演示和安全 Terraform plan 脚手架
├── tests/
│   ├── local_wiring.py
│   ├── unit/                     # Phase 2 核心与边界测试
│   ├── integration/              # 历史、工具、审批、APIM
│   └── support/operations_api/   # 独立执行计数与模拟操作服务
├── docs/
│   └── phases/                   # 阶段任务、运行手册、最终报告和验证边界
```

## 本地使用

在仓库根目录运行。当前 Azure Hosted 环境已清理，仓库只保留四个最小维护脚本：

```powershell
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
.venv/Scripts/python.exe tests/local_wiring.py
pwsh -File scripts/terraform_plan_safe.ps1
```

`terraform_plan_safe.ps1` 使用 `refresh=false`，只生成计划，不执行 apply，
不会改变 Azure 资源。`phase4_production_story.py` 只运行本地 bounded story，
`write_phase5_release_manifest.py` 只生成冻结版本 manifest；二者都不部署 Azure。
Phase 1–5 文档中的其他脚本命令属于历史施工/验证记录，不再作为当前部署入口；
当前没有保持运行的 ReasonFuse Hosted 环境。

## Azure Hosted Agent 部署（显式执行）

本项目采用混合部署边界：Terraform 创建和更新 Azure 基础设施，`azd` 根据
`azure.yaml` 打包并上传 `src/main.py`，然后发布两个 Foundry Hosted Agent。
Terraform 不负责上传 Hosted Agent 业务代码。

使用仓库固定的 `azd` 版本时，流程是：

```powershell
$azd = ".tools/azd-1.33.0/azd-windows-amd64.exe"
$envName = "<azd-environment>"

# 只需首次执行：登录并创建（或选择已有的）azd 环境
& $azd auth login
& $azd env new $envName       # 已存在时改用：azd env select $envName

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

`.azure/` 保存本地环境和 Terraform state，`.venv/`、`.tools/` 保存本地依赖与工具，
这些目录均被 Git 忽略。在另一台机器复用已部署环境时，需要先恢复对应环境与 state。

## 项目记录

- [Phase 1 构建任务](docs/phases/phase-01-runtime-validation/construction-prompt.md)
- [Phase 1 最终验收报告](docs/phases/phase-01-runtime-validation/verification-report.md)
- [Phase 1 验证边界](docs/phases/phase-01-runtime-validation/verification-open-questions.md)
- [Phase 2 核心构建任务](ReasonFuse_Phase2_Core_Construction_Prompt.md)
- [Phase 2 构建报告](docs/phases/phase-02-core/report.md)
- [Phase 2 待验证边界与疑问](docs/phases/phase-02-core/open-questions.md)
- [Phase 2 独立验收任务](ReasonFuse_Phase2_Core_Verification_Prompt.md)
- [Phase 4 Production Story 报告](docs/phases/phase-04-production-story/PHASE4_REPORT.md)
- [Phase 4 Hosted 验证报告](docs/phases/phase-04-production-story/PHASE4_CLOUD_VERIFICATION_REPORT.md)
- [Phase 5 Pre-Competition Freeze 报告](docs/phases/phase-05-pre-competition-freeze/PHASE5_REPORT.md)

学习入口只保留最终结论与必要边界，不再包含旧失败复盘任务。
Phase 1 正式验收、Phase 2/3 的 canonical 报告、Phase 4 Hosted 摘要和 Phase 5
release manifest 保留；原始临时 run/evidence 不作为默认项目资产。
