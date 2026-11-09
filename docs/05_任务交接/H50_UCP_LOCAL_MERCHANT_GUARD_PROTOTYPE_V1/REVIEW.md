# H50 Evaluator Review

Task ID: H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review status: FINAL
Review date: 2026-10-20

## Project context before review

目标为授权、交易绑定、受控执行、恢复及审计连续可信；A–D完成、E本地代表性闭环、F当前。冻结地图r79第一瓶颈B-17是商家执行边界；H50为one_off（一次性本地方法级原型），只验证固定副本/合成授权/模拟付款。相比扩客户端案例，这轮直接针对真实执行位置；支付宝和比赛仍延期，通用平台扩张不能解决商家写协调。

## Pre-review checks

| 检查 | 结果 | 独立证据 |
|---|---|---|
| 合同/计划/HEAD/环境/来源 | 通过 | 冻结baseline：950保护、31冻结文件，原生定义局部性通过 |
| 执行者提交/中央结构 | 通过 | SUBMITTED_FOR_REVIEW；第二次L2=5/5，中央校验OK |
| 历史失败保留 | 有限通过 | 第一次L2=4/5、VP-04连接身份失败的原始流完整；旧完整观察JSON未归档，不能追补 |
| 接受快照 | 通过 | evidence/review_20261020/ACCEPTED_SNAPSHOT.json，131文件 |
| 复跑后接受快照不变 | 通过 | RV-PRESERVE-02，131/131不变；20条L2+10条L3原始输出长度/hash核对 |
| 范围与权限 | 通过 | 只改允许的checkout方法/新增execution_control，db与其他33副本/产品核心不变；四旗false |

接受后未改实现、REPORT或执行者证据；独立探针只放evidence，使用真实冻结方法夹具。下述最终REVIEW、地图/路由和新修复包是在接受快照完整性核对之后的治理写入，不倒写执行者结果。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/L3-GATE.json
- Validation plan: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/VALIDATION_PLAN.yaml

冻结计划原样5/5通过：2原生对照、15保护场景、材料/范围及检查器自测。L2/L3的付款/订单/库存/查询等17条摘要一致（RV-COMPARE-01），随机引用不作逐字比较。计划通过是必要证据，独立补充反例仍使AC不通过，不能仅按5/5签任务PASS。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-01.stderr.log
- Observed result: 固定范围、HEAD/环境/保护及来源局部性通过。

## RV-EV-02

- AC: AC-02
- Meta: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-02.stderr.log
- Observed result: 原生2对照，正常库存4、改数量后库存3；原生金额绑定仍NOT_OBSERVABLE。

## RV-EV-03

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-03.stderr.log
- Observed result: 15固定保护场景通过，含两个真实进程退出和A/B持久化恢复；固定G01仅测mock token成功分支。

## RV-EV-04

- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-04.stderr.log
- Observed result: 材料/保护/来源和固定连接证据通过；不替代所有接口路径人工判断。

## RV-EV-05

- AC: AC-05
- Meta: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/review_20261020/l3_evaluator_01/RV-EV-05.stderr.log
- Observed result: 5种过度结论与5种错误观察被拒，正对照成立。

## Independent findings / 独立反例

原始证据：evidence/review_20261020/RV-COUNTEREXAMPLES-01.meta.json/.stdout.log/.stderr.log，以及COUNTEREXAMPLES.json。只在同一真实方法/原合成数据中改变调用先后或原生允许的handler，未改产品或模拟账本，不修改冻结计划。

### R1 [P2] 付款后B写事务期间跟随请求阻塞事件循环并泄露锁异常

定位：merchant/services/execution_control.py的claim（64–98行），同步sqlite3 BEGIN IMMEDIATE约70行；revoke也有同类同步写等待。complete在原生log_request后持有B事务，再调用after_payment hook，见checkout_service.py约781–794行。

复现：A已完成独立模拟付款、B订单未commit；B请求到before_claim时释放A继续提交。B紧接着同步等待A的写锁，事件循环不能调度A提交；约11.073秒后B抛OperationalError/database is locked，status/code均null，随后A才完成。独立账本仍1调用/1单，没有测到第二次付款，但违反合同“不能靠数据库锁500冒充安全拒绝”及在途竞争明确拒绝/等待的义务。

冻结G10只覆盖占用之前竞争，G09只在A刚commit而B写尚未开始时穿插，因此没有捕获此窗口。不是要求新分布式系统，而是原本地方法合同的未闭合路径。

### R2 [P2] 其他原生成功付款分支未进入绑定观察端口

定位：checkout_service.py的_process_payment约1446–1527行；charge只放在mock_payment_handler/success_token分支约1501行，google_pay/shop_pay及card提前返回旁路该端口。

复现：同一受控checkout、有效合成确认，仅将付款handler换为原生支持的google_pay、仍使用合成token。complete成功并生成1订单，原生付款方法带execution调用1次，但独立模拟付款charge为0，尝试仍IN_FLIGHT。没有真实Google服务或资金动作。

合同冻结接口要求原生付款方法成功执行时携带冻结快照/引用送入模拟端口，未允许其他被接受的成功路径静默跳过。报告诚实写出“未覆盖所有凭据分支”是有益限制说明，但不能代替这条接口义务。修复可统一原生校验后的成功接线，不能把它扩成真实Google/Shop支付接入。

H50R冻结准备另外在未修复制品上运行4条诊断：跟随complete、撤销竞争、google_pay、shop_pay均失败，见H50R/evidence/preparation_20261020/inherited_failures.json。诊断退出0仅表示保存了真实失败，不是修复通过；正式VP-06不带diagnostic且要求全部通过。

## Acceptance matrix

| AC | Decision | 依据 |
|---|---|---|
| AC-01 | 通过 | RV-EV-01/04、131接受文件保护；实现范围、旧源码/核心与权限未越界 |
| AC-02 | 不通过 | 固定正常/拒绝样例通过，但R2证明原生成功分支可完成订单而不经过承诺的绑定付款端口；不得只按固定mock-token正常样例签收接口义务 |
| AC-03 | 不通过 | 固定G07–G10通过，但R1的B写在途窗口产生同步停顿和未声明数据库锁异常，未形成要求的拒绝/等待 |
| AC-04 | 通过 | RV-EV-03/04；固定A前失败、B失败及两种真实退出后的稳定引用查询/不重发均复现；不宣称自动补单/退款 |
| AC-05 | 通过 | 原始两次L2流与报告/限定结论齐备，没有升级生产/身份/Provider/客户；旧逐case观察未归档作为证据限制记录，不能倒填，下一包强制保留 |

## Final verdict

REJECTED

- Failed AC: AC-02, AC-03
- Minimum repair task: H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1
- Required rerun: 原生2条/保护15条/来源与材料自测全部保持，再加四条冻结修复回归和独立L3/源码审阅。
- Missing human fact or authorization: 本地有界修复无缺失；不需要账号或真实凭证，不增加网络/真实支付授权。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

H50为one_off（一次性本地原型），产品核心未改；虽固定样例有真实运行证据，两个合同违例使该原型不可验收，不能报告B-17已经闭合或产品提升。也不把此次原型缺陷称主产品回归。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=H49工程设计已核查；after=固定原型已有运行证据但AC-02/03失败，不升级成熟度；Test=原计划L3及独立反例；Evidence=本REVIEW/原始流/COUNTEREXAMPLES；残余=锁失败/分支观察未闭合、无HTTP/真实身份/Provider/客户，无合规结论。

## Iteration value and continuation decision

Continuation decision: CONTINUE

结束H50原包，按新ID只修上述两类失败。执行者自报38主动分钟、两次正式L2用满；原失败与第二次成功均保留。Evaluator独立5项L3、两条补充探针及新包4条继承失败诊断，均只涉及本地方法/SQLite/模拟账本，网络/ASGI/模型/真实Provider为0。

修复预计低至中复杂度，单独3小时/2次L2；信心来自可复现、源码可定位的共同执行路径缺口。比扩HTTP/真实网络/客户调研更应优先恢复原本地合同，也不值得重新做H49资料研究。若同类修复超预算/无净收益或必须重写商家，应停止回Evaluator，不无限续包。

## Bottleneck movement after review

地图r80：B-17从“本地占用实现待测”缩小到“固定正常/拒绝/恢复成立，但付款后写事务竞争和付款成功分支接线仍不完整”。局部事实变多，能力链仍未验收。下一步只针对这两个断点，真实身份/跨系统撤销/HTTP/Provider/客户及延期支付宝不抢占当前修复。

## Next execution package

- Next task ID: H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1
- Next task path: docs/05_任务交接/H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1/CONTRACT.md
- Next task state: CONTRACT_FROZEN / Executor / repair
- Dispatch mode: SINGLE
- Baseline: 同HEAD；被拒实现复制到新包merchant/并记录36文件继承hash，父任务文件不反写。
- Readiness: 精确两实现文件、原5项计划和15场景保持，加VP-06四条修复回归；具体AC/预算/停止/权限已固定。继承失败诊断已运行，修复实现尚未发生，中央结构/新基线通过后交Executor。
