# ReasonFuse 人工对账与恢复手册

适用范围：当前 Hosted admission 与 `reasonfuse_core_v1`，对应已通过验证的 v10 行为。本手册用于判断是否可以继续业务，不实现自动恢复。代码依据：[宿主边界](../src/reasonfuse/main.py)、[准入记录](../src/reasonfuse/host_admission.py)、[完成边界](../src/reasonfuse/completion.py)。

**fail-closed 阻止没有依据的重复执行，但不会自动恢复业务可用性。当前没有受支持的自动解锁、lease 到期接管或操作重试接口。** 不要删除准入记录、清空 AgentSession、重建旧响应链或新开会话来绕过未知操作。

## 1. 先停止派发，再保存现场

出现 BUSY、UNKNOWN、持久化失败或续接拒绝时，操作人应按以下顺序处理：

1. 停止该业务资源的自动重试、并发续接与新的审批执行；允许独立只读观察。指定一名对账负责人，避免多人同时“恢复”。
2. 保留完整的 response、conversation、previous response、平台 session 标识和 UTC 时间范围。私有标识保存在受控位置；公开证据使用稳定别名，不保存 bearer token 或环境变量全集。
3. 保存客户端完整响应状态和错误、原生审批请求/响应、工具调用及返回、Hosted 日志、AgentSession 快照、准入记录与 ETag、对应 response alias。对证据计算哈希，并注明采集时间、源码版本、Agent 版本和 fixture 是否重启/重置。
4. 从外部系统查询本次操作是否执行，以及执行后是否达到目标。优先使用操作流水/operation ID、resource、generation 与新鲜观察；不要让模型文字代替外部事实。
5. 按下表分类。缺少任何关键证据时保持 UNKNOWN，升级给应用维护者及外部系统负责人；不要以“等了很久”为理由放行。

在演示夹具中，独立的 `GET /test/state` 可以读取 `restart_attempt_count`、`restart_count`、`status_read_count` 与事件时间；该读取不消耗注册验证读取。**不要先调用 `POST /test/reset` 再采集现场。** 管理接口未暴露为 Agent 工具。

## 2. 哪些事实能够证明什么

| 观察 | 可以得出的结论 | 不能据此推断 |
| --- | --- | --- |
| 原生审批被接受 | 这次提议获得授权 | 已派发、已执行或已成功 |
| 工具返回 `accepted=true` / HTTP 202 | 外部系统接受了请求，并可能返回本次 generation | 后置条件已成立 |
| 外部权威操作记录显示本次执行，resource/operation ID/generation 能关联 | 操作已执行或被接受，禁止盲目重复 | 服务已 HEALTHY，或会话保存已成功 |
| 对应 resource、匹配本次 generation 的新鲜 HEALTHY 观察 | 当前注册后置条件成立，可用于人工对账 | 自动修改持久化状态为 VERIFIED 的授权 |
| 匹配 generation 的 UNHEALTHY/DEGRADED | 已观察到本次操作未达到目标 | 重试一定安全 |
| 客户端超时、HTTP 错误、failed Responses 或没有返回文本 | 客户端没有得到完整成功确认 | 操作没有执行 |
| 旧 HEALTHY 结果、generation 不匹配、观察缺失 | 本次结果仍不足以验证 | 可以宣称成功 |
| 同一未重置夹具实例的完整事件窗口，审批前后 attempts/executions 均为 0 | 在该受控测试窗口内未派发/执行 | 真实生产系统通用的“从未执行”证明 |

夹具是内存状态，进程重启或 `/test/reset` 会重置记录，事件列表最多保留 128 条。发生重启、重置、丢失或截断后，`restart_count=0` 不能证明此前未执行。未来真实业务接入必须另行定义持久、可关联的外部审计来源；本手册没有把夹具计数当作生产日志。

## 3. 需要读取的持久化状态

准入位于原生 Foundry State Store：`reasonfuse_host_admission_v1`，启用 `user_isolation=True`，TTL 为 `-1`。读取必须使用拥有该会话的身份和隔离范围；看不到记录不等于记录不存在。当前仓库没有远程准入编辑/解锁命令，以下是维护者使用平台支持的只读诊断时应采集的字段，不是直接修改存储的指令。

| 对象 | 键与检查项 |
| --- | --- |
| 规范准入记录 | 显式会话为 `conversation:<conversation_id>`；根请求为 `root:<response_id>`；读取 `version`、`phase`、`owner`、`head`、ETag |
| 响应别名 | `response:<response_id>` 的 `gate` 必须指向同一规范准入记录；previous-response 续接通过这个别名寻址 |
| 权威 AgentSession | 按当前宿主路径读取对应 conversation 或 previous-response 的会话；保留完整快照及其时间/版本信息 |
| ReasonFuse 核心 | `reasonfuse_core_v1` 内的 `run_id`、`action_lifecycle`、`pending_postcondition`、`last_postcondition_result`、`contained`、`fuse_reason`、各计数、contract 与审批状态 |
| 平台与客户端 | 本次 response 的完成/失败状态、取消记录、SDK 保存错误、原生审批 ID、相应工具调用与外部 operation ID |

正常顺序是：**取得 BUSY → 恢复会话 → 执行/验证 → 保存 AgentSession → 创建 response alias → 条件写 IDLE/new head → 释放 completed 事件**。`IDLE` 仅表示准入允许下一回合，不表示业务成功；会话仍可能保存 FAILED/UNKNOWN 和 containment。

网络异常可能发生在服务端写入成功而客户端尚未收到回执之间。因此，“保存/发布报错”不能单独证明写入没有发生，也不能保证重新读取时一定是 BUSY。应同时核对 gate、alias、session 和外部状态；不一致或无法读取即停止。本项目未验证网络分区恢复。

## 4. 按故障情形操作

| 情形 | 必须检查 | 当前安全处理 |
| --- | --- | --- |
| admission 一直 BUSY | owner response 是否仍在运行/取消；外部派发和执行记录；会话是否保存；alias/head 是否发布 | 活跃 owner 不接管；终态或失联也不按时间解锁。保留现场并人工对账，维持拒绝新的执行 |
| 前次结果 UNKNOWN | 接受结果中的 resource/generation；注册验证为何缺失、陈旧、超时或不匹配；外部最终记录 | 独立只读补充证据。即使人工随后确认结果，也不直接改写历史 UNKNOWN 或自动重试 |
| AgentSession 保存失败 | 工具是否已经执行；完成后的状态是否存在完整持久化副本；审批是否已消费；gate owner | 当前请求不能被当成未执行。不要从旧快照恢复一个新预算，升级维护者确定受控迁移/终结方案 |
| response alias 创建或 head 发布失败 | AgentSession 是否已保存；新 alias 是否存在及指向；gate 的 owner/head/ETag；是否出现客户端回执歧义 | 保存三者快照，拒绝重放旧审批。当前无支持的修复写回命令，不能手工补一个 head 假装完成 |
| 外部副作用可能执行 | 外部操作流水、operation ID、generation、新鲜状态、完整时间窗口 | 分类为已执行/未执行/仍未知；未知保持阻断。不能用响应失败或当前健康状态替代操作对账 |
| authoritative AgentSession 缺失 | 是否使用正确用户隔离范围/键；是否过期、被删除或存储不可用；gate/alias 是否仍存在 | 不创建空会话补位。保存原有准入，原业务资源维持停止；维护者/平台支持检查持久化来源 |
| stale branch 被重放 | 请求 previous_response_id 与当前 head；是否有后续成功或仍未知操作；现有 alias 链 | 丢弃这个旧分支的执行请求，不修改 head。只在已完成对账且 session 一致时，从当前 head 继续普通诊断/对话 |
| legacy previous chain 没有 admission alias | 是否来自 v10 之前的链；历史审批/操作是否已结束 | 该续接被有意拒绝。先结束历史业务对账，再由负责人决定是否开启一个独立的新任务 |

准入冲突当前表现为 `status=failed` 的 Responses envelope，错误码为 `server_error`；不要写只识别 HTTP 409 的自动重试器。外部请求必须 `store=true`。`store=false` 是不支持的请求，历史负向验证返回 HTTP 500；不能用它绕过协调。

## 5. 三类对账结果与重试条件

| 结果 | 判据 | 下一步 |
| --- | --- | --- |
| **已执行** | 外部权威记录能关联本次操作，或已收到有效接受结果且不能排除执行 | 不重复原操作。按新鲜匹配观察判断业务成功/失败；保留 FAILED/UNKNOWN 历史与全部证据，由业务负责人决定后续独立处理 |
| **未执行** | 外部系统的完整、可信记录能排除本次派发/执行，且没有在途 owner；本地/平台证据一致 | 这只满足业务上的必要条件，不自动修复存储。维护者还必须证明审批、会话、gate、alias/head 一致；当前无通用解锁命令 |
| **仍未知** | 记录缺失、重置、截断、资源/generation 不匹配、状态写回不一致或仍有在途请求 | 保持阻断；升级外部系统负责人/平台支持。不要删除记录、重复审批、回退快照或换新会话“试一次” |

允许正常续接的最小条件是：owner 已完成、权威会话存在、gate/alias/head 一致，且请求使用最新 head；会话内 FAILED/UNKNOWN containment 仍然有效。**重新审批不会解除 containment。** 当前实现没有将人工新观察写回并解除旧会话 containment 的产品化操作。

如需恢复业务可用性而上述条件无法满足，应由维护者提出独立的、经过审查的恢复变更，附外部业务负责人确认、状态迁移方案、重复执行风险、回滚/终止依据和审计记录。未完成这一步前，安全终态可以是“停止并交人工处理”，不必强行让 Agent 恢复。不要将这项未来生产能力写成已实现。

## 6. 演示夹具的特殊处理

演示中使用的 `orders` 不是真实基础设施。一个故事完成、无在途请求且已保存结果后，可以通过[准备好的演示流程](demo-script.md)重置夹具，再开启**独立的新故事/新会话**。这只是测试数据重置，不是 BUSY/UNKNOWN 恢复。

若演示中断于执行、保存或发布阶段：先采集现场并停止该故事；不得反复运行直至出现漂亮结果。完成清理和故障分类后才安排新的演示批次，保留失败批次。测试会话清理也不应删除准入状态来制造可续接假象。

## 7. 证据与维护验收

- [v10 云验证报告](evidence/p0-hosted-concurrency-validation.md)：真实 Hosted 并发、失败遏制与已知限制。
- [准入回归测试](../tests/test_host_admission.py)：取消、保存失败、发布失败、缺失会话、存储不可用与 stale head。
- [原始 v7/v8 FAIL](evidence/p0-foundry-cloud-validation.md)：历史失败保留。
- [v9 原生身份诊断](evidence/p0-foundry/hosted-concurrency/V9-native-identity.json)：不得根据 Python 对象锁推断云端互斥。

操作记录至少应写明：事件编号、负责人、UTC 时间、私有证据存放位置与公开哈希、source/Agent/SDK 版本、业务资源及操作关联信息、三类对账结论、是否有任何写操作、谁批准后续业务处理、未解决事项。证据不足时明确写 UNKNOWN，不能用“已恢复”掩盖尚未完成的对账。
