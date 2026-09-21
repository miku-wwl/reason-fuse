# 最终录制脚本（只准备，不录制）

目标约5至7分钟。只讲三个故事；不展示假截图，不把历史结果说成当前正在发生。

**录制前阻塞：** 原 Foundry 资源已不在订阅清单中，云比较未执行。先解决 [最终验收](submission-sprint.md) 的预算与云可用性阻塞，按 [环境手册](demo-environment.md) 建立、确认环境。现在不要宣称只差录像。

## 开始前

- 打开 README 架构、终端、[v10证据报告](evidence/p0-hosted-concurrency-validation.md)、[评测表](evaluation.md)。
- 终端只显示演示摘要，不显示 `.env`、访问 token、注册表登录输出或 Azure 全量配置。
- 先做 demo-smoke，确认 `DEMO_CONFIG_SMOKE=PASS`；这是配置/工具清单检查，不是模型结果。
- 保留足够费用运行一次三故事；已有故事文件时不覆盖。原生审批由 runner 演示协议过程，讲解时不要假装是在 UI 上手动点过审批。

## 片段1：问题（约30秒）

讲解：“Agent 说成功、工具接受请求、外部操作执行、目标状态达到，是不同的事情。HTTP 202 不能证明服务恢复。ReasonFuse 要求成功结论由匹配的新鲜外部证据支持。”

画面：README 问题段落。

## 片段2：架构（约30秒）

画面：README Mermaid 图。

讲解：“一个 Foundry Hosted Agent 使用原生审批与 Toolbox。确定性运行时负责预算、验证和遏制。持久化准入在恢复会话前协调执行权，一直保持到状态保存。”

## 片段3：Demo A，接受之后还要验证（约60秒）

```powershell
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story A -Execute
```

依次指出原生审批请求、runner 发回的审批响应、后端 accepted/g2、注册 service_status、HEALTHY/g2 和最终 OUTCOME_VERIFIED。画面中的 attempts=1、accepted=1 来自独立后端观察。

讲解：“关键不在模型说了成功，而在运行时拿到了本次变化对应的健康观察。”

## 片段4：Demo B，FAILED 后的新审批也被阻止（约75秒）

```powershell
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story B -Execute
```

指出匹配 generation 的 UNHEALTHY、POSTCONDITION_FAILED、containment，然后展示第二份新原生审批后的 BLOCKED。独立 attempts 仍为1，没有第二次派发。

讲解：“审批只表达授权，不会清除失败遏制。失败关闭阻止继续执行，但不自动修复业务。”

## 片段5：Demo C，两个竞争续接（约60秒）

```powershell
pwsh -File scripts/demo-run.ps1 -RunId final-demo -Story C -Execute
```

指出一个 VERIFIED、另一个 failed admission、一次派发和一次接受执行。如果脚本竞争断言未成立，保留失败证据并停止本段，不剪辑成成功。

准确讲解：“In this tested concurrent continuation scenario, only one side-effect execution was accepted.” 随后补充：“这不是通用分布式 exactly-once。”

## 片段6：证据与评测（约45秒）

展示当前最终回归计数，以及历史真实 v10 CLOUD-1..12 PASS。说明 v7/v8 FAIL 和 v9 诊断没有删除，v10 修复位于恢复/保存会话的边界。

展示15对本地控制表：ON无依据成功0、OFF5；重复派发尝试0和2。必须同时说：“这些是脚本化模型的机制对照，真实模型ON/OFF还未执行，不能当作真实模型错误率或统计收益。” 如果将来有新的真实云结果，使用其独立报告，不修改本轮历史计分文件。

## 片段7：限制与结束（约30秒）

讲解：“当前只覆盖注册的重启/状态验证，后端是内存测试夹具。项目不声称通用防幻觉、任意工具正确性、生产就绪、分布式 exactly-once、高负载或网络分区恢复。”

录制结束后执行并确认：

```powershell
pwsh -File scripts/demo-down.ps1 -RunId final-demo -Execute
```

保留原始材料、失败片段和清理结果。人工剩余动作在阻塞解除后应为启动环境、执行上述序列、录像/截图、上传提交；当前阻塞不能靠剪辑或文案消除。
