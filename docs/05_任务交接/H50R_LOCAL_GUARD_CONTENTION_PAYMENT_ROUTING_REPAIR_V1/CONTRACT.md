# H50R 有界修复：在途请求锁等待与付款成功分支接线

Task ID: H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-20-r80
Active bottleneck: B-17
Hypothesis: H-50R（继承H50服务端执行占用方向，只修原合同违例）

目标仍为授权→绑定→受控执行→恢复→审计；A–D完成、E本地闭环、F当前。H50冻结L3虽5/5、原生2条/保护15条通过，但独立反例使AC-02/03不通过：第一笔已模拟付款而B事务未提交时，跟随complete触发同步SQLite锁等待，阻塞事件循环约11秒并抛原始OperationalError；google_pay原生成功分支生成1订单而独立模拟付款0调用。shop_pay和撤销写入同类缺口也作为本包负向准备/冻结回归。没有观察到重复付款或真实资金影响。

相比扩客户端、真实网络或扩大原型，优先最小修复两个受控执行违例，保持正常和旧15场景。H50已REJECTED并用满原2次L2；此包单独3小时/2次预算，不重置历史、不修改父任务成果。

## Single objective / 唯一目标

让继承的本地商家受控付款执行路径满足原H50合同：B写事务在途时，跟随执行/撤销不得同步阻塞事件循环并泄露数据库锁500；原生认可的付款成功路径必须携带同一冻结快照和稳定引用进入独立模拟端口，不能生成没有模拟付款证据的成功订单。

唯一主改变为修复受控执行路径的可判定行为，不增新商家/框架/协议。可以快速识别已有占用返回明确拒绝/等待，或使用正确的异步数据库协调；不能只在10秒阻塞后把OperationalError换成409掩盖事件循环阻塞，也不能依靠进程全局锁。撤销竞争可成功持久撤销或明确WAIT/拒绝（说明尚未应用、可重试），不得吞锁错误假报成功。

## Inherited baseline / 继承快照

36个商家文件从被拒H50复制到本目录merchant/，INHERITED_COPY保存继承hash，H50原件/报告/测试/证据只读。SOURCE_COPY继续指向Apache-2.0的原固定35文件，许可保留。只允许改checkout_service.py和execution_control.py；db.py及其他34文件保持hash。原生未改定义继续受AST保护。

FROZEN_TESTS.py与H50冻结版本逐字复制，仍有原生2条/保护15条/两次真实进程退出，不改其断言。新增Evaluator-owned REPAIR_PROBES冻结四条同接口回归：B写期间跟随complete、B写期间撤销、google_pay/shop_pay合成token成功分支。它们没有真实Google/Shop/Provider调用，仅复用原生接受的分支和独立模拟账本。

本包所有者Executor只修实现；Evaluator只提供测试与合同。已有实现是继承的未提交工作，不能算本包从零建设。环境仍用H47固定Python/30包；本包方法级、合成授权、独立模拟付款，无HTTP/真实身份/跨系统撤销/客户结论。

## Acceptance criteria

### AC-01 — 范围与继承完整

Given固定HEAD/父任务/副本/环境；When VP-01/04；Must observe父任务、冻结计划/脚本、原生非授权定义及权限一致，仅两实现文件和允许交付改变；Must not observe改H50/上游/src/tests/db.py或安装联网；Evidence=baseline/source_locality/INHERITED_COPY。Mandatory: yes。

### AC-02 — 原生成功分支的付款绑定

Given继承G01–G06/G14与R03/R04；When VP-02/03/06；Must observe正常原生/受控交易完成，google_pay与shop_pay原生支持的合成token路径也恰1模拟charge、1订单，完整快照/引用一致，既有拒绝仍零charge；Must not observe成功订单无模拟付款或把缺证据写成覆盖限制免责；Evidence=原/保护/修复观测。Mandatory: yes。

保留原生凭据校验成功/失败语义；将成功后的模拟端口调用统一接线，校验失败不得charge。纯card等原生提前成功返回分支也须审阅，不能留下同类静默绕过；不要引入真实卡片/凭证或新外部处理器。

### AC-03 — 在途竞争有明确结果且不阻塞事件循环

Given继承G07–G10、R01/R02；When VP-03/06；Must observe已有幂等/不同连接竞争保持，第一笔完成1单/1charge，B写期间跟随complete得到明确400/403/409拒绝或202等待，撤销成功或明确拒绝/等待；冻结heartbeat延迟小于2秒；Must not observe原始OperationalError/锁500、同步10秒卡死、伪造成功撤销、第二次charge；Evidence=屏障/回调/状态/独立账本。Mandatory: yes。

2秒只是本地冻结探针排除10秒事件循环停顿的宽裕判据，不是产品性能SLA。正常的异步锁等待不禁止，但必须让首笔继续提交、事件循环能调度；失败分类清楚。

### AC-04 — 原有崩溃与恢复不退化

Given G11/G12/G13/G15；When VP-03/04；Must observeA失败零charge，B失败原生库存/订单回滚但A保留，真实进程退出后按稳定引用QUERY/WAIT，旧/新键不再charge；Must not observe改冻结故障点/回滚等同退款/自动重发；Evidence=原冻结观察。Mandatory: yes。

### AC-05 — 真实材料、预算和历史

Given材料/6项计划；When VP-04/05/06及完整L2；Must observeREPORT/DESIGN/RESULT/账本和真实EV齐备，四条修复回归逐项有结果，父任务拒收、原L2两次及首轮完整观察未归档的限制如实记录；Must not observe伪造旧观察/覆盖失败/扩生产或客户结论；Evidence=原始流及报告。Mandatory: yes。

## Allowed scope

只可改merchant/services/checkout_service.py的H50原允许方法/私有帮助，以及merchant/services/execution_control.py。其他34副本、父任务H50、H47–H49、产品核心/公共工作流只读。副本原生创建/履约/库存/订单流程保留；不重写简化商家。

可写本目录REPORT.md、DESIGN.md、RESULT.json、ATTEMPT_LEDGER.json、evidence/执行者证据；继承H50接口/结果schema不变，RESULT保留LOCAL_SERVICE_PROTOTYPE_ONLY与全部生产/真实身份/Provider/客户false字段。新增修复观察由VP-06产生，不能手造。

CURRENT只可CONTRACT_FROZEN→EXECUTING/Executor及phase更新，next_artifact仍REPORT，其余关联/历史/权限不变。CONTRACT/计划/FROZEN_TESTS/REPAIR_PROBES/ARCHIVE_AND_RUN/EVALUATOR_CHECK/SOURCE_COPY/INHERITED_COPY/许可/EXECUTOR_START/REVIEW/BASELINE冻结。

## Exclusions

不改父任务证据或旧检查器；不接网络/HTTP/ASGI/模型/真实Provider/客户；不新增身份系统、数据库类型、真实支付或自动退款补单；不安装下载、Git提交推送。不能通过隐藏失败、只改结果文档或减少15条回归来过关。

## Validation / Deliverables

VP-01保护；VP-02原生2条；VP-03继承保护15条；VP-04材料与来源；VP-05原检查器自测；VP-06新增四条修复回归。Evaluator使用同冻结计划独立复跑，输出_l3与_l2分开。所有回归都必须通过，随后人工审阅未覆盖的提前成功返回和锁路径。

REPORT按公共v2.2模板，Task ID/HEAD、Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat、全部AC、正式L2/EV、继承/实际改变/成本/残余齐全，L2成功才SUBMITTED_FOR_REVIEW。DESIGN解释具体锁修复与统一成功路由，以及原生分支/恢复不变的证据。

原H50第一次L2原始流仍在，但完整guarded观察被第二次覆盖，不能恢复旧逐case细节；不要编造。新包计划经冻结ARCHIVE_AND_RUN包装，重跑前将已有完整观测按hash保存到observation_archive，避免覆盖；原始失败三件套亦永不覆盖。此包装只作证据保存，不改变原回归的断言或实现行为。

## Budget

主动执行3小时/正式L2最多2次；并发代理0、运行任务并发1，内部并发/worker仅冻结测试。可在原范围做廉价L1；先修再完整六项L2，一次交Evaluator。账本单独计新预算，保留H50历史2/2；asgi_requests/network_calls/model_calls/provider_calls/external_runtime_calls全0，内部调用/模拟账本/子进程按实际输出记录。

## Stop conditions

保护/环境漂移、改合同/计划/判据、超范围/新依赖/网络、预算耗尽或同失败无新依据即停止交Evaluator。不得将未获接受的局部成绩扩展到HTTP/真实支付。局部修复若通过，优先停止该修复方向，再按B-17剩余真实集成证据决定下一有界任务。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## External requirement impact

已复用PCAC映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=H50固定样例通过但存在在途竞争/成功路由违例；after_target=恢复原本地方法合同，不提高产品/生产成熟度；Test=VP-01..06；Evidence=H50独立反例/本包原始流及后续L3；残余=无HTTP/真实身份/跨系统撤销/Provider/客户，无合规结论。
