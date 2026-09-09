# Phase 2 Core — Open Questions and Evidence Boundaries

本文件只列当前未证明的能力或需要后续独立验证处理的疑问。修复过程与当前批次重测见 [construction report](report.md)，完整材料见 evidence index。不要求恢复或 review 已清理的历史中间文件。

## 当前 construction 状态

36 项单元测试、LOCAL_CORE/LOCAL_INTEGRATION、A–J 十项最终 Hosted 用例、14 项兼容性检查和最终复位均已通过。当前 construction 必需范围无未解决 blocker；状态为 `READY FOR INDEPENDENT VALIDATION`，不是独立 Phase 2 PASS。以下条目是保留给下一轮的明确边界与疑问。

## 1. 独立验收尚未执行

状态：`NOT RUN`。construction 的实现者自测不能授予独立 Phase 2 PASS。下一轮须按根目录 Verification Prompt 预先固定 trial 数与配置，运行 detector/recheck/failure 各三次、负对照、clean-start redeploy 和最终 reset；使用新 evidence 目录，不从 construction 索引复制 PASS。

OFF 的结论限定于固定四轮 harness：它证明本次允许冗余调用，不证明任意提示都能让模型无限循环。持续区分 harness stop、voluntary stop 与 fuse stop。

## 2. Foundry IQ

状态：`NOT VERIFIED`。Hosted E 调用 `operations___retrieval_fixture`，证明 fixture 等价 evidence 的 churn containment 经过真实 Middleware/Toolbox 路径。它不证明 Foundry IQ 接入、索引刷新、权限或检索质量。当前 construction 允许该明确标注的 fixture，无需为获得 Phase 2 PASS 擅自新增 RAG 架构。

证据：Hosted E。若以后启用真实 IQ，需单独定义 adapter、KB 版本与真实 integration evidence。

## 3. Production restart 与真实一致性

状态：`NOT VERIFIED`。F/G/I/J 使用 deterministic Operations API 的 simulated restart。已测试 fresh HEALTHY、UNHEALTHY 和 stale HEALTHY，但未验证生产服务 restart/rollback、真实权限、延迟一致性、跨区域或真实故障恢复。不要把模拟服务的 OUTCOME_VERIFIED 表述为生产系统恢复。

## 4. 云端 Core OTel 关联

OTel 核心属性/事件的本地发射测试与 Hosted 权威 runtime decision state 已覆盖。云端 collector 中某次具体 `reasonfuse.*` decision span 与 request/run 的端到端关联仍需独立检查，状态：`NOT VERIFIED`。APIM metadata telemetry 通过不能替代 Core decision span 证明。

后续步骤：选定新的 B/F/G/I 请求 ID，查询对应云端 trace 中的 fuse_reason、useful_recheck、postcondition_delta 和 contract_version；不启用消息正文采集，不导出 token/连接字符串。如 collector 未保留这些属性，区分 instrumentation 与导出/查询配置问题。

## 5. 非默认多副作用与并发边界

冻结 P0 为 `max_side_effects=1`，验证义务是单一 pending_postcondition。本次证明的是一个资源动作与一次绑定重检，不是多资源并发动作。

疑问：如果以后把 side-effect 上限提高到大于 1，必须先证明新动作不会覆盖未完成验证义务；并发/forked turn、强制冷启动恢复也没有独立 Hosted 证据，均为 `NOT VERIFIED`。不要仅修改 env 上限就宣称支持多动作运行；需要单独测试或明确拒绝不支持的配置。当前交付恢复默认 1，不据此扩大 P0 承诺。

## 下一模型入口

阅读 [construction report](report.md)、本文件及索引，再执行 [Core Verification Prompt](../../../ReasonFuse_Phase2_Core_Verification_Prompt.md)。疑问与失败写到独立 `verification-open-questions.md`；不要覆盖 construction 历史报告，也不要把这些边界改写成已验证能力。
