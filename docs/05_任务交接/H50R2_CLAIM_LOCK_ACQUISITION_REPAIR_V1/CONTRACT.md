# H50R2 写锁获取点的最后一次有界修复

Task ID: H50R2_CLAIM_LOCK_ACQUISITION_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H50R2_CLAIM_LOCK_ACQUISITION_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-20-r81
Active bottleneck: B-17
Hypothesis: H-50R2

目标是智能体支付的授权、绑定、受控执行、恢复和可复核证据。A–D完成、E本地代表性闭环、F当前。H50R的6项L2/L3及原生2/保护15/修复4场景通过，付款成功路由、原跟随竞争和撤销忙时分类有实际改进；但独立调度使两个请求均先通过空占用预查，首笔付款并持有订单写事务后，第二笔在claim的同步BEGIN IMMEDIATE仍阻塞约11秒并抛裸锁异常，AC-03失败。因此H50R仍REJECTED；不是没有进展，也不是完整能力验收。

写锁获取点是已测、可定位的小范围残余，先修它比再加客户端控制更有价值；支付宝/比赛仍Human延期，HTTP/真实Provider/商业需求不是本次小修可以替代的证据。只追加这一包90分钟/2次L2；若仍无法在此范围闭合，停止同方向自动追加包并回Evaluator重新比较成本/价值与商家合同。旧H50的2/2、H50R的1/2均保留，不重置其历史。

## Single objective / 唯一目标

使真正的数据库写锁获取及失败转换满足原合同，而不是再增加一个非原子的读预检。SQLite锁忙时可以立即明确拒绝/等待，也可以采用允许事件循环继续运行的正确异步获取；必须保留持久claim、快照绑定、撤销先后及稳定付款引用。不能同步等10秒后仅改成409、使用进程全局锁、按测试键/调度特判或把并发关掉。

只改本任务merchant/services/execution_control.py。其余35个继承实现文件（包括已修好的checkout_service.py）逐字冻结。源码/许可来自原固定UCP副本，INHERITED_COPY记录36文件hash；FROZEN_TESTS、REPAIR_PROBES与父任务逐字相同，新增CLAIM_RACE_PROBES是Evaluator提供的测试而非实现。父任务最终报告/证据只读。

## Acceptance criteria

### AC-01 — 范围及继承不变

Given固定HEAD、依赖和继承清单；When VP-01/04；Must observe仅execution_control.py及允许材料变更，其他35实现、父任务、冻结判据及历史不变；Must not observe依赖安装、产品/父任务源码改动或扩大权限；Evidence=BASELINE/INHERITED_COPY/来源检查。Mandatory: yes。

### AC-02 — 付款路由及确认绑定不退化

Given原生2、保护G01–G06/G14与修复R03/R04；When VP-02/03/06；Must observe正常交易、Google/Shop合成token仍恰1独立模拟付款/1订单且快照引用一致，非法确认及原生凭据失败保持拒绝零付款；Must not observe成功分支无模拟付款、修改checkout接线或夸大原生金额绑定；Evidence=完整观察及源码审阅。Mandatory: yes。

### AC-03 — 写锁获取竞争可判定且不阻塞

Given既有G07–G10/R01/R02，以及新增两请求均在claim之前到达的屏障；When VP-03/06/07；Must observe首笔完成，S01同一checkout跟随者明确拒绝/等待（400/403/409或202），总1付款/1订单/库存4；S02不同checkout争同库写锁时，跟随者可明确拒绝/等待（总1/1/4），也可正确异步等待后成功（总2/2/3），每个实际付款快照匹配自身确认且引用/checkout唯一；独立session及连接、heartbeat<2秒；Must not observe裸数据库异常、同步长等待、重复付款、绕过确认、伪成功撤销；Evidence=两连接屏障、完整事件/结果/账本。Mandatory: yes。

2秒只排除本地约11秒卡死，不是生产SLA。S02防止以再次查询同订单占用替代写锁治理；SQLite写锁属于数据库，不能假定不同订单没有争用。保留原钩子事件的语义及位置，测试不得通过移动钩子或改变屏障来规避争用。

### AC-04 — 故障恢复不退化

Given原G11/G12/G13/G15；When VP-03/04；Must observe原真实子进程退出、事务A/B、稳定引用QUERY/WAIT与禁止盲目重发仍成立；Must not observe用回滚冒充退款或增加自动补单；Evidence=原保护15场景。Mandatory: yes。

### AC-05 — 诚实材料与预算

Given本包7项计划；When完整L2及VP-04/05/06/07；Must observeREPORT/DESIGN/RESULT/账本、全部原始流及两新增观察齐备，新包正式L2<=2/主动时间<=90分钟，旧拒收及预算保留；Must not observe将准备失败写成通过、覆盖既有证据或宣称生产/真实身份/客户；Evidence=原始三件套与报告。Mandatory: yes。

## Allowed scope

唯一实现写入为merchant/services/execution_control.py；允许本目录REPORT.md、DESIGN.md、RESULT.json、ATTEMPT_LEDGER.json、evidence/。CURRENT只允许CONTRACT_FROZEN→EXECUTING/Executor及phase变更，关联、权限、全局历史、next_artifact=REPORT不变。其他任务文件、COMMON工作流、父任务、src/tests/上游全部只读。

结果沿用h50-result/v1、LOCAL_SERVICE_PROTOTYPE_ONLY、LOCAL_NATIVE_SERVICE_METHODS_SYNTHETIC_TRUST_FAKE_PSP_NO_HTTP；生产/真实身份/跨系统撤销/Provider/客户/global_race_closed全部false，需求UNKNOWN，原生金额绑定NOT_OBSERVABLE。本包是恢复局部合同的repair，impact=NOT_APPLICABLE，不新建领域/框架/架构。

## Exclusions

网络/HTTP/ASGI/模型/真实Provider/真实付款/客户联系、安装下载、Git提交推送均零；不改数据库类型、签名/身份系统或订单业务。不能修改冻结测试、合同、计划、checker、基线、许可、REVIEW和EXECUTOR_START。既有checkout预查与付款路由只能继承；需要改这些文件即停回Evaluator。

## Validation / Deliverables

先执行低成本L1及源码审阅，再一次完整运行冻结计划7项：VP-01保护；VP-02原生2；VP-03保护15；VP-04材料；VP-05检查器自测；VP-06原4修复；VP-07新增2写锁调度。正式计划不带--diagnostic；ARCHIVE_AND_RUN自动在覆盖观察前按hash归档。Evaluator接受快照后独立L3及源码审查，7/7本身不等于验收。

REPORT使用公共v2.2模板：Task ID/HEAD、Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat、全部AC、实际改动/成本/残余与原始EV；DESIGN说明写锁获取机制、失败分类、事务/钩子/撤销先后为何不退化。只在完整L2成功后标SUBMITTED_FOR_REVIEW。ATTEMPT_LEDGER沿用字段，active_work_minutes<=90/formal_l2_attempts<=2，继承H50/H50R预算另记，不能复用父任务次数充当本包运行。

## Budget

主动90分钟，正式L2最多2次；并发代理0、任务串行，测试内部并发/子进程照旧。原H50R修复4例已通过，无需重做泛化调研；本包准备两例失败不是Executor结果，不消耗其正式L2。复用H47隔离Python/固定30包。asgi_requests/network_calls/model_calls/provider_calls/external_runtime_calls均0；内部模拟与进程按实记。

## Stop conditions

保护/环境漂移，需改冻结条件/其他实现、增加依赖/外部操作、预算用尽、同失败无新机制或需重写商家时立即停止交Evaluator。不得自动H50R3或滚动增加同类场景。全部通过且独立接受则STOP本地锁修复，再比较B-17的HTTP集成责任与真实需求证据；失败则重新评估本地机制/商家合同可行性，不自动接外网。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## External requirement impact

复用已检查的docs/reference/05_产业与机构资料/pcac/智能体支付应用自律公约_开发指标映射_v1.md。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=本地付款路由/原竞争已修但stale-precheck锁获取失败；after_target=原方法合同竞争结果可判定，无成熟度升级；Test=VP-01..07；Evidence=父任务独立反例、本包准备/正式流与后续L3；残余=HTTP/真实身份/跨系统撤销/Provider/客户未知；不作合规结论。
