# 三段演示的环境与操作

**本轮状态：PREPARED-NOT-DEPLOYED；基础云资源当前不可用。** 脚本、PowerShell DryRun、资源归属拒绝路径、工具配置及本地真实宿主场景已验证。未把 DryRun 当作真实部署 PASS。

2026-09-21 UTC的两次只读核查均显示 `rg-reason-fuse` 和旧临时组不存在，原订阅 Cognitive Services 账户列表为空；[最终证据](evidence/submission/cloud-readonly-final.json) 为22:25 UTC（新西兰9月22日）。原 v10 端点失效；历史云 PASS 不受此状态变化影响。删除操作者和时间未调查，本轮没有删除操作。

## 前置条件

1. Windows PowerShell 7、Python 3.13、锁定的项目 `.venv`；Azure CLI 已登录目标订阅，已安装 Container Apps CLI 扩展；Docker Desktop 的 Linux 引擎可用。
2. 有效的 Foundry 项目、`gpt-5-mini` 模型部署、已验证 v10 `reasonfuse` 与 `operations-tools` Toolbox；当前这些原有资源需要先恢复。**demo-up 只管理临时 fixture，不会隐式重建 Foundry 基础平台。** 若重建产生新的 Agent 版本/包身份，应先做有界验证并明确记录，不能将其自动称为原 v10 部署。
3. 使用已有 `.azure/reason-fuse/.env` 中的非秘密配置，或明确传入 `-Subscription`、`-ProjectEndpoint`、`-ResponsesEndpoint`。凭据来自 Azure CLI 内存，不写入脚本/提交。
4. 为一次部署和三段模型演示预留明确费用上限；当前冲刺没有获知这一数字，不进行云执行。

脚本核对既有 Agent 的名称/版本、v10 包哈希、runtime/ON 与 Toolbox 名称绑定，并要求 Responses 地址与预检的账户/项目/Agent 一致。所有条件在创建临时资源前检查；基础资源缺失会失败退出。响应还核对 Agent 和已拥有的 session 身份。外部 `store=true`，内部模型仍 `store=False`。

## 先预览计划

```powershell
pwsh -File scripts/demo-up.ps1 -RunId final-demo -DryRun
pwsh -File scripts/demo-smoke.ps1 -RunId final-demo -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story A -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story B -DryRun
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story C -DryRun
pwsh -File scripts/demo-down.ps1 -RunId final-demo -DryRun
```

没有 `-Execute` 就只打印计划，云/模型调用均为0；不能同时指定 Execute 和 DryRun。RunId 只允许3至24个小写字母、数字、连字符，且以字母开头。

## 基础资源恢复后的一次执行顺序

```powershell
# 复用有效的本地 Azure 环境配置。
pwsh -File scripts/demo-up.ps1 -RunId final-demo -Execute
pwsh -File scripts/demo-smoke.ps1 -RunId final-demo -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story A -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story B -Execute
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story C -Execute
pwsh -File scripts/demo-down.ps1 -RunId final-demo -Execute
```

若需要明确覆盖配置，只在 up 时传入：

```powershell
pwsh -File scripts/demo-up.ps1 -RunId final-demo -Execute -Subscription '<subscription-id>' -ProjectEndpoint 'https://<account>.services.ai.azure.com/api/projects/<project>' -ResponsesEndpoint 'https://<account>.services.ai.azure.com/api/projects/<project>/agents/reasonfuse/endpoint/protocols/openai/responses?api-version=v1'
```

RunId 不能覆盖已存在拥有清单或故事证据。出现失败时保存原批次，不自动重试到满意为止。

## up、smoke、run、down 各做什么

| 步骤 | 行为与边界 |
| --- | --- |
| up | 预检 Docker/既有 Agent；创建精确命名的资源组，所有权随机标记先落盘；创建一个 Basic ACR、拉取身份、无日志工作区的 Container Apps 环境及固定1副本应用；本地 build/push，并按镜像 digest 部署；不部署新 Agent |
| 发布 | 校验实际 FQDN 并写入 MCP host allowlist；创建新 Toolbox 版本，明确发布默认；保存旧默认以供恢复 |
| smoke | healthz、独立状态、实际 MCP tools/list 恰好两工具；Toolbox URL/原生审批和 Agent 绑定一致；无推理调用 |
| run | 每个故事新 conversation 和明确绑定 v10 的 Hosted session；原生审批由演示 runner 发送协议对象；记录每轮独立后端状态、结果、用量和原始响应 |
| down | 恢复先前 Toolbox 默认、删除本轮新 Toolbox 版本；清理拥有清单中的会话/对话/评测版本，创建回包丢失的版本仅按同一命名范围内的精确 owner metadata 找回；独立检查资源 owner 标签与清单后删除这一个资源组，轮询读回确认不存在 |

资源组为 `rg-reasonfuse-demo-<RunId>`。资源限定为一个 ACR、一个 managed identity、一个 Container Apps environment、一个 Container App；无 AKS、APIM、数据库、监控工作区或真实服务重启。私有拥有清单位于 `.tools/demo/<RunId>/ownership.json`，不得删除它来“重新开始”。

如现存资源组同名，up 拒绝接管。down 遇到额外资源、owner 标签不符、Toolbox 默认被其他人修改、会话版本不符时拒绝对应操作，同时继续其他可独立安全完成的清理。Foundry 不可用不会跳过归属检查合格的临时资源组。逐项结果落盘；未完成项使总结果为 PARTIAL/FAIL 并非成功退出。CLI调用或回执中断可能留下部分资源，此时用原清单运行 down 并确认结果，不能认为异常退出就等于没有创建。

会话版本绑定遵循 [官方 Hosted sessions API](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/manage-hosted-sessions)：先创建 concrete version session，再在 Responses body 指定 `agent_session_id`，同时保留 conversation/previous-response 的语义。这样避免后来发布新版本改变演示对象。清理保留原生准入记录，不提供对未知业务操作的解锁功能。

## 预期输出

- A：原生审批前零派发；完成后 attempts=1、accepted=1、状态读取至少1、匹配 HEALTHY/g2、OUTCOME_VERIFIED。
- B：先 POSTCONDITION_FAILED；再次出现原生审批后返回 BLOCKED；attempts仍1，accepted仍1。
- C：一个完成 VERIFIED，另一个输出为空且带明确的 ReasonFuse 前置准入错误；attempts=1、accepted=1。配额错误或普通 failed 不算准入拒绝。若本次云重叠没有发生，断言失败并保留结果，不能宣称已演示竞争保护。

每个故事成功时输出 `demo_assertions=PASS`，原始材料保存为 `.tools/demo/<RunId>/story-A.json` 等。这是真实运行产生的输出说明，不是预生成成功截图。

## 清理、成本与已知限制

三个故事最多9个 Responses 请求（A2、B4、C3）；内部模型调用数可能大于请求数。独立 HTTP 状态/MCP清单不是推理调用。云脚本限制输出额度并记录 reported usage；缺失用量不编造。没有自动重试模型行为。

临时实例、ACR和模型调用都可能收费。演示期间固定1副本，避免缩容至零丢失内存夹具状态；完成后立即 down，以读回确认作为清理结果。实例仍可能异常重启，因此这不是持久性保证；任何疑似状态丢失必须保留现场并停止该批次。原 Foundry 项目、模型、v10 和历史证据不由这些脚本删除。

本轮没有真实跑 up/down，所以尚无这套新自动化在云端完成一整个生命周期的证明。原有 v10 历史部署/清理证明保留；当前基础资源与预算阻塞需要先解决。
