# 最终提交冲刺：审计与验收

开始日期：2026-09-21。基线 `97738312e7d3ee6e6eb8066ac795fc7755c06a38` 相对 `389d1e1` 只增加中文报告，运行时与 v10 相同。原有未跟踪 PDF 导出保留，用精确 gitignore 项排除；提交文档以 Markdown 为准。

## 修改前的缺口矩阵

| Area | Current | Required | Action |
| --- | --- | --- | --- |
| Core correctness | 与 v10 发布身份相同 | frozen | 保持 src、依赖及架构不变 |
| Local tests | 起始重跑 100/100，6.781 秒 | PASS | 新增工具测试后跑整套 |
| Hosted evidence | 12/12 PASS，28 source + 70 evidence hashes 匹配 | preserved | 新证据分目录，保留历史 |
| README | v6、外部 store=false 等陈旧说明 | current v10 | 重写入口，历史文档单独标识 |
| Demo reproducibility | 低层请求脚本，后端已删除 | ready | up/smoke/run/down 与资源拥有清单 |
| Benchmark | 尚无固定15场景 | bounded result | 冻结协议、控制实验、预算边界 |
| Recovery documentation | 散见代码与报告 | ready | 人工证据对账与升级手册 |
| Local real-model E2E | 历史结果、daemon 可发现 | optional | 现有模型可用才做一次 smoke |
| Submission materials | 无统一摘要与录制脚本 | ready | 三故事、命令、边界、证据链接 |

审计后才开始编辑。并行代理完成初查和部分文件后遇到工具额度限制，由主代理接手。没有扩大架构范围。

## 预算

任务说明剩余预算有限但未给出金额；已询问可用上限。在明确额度之前不新增 Azure/付费模型费用。30 scored executions 不等于30模型调用；原生审批需要多次 Responses 请求，平台未暴露的内部模型调用数保持未知。

## 最终验收

```text
SUBMISSION_READY = NO
```

本地工程、证据整理和提交材料已完成。未解除的具体阻塞是：**云可用性**（原 Foundry 基础资源不存在，无法运行现有 Hosted 演示）与 **预算/真实模型对照证据**（没有可用费用数字上限，云 ON/OFF 未执行）。这不是因可选的生产架构功能而判定未就绪，也不能称为现在只差录像。

| Gate | Result | Evidence |
|---|---|---|
| Core architecture unchanged except required bugfixes | PASS | 32个核心/部署/锁定依赖文件与基线相同；本轮只修改辅助脚本与材料，见 [检查器](../scripts/check_submission.py) |
| Full local regression | PASS | 131/131：原100项、新增31项；[最终验证](evidence/submission/final-validation.json) |
| Existing v10 cloud evidence integrity | PASS | 12/12历史云门禁；28源码、70证据清单项匹配；原139份证据保持不变 |
| README current and authoritative | PASS | [README](../README.md) 包含 v10、当前资源阻塞、外部 store=true 与内部 store=False |
| Old instructions clearly historical | PASS | [历史索引](evidence/README.md)，中文全景报告标明旧快照；v7/v8 FAIL、v9诊断原样保留 |
| Demo environment reproducible | PREPARED-NOT-DEPLOYED | [环境手册](demo-environment.md)、up/smoke脚本与DryRun；所需Foundry基础资源当前缺失 |
| Demo cleanup reproducible | PREPARED-NOT-DEPLOYED | down脚本、owner/精确清单/拒绝路径/部分失败回归通过；本轮未在云跑完整生命周期 |
| Demo A prepared | PASS | [录制脚本](demo-script.md)：审批→接受→注册验证→VERIFIED；本地真实宿主回归通过 |
| Demo B prepared | PASS | FAILED后新审批仍BLOCKED、后端一次派发；脚本与本地回归通过 |
| Demo C prepared | PASS | 只接受明确准入拒绝+另一分支VERIFIED；本地回归拒绝配额错误冒充并发保护 |
| 15-case evaluation protocol frozen | PASS | [固定协议](../evaluation/protocol.json)，15×2、64个Responses请求上限；哈希匹配 |
| ON/OFF results | PARTIAL-BUDGET | [本地30条完成](evaluation.md)；真实云30条 NOT RUN — BUDGET CONSTRAINT，另有云资源阻塞 |
| Evaluation raw data preserved | PASS | [JSON/CSV/manifest](evidence/submission/local-evaluation/manifest.json)、原harness快照；修正后离线复算指标完全一致 |
| Recovery/reconciliation runbook | PASS | [人工恢复手册](recovery-runbook.md)：BUSY、UNKNOWN、保存/发布失败、外部执行不确定、丢会话和陈旧分支 |
| Security/secret check | PASS | 提交集合、部署allowlist与证据检查通过；私有配置/日志/PDF不入Git；启发式检查不等于全面安全认证 |
| Submission-facing summary | PASS | [提交前阅读页](../SUBMISSION-READY.md) |
| Recording script | PASS | [7段短演示稿](demo-script.md)，恰好A/B/C三故事；没有录制或伪造截图 |
| Repository clean | PASS | 本矩阵随冲刺交付提交；最终提交/推送后检查工作树为空，提交身份以Git历史和交付回执为准 |

“Demo prepared”只表示脚本、断言与讲稿齐备，不代表本轮真实云演示通过。PREPARED-NOT-DEPLOYED 也不证明资源缺失时能直接执行 up；该脚本复用基础项目，不隐式重建平台。

## 验证、身份与收尾修正

最终运行以下检查，无Azure/付费模型调用：

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -X utf8 -B -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe -X utf8 scripts/check_hosted_concurrency_evidence.py
.venv/Scripts/python.exe -X utf8 scripts/check_submission.py
git diff --check
```

131项完整回归PASS；Hosted历史检查器输出 `HOSTED_CONCURRENCY_CLOUD_GATE=PASS`。PowerShell四脚本AST、四入口与三故事DryRun、云评测prepare/run的默认DryRun均通过。所有历史证据及源码身份保持；新证据单独位于 `docs/evidence/submission/`。

v10历史发布源码提交 `389d1e10d90352ff2cbb7b92eccc4252580f865b`，包SHA-256为 `1ebeb782fa7ebf71dee65f6975599c0b916afd740d77e47abf28144248999425`。文档更新没有改变这一历史身份。原P0清单78项也按原提交验证，未用新版README去重写旧清单。

收尾审查修正了辅助工具对异常HTTP200、缺失usage、并发失败分类、未知健康值、错误端点和清理中断的处理。详情见 [修正记录](evidence/submission/harness-review.md)。原计分harness四文件已按其记录哈希保存；只离线重算既有30条记录，不新增计分执行，指标全部一致。

## 本轮执行与费用记录

| 动作 | 实际执行 | 用量与边界 |
|---|---|---|
| 本地15场景ON/OFF正式计分 | 30项，一次完整批次 | ON/OFF各32个本地ASGI Responses；脚本化传输36/47；真实模型网络调用0 |
| 真实云ON/OFF | 0项 | 30项明确未运行；云Responses请求0、Azure模型调用0，token缺失 |
| 可选真实Foundry Local smoke | 1次流程，PASS | 已加载qwen2.5-0.5b-instruct-generic-gpu:4；原生审批前零派发，重启一次后VERIFIED；实际内部模型调用数未完整计量、usage缺失 |
| 云状态刷新 | 两次刷新，共8项只读资源操作 | 2次Agent版本GET返回ResourceNotFound；4次资源组exists为false；2次订阅Cognitive Services账户LIST为空 |
| Azure资源创建/删除/部署/更新 | 0 | 没有重建基础资源，没有新增演示组、模型、Agent版本或Toolbox版本 |
| 历史云12门禁 | 没有重新执行 | 仅本地检查既有结果与哈希 |
| 本地回归、SDK接口确认、DryRun | 已完成 | 测试替身、已有本地服务，不是Azure运行证明 |

没有本轮新增的付费Azure模型调用或计费资源。账户账单未查询，不把“未新增计费动作”写成已核实总账单为零。Local烟测旧字段 `local_inference_http_requests=0` 仅为未命中传输的观察hook计数；[原始结果](evidence/submission/local-model-smoke.json) 已附计量限制，实际调用数保持null，不能称为没有本地模型推理。

本地临时会话/夹具已释放，原有Local模型与daemon保留。起始未跟踪的中文PDF仍保留于本机、被精确忽略；`.azure`、`.tools` 和虚拟环境没有提交。

## 当前云资源与后续顺序

[首次资源读回](evidence/submission/cloud-readonly-status.json) 与2026-09-21 22:25 UTC（新西兰9月22日）的 [交付前读回](evidence/submission/cloud-readonly-final.json) 一致：原 `rg-reason-fuse`、`rg-reasonfuse-p0-validation` 均不存在，原订阅Cognitive Services账户清单为空，原Agent端点失效。未调查删除者/删除时间，没有扩大查询范围到所有云资源。此前“v10 active”的报告是历史快照，不能当成当前状态。

1. 明确可用Azure/模型费用上限与目标订阅/项目，恢复必要Foundry基础资源；新部署的版本/包身份须重新核对和有界验证，不能自动冒用历史v10 PASS。
2. 在已验证基础上启动一次受控demo环境，验证新up/smoke/down真实生命周期；预算允许时执行预先固定的最小云ON/OFF子集E01/E04/E12（6项、最多16请求），或一次完整15对。保留所有失败与缺失usage。
3. 依据实际新证据更新独立验收状态；只有云可用性/预算/真实对照证据阻塞解除后，剩余工作才能限于演示、录屏/截图、提交。

不自动扩展到数据库、Dashboard、Foundry IQ、自动解锁或生产恢复系统。ReasonFuse仍不宣称通用防幻觉、生产就绪、任意工具正确性、广义分布式exactly-once、高负载或网络分区恢复已经验证。
