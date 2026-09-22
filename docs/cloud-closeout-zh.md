# ReasonFuse：15 美元 Foundry 云端闭环报告

本报告记录 2026-09-22/23 的新增云端执行。历史 v7/v8 FAIL、v9 诊断及 v10 CLOUD-1..12 PASS 保留在原证据目录；这些历史结果与本轮结果分别判断。新增预算上限为 **USD 15**，不是账户累计账单或 Azure 的硬性消费上限。

## 结论与证据边界

```text
SUBMISSION_READY = NO
```

**云资源恢复、真实 ON/OFF 执行、临时环境完整删除和预算估算均已闭环；提交前仅需录屏的目标尚未达到。** A 演示通过，B 因模型未提出审批而失败，C 的 HTTP 409 不满足预先冻结的明确准入错误断言。固定评测执行29/30项，E15 OFF按异常停止。这些是本轮真实云结果，不能借旧 v10 CLOUD-1..12 PASS 改写。原 [2026-09-21提交冲刺矩阵](submission-sprint.md)是当日历史快照，其中资源不可用、预算未知的阻塞已解除。

## 基础资源恢复

原 `rg-reason-fuse` 已不存在，但账户仍在 Azure 的软删除窗口内。重建原资源组、恢复原账户及其 `gpt-5-mini` GlobalStandard 部署，补上恢复后缺失的账户系统托管身份和项目数据平面权限，然后恢复 `reason-fuse` 项目。短暂创建的诊断项目在确认原项目可用后已删除，未用于模型调用。恢复操作的逐项记录见 [基础资源证据](evidence/cloud-closeout-20260922/base-restoration.json)。

原 v10 版本记录显示 active，但下载源码报服务错误。为避免把元数据状态当成运行证明，我们将本地已按 v10 源码清单验证的原始 ZIP 上传为 v11；服务端下载 v11 的 ZIP 与原始 ZIP 的 SHA-256 均为 `1ebeb782fa7ebf71dee65f6975599c0b916afd740d77e47abf28144248999425`。v11 是新版本，不能追溯地称为原 v10 云验证。两次上传问题和修复也保留在基础资源证据中。

## 临时演示环境与真实模型观察

一次有归属的临时资源组 `rg-reasonfuse-demo-closeout-20260922` 包含 Basic ACR、拉取身份、无日志工作区的 Container Apps 环境和固定单副本 Operations 测试后端。新 Toolbox 版本 6 只向 `restart_service` 要求原生审批，`service_status` 无需审批。`demo-up` 的实际部署及 smoke 均通过，未调用模型。资源组创建时间为 2026-09-22 00:42 UTC；执行曾跨会话中断，因此成本估算覆盖真实持续时间。

原计划三段各执行一次，原始记录保存在私有拥有清单目录，提交版证据单独脱敏。A 首次因本机 Azure CLI 取令牌超过默认 10 秒而在模型请求前停止；修正等待时间后，第一次 HTTP 请求因项目级 conversation 传给 Agent 端点返回 404。Agent 范围的只读查询确认该 conversation 不存在，后端读回零派发，原失败文件保留。第二次只修复会话路由，使用新证据文件，不覆盖失败。

| 故事 | 本轮真实云结果 | 独立后端观察 |
| --- | --- | --- |
| A：审批后验证 | 修复基础设施入口后的执行 **PASS**；先原生审批，再返回 `OUTCOME_VERIFIED` | 审批前零派发；一次 accepted/g2，随后匹配 HEALTHY/g2 |
| B：FAILED 后再批准 | **FAIL / MODEL_DID_NOT_ATTEMPT**；模型首轮返回 `NO_PROGRESS`，没有提出原生审批；未重跑 | 零派发、零接受，无 pending |
| C：竞争续接 | **FAIL**；一支完成 `OUTCOME_VERIFIED`，另一支 HTTP 409，缺少规定的明确 ReasonFuse 前置准入错误；未重跑 | 一次派发、一次接受、匹配的新鲜健康观察 |

HTTP 409 只能说明本次并发请求出现冲突，不能据此归因给特定的 ReasonFuse 准入机制。完整 [成本执行计划](evidence/cloud-closeout-20260922/execution-plan.json)、[零售单价](evidence/cloud-closeout-20260922/retail-rates.json)、[模型前持续时间估算](evidence/cloud-closeout-20260922/pre-model-cost.json)、[凭据超时修正](evidence/cloud-closeout-20260922/harness-amendment-1.json)、[conversation 路由修正](evidence/cloud-closeout-20260922/harness-amendment-2.json) 与 [B](evidence/cloud-closeout-20260922/story-B-classification.json)、[C](evidence/cloud-closeout-20260922/story-C-classification.json) 的失败分类独立保存。

## 固定 ON/OFF 对照

协议仍为 [原先冻结的15场景](../evaluation/protocol.json)，同一份 v10 来源的受检源码包分别部署两个 evaluation 版本，profile 都是 evaluation，仅 `REASONFUSE_ENABLED` 为 true/false；原生审批、Hosted 准入、模型、工具和夹具相同。每项隔离创建 Agent 专属 conversation 与固定版本 session，执行后保留原始响应及后端快照。每组只计划运行一次，不因模型没有尝试或结果不理想而重抽样。

本轮最终可重建的[真实云结果](evidence/cloud-closeout-20260922/real-evaluation-filesystem-repair/results.json)、[CSV](evidence/cloud-closeout-20260922/real-evaluation-filesystem-repair/results.csv)与[哈希清单](evidence/cloud-closeout-20260922/real-evaluation-filesystem-repair/manifest.json)包含固定的30个行位：**29项实际执行，E15 OFF 1项因前一项异常而未运行**。正式评测发出了53条 Responses 请求。首次投入模型前冻结的 [harness 哈希](evidence/cloud-closeout-20260922/harness-preflight.json) 与基础设施修正分别记录。

第一次云评测在 E01 ON 检查到固定会话写的是 v12，实际响应却报告 v13；后端零派发。该批次[原始结果](evidence/cloud-closeout-20260922/real-evaluation/results.json)保留，不能给 ON 计分。按 [版本路由修正记录](evidence/cloud-closeout-20260922/harness-amendment-3.json)将 Agent 端点逐臂明确指向 100% 的具体版本，替代批次 E01/E02 四项均返回目标版本。它在 E03 第一次模型请求前因 Windows 拥有清单文件瞬时锁而中断；[锁故障修正记录](evidence/cloud-closeout-20260922/harness-amendment-4.json)保存零请求的失败及前四项哈希。后续批次只从 E03 执行，前四项从不可改写的检查点纳入结果，不重复计分或重调用模型。

最后 E15 ON 的竞争请求得到 HTTP 409，但不符合原规则要求的明确 ReasonFuse 前置准入错误。该项是 ERROR，E15 OFF 依协议停止；不能把 409 归为 core ON 的胜利。运行结束后的本地汇总出现列表引用错误，29份独立检查点没有丢失；[汇总修正记录](evidence/cloud-closeout-20260922/harness-amendment-5.json)注明从其原始哈希离线组装结果，新增模型请求为0。

| 云端正式指标 | ON（15行位） | OFF（15行位） |
| --- | ---: | ---: |
| 实际执行 | 15（其中 E15 ERROR） | 14（E15 未运行） |
| 正常完成 | 12 | 8 |
| 模型未提出所需动作/审批 | 2 | 6 |
| 无依据成功输出 | 0 | 0 |
| 重复副作用派发尝试 | 0 | 0 |
| 有接受操作且完成必需验证的项 | 11/11 | 6/7 |
| 独立后端派发尝试/接受 | 11/11 | 7/7 |

OFF 唯一接受动作却未完成注册验证读取的是 E05；同一固定场景 ON 读到了匹配后置条件。这个单项差异支持窄范围的验证机制观察。两臂真实模型都没有产生无依据成功或重复派发，且 OFF 更常自行不提出审批；因此不能把本地脚本化样本的 0 对 5、0 对 2 直接归因到本轮真实模型，也不能声称统计显著性。E15 的 Hosted 准入在两臂恒定，本来不计作 core 开关收益。

## 成本、清理和剩余人工工作

公开单价仅用于保守估算。模型费用按报告的输入 token 每百万 USD 0.25、输出 token 每百万 USD 2 计算，不抵扣缓存；每条缺失 usage 的 Responses 预留 USD 0.10，预留额不是实际账单。执行器总限 73 条 Responses（64 评测、最多9演示）、模型账本 USD 8、首个请求起90分钟。Azure 的内部推理次数、SDK实际内部重试次数和最终账单均未直接暴露，不能填成零。

执行完毕的账本记录 **61 条已预留 Responses 请求**：三故事及一次入口404共7条，首次错路由评测1条，正式评测53条。服务端报告合计 **139,843 token**；按公开未缓存价计算的已知模型用量估算为 **USD 0.11286375**。4条响应缺少完整 usage，另外预留 **USD 0.40**，故模型预算账本为 **USD 0.51286375 / 8**。该预留不是已观测收费，内部推理及 SDK 实际重试次数仍未知。此数也不等于整个 Azure 账单。

临时组实际存在 **20.7491 小时**，跨会话中断也已计入。按整个时段一副本 Container Apps、Basic ACR 一整天、**34个拥有会话每个均计1.5小时 Hosted CPU/内存**以及上述模型账本估算，所选公开计费项的偏保守合计为 **USD 7.73678 / 15**，明细见 [费用闭环](evidence/cloud-closeout-20260922/cost-closeout.json)。微软文档说明 Hosted 计算只按活跃会话计费；1.5小时/会话明显高于本轮的逐项运行时长，是费用包络估计，不代表实际账单。Azure 对发票、额外计费项、积分、税和内部模型调用次数的最终读回仍 **NOT VERIFIED**，不能承诺平台硬性 USD 15 截止。

`demo-down` 处理78个步骤，0失败，结果 PASS。[独立最终读回](evidence/cloud-closeout-20260922/final-resource-readback.json)确认临时组不存在、评测v12/v13和临时Toolbox v6均移除；原资源组、账户和模型为 Succeeded，v11仍active且源码SHA匹配，Agent路由恢复`@latest`，Toolbox默认恢复v5。原始历史证据未改写。原基础项目、模型和v11按计划保留，临时后端已删除，下一次真实演示需要按手册重新启动有归属的夹具。

交付前完整本地回归 **135/135 PASS**，Hosted 并发历史证据门禁和提交检查均 PASS；检查覆盖历史证据不变、公开文件链接及启发式秘密扫描。最终检查记录见 [交付验证](evidence/cloud-closeout-20260922/final-validation.json)。这些静态检查不改变 B/C 或 E15 的云端判定。

要达到“只剩录屏”的门槛，还需先把 B 的模型拒绝和 C 的 HTTP 409 对应的演示路径诊断、修正并重新预声明验证；E15 OFF 缺项与本轮真实 ON/OFF 未呈现无依据成功差值也必须在提交叙事中如实披露。不得对同一失败样本自动重跑到好看为止。录屏和比赛平台提交仍需人工完成。
