# 仓库结构整理记录

日期：2026-09-08（Pacific/Auckland）。

ReasonFuse 现在以仓库根目录作为唯一主工程。Phase 1 的任务、报告和原始证据
归入阶段记录；源码、依赖、基础设施和操作脚本按职责组织，供后续阶段继续演进。

## 已完成的调整

- 工程配置提升至根目录，Python 工程名和 azd 项目名统一为 `reasonfuse`。
- 主源码归入 `src/reasonfuse/`，验证钩子集中在 `validation/` 子包。
  `src/main.py` 保留为 Hosted Agent 启动入口，并导入包内实现。
- 集成检查归入 `tests/integration/`；模拟 Operations API 归入
  `tests/support/operations_api/`；共享脚本辅助代码归入 `scripts/support/`。
- Toolbox 配置归入 `config/toolbox/`，移除无人读取的 `runtime_approval` 字段；
  审批仍由 `src/reasonfuse/agent.py` 的真实运行时配置控制。
- 删除未使用的 Foundry connections 模板及对应变量、空输入和两个输出。
- 文档和链接已更新。原施工提示保留历史示例，并注明当前目录以根 README 为准。
- 52 份原始证据按构建批次归档，逐文件 SHA-256 校验一致；新索引使用现有路径。
- `.azure/` 与 Terraform state 已迁移，原 state 内容未改动；`.venv/` 在根目录重建。
  旧虚拟环境和字节码缓存保存在 Git 忽略的 `.tools/legacy-runtime-cache/`。

## 验证结果

| 检查 | 结果 |
|---|---|
| 根工程 `uv lock --check` / `uv sync --frozen` | 通过；106 个导出依赖版本保持不变 |
| Python 编译、PowerShell 语法、脚本导入 | 通过；11 个操作/集成入口可导入 |
| 本地工具阻断、结果序列化、流式探针接线 | 通过 |
| Hosted 启动入口导入与 host 对象构造 | 通过 |
| Terraform init / validate | 通过 |
| Terraform plan，使用原 state 副本，`refresh=false` | 资源变更为 0；仅删除两个无用输出 |
| 新路径下完整 preflight | 通过；doctor 11 passed、0 failed、2 skipped，Toolbox 与 HTTP 探测通过 |
| 新证据目录下 reset | 通过；扫描归档和新运行记录，清理本次预检创建的会话，计数归零 |

相关证据：

- [Terraform 计划摘要](../../../evidence/phase-01-runtime-validation/reorganization-2026-09-07/terraform-plan.json)
- [完整 preflight 日志](../../../evidence/phase-01-runtime-validation/reorganization-2026-09-07/preflight.log)
- [preflight 原始结果](../../../evidence/phase-01-runtime-validation/runs/20260907/20260907T133134984546Z-preflight.jsonl)
- [reset 原始结果](../../../evidence/phase-01-runtime-validation/runs/20260907/20260907T133353026238Z-reset.jsonl)
- [原构建证据及路径索引](../../../evidence/phase-01-runtime-validation/index.json)

## 验证边界

这次整理没有执行 Terraform apply 或 Azure 重新部署。云端继续运行既有 stable 4 /
candidate 1；新目录的源码通过了本地入口和接线检查，云端预检验证的是已有部署。
**整理后源码的新版本云端部署及完整九项重跑：NOT VERIFIED。**

`refresh=false` 计划说明目录整理不会根据保留的 state 产生资源重建，不能作为全量
云端漂移检查。Phase 1 的历史九项实跑证据保持有效，独立验收状态仍为待执行。
