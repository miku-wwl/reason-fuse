# Phase 1 最终验收报告

验证日期：2026-09-08；执行时间以原始 evidence 的 UTC 为准。

## 结论

**PHASE 1 RESULT: PASS。可以进入 Phase 2 核心构建。**

完成了两个固定的完整批次、全量 clean-start 部署和最终 reset。
下表结果只适用于本报告的测试范围，不表示生产能力全部验证完成。

| 验收项 | 第一批 | Clean-start 批次 |
| --- | --- | --- |
| Spike 1：历史与 AgentSession | PASS | PASS |
| Spike 2：Toolbox 本地拦截 | PASS | PASS |
| Spike 3：原生人工审批 | PASS | PASS |
| Spike 4：APIM 路由与 SSE | PASS | PASS |
| 实际部署包与源码身份一致 | VERIFIED | VERIFIED |
| 全量 clean-start 与最终 reset | 不适用 | PASS |

Architecture Unfreeze Required：**NO**。

## 实测要点

- **历史与状态**：两轮中框架、平台 session ID 分别保持一致；counter 7 正确恢复。
  模型输入数为 1→7，canonical items 为 6→11，唯一用户标记各出现一次。
  canonical API 的 `store=True` 与实际模型调用的 `store=False` 分属两层。
  SDK 历史 provider 在工具循环内临时加载消息，跨 Hosted 轮次清空；没有第二份规范历史。
- **工具拦截**：每批两次 allow、两次 block。allow 外部 DNS 计数为 1，
  block 为 0；每个证明区间内 epoch 不变。调用仍经过本地 Function Middleware 与 Toolbox。
- **原生审批**：每批 approve、deny、binding 均通过。批准 orders 后只执行一次；
  拒绝、已消费批准重放不产生额外副作用；payments 获得独立审批 ID，拒绝后计数仍为 0。
  提交调用以请求审批不等于执行动作；restart 保持 `always_require`。
- **APIM 与 SSE**：核对原生 95/5 池、真实后端 URL、操作策略和无缓冲路径。
  每批 8 轮 affinity 保持一致；固定 60 个全新 cookie jar 均得到 stable 57 / candidate 3。
  这不是对长期精确比例的保证。
  两批各 4 个 SSE delta 均先于 completed 到达，且各有精确匹配该请求的入库遥测。
  正文采集关闭，元数据采集开启。
- **Clean-start**：新建虚拟环境、安装锁定依赖、bootstrap、完整部署、第二批 14 条命令、
  最终 reset 全部完成。保留 Terraform state 与资源，不销毁资源组。
  最终 reset 核对 388 个记录 ID：40 个已 deleted，348 个未在完整会话列表中列出，
  无仍存活的已记录会话，外部计数器为空；末次无需新增删除。

## 环境与部署身份

以下为验证时的快照，不是对当前云端状态的持续保证。

- 仓库：`D:\workshop\sep\reason-fuse`。
- Git 基线：`4d88420a2ad3eb56ace7528a1f0dc4c47f8455b1`，加验收时未提交的修正。
- Azure：Australia East；RG `rg-reasonfuse-phase1-aue`；Project `reasonfuse-phase1`。
- Python：本地 3.13.9、Hosted 3.13.15；没有升级锁定依赖或安装 Full Harness。
- 模型：gpt-5-mini，2025-08-07，GlobalStandard，capacity 10。

| 批次 | Stable / Candidate | Toolbox |
| --- | --- | --- |
| 第一批 | 7 / 4，均 active | 5 |
| Clean-start | 8 / 5，均 active | 6 |

两个批次的两后端 content_hash 均等于审计 ZIP 的 SHA-256：

`d7b0ddeb3e2aa21a24360dbcfced1a017d35806e07d171f796a7d9e2e011eb97`

部署源码清单 SHA-256：

`adf7a170d63d7df7bc06d18a7f87f8aef3aa3498cd42c74272f113b8a6b5c372`

源码身份由实际运行时读回，ZIP 逐文件核对。完整依赖、工具版本、命令和哈希
见最终证据索引。

## 保留的验收证据

| 流程 | 原始记录 |
| --- | --- |
| 第一批，14 条命令全部退出 0 | initial batch |
| 新环境、全量部署、第二批和 reset | clean-start orchestration |
| 第二批，14 条命令全部退出 0 | clean-start batch |
| 最终运行态清理 | final reset |

按项目所有者要求，学习目录已移除旧报告和诊断中间产物，不再要求复盘历史尝试。
保留的正式批次记录与部署 ZIP 未改写；此索引是最终验收集，不是所有尝试的完整档案。
文档清理与索引更新不构成一次新的运行时验证。

## 边界与下一步

Operations API 是独立部署的确定性测试服务，restart 为 `SIMULATED_RESTART`；
SSE 验证的是实际 Hosted/APIM 链路中的确定性中间件分块。
生产服务恢复、模型 token streaming、强制冷启动及 Foundry IQ
均不属于本阶段结论，详见[验证边界](verification-open-questions.md)。

[Phase 2 构建 Prompt](../../../ReasonFuse_Phase2_Core_Construction_Prompt.md)已完成交接调整，
可交给 Luna 实施。Phase 2 核心功能尚未构建；后续若源码或部署改变，需要区分新旧证据。
