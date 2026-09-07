# ReasonFuse

ReasonFuse 使用 Foundry Hosted Agent、Microsoft Agent Framework、Foundry Toolbox
和 Azure API Management 构建 agent runtime。

仓库按功能组织为一个工程。Phase 是建设与验收里程碑，阶段记录放在 `docs/phases/`
和 `evidence/`；后续阶段继续演进同一套源码、依赖和部署配置。

当前实现是最小运行时验证版本。Phase 1 的 9 项真实集成检查已通过，构建完成，
独立验收仍待执行。运行时中的测试状态、阻断规则和 SSE 探针集中在
`src/reasonfuse/validation/`，Operations API 是可部署的模拟测试服务。

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
│       └── validation/           # 需要随 agent 部署的验证钩子
├── infra/                        # 同一个 Terraform root module
├── config/toolbox/               # Toolbox OpenAPI 配置
├── scripts/                      # 部署、预检、重置、采集
│   └── support/                  # 脚本和集成检查共用的辅助代码
├── tests/
│   ├── local_wiring.py
│   ├── integration/              # 历史、工具、审批、APIM
│   └── support/operations_api/   # 独立执行计数与模拟操作服务
├── docs/
│   ├── environment/              # 有日期的环境快照
│   └── phases/                   # 阶段任务、运行手册和报告
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
`.sh` 入口通过 `pwsh` 调用对应 PowerShell 脚本，面向 Windows/Git Bash。

`.azure/` 保存本地环境和 Terraform state，`.venv/`、`.tools/` 保存本地依赖与工具，
这些目录均被 Git 忽略。在另一台机器复用已部署环境时，需要先恢复对应环境与 state。

## 项目记录

- [Phase 1 构建任务](docs/phases/phase-01-runtime-validation/construction-prompt.md)
- [Phase 1 结果与限制](docs/phases/phase-01-runtime-validation/report.md)
- [部署前环境快照](docs/environment/2026-09-07-before-deployment.md)
- [证据索引](evidence/phase-01-runtime-validation/index.json)

旧验证环境的 Azure 资源名称保留，目录整理不改变资源身份。原始证据保留原文和哈希，
其中的旧本地路径表示当时的执行位置。
