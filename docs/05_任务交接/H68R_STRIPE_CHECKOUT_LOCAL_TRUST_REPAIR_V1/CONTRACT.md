# H68R：Stripe候选接缝的本地信任边界最小修复

Task ID: H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/VALIDATION_PLAN.yaml
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-12-r112
Active bottleneck: B-21
Hypothesis: H-68R
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

H68的L2失败且状态BLOCKED（受阻），不具备独立验收资格。Evaluator已保存57文件接受前快照并核六份L2原始摘要，原REPORT/RESULT/账本/合同/检查器保持。H68仍为受阻未签收，不改成已通过或完成正式L3；本包显式取代其当前执行路由，不重置任何外部尝试预算。

全局A–D本地关闭，E仅受控本地闭合，F当前；B-21仍无Stripe外部合格旅程。进入外部前，候选接缝必须守住本仓原有安全边界。与继续排查浏览器或换平台相比，修复已复现的错误放行/错绑是更前置的必要条件。现有浏览器在Evaluator隔离自写页已成功点击；Stripe服务资格依旧未知。

Metric baseline: 过期确认仍触发1次付款回调；外部会话引用可产生RECOVERED；错业务付款通知返回True；原生Windows指定74项回归发生6项清理ERROR。
Expected project impact: 消除这些本地反例，恢复进入资格测量的前提；repair不认领外部能力增量。
Expected material cost: 90主动分钟、4小时墙钟、2次实现/2L2/1L3；0外部网络、0浏览器操作、0付款、0下载/安装。
Rollback condition: 需改旧核心规则、冻结检查器/证据、依赖、外部接口或扩大预算即停并交Evaluator；保留当前候选代码和失败，不重写H68。

## Objective and principal change / 目标与主要变化

只在H68新接缝内补全付款动作当前时效、持久原交易和通知对象关联，并关闭本地数据库连接。复用既有验证与恢复规则，禁止改变现有业务模型/规则。四项是同一个候选适配接缝达到原Trust Contract（信任合同）的修复，不扩新功能。

## Acceptance criteria

### AC-01 — 当前动作的确认有效期

创建会话和浏览器付款入口都以本次动作now核验确认，不能只用历史request.occurred_at。已过期、未生效或缺失的确认不得调用创建/付款回调；合法对照仍允许。保留旧请求和证据，不伪造请求时间；复用既有verify_confirmation_binding和Decision语义，不改旧validator。

### AC-02 — 原会话恢复

recover_original先核对持久operation对应的payment_id/request_id/order_id/session_id与传入payment/observation。即使双方provider_ref相同，只要不同于已保存session也须拒绝或返回BLOCKED，不生成RECOVERED记录。正确原会话恢复仍调用assess_payment_recovery、retry_allowed=false；恢复不创建新会话或付款。不得用测试中关闭关联校验的方式恢复通过。

### AC-03 — 通知关联

checkout事件继续核原session；payment_intent事件必须能回指本操作原会话已核实的intent。未知或外来intent不得记作本操作已接受通知；可拒绝，或保持独立未绑定暂存但返回不接受。签名有效不能替代业务关联。合法事件仍接受一次、重放返回False；通知不得独自推进已付/交付。

### AC-04 — Windows数据库资源与原回归

每次公开账本操作的成功/异常路径都提交/回滚并显式关闭真实SQLite连接；不得依赖垃圾回收。Windows Python下原两份新测试及61项历史回归全通过，无临时文件清理错误；资源验证不得改成忽略异常、gc.collect、删除原测试或换Linux宿主。现有单次交付/恢复/取消正向守护保持。

### AC-05 — 保持、预算与证据

BASELINE保护的旧核心、历史任务、H68全部报告和L2保持；仅四个授权文件可修。失败、每次实现和L2逐次保留，BEGIN/END追加账本；时间/尝试不超预算。全部网络/付款/浏览器/安装/提交/推送为0。正式L2通过后才能SUBMITTED_FOR_REVIEW，Evaluator独立重跑同计划并审接线；不能把本包标为已验证Stripe。

## Allowed scope / 允许文件

仅允许修复既有未提交候选四文件：

- src/agentic_payment_experiment/adapters/stripe_checkout.py
- src/agentic_payment_experiment/stripe_checkout_lab.py
- tests/test_stripe_checkout_adapter.py
- tests/test_stripe_checkout_lab.py

本包仅可新增RUN.py、REPORT.md、RESULT.json、ATTEMPT_LEDGER.jsonl、evidence/、versions/；CURRENT仅按工作流改state/phase，禁止改权限/AC/冻结摘要。CHECK.py、CONTRACT.md、VALIDATION_PLAN.yaml、BASELINE.json、PREPARE_BASELINE.py为Evaluator冻结输入。开工先CHECK integrity。

## Exclusions and authorization / 排除与权限

不改H68浏览器脚本/RUN或其冻结任务文件，不实现四旅程编排、不新建HTTP服务；不改models、validator、payment_execution、payment_recovery、lifecycle、旧tests、pyproject、authoritative_trace注册表。只用已有Python/项目依赖。外部沙箱、API查询、匿名创建、CLI、浏览器和付款全部禁止；旧H68权限不得继承到本包。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

本地可逆修复与测试由既有任务及Evaluator工作流授权，不需要Human再点击确认。需要任何外部能力即停止，不自行翻转旗标。

## Validation and budget / 验证与预算

正式L2/L3用公共run_validation.py执行本包冻结计划：VP-01 integrity；VP-02独立安全/资源负例及正向对照；VP-03原74项指定回归（允许新增针对性测试）。所有命令本地、没有Stripe调用。L3在原生Windows独立复跑并审看真实回调、持久关联、连接关闭。红基线只作Evaluator准备证据，不计正式L2。

90主动分钟/4小时墙钟、实现2、L2 2、L3 1、顺序执行。Executor首次实现前追加BEGIN，外层active_work覆盖所有工作；L2前预留次数，失败照计；结束前补END，不能覆盖旧行。达到预算/两次同断点无净收益、需改合同或出现新安全异常即STOP。CHECK integrity验证追加账本与范围，不负责推断漏报的真实世界动作；Evaluator仍核接线及原始输出。

## Impact and next step / 影响与下一步

Impact verdict应为NOT_APPLICABLE（修复不评能力增量）；本包通过只证明本地缺陷消除。修复通过且无新反例→CONTINUE一个独立的Stripe环境资格测量；该测量需另冻来源/操作/授权/停止条件，不在本包偷跑。修复失败/超预算→STOP交Evaluator；无需重搜平台或恢复H67。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/18/20；适用性CORE/EVIDENCE_ONLY的本地接缝；maturity_before=候选实现未签收，maturity_after=按本地Test/Evidence记录，不提高外部成熟度；Test=VP-02/03，Evidence=L2/L3及本地反例；残余风险=Stripe资格、真实通知/交易、强认证、凭据治理、资金安全与合规未证实。
