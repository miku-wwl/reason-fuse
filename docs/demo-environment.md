# 三段演示的环境与操作

**2026-09-22/23 的真实云生命周期：部署、smoke 与删除均 PASS，临时夹具已删除。** Foundry 基础项目、模型和 v11仍可用。本轮演示 A PASS，B/C 严格断言 FAIL；下一次录制前仍要处理这两项，详见 [云端闭环报告](cloud-closeout-zh.md)。

2026-09-21 的[资源缺失读回](evidence/submission/cloud-readonly-final.json)是历史快照。之后原账户从软删除恢复，原项目重建；旧 v10 的记录虽为 active，源码下载曾失败，故将已核验的相同 ZIP 发布为 v11。本轮创建的诊断项目及临时资源组均已删除；[最终资源读回](evidence/cloud-closeout-20260922/final-resource-readback.json)保留当前状态。

## 前置条件

1. Windows PowerShell 7、Python 3.13、锁定的项目 `.venv`；Azure CLI 已登录目标订阅，已安装 Container Apps CLI 扩展；Docker Desktop 的 Linux 引擎可用。
2. 已恢复的 Foundry 项目、`gpt-5-mini` 部署、v11 `reasonfuse` 与 `operations-tools` Toolbox；每次新运行仍要读回验证。**demo-up 只管理临时 fixture，不会隐式重建 Foundry 基础平台。** v11源码包哈希与历史v10相同，但新版本的执行证据单独计。
3. 使用已有 `.azure/reason-fuse/.env` 中的非秘密配置，或明确传入 `-Subscription`、`-ProjectEndpoint`、`-ResponsesEndpoint`。凭据来自 Azure CLI 内存，不写入脚本/提交。
4. 本轮已获 USD15上限并执行、清理完毕；后续批次仍须在同一总预算内核算剩余额度、费用读回及新RunId，不能把上限重新计为 USD15。历史 [费用记录](evidence/cloud-closeout-20260922/cost-closeout.json)是当前预算账本的基础。

脚本核对既有 Agent 的名称/版本、v10 包哈希、runtime/ON 与 Toolbox 名称绑定，并要求 Responses 地址与预检的账户/项目/Agent 一致。所有条件在创建临时资源前检查；基础资源缺失会失败退出。响应还核对 Agent 和已拥有的 session 身份。外部 `store=true`，内部模型仍 `store=False`。

## 先预览计划

```powershell
pwsh -File scripts/demo-up.ps1 -RunId final-demo -AgentVersion 11 -DryRun
pwsh -File scripts/demo-smoke.ps1 -RunId final-demo -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story A -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story B -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story C -DryRun
pwsh -File scripts/demo-down.ps1 -RunId final-demo -DryRun
```

没有 `-Execute` 就只打印计划，云/模型调用均为0；不能同时指定 Execute 和 DryRun。RunId 只允许3至24个小写字母、数字、连字符，且以字母开头。

## 基础资源恢复后的一次执行顺序

```powershell
# 复用已恢复的原项目及v11；使用新的RunId。
pwsh -File scripts/demo-up.ps1 -RunId final-demo -AgentVersion 11 -Execute
pwsh -File scripts/demo-smoke.ps1 -RunId final-demo -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story A -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story B -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story C -Execute
pwsh -File scripts/demo-down.ps1 -RunId final-demo -Execute
```

若需要明确覆盖配置，只在 up 时传入：

```powershell
pwsh -File scripts/demo-up.ps1 -RunId final-demo -AgentVersion 11 -Execute -Subscription '<subscription-id>' -ProjectEndpoint 'https://<account>.services.ai.azure.com/api/projects/<project>' -ResponsesEndpoint 'https://<account>.services.ai.azure.com/api/projects/<project>/agents/reasonfuse/endpoint/protocols/openai/responses?api-version=v1'
```

RunId 不能覆盖已存在拥有清单或故事证据。出现失败时保存原批次，不自动重试到满意为止。

## up、smoke、run、down 各做什么

| 步骤 | 行为与边界 |
| --- | --- |
| up | 预检 Docker/既有 Agent；创建精确命名的资源组，所有权随机标记先落盘；创建一个 Basic ACR、拉取身份、无日志工作区的 Container Apps 环境及固定1副本应用；本地 build/push，并按镜像 digest 部署；不部署新 Agent |
| 发布 | 校验实际 FQDN 并写入 MCP host allowlist；创建新 Toolbox 版本，明确发布默认；保存旧默认以供恢复 |
| smoke | healthz、独立状态、实际 MCP tools/list 恰好两工具；Toolbox URL/原生审批和 Agent 绑定一致；无推理调用 |
| run | 每个故事新建 Agent 端点范围的 conversation 和绑定 v11 的 Hosted session；原生审批由演示 runner 发送协议对象；记录每轮独立后端状态、结果、用量和原始响应 |
| down | 恢复先前 Toolbox 默认、删除本轮新 Toolbox 版本；清理拥有清单中的会话/对话/评测版本，创建回包丢失的版本仅按同一命名范围内的精确 owner metadata 找回；独立检查资源 owner 标签与清单后删除这一个资源组，轮询读回确认不存在 |

资源组为 `rg-reasonfuse-demo-<RunId>`。资源限定为一个 ACR、一个 managed identity、一个 Container Apps environment、一个 Container App；无 AKS、APIM、数据库、监控工作区或真实服务重启。私有拥有清单位于 `.tools/demo/<RunId>/ownership.json`，不得删除它来“重新开始”。

如现存资源组同名，up 拒绝接管。down 遇到额外资源、owner 标签不符、Toolbox 默认被其他人修改、会话版本不符时拒绝对应操作，同时继续其他可独立安全完成的清理。Foundry 不可用不会跳过归属检查合格的临时资源组。逐项结果落盘；未完成项使总结果为 PARTIAL/FAIL 并非成功退出。CLI调用或回执中断可能留下部分资源，此时用原清单运行 down 并确认结果，不能认为异常退出就等于没有创建。

会话版本绑定遵循 [官方 Hosted sessions API](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/manage-hosted-sessions)：先创建 concrete version session，再在 Responses body 指定 `agent_session_id`，同时保留 conversation/previous-response 的语义。这样避免后来发布新版本改变演示对象。清理保留原生准入记录，不提供对未知业务操作的解锁功能。

## 预期输出与本轮观察

以下是严格断言目标，不表示三项已通过。本轮真实云 A 达标；B 的模型首轮没有提出审批，C 另一竞争分支返回 HTTP409但缺少明确 ReasonFuse 错误，因此 B/C 均 FAIL，未重跑取样。

- A：原生审批前零派发；完成后 attempts=1、accepted=1、状态读取至少1、匹配 HEALTHY/g2、OUTCOME_VERIFIED。
- B：先 POSTCONDITION_FAILED；再次出现原生审批后返回 BLOCKED；attempts仍1，accepted仍1。
- C：一个完成 VERIFIED，另一个输出为空且带明确的 ReasonFuse 前置准入错误；attempts=1、accepted=1。配额错误或普通 failed 不算准入拒绝。若本次云重叠没有发生，断言失败并保留结果，不能宣称已演示竞争保护。

每个故事成功时输出 `demo_assertions=PASS`，原始材料保存为 `.tools/demo/<RunId>/story-A.json` 等。这是真实运行产生的输出说明，不是预生成成功截图。

## 清理、成本与已知限制

三个故事最多9个 Responses 请求（A2、B4、C3）；内部模型调用数可能大于请求数。独立 HTTP 状态/MCP清单不是推理调用。云脚本限制输出额度并记录 reported usage；缺失用量不编造。没有自动重试模型行为。

临时实例、ACR和模型调用都可能收费。演示期间固定1副本，避免缩容至零丢失内存夹具状态；完成后立即 down，以读回确认作为清理结果。实例仍可能异常重启，因此这不是持久性保证；任何疑似状态丢失必须保留现场并停止该批次。原 Foundry 项目、模型、v11 和历史证据不由这些脚本删除。

本轮已在真实云完成一次 up/smoke/down；拥有清单记录78项清理步骤零失败，临时组不存在，Agent/Toolbox默认恢复，详见[闭环报告](cloud-closeout-zh.md)。这证明本次生命周期清理，不保证每次模型会按 A/B/C 脚本提出相同审批。
