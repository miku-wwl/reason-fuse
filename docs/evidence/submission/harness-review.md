# 计分脚本溯源与收尾修正

审查日期：2026-09-21 UTC（收尾跨越新西兰本地2026-09-22）。核心基线为 `97738312e7d3ee6e6eb8066ac795fc7755c06a38`，与历史 v10 运行时一致；本次只修辅助脚本，没有改动 Agent 核心或云夹具。

## 原始证据保持不变

[30条本地结果](local-evaluation/results.json) 记录的四个 `harness_source_hashes`，逐项匹配 [runtime](evaluation-harness-v1/evaluation/runtime.py)、[scoring](evaluation-harness-v1/evaluation/scoring.py)、[包入口](evaluation-harness-v1/evaluation/__init__.py)、[runner](evaluation-harness-v1/scripts/evaluate.py) 快照。快照仅供溯源，不作为修正后的执行入口。

原始 JSON、CSV、manifest 与协议未覆盖。修正后只对既有30条原始响应离线重算，所有字段一致：没有新计分执行、模型调用或挑选性重试。0/5无依据成功、0/2重复派发的本地控制结果保持有效。

## 修正内容

- HTTP 200 内的 failed/incomplete 不能误记 COMPLETED。只在并发案例接受已知前置准入拒绝；其他异常停止云批次，保留原始响应、后端观察和中断标记，不继续重置夹具。已在途并发分支都结束后才记录批次失败。
- admission failure 必须为明确的 ReasonFuse 准入错误且无输出。Demo C 还需另一分支完成 VERIFIED、独立后端恰好一次派发/接受，不能把模型配额错误当并发保护。
- 未知健康值保持 UNKNOWN，无效答案枚举标为无法评分；任何缺失 usage 均停止后续云请求，不推断免费。
- 校验调用地址与预检项目/Agent 一致；响应核对 Agent 与已创建的 session，不接管响应中突然出现的陌生 session。
- 临时夹具固定1副本直至清理。Foundry 清理失败不阻止可独立安全完成的临时组清理；版本发现限定本次 owner、同一命名资源，删除后读回，未完成项如实报 PARTIAL/FAIL。

原记录中只有 E15 两组预期的准入拒绝，没有普通失败响应、无效枚举或未知健康值触发上述缺陷。新增回归用构造响应和本地 SDK/CLI 替身覆盖故障边界，不宣称云部署验证。

最终完整回归 **131/131 PASS**，包含原100项与新增31项。具体验证命令、源码哈希、费用与资源边界见 [最终验证记录](final-validation.json) 和 [验收矩阵](../../submission-sprint.md)。
