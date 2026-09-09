# Phase 2 Core 构建与验证入口

从仓库根目录运行。Phase 2 继续使用同一个 Hosted Agent、AgentSession、原生审批和 Toolbox；资源名中的 `phase1` 是现有 Azure 资源名称。

## 本地验证

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m unittest discover -s tests/unit -v
.venv/Scripts/python.exe scripts/phase2_local.py
.venv/Scripts/python.exe scripts/phase2_operations_local.py
```

三个入口分别产生 LOCAL_UNIT、LOCAL_CORE 和 LOCAL_INTEGRATION 结果。单元测试如需持久化命令与输出，使用 `scripts/verification_command.py <label> -- <command>`。

## 完整 construction 复现

```powershell
pwsh -File scripts/phase2_construction.ps1 -Batch construction-<UTC>
```

此命令会部署并顺序运行：默认 ON 的 B/E/F/G/I/J、默认 OFF 的 A、放宽 stall/interval 的 C/D/H、恢复默认 ON、环境读回、兼容性回归和最终 reset。共享计数器场景禁止并行。命令失败会停止；临时 OFF/检测器配置在 finally 中恢复。

H 每次模型 turn 前固定等待 45 秒，降低共享模型配额的瞬时压力；预算仍为 10 次工具调用，第 11 次必须拦截。H 的提示明确禁止额外诊断，不能把其它工具消耗的额度误计为 10 次 DNS。若仅 H 因环境/driver 问题中断且源码未变，可用同一 `-Batch` 加 `-ResumeBudget`，保留原尝试并重置为新场景后继续 H、恢复、回归和 reset。源码改变时必须完整重跑。

脚本使用仓库锁定的工具与现有 `.azure/` state。完整部署通过 `scripts/deploy.ps1` 生成 identity、审计 ZIP，并读取 stable/candidate；同一源码包的 OFF/ON 配置切换仅部署 stable。对比始终使用明确的 stable endpoint。每个场景新建 conversation 并重置外部世界，每次 reset 产生新 epoch；场景内 epoch 必须保持不变。

construction 复现不是独立验收，独立测试须遵循仓库根目录的 `ReasonFuse_Phase2_Core_Verification_Prompt.md`，使用新的证据目录。

## 当前执行语义

| 项目 | 规则 |
| --- | --- |
| run 生命周期 | 一个新 conversation 开始一个 run；后续 turn 和原生 approval resume 保持 run_id、计数、模式及 contract |
| 身份 | framework_session_id 是 AgentSession ID；agent_session_id 是 Hosted 平台 ID；conversation ID 同时由客户端证据记录 |
| step / tool budget | step 计入已尝试的非观测工具 dispatch，包括失败；read_runtime_state 不消耗预算；已拦截提案单列计数 |
| side effect | 仅对副作用工具检查 side-effect 上限；失败尝试也消耗额度；原生拒绝不执行工具、不产生 postcondition |
| verification reserve | 接受动作前，step/tool 上限内至少剩余动作和一次 service_status 两个位置；不允许超额借用 |
| useful recheck | 仅放行 accepted action 对应资源的一次 service_status 或同 schema 的 database_health；跨 turn 恢复，过期/失败观察也消耗该次许可 |
| 默认 stall | max_stalled_steps=2 与 required_objective_progress_interval=2 均执行；先到的阈值生效 |
| 检测器配置 | C/D/H 固定 max_stalled_steps=20、required_objective_progress_interval=20，其余默认；C 在第三次提案前拦截，D 在第四次提案前拦截，H 在第十一次提案前拦截 |
| 进展 | 累积 evidence；分资源比较 world；缺少某类观察不代表该类发生变化；Todo 只是规划信号；accepted 不表示世界已改变 |
| retrieval | source/citation/chunk/content-hash 集合和知识库版本共同定义有效 evidence；query 文案与分数噪声不产生进展 |
| reason 顺序 | 已 containment 保持原理由；dispatch 前 budget、stall、exact、oscillation；完成 retrieval 后 churn 优先于 stall；绑定 verifier 的结果由 OutcomeVerifier 决定 |
| outcome | 先验证资源、状态、新鲜 generation 和合法 health，再判 HEALTHY；stale HEALTHY、缺失或不可用结果为 OUTCOME_UNKNOWN |
| OFF | 不执行 ReasonFuse 行为/预算 containment；原生审批与安全规则继续有效；harness 有固定上限 |

I 是新增的 stale-HEALTHY outcome-unknown 场景，J 覆盖 database_health 重检别名。F 必须从真实 runtime state 断言 useful_recheck 和 postcondition_delta，不能由测试脚本直接填写 true。

## 证据与交付

完成上述测试并记录 unit 命令后运行：

```powershell
.venv/Scripts/python.exe scripts/phase2_index.py --batch construction-<UTC>
```

索引要求该批 A–J 最终通过、同源码 identity、OFF/ON contract 相同、兼容性回归通过、reset 完成、默认 ON 已恢复，并保存已审计 ZIP。每次尝试都保留在选定批次内；不能从其它批次挑选 PASS 拼凑。

生成的 build identity 指向实际构建源码 commit；后续证据/文档提交拥有不同 SHA 是正常的。不要手工改写 identity 为最新文档提交，也不要把旧部署的结果当成新源码结果。Git push 不构成一次新的部署。
