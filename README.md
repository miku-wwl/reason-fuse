# ReasonFuse

ReasonFuse 使用 Foundry Hosted Agent、Microsoft Agent Framework、Foundry Toolbox
和 Azure API Management 构建 agent runtime。

仓库按功能组织为一个工程。Phase 是建设与验收里程碑，阶段记录放在 `docs/phases/`
和 `evidence/`；后续阶段继续演进同一套源码、依赖和部署配置。

Phase 1 独立验收已通过：四项验证、完整 clean-start
及部署源码身份均有实跑证据，见 [最终报告](docs/phases/phase-01-runtime-validation/verification-report.md)。
Phase 2 核心已实现，当前 construction 结果与实际证据见
[Phase 2 报告](docs/phases/phase-02-core/report.md)。核心代码位于 `src/reasonfuse/core/`；
`src/reasonfuse/validation/` 保留兼容性回归探针。Operations API 是可部署的模拟测试服务，
retrieval 使用明确标注的 fixture，不代表生产 restart 或 Foundry IQ 已验证。
下一步是单独执行 Phase 2 独立验收，不能复用 construction PASS 代替它。

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
├── scripts/                      # 部署、预检、重置、采集
│   └── support/                  # 脚本和集成检查共用的辅助代码
├── tests/
│   ├── local_wiring.py
│   ├── unit/                     # Phase 2 核心与边界测试
│   ├── integration/              # 历史、工具、审批、APIM
│   └── support/operations_api/   # 独立执行计数与模拟操作服务
├── docs/
│   └── phases/                   # 阶段任务、运行手册、最终报告和验证边界
└── evidence/                     # 按阶段和运行批次保存证据
```

## 本地使用

在仓库根目录运行，需要 PowerShell 7、Azure CLI、uv 和 Terraform：

```powershell
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
.venv/Scripts/python.exe tests/local_wiring.py
pwsh -File scripts/preflight.ps1
```

`preflight` 会连接当前 Azure 验证环境并执行一次 DNS smoke，不能与共享计数器的
集成检查同时运行。Azure 区域为 Australia East；当前环境名为 `rf-phase1-aue`。

部署入口为 `scripts/deploy.ps1`，重置入口为 `scripts/reset.ps1`。
全部检查命令及其边界见 [Phase 1 运行手册](docs/phases/phase-01-runtime-validation/runbook.md)。
Phase 2 部署、A–J 场景、预算续跑和证据生成见 [Core 运行手册](docs/phases/phase-02-core/runbook.md)。
`.sh` 入口通过 `pwsh` 调用对应 PowerShell 脚本，面向 Windows/Git Bash。

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
- [Phase 1 证据索引](evidence/phase-01-runtime-validation/index.json)
- [Phase 2 证据索引](evidence/phase-02-core/index.json)

学习入口只保留最终结论与必要边界，不再包含旧失败复盘任务。
Phase 1 正式验收及 Phase 2 最终批次、源码身份和部署包保留；清理不改变 Azure 资源。
