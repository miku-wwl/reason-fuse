# Phase 2 ReasonFuse Core Construction Report

依据：[Core Construction Prompt](../../../ReasonFuse_Phase2_Core_Construction_Prompt.md)。本次续作使用原 construction 结论及 evidence 定位缺口；保留同一工程、冻结架构及依赖，不重建 Phase 1。

## 结论与范围

本次修复后的 36 项单元测试、LOCAL_CORE、LOCAL_INTEGRATION、云端 A–J 十项用例、14 项兼容性检查及最终复位全部通过。construction 必需范围无未完成 blocker。

```text
PHASE 2 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

独立 Phase 2 verification 尚未执行。construction 通过也不等于独立 `PHASE 2 RESULT: PASS`。

最终证据入口：[完整索引](../../../evidence/phase-02-core/index.json)、[当前批次索引](../../../evidence/phase-02-core/construction-20260908-final/index.json)。复现入口：[运行手册](runbook.md)。尚未证明的能力单列于 [open questions](open-questions.md)。

## 修复过程与实现结果

先增加 12 项缺口回归，在旧实现上出现 14 个失败断言；随后修复并扩展边界覆盖，最终共 36 项单元测试。早期探索输出不再作为当前学习材料；当前批次的失败与修复后重测保留在同一索引中。

| 缺口 | 本次修复及验证 |
| --- | --- |
| OFF 仍可能受预算约束 | OFF 绕过全部 ReasonFuse 行为/预算 containment；原生审批不受影响；本地覆盖超过各预算后的 OFF 行为 |
| Contract 未完整执行 | 执行 max_steps 和 required_objective_progress_interval；side-effect 上限只检查副作用提案，普通诊断不被误拦截 |
| 动作可能耗尽验证额度 | 在 step/tool 总预算内预留一次验证；动作前至少剩两个位置；失败 dispatch 计入尝试次数 |
| useful recheck 恢复及绑定不完整 | AgentSession 跨 turn 恢复待验证状态；只允许动作对应资源的一次 service_status 或 database_health；不相关资源不消耗许可，失败/过期的绑定观察会消耗许可 |
| accepted 被当成成功/世界进展 | accepted 只建立验证义务，不声称 world delta；拒绝不建立义务；fresh HEALTHY、UNHEALTHY、stale HEALTHY 分别产生三种 outcome |
| 伪进展及 detector 边界 | 累积 evidence，分资源比较 world；缺少某类观察不等于变化；过滤噪声；真实新 evidence 打断循环历史 |
| retrieval 判定不完整 | source/citation/chunk/content hash 与 KB version 构成有效 evidence；改 query 或 score 不制造进展；本地覆盖新来源负对照 |
| 状态/遥测不足 | 保存失败 dispatch、权威 last_signals 与真实 TodoProvider 规划状态；区分 framework/platform session ID；OTel 属性与事件有单元测试 |
| Hosted driver 可能虚报 useful=true | F 从实际 runtime state 断言 useful_recheck/postcondition_delta；增加 I unknown、J database_health 别名的真实 Hosted 用例 |

核心位于 `src/reasonfuse/core/`，继续接入 AgentSession / ContextProvider / Function Middleware / Foundry Toolbox。原生历史及审批仍由平台/框架拥有；未添加数据库、替代 MCP、RAG 或其他云架构。

## 最终构建身份

| 字段 | 已核对值 |
| --- | --- |
| runtime source commit | `4fb12e6c34f77b3a0814f55fc268e10487111ad7` |
| source manifest SHA-256 | `8b8c1247360c93469bfc982920136d2adc0ec8dd800ea1bb286927712773b11e` |
| audited native ZIP / Hosted content SHA-256 | `8e9f9f9ade984691c21e73584e01a16f6988e2d3d7a59cc23db10ee3c132ac8b` |
| Toolbox | `reasonfuse-operations` version 11 |
| 最终 Hosted release | stable 27 / candidate 13，均 active |
| evidence batch | `construction-20260908-final`（UTC，实际日志时间为准） |
| 最终配置 | `REASONFUSE_PROFILE=phase2`、`REASONFUSE_ENABLED=true`、`REASONFUSE_CONTRACT_JSON={}` |

默认 ON 恢复后已完成 [最终环境读回](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T222929495196Z-environment.jsonl)，两端 content hash 均匹配同一 audited package。后续文档/evidence 提交的 SHA 可以不同于 runtime source commit；不能手工把 embedded identity 改成文档提交 SHA。`git push` 不等于部署。

## Hosted Core Scenarios

真实链路为 Responses API → Agent Framework Function Middleware → Foundry Toolbox → deterministic Operations API。模型没有被 mock；Operations 是模拟服务，E 是 retrieval fixture，不是 Foundry IQ。

| 场景 | 结果 | 独立外部计数与权威 runtime 观察 | Evidence |
| --- | --- | --- | --- |
| A — OFF | PASS | 同默认 contract、相同前四轮提示；4 次 DNS，无 containment；harness_stop=true，voluntary_stop=false | [A](../../../evidence/phase-02-core/construction-20260908-final/20260908T143115309935Z-hosted.jsonl) |
| B — ON no-progress | PASS | 2 次实际 DNS 后 NO_PROGRESS；后续请求未增加外部执行数 | [B](../../../evidence/phase-02-core/construction-20260908-final/20260908T142239014836Z-hosted.jsonl) |
| C — exact loop | PASS | 2 次执行，第 3 次提案因 EXACT_LOOP 被拦截 | [C](../../../evidence/phase-02-core/construction-20260908-final/20260908T143350653960Z-hosted.jsonl) |
| D — oscillation | PASS | period-2，3 次执行，第 4 次提案因 OSCILLATING 被拦截 | [D](../../../evidence/phase-02-core/construction-20260908-final/20260908T143455116253Z-hosted.jsonl) |
| E — retrieval churn | PASS | 3 个不同 query 返回等价 fixture evidence；RETRIEVAL_CHURN | [E](../../../evidence/phase-02-core/construction-20260908-final/20260908T142354698801Z-hosted.jsonl) |
| F — useful recheck/success | PASS | 2 次 service_status、1 次原生审批后的 restart；useful_recheck=true、postcondition_delta=true、OUTCOME_VERIFIED | [F](../../../evidence/phase-02-core/construction-20260908-final/20260908T142506073249Z-hosted.jsonl) |
| G — outcome failure | PASS | accepted 后仍 UNHEALTHY；必要重检被允许，结果 POSTCONDITION_FAILED 并 containment | [G](../../../evidence/phase-02-core/construction-20260908-final/20260908T142632318470Z-hosted.jsonl) |
| H — tool budget | PASS | budget-1 至 budget-10 各执行 1 次，无其它外部工具；第 11 次 BUDGET_EXHAUSTED，tool_call_count=10 | [H](../../../evidence/phase-02-core/construction-20260908-final/20260908T221247287353Z-hosted.jsonl) |
| I — outcome unknown | PASS | stale HEALTHY 不被误判成功；OUTCOME_UNKNOWN，后续无 external dispatch | [I](../../../evidence/phase-02-core/construction-20260908-final/20260908T142735190823Z-hosted.jsonl) |
| J — database health recheck | PASS | database_health → accepted restart → database_health；别名同样保留 useful recheck | [J](../../../evidence/phase-02-core/construction-20260908-final/20260908T142842619679Z-hosted.jsonl) |

A/B 使用同一 stable backend、同源码/模型/工具/default contract 和等价 reset world；各自 reset 产生不同 epoch，单场景内 epoch 保持不变。C/D/H 显式将 max_stalled_steps 与 required_objective_progress_interval 均设为 20，以隔离对应检测器；其余 budget 不变。

## 本批问题、纠正与重测

1. 完整部署首次遇到 Azure 管理接口超时；恢复连接后通过完整 `scripts/deploy.ps1` 重做并成功完成 Operations、Toolbox、原生 ZIP 审计和 stable/candidate 部署。[失败命令](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T140951839110Z-construction-20260908-final.jsonl)、[成功重试](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T141454868526Z-construction-20260908-final.jsonl)。分类：外部部署环境瞬态错误；不是 detector 失败。
2. H 初次尝试遇到模型配额错误；检查真实 tool sequence 也发现宽泛提示触发了额外诊断。修正为每轮仅一次 DNS，并在每轮前固定间隔 45 秒；添加 10 个 hostname 各执行一次及 tool_call_count=10 的精确断言。未增大预算，未更换模型，未把其它诊断算成 DNS。[原尝试](../../../evidence/phase-02-core/construction-20260908-final/20260908T143601990260Z-hosted.jsonl) 保留 FAIL。只修改 driver，runtime source 不变，使用 `-ResumeBudget` 新建 conversation/reset 后重跑，最终 H PASS。分类：TEST_DATA_BUG + 模型配额限制，已解决。

## Local Verification

- 36 项 unit tests：PASS，[持久化命令与输出](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T141017170195Z-construction-20260908-final-unit.jsonl)。覆盖 canonicalization、OFF/ON、所有预算、恢复、噪声/缺失观察、Todo-only、post-trip、recheck 绑定、unknown 边界和 OTel。
- LOCAL_CORE：PASS，[结构化本地核心证据](../../../evidence/phase-02-core/local-20260908/20260908T141024548180Z-local-core.jsonl)。
- LOCAL_INTEGRATION：PASS，[Operations API 证据](../../../evidence/phase-02-core/local-20260908/20260908T141030286586Z-operations-api.jsonl)。
- local wiring、compileall、PowerShell parse、`uv lock --check`、`git diff --check`：PASS。本地结果不冒充 Hosted 独立验收。

## Compatibility Regression Gate（Phase 1）

固定 14-command batch 全部 PASS：[批次完整记录](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T222652284027Z-batch-construction-20260908-final-compatibility.jsonl)。包含 preflight、环境身份、history/session、两轮 allow/block、approval approve/deny/binding、APIM affinity、新会话控制、SSE 与 metadata telemetry。

60 个新会话为 stable 57 / candidate 3，固定 99% Wilson 一致性检查通过：[routing evidence](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T223833998766Z-spike04_new_session_control.jsonl)。这是 5% 配置一致性检查，不是生产流量比例的精确估计。

本节只证明 Phase 2 没有破坏既有运行时，不是重新建设 Phase 1，也不能替代上面的 Phase 2 A–J。SSE 使用原确定性探针，metadata telemetry 是 APIM 元数据，不能扩大解释为模型 token streaming 或 Core 云端 trace 关联。

## 最终复位与清理

最终 [reset evidence](../../../evidence/phase-01-runtime-validation/runs/20260908/20260908T224812097335Z-reset.jsonl) 为 RESET_COMPLETE：核查两阶段证据记录的 406 个 test session ID，非 deleted/absent 的剩余 session 为 0；本次无需新增删除（3 条 terminal deleted 元数据仍可列出，其余 absent）。外部 counts=`{}`，scenario=`phase1`（Operations baseline 名称），service_health=`{}`，本地 validation-last-run 已不存在。`phase1` baseline 不表示 agent profile 切回 Phase 1；两端部署仍为 phase2/default ON。

清理删除了 138 个已被替代的旧 JSONL 中间文件，共 3,219,152 bytes，并移除相应空目录。删除前校验精确路径、确认未被最终索引引用且不是 tracked 历史验收文件；恢复包逐文件 SHA-256 校验通过。恢复包仅在 Git 忽略的 `.tools/phase2-superseded-20260908.zip`，不进入学习入口或 GitHub。

原 Phase 1 正式验收、当前批次所有尝试、源码身份及审计 ZIP 保留；清理后 74 个索引关联文件的 SHA-256、24 个源文件清单、Markdown 链接和凭据扫描均通过。未删除 Azure 资源、环境配置或 Terraform state。历史 Construction Prompt SHA-256 保持 `AF2CDAAD373740DDD52E49A880C889231C58BD78EE558E48ADBE9B64CA4E1E56` 不变。

## 复现命令

从仓库根目录执行；命令会修改当前测试环境，不能并行跑共享计数器测试：

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe scripts/verification_command.py construction-<UTC>-unit -- .venv/Scripts/python.exe -m unittest discover -s tests/unit -v
.venv/Scripts/python.exe scripts/phase2_local.py
.venv/Scripts/python.exe scripts/phase2_operations_local.py
pwsh -File scripts/phase2_construction.ps1 -Batch construction-<UTC>
.venv/Scripts/python.exe scripts/phase2_index.py --batch construction-<UTC>
```

本次 H 续跑命令为 `pwsh -File scripts/phase2_construction.ps1 -Batch construction-20260908-final -ResumeBudget`；该入口只适用于源码未变且此前 9 项已通过的同一批次，不是新的独立完整验收。
