# H73：外部交易的授权与确认事实连续性测量

Task ID: H73_AUTHORITY_CONTINUITY_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Validation plan file: docs/05_任务交接/H73_AUTHORITY_CONTINUITY_MEASUREMENT_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-15-r124
Active bottleneck: B-22
Hypothesis: H-73
Measurement status: unknown
Metric baseline: H72四条外部功能事实及H72R2技术修复已核；尚无逐字段、逐边界的原授权事实连续性测量。不得预填0/4失败。
Estimated affected scope: 仅原N01/C01/R01/D01，创建会话、付款前、恢复三个边界；C01无付款，恢复阶段不重新要求付款确认。
Expected project impact: 判断下一能力是否应为“持久保存并消费原授权/明确续授事实”，或现有材料已充分、或输入受限；不计产品能力增量。
Principal change: 只增加一份可独立回查的授权事实测量视图，无产品实现。
Expected material cost: 新独立预算150分钟保守角色工作窗，Executor≤105、Evaluator≤45；最多2次L2、1次L3、一版测量方法，网络/安装/服务/浏览器/付款/模型服务0。
Bounded retry / iteration budget: 同一方法内修正解析、引用和格式可自行继续；失败与累计成本保留，不改变假设/字段/样本/来源。足够判断即停止。
Rollback condition: 需新来源、私有文件白名单外读取、产品运行、外部权限或更改验收语义即停止交Evaluator。
Expected value of another round if successful: 仅在共同证据断点成立且最小修复可定义时另冻能力包；本包不预授权后继实现。

全局目标为授权→绑定→受治理执行→恢复→审计可复核。A–D本地关闭、E受控本地代表闭合、F受控Stripe切片关闭。B-22是E–F接缝的证据不确定性，尚非已证实漏洞。它比再加Stripe付款案例优先，因为前端授权事实仍是端到端链的关键输入；比真实发行者/钱包接入先行，因为可用既有交易取证而不增加权限义务。H67及六类攻击扩展维持人工延期。

已知事实不作新发现：h72_operation.create_context会用当前时间生成合成mandate/order/confirmation；N01恢复调用同一工厂并保留原标识；ledger持久化交易标识而非完整GateContext；08:54:39Z负责人明确续行授权存在。它们均不单独证明越权，也不证明真实强认证。

## Single objective / 唯一目标

对原四旅程，在冻结来源内回答：实际外部操作能否回指当时有效、作用域明确的授权与确认事实？区分任务负责人运行许可、合成领域授权/确认、外部付款事实三个层次；逐字段记录原始观察、明确续授、代码重建、缺失、冲突或不适用，并给出有证据的下一步决策。

## One bounded package / 步骤、依赖与分支

1. 前置：核INPUTS与FREEZE、工作区/环境及原接受结论；开启新成本窗。输入缺失/漂移即INPUT_LIMIT，不修旧门禁。
2. 一次清点全部固定来源及两项白名单私有材料，构建四旅程三个边界的事实矩阵。按SPEC逐字段查原源，不按预期结果挑选引用。
3. 追踪工厂、调用点、adapter与ledger的静态数据路径；代码意图和历史执行观察分别记录。允许标准库离线提取，不import/执行H72运行器、产品或支付SDK。
4. 统一作时序和权限作用域判定，显式考虑负责人续行授权及合法重确认。缺原对象时间不能用当前重建时间填补；不能从会话创建时间推算原确认时间。
5. 生成RESULT、矩阵、成本账本及REPORT，一次完成六项公共L2。预算内修复测量脚本/引用/格式可继续，最多第二次L2，旧失败不覆盖。
6. Executor提交接受快照，切READY_FOR_REVIEW。Evaluator独立回读全部决定性引用、四例全部边界、两私有材料和适用性，再运行唯一L3与逐AC判定；不冒充Executor复述。

分支：共同断点成立→RECOMMEND_MINIMAL_CAPABILITY；现有事实充分或只复述已知合成边界→STOP_VIEW；白名单/可用来源不足以判定→INPUT_LIMIT；相互矛盾或潜在零容忍反例→STOP_ESCALATE。全部分支只输出证据，不追加实现或现场活动。

## Allowed scope / 允许范围

Executor可新增本目录ANALYZE.py、RESULT.json、MATRIX.json、ATTEMPT_LEDGER.json、REPORT.md、SUBMISSION.json、derived/和evidence/；CURRENT仅更新本任务执行状态/角色/阶段及报告路由。其他本目录文件冻结。旧任务、src、tests、公共工作流、原L2/L3与地图/REMOTE均只读。

INPUTS.json的sources是允许分析的公共源；protected是完整性保护，非额外读取许可。私有材料仅通过原PRIVATE_REF定位n01_operation_private.json及merchant.sqlite3：前者只可读完整JSON于内存并输出键是否存在及白名单字段摘要，后者用mode=ro、PRAGMA query_only和固定表列SELECT读取。禁止原地写DB/创建表、读取CREDENTIALS、密钥、cookie、URL、webhook原文或其他私有日志。引用用PRIVATE:n01_operation或PRIVATE:merchant_operations，不落本机路径/原始业务标识。存在私有材料不等于其中包含完整原授权；未获准读取的其它材料必须记INPUT_LIMIT，不能声称全局不存在。

Public输出只含来源路径、JSON Pointer/代码行、摘要、必要非敏感时间/金额与类别。原始外部ID和本机绝对路径不复制到公开产物。无新下载/研究、依赖、产品测试或运行、服务进程、API、浏览器、签名、钱包、付款、提交、推送。原480分钟/Stripe额度及预算例外不继承；历史UNKNOWN与拒收不改判。

## Acceptance criteria

### AC-01 — 输入、范围及历史保护

Given INPUTS/FREEZE；When VP-01/06及独立L3；Must observe所有锁定原件摘要保持、仅允许输出发生变化、合法Executor/Evaluator路由和全false外部权限。私有输入缺失/漂移应明确停止，不改白名单或旧接受记录。Mandatory: yes。

### AC-02 — 完整清点与可回查来源

Given四固定旅程与SPEC字段；When VP-02及独立逐源审阅；Must observe4×3边界完整矩阵，每项有状态、适用理由、来源层次、引用或具体缺失原因。JSON Pointer必须实际存在；代码引用必须在锁定行范围内；PRIVATE引用按白名单直接复算。完整枚举n01私有JSON顶层键、operations表列及四行是否存在，输出键名/结构和摘要，不输出原值。缺失不能用相邻、同额、同ID或代码存在代替。Mandatory: yes。

### AC-03 — 授权、时间和恢复语义

Given原工厂/调用点/点击收据及负责人续行授权；When VP-03及独立语义复核；Must observe分别评价任务级许可、领域确认和外部付款证据。ORIGINAL_OBSERVED/EXPLICIT_REAUTH须有执行前直接来源、明确对象/版本/金额/收款方/有效期关系；CODE_RECONSTRUCTED不得冒充原事实。真实身份与签名来源保持未知。C01无付款边界为NOT_APPLICABLE；R01付款后只读对账不因原确认过期被要求另付；D01仅记账恢复。未观察原时间的expiry判定必须UNKNOWN。Mandatory: yes。

### AC-04 — 决策及共同断点门槛

Given矩阵；When VP-04及Evaluator判断；Must observe只选四分支之一。RECOMMEND_MINIMAL_CAPABILITY须至少两个独立历史边界/旅程直接证据指向同一需要消费的授权事实断点，并区分“审计证据缺口”与“错误放行”；同一工厂代码重复引用、已知合成标签或私有来源未读不计共同断点。还须给出下一包唯一能力、既有消费者、最小对象/持久化/消费接缝、同基线正反对照、成本估计及残余风险。其他分支给出停止或输入解除条件。缺共同断点不扩建，禁止声明产品增量/监管合规或据此推翻旧窄范围成绩。Mandatory: yes。

### AC-05 — 测量器可信与独立复核

Given冻结CHECK和提交产物；When VP-05及L3；Must observe合法结构正面对照通过，至少缺边界、缺字段、无效Pointer、CODE冒充原证据、C01虚构付款、无共同断点却建议能力六个损坏被真实检查函数拒绝；保留每次返回码/错误。结构校验不替代人工语义复核。L2用公共runner六项全通过后方可提交；Executor不得运行/声称L3。Mandatory: yes。

### AC-06 — 成本与交付

Given独立新账本；When VP-06及最终复核；Must observeExecutor≤105、Evaluator≤45、合计≤150保守角色窗分钟；从每次BEGIN到END整段墙钟入账，不用声明主动值抵扣；开窗检查时加当前已逝墙钟。最多2L2/1L3，所有失败计入，跨角色窗不得重叠。每次工具/取证/检查前估计剩余预算；Executor提交前至少预留10分钟收尾。执行墙钟≤4小时、评估工作窗≤2小时，Owner等待只在明确END/BEGIN间排除，不自动续期。报告制作、公共捕获和L3均计费。最终账本、报告及SUBMISSION包含提交文件摘要；Evaluator独立确认快照未变。Mandatory: yes。

## Validation plan / 六项验收

VP-01 preservation→AC-01；VP-02 matrix→AC-02；VP-03 semantics→AC-03；VP-04 decision→AC-04；VP-05 guards→AC-05；VP-06 final→AC-01/06。精确argv见冻结YAML，公共runner顺序运行。测量不改变产品，故用src/tests摘要保护代替重跑旧业务回归；不削弱旧包必须通过的原测试或追认旧结果。

## Exclusions / 明确排除

不扩展四旅程或攻击族，不修产品/旧门禁，不集成身份发行者、钱包、其它支付平台，不重新申请权限或外取证据。保护清单不是额外分析许可；只能读取允许sources和两个私有材料。不声称真实身份、生产资金安全或第三方采用。

## Authorization / 成本来源

Human要求Evaluator基于当前瓶颈制定下一执行包，授权本地可逆制包与测量准备。本包只冻结既有材料的离线读取/任务内写入权限；正式Executor和独立Evaluator分工仍保留。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_reference_read: false
authorization_install: false
authorization_local_service: false
authorization_browser_test_only: false
authorization_test_payments: false

新预算从Executor第一次BEGIN开始；本次Evaluator制包成本单列PREPARATION.md/READINESS.json，不能塞回已关闭H72预算。冻结计划不是已执行L2/L3或产品成绩。

Baseline correction before handoff: 制包期间出现61414d0文档提交，仅三份Robinhood参考/索引文件变化，已锁输入的实际HEAD即61414d0。首次草案仍沿用旧c6c617c，最终完整性检查因此拒绝。Evaluator保存首次23冻结文件及原CURRENT于references/before_baseline_rebind，将本合同/路由绑定到实际输入HEAD；假设、范围、AC、预算、权限与来源摘要不变，Executor尚未开工。详见BASELINE_REBIND.json。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12为CORE/ADAPTER，PCAC-15为数据边界，PCAC-20为EVIDENCE_ONLY。对象=原mandate/confirmation/order/operation与本测量合同；代码=冻结来源中的工厂/adapter/ledger及任务内只读分析；Test=六VP/六损坏/独立语义回查；Evidence=未来本包L2/L3。产品成熟度before/after不变；本包仅把既有外部切片的事实充分性从unknown变为measured/INPUT_LIMIT，不能升级真实身份、强认证、凭据治理、签名信任源或合规结论。

## Stop conditions / 停止与后继

任一输入/冻结漂移、预算或重试限额、测量无法独立回查、需范围外来源或副作用、潜在零容忍反例，即停止新增操作并交Evaluator。仅保留受阻产物，不自修旧任务/授权。即使通过也不自动执行能力建设；Evaluator依测量结果另冻包。若只是重述已知合成局限，STOP_VIEW且不再派同字段静态修补。
