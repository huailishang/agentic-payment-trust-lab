# H49 冻结执行包：商家服务端执行边界的工程可行性与外部能力复用判断

Task ID: H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-18-r77
Active bottleneck: B-17
Hypothesis: H-49
Measurement status: H48 客户端确认桥接与两个旁路/穿插反例已经独立复核；服务端改动形态、所有相关写入口及外部凭证可承担的部分尚未形成可实施合同。
Metric baseline: H48 正常 1 次模拟处理；检查前变更/缺证据/过期零处理；检查后修改和绕过客户端仍各完成 2 件。它是 CLIENT_GUARD_ONLY，不是服务端修复。
Estimated affected scope: 一个固定 UCP Python 商家、11 个读写/入口审计单元、3 种机制、14 个未来验收场景；不代表市场或行业覆盖。
Expected project impact: 给出有源码依据、可冻结为下一样机合同的最小服务端边界，或明确停止该候选；本包不实现产品或服务端控制。
Rollback condition: 无法证明覆盖相关写入口或缺可信输入时，不通过扩大核心、合成真实凭证或任意补字段形成正结论。

最终目标仍是授权→绑定→受控执行→恢复→审计。A–D 完成，E 本地闭合，F 当前；B-17 优先于重开通用认证/审计或恢复支付宝/比赛。H48 已回答客户端效果和限制，不再重做同类矩阵。本包收敛一个工程决策：原生商家是否有可用机制；若没有，最小商家侧改动应放在哪里、依赖哪些真实权限、如何判定它有效。ServiceNow 强化基础设施竞争，不证明它已闭合本固定交易问题，也不证明本项目有独占优势。

## Single objective / 唯一目标

形成一份有来源的服务端边界可行性结论，包含覆盖路径、最小输入/接口、事务及恢复义务、与外部授权服务的分工、下一样机的可判定验证设计和一个可验证商业问题。

本包是只读工程设计与来源审计，唯一主产物是边界合同建议。不是再测 H48 已知漏洞，不新增框架、模拟“安全平台”、客户端补丁或生产适配器。14 场景是未来验收设计，不能写成 14 项测试已通过。工程样机只有本包评估后才可能另获有界预算；若证据不足应明确 NO_SAFE_SEAM，不连续派同类调研。

## 固定输入与已知前提

- H47 sources/ucp 固定 commit `99724a32da48bd0f4962c83e25f17c8345ce055e`，49 个原文，Apache-2.0；SDK 0.4.6、协议 2026-04-08；不下载最新版。
- H47/H48 的已接受原始观测、源码审计、投影和 REVIEW 只读；使用它们的事实，不重跑商家/网络/模型。
- NATIVE_FACTS.json 由 Evaluator 从固定 AST（源码语法树）提取，记录 complete 中幂等、读状态、模拟付款、库存与提交位置。它是源码证据，不是并发/崩溃测量。
- complete 的 checkout_complete 参数被纳入请求 hash 不等于其中凭证被验证，更不等于已与持久化 checkout 快照原子绑定。必须分别核对接收、验签/验授权、业务绑定、执行前不可穿插、重试和存证。
- “库存/订单数据库事务”不能等同“外部付款与数据库事务”；当前模拟付款发生在库存和订单提交之前。任何建议都要处理付款已发生而提交失败的未知结果，不能承诺分布式 exactly-once（恰好执行一次）。
- EXTERNAL_BASELINE.json 为 2026-10-18 核对的官方发布事实摘要。AI Passport 有运行时授权、委托/撤销/审计主张；预计 Q4 可用。未取得可执行 SDK/测试凭证或本项目交易绑定证据，默认 REFERENCE_ONLY。不能用不相干同名 GitHub 项目替代官方实现。
- H47 三团队只提供工作流/已有控制/问题线索；需求、预算、采用和购买均 UNKNOWN，不对外联系。

## 串行阶段与交付

| 阶段 | 内容 | 产物 |
|---|---|---|
| S0 | 保护、来源与现行任务核对 | baseline；发现漂移先停止 |
| S1 | 审计全部固定入口、调用路径、写对象、事务和缓存捷径 | SEAM_MAP.json、SOURCE_AUDIT.md |
| S2 | 比较继续客户端、商家原子边界、外部权限服务三条路线 | MECHANISM_COMPARISON.json、COMPARISON.md |
| S3 | 给出最小商家侧输入/接口和状态责任；若不成立写阻塞 | BOUNDARY_DESIGN.json、BOUNDARY_DESIGN.md |
| S4 | 设计 14 个可证伪验收场景及判定器、轨迹和计数 | VALIDATION_DESIGN.json、VALIDATION_DESIGN.md |
| S5 | 收窄潜在付费问题及平台复用/停止条件 | BUSINESS_CHECK.md、DECISION.json |
| S6 | 自查反对理由、完整 L2、账本和报告 | REPORT、ATTEMPT_LEDGER、原始 EV；一次交回 L3 |

阶段之间不等签字。只读资料已经足够完成审计；没有可用机制/SDK也应完成“需要改变商家合同/延期/停止”的有据结论。仅保护、权限、范围或预算变化属于硬停止。

## 审计与机制要求

11 单元：create_checkout、get_checkout、update_checkout、complete_checkout、cancel_checkout、create_cart、update_cart、cancel_cart、update_order、ship_order、order_event_webhook。每行记录 source_refs（固定仓库相对路径、AST symbol、行范围）、read_set、write_set、effect、payment_relevance、bypass_reason、proposed_treatment。查询写日志和“能改已生成订单但不能触发新付款”要与付款入口区分，不能把所有写接口都误叫付款旁路。MCP 仅列工具与真实执行入口的区别另写 SOURCE_AUDIT。

3 机制固定为 CLIENT_RECHECK、MERCHANT_ATOMIC_GUARD、EXTERNAL_AUTHORITY_GATE。逐个写 ABSORB/REFERENCE_ONLY/REJECT/DEFER、已有保护、能覆盖的 H48 失败、不能覆盖的失败、所需信任来源/服务端控制权、改动位置、维护/运行成本及最强反对理由。对外部服务不能只标“认证”：它宣称运行时权限治理；也不能推断已支持具体订单绑定。需要的机制可以组合，但下一样机只能一个主改变，不把安装多个平台当主线。

## 最小边界设计要求

必须说明可信确认由谁创建/存储/撤销，用户意愿如何绑定 checkout、完整商品内容/金额/币种/收款人、授权版本、有效期及请求引用；哪些字段能复用，哪些仍为合成假设/真实缺口。不要机械新增同名模型。

指定服务端核验发生在何处、哪些写入口必须共享同一保护，以及跨进程/多实例是否受约束；先读后写、本进程 mutex、数据库 CAS/条件写分别讨论，不能把进程锁称多实例原子保证。只有拒绝陈旧更新或锁定执行快照、且所有相关写路径遵守它，才可提出原子边界候选。直接 DB 写若属管理权限边界，明确假设和无法保障之处。

说明幂等缓存命中与重新授权/撤销的顺序：返回既有结果和发起新付款是两个动作，不能把撤销后查询原结果视为新付款，也不能借旧结果掩盖新请求。定义 UNKNOWN 的查询恢复，付款前/付款后/提交后失败的不同责任，保留事实与因果关系。不改现有支付决策词表、核心接口或生产凭证。

BOUNDARY_DESIGN.json 至少包含 schema=h49-boundary-design/v1、mechanism、entrypoint、trusted_inputs、assumptions、write_coordination、idempotency_ordering、revocation_ordering、unknown_recovery、trace_requirements、minimal_changes、rollback、unresolved。每个说明必须有意义、不得留 TODO。服务端实现和竞态闭合标记一律 false。

## 冻结的未来验收设计

14 个 ID：T01_NORMAL、T02_CHANGED_BEFORE、T03_UPDATE_DURING_EXECUTION、T04_MISSING_CONFIRMATION、T05_FORGED_CONFIRMATION、T06_REVOKED、T07_EXPIRED、T08_SAME_KEY_REPEAT、T09_SAME_KEY_DIFFERENT_BODY、T10_NEW_KEY_AFTER_COMPLETE、T11_UNKNOWN_THEN_QUERY、T12_CONCURRENT_COMPLETE、T13_PAYMENT_BEFORE_COMMIT_FAILURE、T14_DIRECT_ENTRY。

每项写 setup/steps、independent_oracle、expected_decision（既有 ALLOW/DENY/CONFIRM/WAIT/QUERY/RETRY 等语义及代码映射）、expected_payment_calls、expected_persisted_state、required_trace、residual_risk、executed=false。T03 明确插入点、两个参与者、快照及写入顺序；T12 写如何调度两个独立会话/事务，不用串行重复冒充并发；T13 不允许假定付款与数据库一起回滚；T14 不调用客户端治理包装，检查直接服务端入口。正常场景必须允许，不能全阻断。

这些只决定下一样机怎样验收，本包不执行这些场景。若未来无 mock 场景可提供独立判定器，就不能认定样机合同已就绪。

## Decision / 商业边界

DECISION schema=h49-decision/v1；classification 仅 BOUNDED_SERVICE_PROTOTYPE_CANDIDATE / SERVICE_CONTRACT_CHANGE_REQUIRED / NO_SAFE_SEAM；reason、strongest_alternative、next_step、stop_condition、customer_question 有来源。product_improved/server_guard_implemented/race_closed/provider_verified/customer_validated/third_party_verified/servicenow_payment_binding_verified 全 false；customer_demand=UNKNOWN、external_classification=REFERENCE_ONLY、full_product_gate_comparison=NOT_MEASURED。

BUSINESS_CHECK 只写一个可验证问题：例如交易集成团队是否为确认到付款及异常恢复的人工排查承担了可量化成本。沿用 H47 一个具体团队的已有工作流及已有保护，列出需要索取的脱敏轨迹、问题负责人、发生频率、排查工时和预算事实；无答案均 UNKNOWN。将来若平台原生已足够或成本更低，应复用/停止独立产品。跨平台、支付垂直、认证或审计名词本身不是优势；本包不定价、不宣传、不发消息。

## Acceptance criteria

### AC-01 — 历史与权限完整

Given 固定 HEAD/历史/环境；When VP-01；Must observe 全部保护 hash、当前 route/四旗一致，无新文件越界；Must not observe 改 H48/核心/上游、安装或外部调用；Evidence=baseline。Mandatory: yes。

### AC-02 — 执行路径与事务事实有源可核

Given 固定源码及 NATIVE_FACTS；When VP-02 和人工复核；Must observe 11 单元、真实存在的函数/行范围、付款与提交顺序、缓存/查询/旁路的区分；Must not observe 用接口名称推断副作用或把源码分析当运行测试；Evidence=SEAM_MAP/SOURCE_AUDIT。Mandatory: yes。

### AC-03 — 最小机制与输入边界明确

Given H48 反例与 3 机制；When VP-02；Must observe 可信输入、服务端位置、写协调/撤销/幂等/UNKNOWN/证据及最强反对理由完整；Must not observe 通用平台扩张、多个消费者未经证明回抽、厂商能力未经验证升级；Evidence=COMPARISON/BOUNDARY_DESIGN。Mandatory: yes。

### AC-04 — 未来验证可证伪

Given 14 场景；When VP-02/03；Must observe 正常可通过设计、独立判定/调度/轨迹、竞态与故障反例、一律 executed=false；Must not observe 全阻断或 14/14 已测试声明；Evidence=VALIDATION_DESIGN、Checker 负例自检。Mandatory: yes。

### AC-05 — 有界结论与业务假设诚实

Given 全部材料；When 完整 L2 后提交；Must observe 单一结论、停止/复用条件、公开工作流依据、客户与生产能力未知、预算及原始 EV 完整；Must not observe 产品提升/客户/Provider/ServiceNow 成绩声明；Evidence=DECISION/BUSINESS_CHECK/REPORT。Mandatory: yes。

## Allowed scope / 允许范围

可新增/修改 SEAM_MAP.json、SOURCE_AUDIT.md、MECHANISM_COMPARISON.json、COMPARISON.md、BOUNDARY_DESIGN.json/.md、VALIDATION_DESIGN.json/.md、BUSINESS_CHECK.md、DECISION.json、ATTEMPT_LEDGER.json、REPORT.md、本目录 evidence/。不得新增任何服务端或产品实现脚本。
CURRENT 仅允许 CONTRACT_FROZEN→EXECUTING/Executor、phase/next_artifact_path 更新；不能动任务/地图/授权/历史；提交仍为 Executor，由 Evaluator 接受。
合同、EVALUATOR_CHECK、FREEZE、BASELINE、NATIVE_FACTS、EXTERNAL_BASELINE、计划、EXECUTOR_START、REVIEW 冻结。H48 及其他目录、src/tests、公共工作流全部只读。

## Exclusions / 排除范围

不实现服务端、核心、客户端补丁或新框架；不重跑商家/ASGI/模型/Provider；不下载、安装、注册、对外联系或使用真实支付。未来14场景不在本包运行，不能报告其通过率。不重做H48已闭合的客户端矩阵。

## Validation / Budget

VP-01 baseline；VP-02 材料/源码引用及声明检查，语义由独立人工审阅；VP-03 Checker 正对照与破坏材料负例。精确命令在 VALIDATION_PLAN.yaml。中央结构校验另行运行。只读材料不重复跑已有产品回归或商家矩阵。

主动执行上限 6 小时；正式 L2 最多 2 次，连续同一失败无新依据即停止；并发度 1。运行商家/ASGI/模型/Provider/外部接口预算均 0；不下载、安装、注册或索取账号。ATTEMPT_LEDGER schema=h49-attempt-ledger/v1，formal_l2_attempts、active_work_minutes，asgi_requests/model_calls/provider_calls/external_runtime_calls=0；正式每次目录/原因，工时自报与客观 meta 分开。

- commit: false
- push: false
- history_rewrite: false
- api_call: false

## Stop conditions / 下一步

保护漂移、源/环境缺失、需新权限/依赖、需改本包目标或预算耗尽即 BLOCKED。普通机制不可用或真实信任输入缺失，应完整形成有据否定结论，不拓展研究。
有明确位置、全部关键写入口和可判定测试→Evaluator 才考虑一个本地商家样机；缺商家控制权/可信凭证/原子语义→SERVICE_CONTRACT_CHANGE_REQUIRED 或 NO_SAFE_SEAM，并比较换候选/停止。不得用“再研究一下”无限追加同类包。本包结果不自动授权实现、支付宝、比赛、生产、真实资金或客户联系。

## External requirement impact

已核对 PCAC 指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；maturity_before=H48 固定客户端可复核、商家执行边界未建；maturity_after_target=服务端边界工程合同与验证设计，产品实现/生产成熟度不变；Test=VP-01..03；Evidence=固定源码/历史 L3/边界与验证设计；残余=无服务端实现/真实身份/Provider/并发实验/客户。无合规结论。
