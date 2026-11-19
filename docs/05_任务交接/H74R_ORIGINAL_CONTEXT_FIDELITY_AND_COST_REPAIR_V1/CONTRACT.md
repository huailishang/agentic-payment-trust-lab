# H74R：原上下文幂等、类型保真与收尾成本修复

Task ID: H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Validation plan file: docs/05_任务交接/H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r126
Active bottleneck: B-22
Hypothesis: H-74
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Metric baseline: H74原L3 8/8但REJECTED/INCONCLUSIVE，AC-02/08不通过；独立9组为7通过/2失败。正常冷进程/两stored消费者/生命周期/原19/9/74已过，不能抵消已知失败。
Principal change: 只恢复原事实保存语义及闭集codec，并追加同一次交付的成本证据。
Expected material cost: 估计25执行/10评估分钟，硬限45执行/15评估/合计60；同时受主线累计105执行/45评估/总150约束，制包按Evaluator计入累计。
Bounded retry / iteration budget: 本包1实现尝试、1公共L2、1独立L3；原H74实现1/L2一次/L3一次保持，不能倒写或重置。低成本同方法修复可预算内继续，正式失败不能再开同包门禁。
Expected project impact: repair/NOT_APPLICABLE；保留H74拒收，修复通过才重新判断B-22受控代表切片。
Rollback condition: 新的错误放行、同原事实变化、需续授/新类型体系/外部来源或额度即停止交Evaluator。

全局目标为授权→执行前治理→支付→恢复→审计可独立复核。A–D本地关闭、E本地代表闭合、F受控Stripe切片关闭。B-22已有实际消费者，当前卡在两个可复算原事实语义问题；此最小修复优先于换环境、再付款、扩Case或真实身份接入。真实主体/凭据/签名来源仍未知。

## Single objective and steps

在保留H74全部原件的前提下，一次修复：同原GateContext在仍有效的不同记账时刻重试返回首次引用且不改原时间；拒绝未注册但同名Enum；追加覆盖原交付收尾的保守成本。然后统一完成旧13测试、独立反例与19/9/74回归，提交一次L2，交独立Evaluator唯一L3。

1. 核FROZEN/BASELINE、原H74拒收与独立原反例，开新工作窗；初始失败仅作为已知红基线，不伪称通过。
2. 在record_authority区分原授权事实与本次记录尝试时间。已存同原事实、recorded_at=T+1秒且仍有效，应返回首次digest/payload；原recorded_at/confirmed_at/expires_at/版本均不改。不同ctx仍拒绝，执行门禁仍按当前时间检查。
3. codec按注册真实Enum class校验，不能只查__name__；保留全部合法注册Enum往返。不可为修反例硬编码某个字段或名称。
4. 追加COST_RECONCILIATION.json，不改旧ledger/report/submission。原BEGIN→Evaluator保守起点06:24Z作为收尾上界，25.019200分钟；原20.825250、原实际UNKNOWN及差额分列。这是未超原105限额的保守补账，不追认为原窗口完整。
5. 一次完成六VP/L2和报告/快照；Evaluator复算反例、成本及原断言，唯一L3和逐AC验收。预算内普通修复不逐步交Human。

## Allowed scope

只可改src/agentic_payment_experiment/stripe_checkout_lab.py、stripe_authority_context.py及tests/test_stripe_authority_context.py（仅追加有意义测试，原类继承和所有原方法体保持）。Adapter、其它src/tests、H74/H73/旧任务、公共工具及本包冻结文件只读。原四份H74提交源码/测试另存references/rejected_source。

本任务可新增RUN脚本、RESULT/REPORT/ATTEMPT_LEDGER/COST_RECONCILIATION/SUBMISSION、derived与evidence；CURRENT仅改本任务状态/角色/阶段。只用合成临时DB、既有依赖和Fake client，任务局部tests shim，禁止改共享环境。HOLDOUT是Evaluator独立程序的冻结副本，结果写本任务，不能改其断言。

## Acceptance criteria

### AC-01 — 原件与范围

Given BASELINE/FREEZE；When VP-01/06；Must observe原147提交文件/4原源码存档、原20冻结文件/门禁/拒收/账本保持；只有允许三文件变更，原测试方法与继承保持，原生隔离/合法路由/外部全false。Mandatory: yes。

### AC-02 — 原事实幂等

Given同ctx/operation/resource，T及T+1秒都有效；When VP-02/03与独立对照；Must observe返回同首次digest，payload/原recorded_at/原确认和有效期不变。不同ctx同operation仍拒绝；过期门禁不因重试复活，不建设续授流程。Mandatory: yes。

### AC-03 — 闭集真实类型

Given合法Enum及未注册同名PaymentStatus/Decision；When VP-02/03；Must observe合法原图类型保持，两个外来同名类型均在serialize/record阶段拒绝，fake副作用0。不能用同一有缺陷codec生成原/恢复摘要来自证保真。Mandatory: yes。

### AC-04 — 必要守护

Given冻结HOLDOUT、原13测试与旧回归；When VP-02/03/04；Must observe冷子进程原图、两个stored消费者、缺失/错引用/篡改、future/expired/revoked、C01/R01/D01全部保持；原19/9/74通过，旧断言不改。Mandatory: yes。

### AC-05 — 追加成本证据

Given原END/提交/原辅助程序与评估接受时刻；When VP-05；Must observe原记录摘要绑定、25.019200分钟保守上界与4.193950分钟差额、actual_active=UNKNOWN、原账本不回写，说明mtime只是支持证据。修复执行/评估/制包及父包成本分别列示，累计受105/45/150约束；父子计数分别保存。Mandatory: yes。

### AC-06 — 有界完整交付

Given独立账本；When VP-06和最终验收；Must observe本包45/15/60及累计105/45/150不超，1实现/1L2/1L3，失败保留；BEGIN→END整窗覆盖报告和SUBMISSION收尾，未知主动时间保留。执行墙钟≤3小时、评估≤1小时，至少留8分钟收尾；全raw三件套、报告/差异/源码及提交摘要齐全，独立Evaluator不改接受字节。Mandatory: yes。

## Validation plan

VP01保护/环境，VP02冻结独立HOLDOUT（原9组+两个同名枚举codec对照），VP03原测试模块及追加测试，VP04原19/9/74，VP05成本证据，VP06范围/预算。精确命令见冻结YAML；公共runner顺序执行。Evaluator须独立确认两反例消失与合法控制保留，并检查FIRST payload/recorded_at，不能只读汇总。

## Exclusions and authorization

不修改原H74报告/ledger/SUBMISSION/门禁，不回填旧历史，不改adapter或原安全门禁，不加支付/平台/续授/身份/签名体系，不安装、不联网、不启服务/浏览器、不调用真实支付/模型或Git写入。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_reference_read: false
authorization_install: false
authorization_local_service: false
authorization_browser_test_only: false
authorization_test_payments: false

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/15/20，沿原GateContext/confirmation/operation对象及CORE/ADAPTER/EVIDENCE_ONLY边界；代码为两处最小修正，Test=六VP及独立反例/原回归，Evidence=未来L2/L3。修复不单独升级成熟度，不构成真实认证/签名或监管合规结论。

## Stop conditions

新零容忍反例、保护/旧断言漂移、需范围外依赖/权限/字段/机制、预算或唯一正式尝试耗尽即停止。达标后停止同类修补，再由Evaluator判该代表切片；不能自动重开H67/外部平台或续授能力。
