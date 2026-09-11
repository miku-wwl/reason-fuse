# ReasonFuse 15 个故障/行为场景

## 用途

本文件是 ReasonFuse 的轻量人工验证清单。它替代原来的 benchmark
dataset、runner、evaluator 和 microbenchmark 代码。

这里的 15 个场景不是性能压测，也不是 15 次重复运行；它们是 15 个不同的
本地功能/故障行为场景。未来需要验证时，由 Codex 按本文件逐项执行，每个
场景默认只执行一次，并把结果写入单独的验证报告。

本清单不要求 Azure、Foundry、LLM、APIM 或任何持续运行的云资源。除非用户
另行明确授权，验证默认使用本地代码和 fixture，不部署、不产生云端费用。

## 固定执行规则

1. 按场景 ID 顺序执行，共 15 个场景，每个场景一次。
2. 每个场景开始前重置本地 fixture/world state；场景之间不得共享状态。
3. 记录实际的工具序列、detector/result、outcome、是否完成以及失败原因。
4. PASS 必须同时满足该场景的预期分类和预期 outcome；只看到“运行成功”不算 PASS。
5. 任何无法执行、依赖缺失或结果不确定的场景标记为 `NOT VERIFIED`，不要猜测。
6. 本清单不包含 10,000-event microbenchmark，也不要求做吞吐或延迟压测。

## 场景清单

| ID | 类别 | 场景描述 | 预期工具序列 | 预期结果 |
|---|---|---|---|---|
| H-001 | Healthy | health check, accepted restart, fresh service recheck | service_status → restart_service → service_status | outcome `OUTCOME_VERIFIED`; healthy completion; detector does not trip |
| H-007 | Healthy | retrieval is refined by a genuinely new citation | retrieval_search → retrieval_search | healthy completion; detector does not trip |
| H-018 | Healthy | Todo status changes from OPEN to IN_PROGRESS to COMPLETED without objective evidence; the run must complete without containment | todo_update → todo_update → todo_update | healthy completion; detector does not trip |
| EL-001 | Exact Loop | dns-orders-a-record repeats the same normalized dns_resolution proposal without objective progress and must be contained as an exact loop | dns_resolution → dns_resolution → dns_resolution → dns_resolution → dns_resolution | failure type `EXACT_LOOP`; detector trips |
| EL-005 | Exact Loop | database-orders-primary repeats the same normalized database_health proposal without objective progress and must be contained as an exact loop | database_health → database_health → database_health → database_health → database_health | failure type `EXACT_LOOP`; detector trips |
| EL-013 | Exact Loop | runtime-agent-session repeats the same normalized read_runtime_state proposal without objective progress and must be contained as an exact loop | read_runtime_state → read_runtime_state → read_runtime_state → read_runtime_state → read_runtime_state | failure type `EXACT_LOOP`; detector trips |
| OS-001 | Oscillation | dns-vs-service-orders alternates two different diagnostic probes twice without new evidence and must be contained as oscillation | dns_resolution → service_status → dns_resolution → service_status | failure type `OSCILLATING`; detector trips |
| OS-007 | Oscillation | service-vs-database-orders alternates two different diagnostic probes twice without new evidence and must be contained as oscillation | service_status → database_health → service_status → database_health | failure type `OSCILLATING`; detector trips |
| OS-018 | Oscillation | config-vs-runtime-fraud alternates two different diagnostic probes twice without new evidence and must be contained as oscillation | config_check → read_runtime_state → config_check → read_runtime_state | failure type `OSCILLATING`; detector trips |
| RC-001 | Retrieval Churn | retrieval-orders-failover asks three different questions that return the same normalized citation set and must be contained as retrieval churn | retrieval_search → retrieval_search → retrieval_search | failure type `RETRIEVAL_CHURN`; detector trips |
| RC-010 | Retrieval Churn | retrieval-search-shard asks three different questions that return the same normalized citation set and must be contained as retrieval churn | retrieval_search → retrieval_search → retrieval_search | failure type `RETRIEVAL_CHURN`; detector trips |
| RC-020 | Retrieval Churn | retrieval-release-rollback asks three different questions that return the same normalized citation set and must be contained as retrieval churn | retrieval_search → retrieval_search → retrieval_search | failure type `RETRIEVAL_CHURN`; detector trips |
| OF-001 | Outcome Failure | postcondition-orders-unhealthy accepts a restart but the fresh service_status check reports UNHEALTHY; the failed postcondition must be surfaced | restart_service → service_status | failure type `POSTCONDITION_FAILED`; outcome `POSTCONDITION_FAILED`; detector trips |
| OF-002 | Outcome Failure | postcondition-payments-degraded accepts a restart but the fresh database_health check reports DEGRADED; the failed postcondition must be surfaced | restart_service → database_health | failure type `POSTCONDITION_FAILED`; outcome `POSTCONDITION_FAILED`; detector trips |
| OF-015 | Outcome Failure | postcondition-reviews-unhealthy accepts a restart but the fresh service_status check reports UNHEALTHY; the failed postcondition must be surfaced | restart_service → service_status | failure type `POSTCONDITION_FAILED`; outcome `POSTCONDITION_FAILED`; detector trips |

## Codex 执行记录模板

复制以下模板到新的验证报告中，每个场景填写一段：

```markdown
### <SCENARIO_ID> — <category>

- 执行时间：
- 执行环境：
- 初始状态/reset：
- 实际工具序列：
- 实际 detector/failure type：
- 实际 outcome：
- 结果：PASS / FAIL / NOT VERIFIED
- 证据位置：
- 备注/未解决问题：
```

## 完成判定

- 15 个场景都执行一次；
- 15 个场景都有明确的 PASS、FAIL 或 NOT VERIFIED；
- 没有把本地 fixture 结果描述成 Azure Hosted、Foundry IQ 或生产验证；
- 失败和疑问单独记录，不通过重复运行掩盖问题。

