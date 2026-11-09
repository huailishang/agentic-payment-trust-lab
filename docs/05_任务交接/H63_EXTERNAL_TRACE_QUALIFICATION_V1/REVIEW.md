# H63 独立复核：来源观察可保留，P1–P5合同映射不通过

Task ID: H63_EXTERNAL_TRACE_QUALIFICATION_V1
Task kind: one_off
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review date: 2026-11-08
Reviewer: Evaluator
Task verdict: REJECTED
Impact verdict: INCONCLUSIVE
Continuation decision: CONTINUE

## 全局位置

目标是在本地可重置边界内证明授权、交易绑定、执行前治理、异常恢复和审计形成可独立复核的信任链。地图2026-11-07-r101：A–D本地阶段关闭，E受控本地代表性闭合，F外部协议/消费者适用性当前。B-18仍是第一可执行测量缺口：外部轨迹是否能形成对本仓既有合同有效的独立观察。H62局部订单恢复已停止扩张；B-06真实身份/PSP受Human后置约束；两者均不抢占本轮。

H63为来源资格测量，不是能力建设。完成须同时满足真实引用与既有合同语义；结构L3通过不能抵消错误映射。

## Pre-review checks / 评估前检查

- 当前提交REPORT、MEASUREMENT、EXTRACT、账本、合同、计划与CHECK/INPUTS的hash保存在 `evidence/REVIEW_SNAPSHOT_20261108.json`；接受后未改提交原件。
- 中央workflow validator在接受前及READY_FOR_REVIEW状态均OK。独立执行冻结四VP，L3 4/4 PASS；未执行产品、模型、商家或支付。
- 独立脚本不import执行者EXTRACT/CHECK/产品代码，逐一读取六源并复算原源hash、全部事实引用的JSON pointer/value hash、调用id和响应id，保存RV-EV-06。首次RV-EV-05在全部内存检查后因GBK输出编码失败，原始失败保留；只修复审阅脚本UTF-8输出，未改样本或提交原件。
- CHECK旧版读取snake_case `tool_calls`，真实预览是camelCase `toolCalls`。独立diff确认修复限定明确付款相关函数，且新增正负例；INPUTS只有CHECK一项hash变化，其余条目不变。**本评估接受该兼容性例外作为复核基线**，不据执行者自述独立证明历史Human授权，也不把此例外推广到AC、权限或付款规则变更。
- RV-EV-01/04核对H62 1154、其它保护1719、冻结23和原数据库3。H63原报告/账本中的执行期零外部调用为记录值及源码审阅支持，并非操作系统级完整网络取证。本轮公开网页读取验证两次不可达，不新增样本；不回写执行者零网络账本。

## L3 Independent Gate / 独立复核门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/L3-GATE.json
- Validation plan: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/VALIDATION_PLAN.yaml
- 4/4 mandatory checks；语义复核单独见RV-EV-06。此处PASS只表示冻结结构检查可复现。

## Acceptance matrix / AC 逐条裁决

| AC | 裁决 | 独立证据 |
| --- | --- | --- |
| AC-01 来源与保护 | 通过 | RV-EV-01/04/06；固定六源、原保护材料及hash；上述单独接受的CHECK兼容例外，不修改原合同 |
| AC-02 六条源事实可回指 | 通过 | RV-EV-02/06及逐源审阅；七类事实、角色、调用/响应id均可回指；S03令牌/S06模拟收据维持TRANSCRIPT_ONLY |
| AC-03 映射既有P1–P5 | **不通过** | RV-EV-06、EXTRACT的contracts构造、MEASUREMENT六例、项目confirmation/payment_binding/execution_facts/context_policy/replay定义；编号与合同语义错位，影响六例 |
| AC-04 证据/预算/声明 | 通过 | RV-EV-03/04/06；6/18提取、1/2 L2、记录13/120分钟，模拟/非留出/不测产品效果边界保留；不升级监管成熟度 |

## 必须修复的反例

既有定义由产品代码确定，而不是按购物步骤重新编号：

| 合同 | 既有含义 / 权威代码 | H63目前映射的问题 |
| --- | --- | --- |
| P1 | confirmation.py：确认记录与订单摘要/授权版本/有效期绑定 | 仅user_request就给OBSERVABLE；S01明示价格确认ABSENT，却P1 OBSERVABLE。用户请求存在只能是部分输入，不能代表P1所需输入齐全 |
| P2 | payment_binding.py：Authority→Order→Request→Execution连续绑定 | 写成价格确认/checkout，未按授权版本、agent/payee和连续引用清点缺输入 |
| P3 | execution_facts.py：Agent/Executor Identity Assurance | 写成checkout/payment关联，交易id关联不能提供执行身份事实 |
| P4 | context_policy.py：可信来源、上下文与策略完整性 | 写成付款调用/PSP结果，未评价source×fact-domain策略、来源和更新历史输入 |
| P5 | replay.py：证据收据与运行时治理事实回放 | 写成订单结果，get_order不能替代RuntimeGateRecord或完整治理收据链 |

P1–P5误映射不是单纯报告标题；相同逻辑在EXTRACT和六份MEASUREMENT中。冻结CHECK仅校验键/枚举/引用，不校验上述含义，因此L2/L3均可通过。AC-03本来明确要求Evaluator独立语义审阅，本次据此拒收，不修改原CHECK让它“证明自己正确”。

## 六源能证明什么

- S01乐器：用户购买请求、选色及checkout可见，没有后续明确价格确认/付款/订单记录。
- S02汽配：40行确认58.18美元；41–42行load_payment_data得到钱包数据；43–46行complete_checkout/get_order。直接pay未见，不等于未付款或支付失败。
- S03童装/家居：28行确认183.58美元，29–30行shop_pay_payment_request得到令牌，31–34行complete_checkout/get_order。checkout id可关联，令牌不等于清算。
- S04钱包：17行同意选品；不是带价格付款确认。S05图书：选书，不等于批准扣款。两者未到付款。
- S06服饰：23–24行请求支付挑战，26行确认25.42美元，29–30行pay及模拟收据，31–32行get_order；可检查“挑战→确认→pay”顺序，不能把预先请求挑战误说成提前扣款。总额2542与25.42美元的换算须明确来源单位，不能靠字符串相等作绑定。

来源为General Machines在Hugging Face公开的CartTrace-100k，revision `86cab5e539e161e0915d78d8abdd9023f09b411e`。准备记录按字典序前六类别各首路径取六个JSONL，不按成功结果挑选；不是随机代表样本或新鲜留出集。数据说明称模型在模拟商城中运行，商品来自开放目录，用户/价格/库存/PSP/钱包模拟，上游评分未做人工标签校验。这里可独立复算的是**记录中的关系**，并非真实机构对付款或身份的证明。

数据源与本仓独立；其事实层级仍是模拟轨迹。全部10万级数据集是否还有更充分后端/协议证据，不由六份预览推断。本轮在线页面不可达，来源解释依据已固定README/SCHEMA/NOTICE与准备hash，不声称重新在线核实发布者。

## Project impact verdict / 项目影响裁决

Impact verdict: INCONCLUSIVE

已收敛六源的局部可观察性，但错误合同映射尚未闭合B-18；没有产品控制效果、未见样本泛化、生产安全或真实消费者价值增量。不能把REJECTED解读为支付系统发现漏洞；缺陷位于测量产物。

## Iteration value and continuation decision

Continuation decision: CONTINUE

只继续一次最小语义修复：`docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/CONTRACT.md`，新ID H63R_CONTRACT_MAPPING_REPAIR_V1，repair，CONTRACT_FROZEN/Executor；保留H63全部拒收原件，另产MAPPING.json，复用固定事实与原有代码定义，不新增下载、适配器、产品/付款或模型调用。60主动分钟/2L2，上游和本仓历史均只读，修复后L3独立检查30个映射。

此预算优于直接开展S03/S06比较：先修正判定对象，避免比较错误目标；也优于扩H62或恢复受限PSP。修复通过后再判断是否值得单独冻结确认—checkout—工具调用的窄比较；若只能重复已知缺失，STOP此预览视图。地图r101冻结字节不改，B-18优先级与全局阶段未变；当前路由记录修复任务，不假装新产品阶段已完成。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20；对象=原源资格合同；代码=H63测量/检查及既有P1–P5定义；Test=四VP+独立源审阅；Evidence=L3/RV-EV-06；before/after产品成熟度不变；真实身份、付款、客户价值、合规unknown。

## Final verdict

REJECTED

## RV-EV-01 — VP-01

- AC: AC-01
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-01.stderr.log
- Observed result: 0 / PASS.

## RV-EV-02 — VP-02

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-02.stderr.log
- Observed result: 0 / structural PASS; AC-03 semantic failure above.

## RV-EV-03 — VP-03

- AC: AC-03, AC-04
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-03.stderr.log
- Observed result: 0 / PASS.

## RV-EV-04 — VP-04

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l3_evaluator_20261108/RV-EV-04.stderr.log
- Observed result: 0 / PASS.

## RV-EV-06 — 独立源审阅输入与合同反例

- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/semantic_evaluator_20261108/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/semantic_evaluator_20261108/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/semantic_evaluator_20261108/RV-EV-06.stderr.log
- Observed result: 0 / independent provenance/citation audit; recorded counterexample supports AC-03 不通过. RV-EV-05为保留的编码失败，不充作成功证据。
