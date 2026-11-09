# H52 Evaluator Review

Task ID: H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review status: FINAL
Review date: 2026-10-31

## Project context before review

项目最终目标是令高风险智能体支付的身份、授权、绑定、执行、恢复与审计有独立证据。冻结地图r84：A–D阶段关闭，E仅本地受控代表性验证，F当前。B-17是标准授权、可信来源、已验签原文到业务投影和唯一商家执行点的组合缺口。它优先于已PASS/STOP的本地锁及HTTP方向；Stripe/Medusa会增加新变量，支付宝/比赛保持延期。

H52是one_off（一次性测量），只收敛就绪与下一最小边界，不建设能力。完成条件为固定来源/版本、四合成角色、12真实签名材料和12义务逐项可复核、8项计划通过且诚实保留缺口。材料可复算则接受测量；需要商家变化则转合同设计；无净信息收益则停止继续测量，不以PASS自动派实现。

## Pre-review checks and accepted snapshot

中央工作流校验在接受前返回OK；冻结baseline（基线）检查HEAD、1367保护文件、21冻结文件和依赖版本通过。未安装依赖，四项权限均false。继承的其他工作区改动未处理。

evidence/review_20261031/AUDIT.py先核对正式L2 8/8及16条原始输出流的长度/SHA-256，固定90文件到ACCEPTED_SNAPSHOT.json；然后CURRENT转READY_FOR_REVIEW/Evaluator，执行原冻结计划完整L3。复跑后90/90接受文件一致、L2/L3共32条原始流长度/哈希一致，12条稳定观察和Q07独立根诊断均相等。证据见PRESERVATION_AND_COMPARISON.json。签名字节和公钥每轮重新生成，不要求相等，也没有覆盖L2输入。

正式L3后再次检查1367保护文件、21冻结文件和工作流通过，才写本最终REVIEW、地图r85、CURRENT与H53草案。这些为明确的治理变动；H52合同、计划、来源、产品/商家、REPORT、Executor账本和原始证据不反写。最终REVIEW替换了接受快照中的占位REVIEW，因此保全结果描述的是裁决写入前的快照。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/L3-GATE.json
- Validation plan: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/VALIDATION_PLAN.yaml

原计划串行8/8通过，mandatory failures=0；76相关回归、旧H37八例全部通过；检查器拒绝11种过度结论/坏输入。该检查器自测不等于完整攻击覆盖。Evaluator签名材料12/72，Executor预留48/144（包括失败的首轮12）、正式L2=1/3；主动70分钟为Executor自报，无法独立计时。所有网络/ASGI/模型/Provider（支付服务方）/付款计数为0，未运行商家、联系他人或执行Git写操作。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-01.stderr.log
- Observed result: 1367保护/21冻结摘要及现有环境通过，安装0。

## RV-EV-02

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-02.stderr.log
- Observed result: 来源/版本/12义务结构通过；真实性另做逐项源码审阅，见下文及SOURCE_EXCERPTS.txt。

## RV-EV-03

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-03.stderr.log
- Observed result: 新生成12例，局部crypto VALID共9例、业务ALLOW共7例，均没有商家执行证据。

## RV-EV-04

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-04.stderr.log
- Observed result: 从完整原始token、公钥、JSON与时钟重算12/12一致。

## RV-EV-05

- AC: AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-05.stderr.log
- Observed result: 材料、结果九项false、范围、账本与diff空白检查通过；分类含义由Evaluator独立判断。

## RV-EV-06

- AC: AC-05
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-06.stderr.log
- Observed result: 76/76相关回归通过；没有把历史全量结果当本轮全量复跑。

## RV-EV-07

- AC: AC-01, AC-05
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-07.stderr.log
- Observed result: 原H37八例8/8通过，含正常与七类无效签验。

## RV-EV-08

- AC: AC-05
- Meta: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.meta.json
- Stdout: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.stdout.log
- Stderr: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/review_20261031/l3_evaluator_01/RV-EV-08.stderr.log
- Observed result: 拒绝9项错误能力声明与2种坏观察输入，11/11。

## Independent source and observation review

逐行审阅PROBES/RUN_PROBES/RUNTIME/REFERENCE/PACKET_CHECK并核对既有产品API：PROBES独立生成四把内存私钥，实际调用MandateClient.create/present/verify、既有验签适配/协议边界/validator；没有调用REFERENCE.recompute代做测量，没有修改既有拒绝规则。公钥与公开合成材料落盘，私钥未进入结果；SDK日志只定向任务临时目录。验签结果与业务观察分别保存，血缘布尔值只描述固定root/terminal字段相等，不是完整端到端授权判据。

12例独立观察归因如下，不能将它们合并为一个支付成功率：

| Case | 独立结果与含义 |
|---|---|
| Q01 | 链/商家签名/边界有效、ALLOW、投影血缘一致；只证明局部API组合事实。 |
| Q02 | 授权链仍有效，商家签名与checkout hash均无效；root/terminal血缘仍true说明该字段不覆盖整个checkout。 |
| Q03 | 新商家签名有效，但旧PM与新checkout hash绑定不符，边界拒绝。 |
| Q04 | 投影金额1000→1500，签名链未变，血缘false，业务仍ALLOW并产生15美元请求；这是最清楚的投影组合断点。 |
| Q05 | 投影收款方变化，血缘false，业务DENY/merchant_out_of_scope；不能写成所有投影篡改都放行。 |
| Q06 | 投影币种USD→EUR，血缘false，却产生USD请求并ALLOW；ap2.py:389–394、444–465对mandate和request使用根约束中的同一个currency。不是已执行EUR支付，也不能当币种冲突已被独立校验。 |
| Q07 | 可信预置根验攻击者链INVALID；换成攻击者公钥的诊断VALID。后者只说明自签可验，不能证明身份。业务层仍ALLOW，说明各层没有共同消费者。 |
| Q08 | 移除独立合成确认标记，既有三API仍给局部通过；标记根本未传入API，不是观测到生产无确认付款。 |
| Q09 | 验签时钟过期使链INVALID，局部业务仍ALLOW；业务输入occurred_at未随验签时钟改变，不能由此断言validator自身过期判断失效。 |
| Q10 | 错受众使链INVALID，局部业务仍ALLOW；业务投影不消费该密码学结果。 |
| Q11 | 无状态链验签有效，但显式seen-id令业务DENY/duplicate_request；未测跨进程持久去重或换键重放。 |
| Q12 | 链有效，缺上下文使边界MISSING_EVIDENCE，未伪造上下文补齐。 |

L2/L3使用同一SDK与冻结参考算法，因此一致性证明可复算，不是独立密码学审计，也不是官方协议全量符合性。可选Frequency枚举失败后移除该可选约束只发生在探针内，最终仍满足冻结12例；不代表可选递归约束兼容性已解决。

12项义务均逐条检查原文/源码，而非仅信任结构checker（检查器）。摘录保存在evidence/review_20261031/SOURCE_EXCERPTS.txt：

| 义务 | 裁决与限制 |
|---|---|
| VERSION_SCHEMA | GAP正确：商家2026-04-08与参考2026-08-25不同；差异本身不证明必须全面升级。 |
| CAPABILITY_NEGOTIATION | GAP正确：完整profile没有AP2扩展；规范要求能力交集激活后锁定会话，未运行此协商。 |
| MERCHANT_SIGNATURE | GAP正确：普通紧凑小对象签名不等于商家完整detached JWS（分离载荷签名）。 |
| FULL_CHECKOUT_JCS | GAP正确：规范覆盖完整checkout、保留未知字段并排除ap2；H52排序ASCII JSON无此证明。 |
| TRUSTED_CONSENT_ISSUER | GAP正确：根公钥由API参数提供；真实身份/确定性确认来源未测。未来可先使用明确合成研究来源。 |
| DELEGATION_KEY_BINDING | MEASURED_LOCAL/REUSE正确，仅固定SDK两跳签验；不证明现实持有人。 |
| AMOUNT_CURRENCY_PAYEE | 接受MEASURED_LOCAL仅指现有规则与本轮观察，不接受“终端币种冲突已校验”的延伸解释；Q06归因如上。 |
| VERIFIED_PAYLOAD_LINEAGE | GAP正确：验签事实不携带强制投影消费关系，Q04/Q06暴露重复共同断口。 |
| REPLAY_REVOCATION_ORDER | GAP正确，仅外部授权接入的撤销/去重顺序缺证据；不推翻H51既有同库合成控制。 |
| EXECUTION_SNAPSHOT_CLAIM | GAP正确指未消费AP2材料；H51已有确认快照/claim，不得表述成现有商家完全没有快照控制。 |
| PROVIDER_REFERENCE_QUERY | NOT_OBSERVABLE正确，本轮未调用真实Provider；不要求本轮补真实服务。 |
| TRACE_CONSUMPTION | NOT_OBSERVABLE正确，仅缺本次外部授权到执行的消费链；原A–D已有审计能力不重开。 |

另查H51 merchant/dependencies.py:253–271：默认get_checkout_service不传execution_control；服务complete_checkout:745–747仍拒绝，不能因H51夹具注入或H52材料就宣称默认部署就绪。官方三个来源按冻结快照核查许可/摘要与归因；没有重新获取实时网页、执行教程命令或将规范文字当本地实现。

## Acceptance matrix

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | RV-EV-01/02/07；1367保护/21冻结摘要、固定环境、来源版本及源码核对，无静默升级。 |
| AC-02 | 通过 | RV-EV-03/04；12份真实公开材料重算、四独立公钥、正常和双根诊断符合合同，观察摘要与L2一致。 |
| AC-03 | 通过 | RV-EV-03..05及逐例源码归因；原始结果如实揭示不强制的责任，不用ALLOW代替执行或官方漏洞结论。 |
| AC-04 | 通过 | RV-EV-02/05和12义务人工审阅；分类MERCHANT_CONTRACT_CHANGE_REQUIRED成立，下一实现仍须收窄并冻结，不能直接照搬宽候选。 |
| AC-05 | 通过 | 完整8项L2/L3、76+8回归、32条原始流、90文件保全及账本/失败保留，预算内。 |

## Final verdict

PASS

接受H52离线就绪测量，工程分类为MERCHANT_CONTRACT_CHANGE_REQUIRED（需要商家消费合同变化）。这既不表示已有端到端授权能力，也不是发现了正在执行的错误付款。当前合同内未发现需另开repair（修复）的实质验收失败。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

本任务为one_off（一次性测量），没有产品或商家能力增量。信息收益是组合unknown（未知）缩为可重复的已验签载荷/投影断口及商家消费责任缺失。不能写成0→12能力提升；九项能力声明保持false，customer_demand=UNKNOWN。E阶段不升级为真实主体/凭据治理验证。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=既有本地签验/HTTP能力、组合未知；after=组合缺口有独立离线证据，产品成熟度不变；Test=VP-01..08；Evidence=原始材料/L3/本REVIEW及保全记录；残余=真实主体、信任锚/确认来源、完整协议兼容、跨系统撤销、Provider与客户未知。无监管合规结论。

## Iteration value and continuation decision

Continuation decision: STOP

停止H52同类就绪矩阵与签名材料扩充：重复再加合成案例不能消除商家消费合同。保留B-17为第一瓶颈，转一个Evaluator-owned（评估者负责）的合同收敛草案。比直接升级整个商家/接Stripe更有价值，因为能先排除版本/签名格式误配和范围扩张；比重测锁/HTTP更能触及真实剩余断口。

不完全接受Executor下一边界的实施广度：完整2026-08-25迁移、完整JCS、可信确认、不可绕过执行与审计/Provider回传是多项义务，不能用“claim前一个接缝”包装成已就绪的单变量实现。版本差异不等于必须全面升级；完整UCP凭据格式也不等同H52的四字段compact JWS和旧AP2两跳链。下一轮先定义精确输入、研究信任模型与独立判定，不提前宣称READY_FOR_BOUNDED_IMPLEMENTATION（有界实现已就绪）。

## Bottleneck movement after review

地图r85：B-17缩小、未关闭。新增证据为Q04的有效签名/改金额ALLOW、Q06币种被归一后的血缘缺口、Q07/09/10密码学失败不被业务层消费，以及12项商家义务归因。局部SDK与业务规则可复用，缺的是可信原文、确认、业务投影和执行快照在同一消费合同中的不可绕过结合。尚无生产、真实Provider或客户证据。

CONTINUE（继续）的条件是精确样本/格式、现有序列化机制、合成信任来源和最小修改范围可冻结并可独立判定；若只能重写完整商家或仍缺可信输入/授权，则STOP/SWITCH（停止/转向）。此后才考虑受控实现，再按授权进入外部协议/网络/Provider验证，支付宝/比赛后置不变。

## Next execution package

- Next task ID: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
- Next task path: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/CONTRACT.md
- Next task state: DRAFT_CONTRACT / Evaluator / evaluator_design / NOT_DISPATCHED
- Readiness: NOT_READY；精确缺项为完整原生checkout/凭据格式与版本边界、现成JCS机制和独立向量、研究信任/确认来源及唯一写入口消费范围。均先由Evaluator核对现有证据，无需先找付费客户或索要真实密钥。
- Budget proposal: 2主动小时只读设计，实际AC/命令/权限须就绪后冻结；不是H52预算重置，也不是新实现派发。草案不运行商家/模型/外网/ASGI/Provider，不安装、不联系他人、不执行Git写操作。
- Routing: CURRENT保留H52最终PASS与冻结r84关联，next_artifact指H53草案；地图现状为r85。H52 REPORT、RESULT、NEXT_BOUNDARY和所有Executor证据保持原样，Evaluator裁决与收窄意见以本REVIEW为准。

## Evaluator diagnostic notes

正式验证外的工具准备有两次仓库scripts路径调用失败（正确脚本位于同级localagent-common，随后使用准确路径）；源码摘录辅助脚本首次控制台输出遇GBK编码错误，但UTF-8摘录文件已完整写出，后来仅修复Evaluator辅助脚本的stdout编码。均不涉及探针、正式L3重跑、材料预算、产品变更或原始证据覆盖。正式L3仅一次8/8，不掩盖这些工具准备失败。
