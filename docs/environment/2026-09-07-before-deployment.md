> 历史快照：本报告记录 2026-09-07 部署前的只读检查。文中的资源缺失和未配置状态
> 不代表当前环境；后续部署与实跑结果见 [Phase 1 报告](../phases/phase-01-runtime-validation/report.md)。

# ReasonFuse 环境验证报告

**日期：** 2026-09-07  
**环境：** Azure for Students（临时开发环境）  
**范围：** 仅执行只读验证。未修改 Azure 资源、架构或仓库代码。

## 总体结论

该订阅可用于初步开发，但**尚未达到冻结版 ReasonFuse 架构的部署条件**。

- Azure 身份验证和核心资源提供程序注册通过。
- 该订阅已启用消费额度上限，并通过订阅级策略将资源部署区域限制为五个区域；GPT-5-mini 在 Australia East 和 Southeast Asia 有 `500 TPM` 的 GlobalStandard 配额。
- 对 Intelligent Model Routing 而言，Australia East 的可用模型配额最丰富；Southeast Asia 可使用 3 个 OpenAI 在线模型；Japan West 可使用 MaaS 开源模型配额。
- `gpt-5-mini` 以上的 GPT-5 系列在 Australia East 和 Southeast Asia 均显示 `limit=0`；Japan West 没有返回 GPT-5 以上模型行。
- 当前订阅尚未创建 Foundry、Hosted Agent、APIM 或 Application Insights 资源。
- 仓库中没有 Terraform 文件、`azure.yaml`、`.azure/deployment-plan.md`、应用源码或 tracing 配置。
- 未发现真正的架构阻塞问题。目前的阻塞因素是环境容量和缺失的项目配置。

## 验证矩阵

| 要求 | 结果 | 证据 | 问题分类 |
|---|---|---|---|
| 订阅 / 租户 | **通过** | 订阅为 `Azure for Students`，ID 为 `7c73b89d-485e-43a9-8d66-b12b766d567f`；租户为 `96e2f052-4512-4d4c-b2c0-cd0d36ad6437`；订阅状态为 `Enabled`。 | 无 |
| 区域 | **通过但受限** | 订阅级 `Allowed resource deployment regions` 策略以 `Deny` 强制限制为 Australia East、Southeast Asia、Japan West、Indonesia Central 和 Malaysia West。 | **2. 学生订阅限制** |
| 必需资源提供程序 | **通过** | `Microsoft.CognitiveServices`、`Microsoft.MachineLearningServices`、`Microsoft.App`、`Microsoft.ApiManagement`、`Microsoft.Insights`、`Microsoft.OperationalInsights`、`Microsoft.ManagedIdentity`、`Microsoft.Authorization`、`Microsoft.ContainerRegistry`、`Microsoft.Storage` 和 `Microsoft.Network` 均为 `Registered`。 | 无 |
| Foundry 可用性 | **有条件可用** | Cognitive Services 提供程序支持 Foundry account/project 类型，但实际部署只能使用上述五个订阅允许区域。当前没有 Foundry account 或 project，无法测试创建和 API 访问。 | **2. 学生订阅限制**；项目目标缺失另属 **1. 代码/配置问题** |
| Hosted Agent 可用性 | **有条件可用** | Hosted Agent 所需资源类型在 Azure 控制平面可见，但订阅策略只允许上述五个区域；未实际执行 Hosted Agent 创建。 | **2. 学生订阅限制**；模型容量另有 **3. 区域/配额问题** |
| 模型配额 / Intelligent Model Routing | **部分通过** | Australia East 有 `o4-mini`、`4.1-mini`、`gpt-5-mini` 以及 MaaS 模型配额；Southeast Asia 有 `o4-mini`、`4.1-mini`、`gpt-5-mini`；Japan West 有 Llama、Phi、Mistral、Codestral 和 `gpt-oss-120b` MaaS 配额。`gpt-5-mini` 以上的 GPT-5 系列在已查询区域均为 `limit=0` 或未返回。 | **3. 区域/配额问题** |
| APIM 可用性 | **有条件可用** | `Microsoft.ApiManagement` 已注册，但实际部署只能使用学生订阅允许的五个区域。当前没有 APIM 实例。 | **2. 学生订阅限制**；实际 SKU 创建仍未验证 |
| Managed Identity / RBAC | **操作员访问通过；部署身份未验证** | 当前登录用户可解析，并在订阅范围拥有 `Owner`。`Microsoft.ManagedIdentity` 和 `Microsoft.Authorization` 已注册。没有 ReasonFuse 的 user-assigned 或 system-assigned identity。 | 缺少部署身份接线属于 **1. 代码/配置问题** |
| Application Insights / tracing | **未配置** | `Microsoft.Insights` 和 `Microsoft.OperationalInsights` 已注册，但订阅资源清单中没有 ReasonFuse App Insights component 或 workspace。仓库中没有应用源码或 telemetry 配置。 | **1. 代码/配置问题** |
| Terraform 部署 | **未就绪** | `terraform validate` 返回成功，但原因仅是仓库没有 Terraform 配置可供验证。 | **1. 代码/配置问题** |
| azd 部署 | **未就绪** | `azd env list` 报告 `ERROR: no project exists; to create a new project, run azd init`。不存在 `azure.yaml`。 | **1. 代码/配置问题** |
| 干净重新部署可行性 | **未证明** | 没有 IaC 文件、azd 项目、目标资源组、Foundry project、模型部署、APIM 实例、identity 或 telemetry 资源可供销毁和重建。即使补齐配置，模型部署应优先选择 Australia East 或 Southeast Asia。 | **1. 代码/配置问题**；模型区域选择属于 **3. 区域/配额问题** |

## 订阅和区域详情

当前账户信息：

```text
Name:       Azure for Students
Subscription: 7c73b89d-485e-43a9-8d66-b12b766d567f
Tenant:     96e2f052-4512-4d4c-b2c0-cd0d36ad6437
State:      Enabled
Quota ID:   AzureForStudents_2018-01-01
Spending limit: On
```

订阅级 `Allowed resource deployment regions` 策略（策略 ID：`sys.regionrestriction`）以 `Deny` 生效，只允许以下五个资源部署区域：

```text
Australia East       australiaeast
Southeast Asia       southeastasia
Japan West           japanwest
Indonesia Central    indonesiacentral
Malaysia West        malaysiawest
```

这五个区域是学生订阅的实际资源部署范围；`az account list-locations` 返回的其他 Azure 公共区域不代表本订阅可以部署资源。

## 模型配额详情

只读命令 `az cognitiveservices usage list --location` 对五个允许区域的非零模型相关配额扫描结果如下。单位为 TPM（千 token/分钟）；RPM 为请求/分钟。

| 区域 | 在线/GlobalStandard 模型 | MaaS 模型 | 其他模型配额 |
|---|---|---|---|
| Australia East | `o4-mini` 100；`4.1-mini` 200；`gpt-5-mini` 500 | `Llama-3.3-70B-Instruct` 20；`Phi-4` 20；`Phi-4-mini-instruct` 20；`Phi-4-mini-reasoning` 20；`Phi-4-multimodal-instruct` 20；`Phi-4-reasoning` 20；`mistral-medium-2505` 20；`mistral-small-2503` 20；`Codestral-2501` 20；`Llama-4-Scout-17B-16E-Instruct` 20；`gpt-oss-120b` 5000 | Embeddings：`text-embedding-3-small` 350/1000；`text-embedding-3-large` 350；`Text-Embedding-Ada-002` 350；FLUX.2-pro 15 RPM；FLUX.2-flex 5 RPM |
| Southeast Asia | `o4-mini` 100；`4.1-mini` 200；`gpt-5-mini` 500 | 本次查询未返回非零 MaaS 单模型配额 | Embeddings：`text-embedding-3-small` 1000；`text-embedding-3-large` 350 |
| Japan West | 本次查询未返回非零 OpenAI 在线模型配额 | `Llama-3.3-70B-Instruct` 20；`Phi-4` 20；`Phi-4-mini-instruct` 20；`Phi-4-mini-reasoning` 20；`Phi-4-multimodal-instruct` 20；`Phi-4-reasoning` 20；`mistral-medium-2505` 20；`mistral-small-2503` 20；`Codestral-2501` 20；`Llama-4-Scout-17B-16E-Instruct` 20；`gpt-oss-120b` 5000 | 无相关 embedding 行返回 |
| Indonesia Central | Cognitive Services usage API 不支持该区域 | 无法通过该 API 验证 | 无法通过该 API 验证 |
| Malaysia West | Cognitive Services usage API 不支持该区域 | 无法通过该 API 验证 | 无法通过该 API 验证 |

### Intelligent Model Routing 建议

如果路由器要求多个可实际调用的模型，优先考虑以下组合：

1. **Australia East：** `gpt-5-mini`、`o4-mini`、`4.1-mini`，并可加入 MaaS 的 `Llama-3.3-70B-Instruct`、`Phi-4` 或 `mistral-small-2503`。
2. **Southeast Asia：** `gpt-5-mini`、`o4-mini`、`4.1-mini`，适合作为跨区域的 OpenAI 模型候选。
3. **Japan West：** 适合作为 MaaS 开源模型候选区域，不应假定 GPT-5-mini 或 OpenAI 在线模型可用。

`500 TPM`、`200 TPM`、`100 TPM` 等数值是订阅配额上限，不代表模型部署、Foundry Hosted Agent、APIM 路由或实际推理调用已经成功；仍需在具备 IaC/项目配置后执行部署级验证。Quota 行也不等同于模型目录中的可部署 SKU，最终还要检查模型版本、部署类型和区域容量。

原先 East US 的 GPT-4/GPT-4o 零配额结果仍然成立，但 East US 不在该学生订阅允许的五个资源部署区域内，因此不应作为 ReasonFuse 的候选部署区域。

### GPT-5-mini 以上系列

在允许区域中，命令查询到的更高 GPT-5 系列均没有可用配额：

| 区域 | 查询结果 |
|---|---|
| Australia East | `gpt-5`、`gpt-5-chat`、`gpt-5-pro`、`gpt-5.1`、`gpt-5.2` 及后续 GPT-5 系列均为 `limit=0` |
| Southeast Asia | `gpt-5`、`gpt-5-chat`、`gpt-5-pro`、`gpt-5.1`、`gpt-5.2` 及后续 GPT-5 系列均为 `limit=0` |
| Japan West | 未返回 GPT-5-mini 以上系列配额行 |
| Indonesia Central | Cognitive Services usage API 不支持该区域 |
| Malaysia West | Cognitive Services usage API 不支持该区域 |

因此，当前订阅可验证的 OpenAI 在线模型上限是 `gpt-5-mini`，不是 `gpt-5` 或更高版本。目录中出现模型名称不等于该订阅已获得可部署配额。

## 现有 Azure 资源

该订阅中只有无关的 `CERTFORGE-RG` VM/网络资源和 Azure Network Watcher 资源。未找到 ReasonFuse 目标资源：

- 没有 Cognitive Services / Foundry account 或 project
- 没有 APIM service
- 没有 ReasonFuse Application Insights component
- 没有 ReasonFuse Log Analytics workspace
- 没有 ReasonFuse managed identity

## 本地部署证据

仓库中只有 `README.md` 和 `.git/`。不存在：

- `azure.yaml`
- `.azure/deployment-plan.md`
- Terraform `.tf` 配置
- 应用源码或容器定义
- 模型部署配置
- APIM 配置
- managed identity/RBAC 配置
- Application Insights/OpenTelemetry 配置

因此，在该仓库没有冻结版架构现有部署制品的情况下，无法测试干净重新部署。创建这些制品属于实现工作，本次验证未执行。

## 架构评估

**未发现真正的架构阻塞问题。** Azure 控制平面公开了所需的资源类型和候选区域，操作员拥有订阅级 Owner 权限。当前环境受到学生订阅区域限制、不同区域模型配额不均，以及缺失的部署/项目配置影响。这些问题分别归类为订阅限制、区域/配额问题或代码/配置问题，不要求修改冻结版架构。

## 已执行命令

```text
az account show
az account list --all
az account list-locations
az provider show --namespace <provider>
az resource list --subscription <subscription-id>
az rest --method get --url /subscriptions/<subscription-id>
az ad signed-in-user show
az role assignment list --assignee-object-id <user-object-id> --all --include-inherited
az cognitiveservices usage list --location eastus
az cognitiveservices usage list --location australiaeast
az cognitiveservices usage list --location southeastasia
az cognitiveservices usage list --location japanwest
az cognitiveservices usage list --location indonesiacentral
az cognitiveservices usage list --location malaysiawest
az policy assignment list --scope /subscriptions/<subscription-id>
az policy definition show --name b86dabb9-b578-4d7b-b842-3b45e95769a1
az cognitiveservices account list --subscription <subscription-id>
az apim list --subscription <subscription-id>
terraform validate
azd env list
git status --short
```

未执行资源创建、部署、角色分配、配额申请或架构变更。