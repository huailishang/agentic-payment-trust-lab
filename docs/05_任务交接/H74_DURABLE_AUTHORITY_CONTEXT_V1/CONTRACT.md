# H74：原授权上下文持久化与恢复后消费

Task ID: H74_DURABLE_AUTHORITY_CONTEXT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Validation plan file: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/VALIDATION_PLAN.yaml

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r125
Active bottleneck: B-22
Hypothesis: H-74
Measurement status: measured
Metric baseline: H73独立L3六项、521引用、12边界96字段通过，三份独立历史点击在所选完整审计存储缺原授权/确认快照引用；不是错误放行或原确认过期证明。旧代码没有持久化上下文API，三代表单元的同基线运行结果必须实测，不预填产品失败率。
Estimated affected scope: 仅现有StripeLabLedger及StripeCheckoutAdapter的新增stored入口，三个新合成离线单元N01/R01/D01，C01为零付款守护；旧入口保持兼容，不追填旧H72历史。
Expected project impact: 原GateContext在副作用前存入持久存储，进程重开后载入原值并被既有adapter执行前校验消费，补齐一个本地证据连续性能力。
Principal change: immutable durable original authorization context + consumption at the existing Stripe seam.
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Expected material cost: 估计90执行分钟，硬限Executor105/Evaluator45/合计150保守工作窗；0外部动作，新增维护面限两个既有文件和一个可选局部codec模块。
Bounded retry / iteration budget: 最多2实现尝试、2公共L2、1独立L3；同一方法内普通代码/测试/序列化修复可自主继续，失败与累计成本保留。
Rollback condition: 出现错误放行/跨操作载入/重复副作用，或需要新增依赖、外部源、权限、通用运行时/身份体系、续授状态机，停止交Evaluator。
Expected value of another round if successful: 达标即关闭这个代表性本地切片，不继续堆字段/Case；真实来源/凭据/显式续授流程须依据后续瓶颈另评。

全局：A–D本地关闭，E受控本地代表闭合，F受控Stripe切片关闭。当前B-22有三个有界审计断点和现成消费者；本包优于重复H73静态清点、再付款或换支付平台。真实身份/发行者/签名来源仍需前置证据与授权，本包不替代。

## Single objective

让新合成受控操作的原授权上下文先持久保存，再由存储读取并进入现有创建会话/付款前治理；重开进程必须得到原对象、原版本和原时间。缺失/错绑/篡改/过期不能以当前时间重建替代；原付款只读恢复不因原确认过期而要求再付款。

## Package steps and branches

1. 核冻结/环境/保护输入，开新成本窗；用同一解释器对固定原src快照执行baseline探针，报告UNSUPPORTED_DURABLE_API而非旧产品失败。
2. 复用GateContext、ConfirmationRecord和原校验器，实现最小显式codec与SQLite不可变快照；一次事务绑定原operation/run/order/request/payment/resource，重复保存同事实返回原引用。
3. 增加两个stored入口，载入原事实后调用既有adapter治理路径，fake client/browser可计数；不得绕过原_validate_operation、原session绑定或runtime gate。
4. 完成冷进程还原、两stored入口、缺失/篡改/错绑/版本/金额/收款方/资源/时间拒绝及恢复守护的统一测试；同基线三代表单元输出前后事实。
5. 一次提交八项公共L2、完整原始证据/报告/账本/接受摘要；Evaluator独立冷进程与拒绝对照、必要原回归及唯一L3后逐AC签收。预算内修复不逐步交Human。

关键失败/分支：初始保护或原回归失败→停止且不修范围外缺陷；存储/消费已正确且守护全过→提交即停；只有序列化/引用/测试脚本问题→预算内修复；涉及真实认证、续授或新外部机制→停止，不能扩包。

## Frozen interface and data boundary

复用现有领域对象，不发明新的授权语义。接口具体参数与测试义务见SPEC.json，冻结公开入口为：

- StripeLabLedger.record_authority(operation_id, ctx, *, resource_sha256, recorded_at) -> sha256
- StripeLabLedger.load_authority(operation_id, *, expected_sha256) -> GateContext
- StripeCheckoutAdapter.create_stored_session(store, *, operation_id, expected_authority_sha256, success_url, cancel_url, now)
- StripeCheckoutAdapter.authorize_stored_browser_payment(store, *, operation_id, expected_authority_sha256, now, browser_payment)

stored入口不接受caller提供的ctx、run/session/resource替代原事实；从持久上下文及既有operation行取值，验证两者绑定，再调用原入口。create的会话绑定继续使用原bind_session流程；调用者可传其原生响应完成该步骤，不能由无来源ID伪造其它字段。

SQLite表authority_contexts至少含snapshot_sha256、operation_id、payload_json，禁止原地替换原payload。同一operation首次原事实固定；相同事实重复保存幂等，不同事实即拒绝。本包不建设续授状态机，过期/撤销/新确认需求明确返回拒绝/需确认，不自动生成新时间/确认或覆盖旧对象。未来显式续授须另冻，不把任意字符串标记视为已认证同意。

payload只含原操作绑定、codec schema和现有GateContext中校验器实际消费的事实；保留Decimal、带时区时间、集合、Enum、嵌套dataclass及confirmation原内容/摘要/状态的语义。禁pickle/eval/动态类型加载；解码失败/未知schema/字段缺失一律拒绝。digest仅是本地完整性/引用，不抵抗能同时改写DB和外部期望引用的攻击者，不冒称密码学签名或真实主体认证。

## Allowed scope

可改src/agentic_payment_experiment/stripe_checkout_lab.py及adapters/stripe_checkout.py；可新增src/agentic_payment_experiment/stripe_authority_context.py和tests/test_stripe_authority_context.py。可新增本任务RUN/MEASURE脚本、MEASUREMENT.json、RESULT、REPORT、ATTEMPT_LEDGER、SUBMISSION、derived和evidence。CURRENT仅改本任务状态/角色/阶段。其它本包文件冻结。

旧src/tests、H72/H72R/H72R2/H73合同/门禁/报告/原日志、公共工具及现有测试只读。codec模块确实不需要时可不新增。只用标准库及既有环境，不读旧私有材料，不修改源数据库；测试仅使用本任务临时合成DB和fake client/browser。源码快照保护不等于读取任意私有内容的许可。

## Acceptance criteria

### AC-01 — 保护与环境

Given BASELINE/FREEZE；When VP-01/08及独立L3；Must observe保护/冻结摘要一致、仅允许文件变化、原测试文件保持、原生Windows既有Conda agent及任务局部tests路径隔离、全false外部权限。Mandatory: yes。

### AC-02 — 原事实不可变持久化

Given新合成有效GateContext；When VP-03和冷进程回查；Must observe先保存后副作用、原业务绑定与完整校验语义持久化，独立新进程load与原图一致，原时间/版本/confirmation内容和状态不变。同事实重复记录返回原digest，异事实同operation拒绝。不能只保存hash却无可回查原件。Mandatory: yes。

### AC-03 — 真实消费者接线

Given持久引用和原operation；When VP-04及独立fake计数；Must observestored create/pay都实际加载DB原上下文并调用原gate；正确情形分别一次创建回调/一次browser回调，且副作用发生前DB已有原事实。API不允许传入替代ctx覆盖原事实；不是仅测试存储读写。Mandatory: yes。

### AC-04 — 必须拒绝的原事实错误

Given缺snapshot、错digest/operation、payload被改、旧confirmation对应新order版本/金额/收款方/资源、future confirmation及原时间已过期；When VP-05与独立损坏；Must observe每项fake create/get/browser副作用计数0或原受治理拒绝结果，不能只检查异常字符串。仅将工厂时钟刷新/同ID重建不能修复资格，记录不能覆盖旧事实。Mandatory: yes。

### AC-05 — 生命周期守护

GivenR01已付UNKNOWN后只读对账、D01记账恢复与C01无付款；When VP-04/06及独立边界回查；Must observe原交易/快照引用保持，恢复不新增付款或成功交付，已付查询不因原确认过期被要求新付费确认，C01零付款，D01不升级HTTP传输重试。Mandatory: yes。

### AC-06 — 必要原回归

Given初始既有安全/支付行为；When VP-06；Must observe原Stripe adapter/lab/H72三模块、H68R安全9和业务74通过，原断言不改不降。解析/收据工具未改，用摘要保护而非重复旧全任务门禁。Mandatory: yes。

### AC-07 — 同基线前后证据

Given固定三合成单元及初始源码快照；When VP-02/07和独立重放；Must observebaseline明确为API不支持（不计旧安全失败），after三单元均冷载入原上下文并消费/审计，单位/输入/时钟/环境固定。每单位给出原/恢复图摘要、原时间、实际consumer回调与snapshot引用；负例真实拒绝，不用合成总分或fake摘要代替。产品增量只限本地durable stored路径，旧H72历史不升级。Mandatory: yes。

### AC-08 — 完整交付与成本

Given新账本；When VP-08与最终签收；Must observeExecutor≤105/Evaluator≤45/合计≤150保守整窗、2实现/2L2/1L3，失败照计，原账本和接受快照保持。执行墙钟≤4小时，评估≤2小时；每次BEGIN至END整段墙钟计费，未知主动时间不填0，至少留10分钟收尾。完整提交报告、raw三件套、source/变更摘要和SUBMISSION；独立Evaluator逐AC验收，无自签L3。Mandatory: yes。

## Validation plan

冻结八VP依次为保护/环境、原基线、原事实存储、stored消费者、拒绝对照、必要回归、三单元前后证据、最终范围/成本。精确argv见YAML。Executor测试三类名固定AuthorityStoreCases/StoredAdapterCases/AuthorityDenialCases，至少覆盖SPEC的全部义务；测试数量不当产品覆盖率。

Evaluator必须另写独立对照（不复用Executor断言）：冷进程恢复与原图逐字段比对；改payload/错operation/ref/仅刷新时钟；future/expired确认；两个stored入口零回调拒绝；R01已付只读恢复、D01/C01边界。公共L3全部通过仍须真实语义签收。

## Exclusions

不改旧H72运行脚本或证据、不补造历史快照、不新增真实付款/网络/SDK/服务/钱包/模型、不集成发行者/强认证/签名信任源，不扩通用runtime/控制平面，不做全量上链/加密签名体系。旧legacy入口兼容保留；本包不宣称所有调用已强制迁移，也不把新synthetic原事实当真实用户同意。

## Authorization

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_reference_read: false
authorization_install: false
authorization_local_service: false
authorization_browser_test_only: false
authorization_test_payments: false

本合同只授权本地受限代码、合成测试与证据；新150分钟预算自Executor BEGIN开始，H73及H72成本不继承/不重置。制包费用另列PREPARATION，未执行任何新产品成绩。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12为CORE/ADAPTER，PCAC-15数据最小化，PCAC-20为验收证据。对象=既有GateContext/ConfirmationRecord及operation；代码=本地store+两个stored入口；Test=八VP及独立冷载入/零回调反例；Evidence=未来L2/L3。before=三处已测本地审计断点，after目标=新合成stored路径M3/M4，须实测才升级；真实身份/凭据治理/密码学签名/生产/采用/合规均不升级。

## Stop conditions

保护或初始回归失败、零容忍反例、预算/次数耗尽、需新增来源/权限/依赖或修改假设/AC、需扩大领域或续授义务，均停止交Evaluator。仅序列化/当前包脚本/测试修复可预算内继续。成功后停止同类扩展，不自动再付款或实施下一方向。
