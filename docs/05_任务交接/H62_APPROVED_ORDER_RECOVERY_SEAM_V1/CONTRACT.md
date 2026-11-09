# H62：人工批准驱动的一次订单侧恢复接缝

Task ID: H62_APPROVED_ORDER_RECOVERY_SEAM_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L2（仅隔离本地合成副本，真实业务执行不在授权范围）
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-06-r100
Active bottleneck: B-17
Hypothesis: H-62
Measurement status: measured（原M06付款1/订单0、无消费者）；unknown（本候选运行安全性与恢复收益）。
Metric baseline: 同一M06来源副本付款记录1、订单0、库存5；原生query-only只能查询与拒绝新扣款，不能创建订单。
Estimated affected scope: 已付款而原订单提交失败的一个代表性本地链路，不代表所有商城/PSP。
Expected project impact: 同来源新副本的首次有效批准可使订单0→1、库存5→4；恢复额外付款调用0，重复/越权/失效/崩溃/竞争不产生第二张订单或第二次扣库。
Rollback condition: 错误放行、重复订单/扣库、恢复付款调用、父来源漂移、正常六旅程回归失败，或预算耗尽则不接入，保留query-only。
Expected material cost: 中等偏高估计；主要为原生订单逻辑抽取、两个本地数据库锁序、进程退出与竞争验证。Executor360主动分钟/2L2/至多3完整套；Evaluator独立一套和至多16附加case，网络/模型/安装/真实资金0。
Bounded retry / iteration budget: Executor恢复case预留<=48、批准回归case<=72、原生ASGI请求<=80、冻结worker操作<=320；失败与L1均计费。Evaluator恢复case<=32、批准回归24、ASGI请求<=40、worker操作<=160。禁止并行派发；冻结case内部两个竞争进程是被测机制，不是重复付款尝试。

最终目标是交易信任验证场。A–D本地代表闭合、E仅本地受控、F当前。H61独立L3六项通过并STOP，证据把瓶颈缩到批准消费、撤销与订单提交的执行协议。已有共享AP2适配器/校验器及跨算法第二消费者，不再泛化测量这些已闭合机制。相比保持查询，本包有可观测订单增量；相比第二商城/SDK/全量平台接线，它直接针对真实已观测断点，变更和授权更有界。README漂移和确认辅助函数职责混放登记为非主线，不夹带重构。

## Single objective / 唯一目标

在新任务副本中，用一个显式、受批准约束的本地入口，复用原商城订单事务恢复一次订单，恢复过程绝不再次付款。冻结原件只读；历史批准不被重新使用为当前执行权，所有测试在新来源副本上新建合成批准。只做这个消费者，不建通用恢复平台或统一运行时。

## Allowed scope / 允许范围

可改产品文件仅四个：本包 merchant/services/checkout_service.py、merchant/db.py、APPROVAL_INBOX.py，以及新增 ORDER_RECOVERY.py。前38商家文件均由已接受H57R复制，仅上述两商家文件可改；其余文件/源SDK/src/tests/平台/所有父任务只读。APPROVAL_INBOX从H60R原样复制，保留构造期别名/硬链接拒绝；只为活跃事务读取、消费结果读取和撤销串行化修改，不放宽角色/上下文/摘要/有效期/旧确认撤销/幂等语义。

Executor可写本包REPORT.md、RESULT.json、ATTEMPT_LEDGER.json和evidence/，以及.task_envs/H62/runs下测试副本。合同/INPUTS/全部冻结验证脚本/计划/参考源/入口不可改。CURRENT仅同任务state/phase可改，不能改权限/历史/瓶颈。

### 冻结 Interface

ORDER_RECOVERY.py导出同步函数 `run(config, request, *, hook)`。config为请求外受信配置，含transactions_path、products_path、psp_path、ledger_path、operator_context、now（测试受信整数时钟）、base_url；request精确为approval_id、checkout_id、payment_ref、request_key。返回JSON兼容字典，status只可RECOVERED、REPLAY、DENIED；成功含order_id，拒绝含reason。函数可内部运行独立async事件循环，但不在现有商城服务器事件循环内阻塞持锁等待。冻结WORKER负责网络/付款调用拦截、进程执行与输出，不能在导入时执行恢复或写业务库。

hook是冻结验证器传入的同步观测回调：`approval_locked`在批准写锁已持有之后；`before_commit`在实际订单/库存/收据事务提交前；`after_commit`在提交完成而响应尚未返回时。普通运行传空操作。hook不得替代业务判断或提供批准事实。恢复不调用complete/claim/recover/_process_payment/charge；冻结worker拦截前三个付款执行入口并独立核PSP内容不变。

### 冻结事务与撤销合同

1. 保留原claim、付款引用、原授权/确认，绝不解锁旧claim重走complete。
2. 首次执行：请求外操作员有效/角色/策略与批准上下文相符；新批准处置ORDER_COMPLETION、未过期/撤销；原确认未撤销（其历史过期不单独否定新补救批准）；原付款/checkout/snapshot绑定与全量source_digest一致。
3. 全量摘要范围仍为H60R的checkout/attempt/authorization/confirmation/receipt/inventory/orders。首次消费在实际事务连接中读取实时源，不用immutable读取活跃WAL库；静止假PSP可只读。其他业务造成摘要改变也保守拒绝，不偷偷缩窄摘要。
4. 统一锁序：批准库BEGIN IMMEDIATE → 实际原生订单连接BEGIN IMMEDIATE；持批准锁到订单提交完成。忙锁必须在<=3秒返回明确拒绝/可重试结果，不以sleep重试取得无限权限。批准CLI和类revoke都遵循相同串行协议，不能遗留旧撤销入口绕过。
5. 交易库新增h62_consumptions：approval_id主键、checkout_id唯一、payment_ref唯一；至少source_digest、context_digest、order_id、response_json。订单、库存、checkout、成功幂等记录与收据在同一原生事务一次提交。提交前崩溃全部回滚；提交后崩溃重新读收据，不再执行。
6. 交易库收据是执行结果权威；不声称两WAL数据库共同原子提交。批准库不额外写第二份消费权威事件。show必须把已提交结果显示为effective_state=APPROVAL_CONSUMED、current=false；其execution_enabled仍false，读取不等于再次授权。
7. 撤销先提交则首次消费拒绝。消费先提交则后到revoke返回APPROVAL_CONSUMED且不写REVOKED事件，不追溯否认已完成订单。相同owner/配置可读取既有收据，即使批准后来到期或自身写入改变源；错绑checkout/payment/approval始终拒绝，不能以任意收据绕过绑定。
8. 从原complete抽出唯一订单准备/保存逻辑，普通complete和恢复共同调用；共享逻辑不自行付款，提交由调用方控制。不得整段复制822–970形成第二套订单业务。首次恢复需重核目录商品存在、库存与履约；缺商品/库存明确失败关闭。原生普通完成/重放/拒绝/退出后查询六旅程保持。
9. 本包禁外网通知。恢复订单成功返回notification_status=PENDING_NOT_SENT；通知失败/待发不允许重建订单。可靠通知发件箱和最终交付另评，不在本包承诺。

## Acceptance criteria

### AC-01 — 保护与最小变更

Given INPUTS保护原件与产品副本；When VP01/02/08及源码审查；Must observe 四产品文件内变更、来源hash保持、继承别名隔离保持、无核心/SDK/旧任务变更。Mandatory: yes。

### AC-02 — 同源业务增量且不重扣

Given 新M06副本及新有效批准；When R01/R02；Must observe订单0→1、库存5→4、一次收据、checkout完成、成功幂等记录，原claim/授权/确认/PSP内容保持，恢复付款入口调用0；后续进程和过期读取同订单。Mandatory: yes。

### AC-03 — 授权与输入失败关闭

Given 已撤销/过期/变源/错payment/错角色/变策略/库存不足/商品缺失/旧确认撤销/假PSP错绑；When R03–R10/R15/R16；Must observe明确拒绝、零订单/收据/库存变化，批准回归24例保持。Mandatory: yes。

### AC-04 — 提交、崩溃、竞争与撤销先后

Given 两独立进程和冻结事务观测点；When R11–R14；Must observe 首进程真实退出、提交前全回滚/提交后可重放、并发至多一单一次扣库、消费持锁时revoke有界拒绝、消费完成后所有revoke入口均CONSUMED不写撤销。Mandatory: yes。

### AC-05 — 原生逻辑复用与回归

Given 新商城普通入口与原生六旅程；When VP05及手工AST/调用审查；Must observe 普通与恢复共用一个订单逻辑，普通成功1付款1单，四拒绝例零付款订单，旧M06仍1付款0订单可查询不重扣；签名/路由/默认工厂原样，原25AP2回归保持。Mandatory: yes。

### AC-06 — 证据、预算与能力声明

Given 八VP、冻结判别器自测与真实账本；When L2/L3；Must observe 所有case/worker/HTTP操作调用前耐久唯一预留，失败原始流不覆盖，预算闭合；仅本地假PSP/操作员假定身份，无真实身份/Provider/部署/客户/监管合规虚报。Mandatory: yes。

## Validation plan / 验证计划

VP01父保护与HEAD；VP02副本范围/环境；VP03冻结恢复16case；VP04独立原库/业务判别；VP05原生六旅程和25AP2；VP06原批准24例；VP07判别器损坏自测与成本；VP08保护复查。exact argv在VALIDATION_PLAN.yaml。L3独立新副本重跑；源码/实际事务接缝、撤销全入口和正常共享逻辑仍需Evaluator语义审查，JSON结构通过不能替代它。

## Authorization / 授权

仅本地任务副本合成订单/库存/批准/收据写入及本地进程ASGI回归允许；原始库、真实订单/资金/PSP/凭据/外部消息全部不授权。复用已安装H47/H37运行时，不安装/升级。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## Exclusions / 明确排除

不改src/tests/SDK/平台、不创建通用SDK或第二商城、不做真实网络/资金/身份认证/模型调用/安装/对外联系/Git；不建新HTTP恢复路由、通知发件箱、退款/售后平台；不通过删除旧占用/伪造授权/伪造订单字段达到成功。不回写父H57/H60拒收或H60R/H61报告与成绩。

## Stop conditions / 停止条件

需要范围外文件/模型/新授权/新协议依赖即停交Evaluator；父漂移或错误放行/重扣立即保留证据并停。超过360主动分钟、2L2、任一case/worker/HTTP预算即停，失败不重置。完整一套通过即可提交，不花剩余额度堆案例。通过后STOP本切片，另按消费者/部署证据重排，不自动后续售后功能。无法统一撤销锁序或实际订单同事务则STOP回query-only。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/18/20 CORE/ADAPTER；before=批准登记本地M3/M4、实际消费缺失；after目标仅本地恢复切片M3/M4，尚未实现不提前升级。对象=新批准消费合同与消费收据；代码=四产品文件；Test=16恢复/24批准/6原生旅程/25AP2；Evidence=正式L2/L3/原始子进程流/原库独立核验。真实身份/PSP/标准互通/商户/客户/生产与监管合规unknown。
