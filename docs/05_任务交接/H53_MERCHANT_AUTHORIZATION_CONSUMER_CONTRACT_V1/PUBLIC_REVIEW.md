<!-- Public display copy; original SHA-256: 4a8303d44e523589189a8d4cd1ecccba9ee8a8516ebd8a8fcf3a6300b3815474; only trailing whitespace/line endings normalized. -->

# H53 Evaluator Review

Task ID: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review status: FINAL
Review date: 2026-10-31

## Project context before review

项目目标是高风险支付的身份、授权、绑定、执行、恢复和审计可独立复核。地图r86：A–D阶段关闭，E仅本地受控代表性验证，F当前。B-17是标准授权到商家执行的可信接缝；H53只在任务副本建设本地方法样机，优先于重复锁/HTTP样本及新增支付服务方。完整JCS、标准UCP升级、真实身份和Provider（支付服务方）仍未验证。

H52已测到原文/业务投影脱节，H53试图在同一claim（持久执行占用）事务中结合已签原文、投影、确认及完整当前快照。通过则停止本地切片；新反例违反冻结的两跳/受众/nonce（一次性标识）合同则拒收并收窄修复，不能用固定测试PASS掩盖安全边界。

## Pre-review checks and accepted snapshot

发现Executor已经SUBMITTED_FOR_REVIEW，按实际提交做独立复核。接受前中央工作流OK、1398保护文件/51冻结文件与环境通过；正式L2为9/9、mandatory failures=0。

AUDIT.py核对L2的18条原始输出流长度/hash，保存139个接受文件到ACCEPTED_SNAPSHOT.json，再将CURRENT转READY_FOR_REVIEW/Evaluator。完整L3后28条稳定观察与L2一致，139/139接受文件未变、L2/L3共36条原始流长度/hash一致；独立六例后再核对仍一致，证据PRESERVATION_AND_COMPARISON.json。实现、REPORT、Executor账本、来源及既有L2未改。

正式L3及独立反例完成后再次通过原baseline和工作流，才创建修复包、写本REVIEW及地图/CURRENT治理更新。最终REVIEW替换接受快照中的占位REVIEW；H53的合同、计划及冻结r86关联不反写，也不在治理变动后假装再次通过旧保护地图的baseline。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/L3-GATE.json
- Validation plan: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/VALIDATION_PLAN.yaml

冻结计划原样9/9通过，28/28方法观察可复算，76相关回归/H37八例保持，九种过度声明拒绝。**本任务最终REJECTED**：固定计划未覆盖终结链形状，独立反例违反冻结输入/受众/nonce要求。门禁PASS仅证明列出的检查通过。

Executor正式L2=1/2、预留56/280case，主动60分钟为自报；Evaluator完整L3 28例+独立6例=34/112。L3四次假付款，独立六例四次假付款（含三条应拒绝的反例）；均为本地SQLite假PSP，不是真实或沙箱支付。网络/ASGI/模型/Provider/真实资金/安装/对外联系/Git写操作均0。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.stderr.log
- Observed result: 1398保护/51冻结摘要与零安装环境通过。

## RV-EV-02

- AC: AC-01
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.stderr.log
- Observed result: 完整checkout输入签名与两跳夹具检查通过，只是输入smoke（准备检查）。

## RV-EV-03

- AC: AC-01
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.stderr.log
- Observed result: 34不可改商家文件及指定两文件修改范围通过，新模块语法可用。

## RV-EV-04

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.stderr.log
- Observed result: 原生方法28例通过：4个正向/生命周期场景各一次假付款，24个固定负例零付款。

## RV-EV-05

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.stderr.log
- Observed result: 原始28例检查及正例官方SDK重算通过，未包含中间型末跳反例。

## RV-EV-06

- AC: AC-05
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.stderr.log
- Observed result: 76/76相关产品回归通过。

## RV-EV-07

- AC: AC-05
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.stderr.log
- Observed result: 旧H37八例8/8通过，不代表新增链形状覆盖。

## RV-EV-08

- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.stderr.log
- Observed result: 材料、账本及范围通过；最终安全裁决需独立反例与源码审阅。

## RV-EV-09

- AC: AC-05
- Meta: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-09.meta.json
- Stdout: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-09.stdout.log
- Stderr: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-09.stderr.log
- Observed result: 九种错误能力声明被拒绝，仅检查器自测。

## Independent counterexamples and source review

独立证据：evidence/review_20261031/RV-INDEPENDENT-01.meta.json/.stdout.log/.stderr.log，完整公开材料在INDEPENDENT_OBSERVATIONS.json。观察命令退出0表示成功保存观察，不表示六例均满足合同。独立代码使用真实官方SDK生成签名，没修改产品/SDK/冻结测试，也没伪造密码学成功状态。

| 独立case | 期望 | 实际 | 裁决 |
|---|---|---|---|
| S01 正常对照 | 一次合法付款一单 | SDK VALID、方法成功、1付款1单 | 通过 |
| S02 缺可信配置 | 拒绝、零副作用 | 403/H53_AUTHORIZATION_DENIED、全0 | 通过 |
| S03 claim提交前故障 | 两表回滚、零付款订单 | 注入异常、attempt/auth/payment/order全0 | 通过；是故障注入，不是安全拒绝状态码 |
| S04 root/terminal凭据类型反转 | 拒绝、零副作用 | SDK VALID、方法成功、1付款1单 | 不通过 |
| S05 中间型末跳+错误aud | 拒绝、零副作用 | SDK VALID、方法成功、1付款1单 | 不通过 |
| S06 中间型末跳+错误nonce | 拒绝、零副作用 | SDK VALID、方法成功、1付款1单 | 不通过 |

**[P1] 消费者将仍可继续委托的链当作最终支付指令。** ap2_authorization.py:70–107只检查SDK返回list长度2，随后按vct递归收集类型，没有证明第一跳就是受信OpenPaymentMandate、第二跳就是已终结PaymentMandate，未检查末跳不再携带cnf。S04用用户签PaymentMandate并授代理、代理签无cnf的OpenPaymentMandate，反向类型仍被收集为一组合法字段并付款。

S05/S06保持标准OpenPaymentMandate根与PaymentMandate末载荷，但在最后载荷添加下一受托者cnf，官方SDK因此生成typ=kb+sd-jwt+kb（仍可继续委托）；分别将aud改成h53-other-merchant、nonce改成h53-wrong-confirmation。其他金额/币种/收款方、完整签名checkout及独立确认均保持合法。该链经SDK验证可返回两个有效载荷，H53继续执行。

固定SDK kb_sd_jwt.py:128–138只对终结型typ调用verify_expected_claims；中间型cnf表示还可继续委托。它验证这种可继续委托链本身不等于批准作为H53最终支付授权。H53未收窄消费者所接受的链形状，因而不能声称它传入expected_aud/nonce后就必然检查了最终支付上下文。结论限于本地消费者组合错误，不把SDK正常的前缀验证能力写成官方漏洞或生产事故。

实现合理部分保留：验证调用确在BEGIN IMMEDIATE内、原确认和完整当前DB快照检查之后、两表写入之前；两表同事务，S03额外证实故障回滚。checkout_service只有指定传参变动，其他34商家文件及恢复/付款端口不变。完整商家签名/投影/金额币种收款方冲突、未知字段变化和原28例已有实证，但这些不能补偿末跳语义缺口。

最小修复应只改变任务副本ap2_authorization.py：显式限制完整两跳次序、根/末凭据身份和终结状态，再复用官方SDK验签/绑定；任何不支持形状在写claim前拒绝，禁止通过改SDK、降低aud/nonce预期或只补一个攻击字符串来通过。无需重写锁、付款、确认或完整协议。

## Acceptance matrix

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | RV-EV-01..03，1398/51摘要、34只读文件及精确范围保持。 |
| AC-02 | 不通过 | 原28例虽过，S04违反Open→Payment顺序，S05/S06错误aud/nonce仍实际模拟付款，违反冻结输入第7条及最终授权上下文。 |
| AC-03 | 通过 | 限本AC列出的T12–T19/T22/T23/T28路径及事务位置，独立缺配置/回滚也通过；不能外推全局不可绕过。 |
| AC-04 | 通过 | 原T01/T20/T21正常重放、两连接竞争与异常恢复保持，付款快照相符；不表示所有授权输入合法。 |
| AC-05 | 通过 | 完整L2/L3、原始流/接受快照保全、76+8回归及预算透明；未把新反例隐藏。 |

## Final verdict

REJECTED

仅AC-02失败。固定回归中有明确局部净收益，但消费者终结链形状不严，错误受众/nonce仍可触发模拟付款，不能验收本地授权消费能力。旧合同/实现/报告/原证据保留，不在H53内覆盖修复或修改冻结测试。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

H53为one_off（一次性本地样机），不作产品级IMPROVED或生产安全结论；原28例收益保留但样机未被接受。九项能力声明继续false，客户需求UNKNOWN。B-17未关闭，最前可行动缺口由泛化接线进一步收敛为终结授权链形状及上下文约束。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=本地原文/投影组合缺口；after=原28例可运行，独立反例暴露最终授权消费者缺陷，产品成熟度不升级；Test=VP-01..09+独立S01–S06；Evidence=原始签名/DB/假PSP/L3/独立流；残余=真实主体/确认来源、完整协议/JCS、跨系统撤销、Provider/部署/客户未知。无监管合规结论。

## Iteration value and continuation decision

Continuation decision: CONTINUE

继续B-17的一次有界repair（修复），停止扩案例或迁移协议。根因可定位于一个新模块，原锁/确认/付款/恢复和34只读商家文件已有保持证据；修复成本与风险小于重开HTTP/新服务方，预期收益是堵住已复现零容忍授权上下文错误。旧H53的L2预算1/2和56/280不重置，不冒充父任务通过。

修复包只许ap2_authorization.py变化，保留原28回归与独立6例（其中3反例必须转拒绝）；2主动小时/2正式L2/272材料case、Evaluator另102。无新架构或外部权限。通过后STOP该切片；范围/预算变化或同一缺陷无净收益即回Evaluator重排。

## Bottleneck movement after review

地图r87记录B-17未关闭、H53拒收；同事务组合已有代表性正向结果，当前第一缺陷是完整链的根/末角色、终结状态与aud/nonce校验责任，不再是执行写锁本身。这个反例家族比完整JCS/协议升级、真实Provider与客户未知更优先，因为它直接违背当前本地信任合同且可单文件修复。

## Next execution package

- Next task ID: H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1
- Next task path: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/CONTRACT.md
- Next task state: CONTRACT_FROZEN / Executor / repair / SINGLE
- Readiness: 精确失败输入/SDK行为/本地付款和源码根因均已固定；只修新模块、37个继承商家文件中其余36只读；原28+独立6=34回归。
- Authority: 网络/ASGI/模型/Provider/真实支付/安装/对外联系/Git全0，四旗false；H51/H52 STOP和支付宝/比赛延期不变。
- Routing: 完成H53最终REJECTED校验后CURRENT转H53R，父任务冻结r86不反写，最新地图r87；Executor从H53R/EXECUTOR_START.md开始。
