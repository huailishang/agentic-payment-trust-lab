# H64独立复核：访问限制属实，调用关联与金额提取不通过

Task ID: H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1
Task kind: one_off
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review date: 2026-11-08
Reviewer: Evaluator
Task verdict: REJECTED
Impact verdict: INCONCLUSIVE
Continuation decision: CONTINUE

## 全局位置

最终目标是使授权、交易绑定、执行前治理、执行/恢复与审计形成可独立复核的信任链。冻结地图r103：A–D本地闭合，E受控本地代表性闭合，F当前。第一可执行证据缺口B-18仍是外部轨迹的独立判定；H62已闭合本地切片，B-06真实支付仍Human后置，均不因本轮结果扩张。

H64为完整材料的来源资格测量，不是产品能力实验。完成需要选样固定、源事实完整清点、原生关联与金额判定有证据；允许INPUT_LIMIT（输入获取受限），但该结论不能豁免其余可取得数据的正确测量。下一步优先离线修复已测材料，暂不重复GET或安装运行时。

## Pre-review checks / 评估前检查

- CURRENT为EXECUTING/Executor、REPORT为SUBMITTED_FOR_REVIEW，执行者L2 4/4 PASS；接受前中央workflow validator（工作流结构检查器）OK。
- RV-EV-05保存12项提交/冻结文件SHA，包括REPORT、MEASUREMENT、SELECTED、账本和三个实现文件；不import执行者ACQUIRE/MEASURE/CHECK/ORACLE，独立从已获Parquet读取固定六例的原始用户话语和逐调用结果/协议关联。提交原件不改。
- 接受后CURRENT置READY_FOR_REVIEW/Evaluator，结构检查OK。按冻结计划独立运行L3 4/4 PASS；另有RV-EV-06原源反例，不以结构成功代替语义裁决。
- RV-EV-01/04：2944保护文件、34冻结文件、HEAD和既有三库未漂移；指定wheel一次隔离安装。评估者仅复用现有解码器离线读表，新增网络/安装/上游回放/模型/产品/付款0。
- 执行期账本：18/20 GET、88,710,515/268,435,456字节，成功16、失败2；样本读取12/12，测量版本1/2，L2 1/2，记录工时20/180分钟。未独立取证全部操作系统行为或真实主动工时，账本值与源码/原始门禁分开评估。

## L3 Independent Gate / 独立复核门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/L3-GATE.json
- Validation plan: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/VALIDATION_PLAN.yaml
- 4/4强制检查、8个冻结金额用例和7项边界自测通过。这只证明既有结构及纯函数用例，不证明实际源数据被充分提取。

## Acceptance matrix / AC 逐条裁决

| AC | 裁决 | 独立证据与解释 |
| --- | --- | --- |
| AC-01 来源/隔离/保护 | 通过 | RV-EV-01/04、下载摘要与安装记录；指定四Parquet/wheel摘要保持、旧材料无漂移；失败GET记录未删除 |
| AC-02 固定样本与完整事实资格 | **不通过** | 固定选样和引用摘要可复算，但RV-EV-06证明第4例PRESENT关联引用实际为call-32/call-32/call-34；不是同一个原生调用id |
| AC-03 金额判定与复现边界 | **不通过** | ORACLE八用例通过；实际测量输入却统一payment=None/exact_link=False，未清点第6例协议已报告金额/币种/checkout。又以用户文字无signed/ref-bound checkout为全部丢弃付款字段的理由，超出本包只读观察范围 |
| AC-04 证据/预算/一次决策 | 通过 | RV-EV-04/05/06与账本：某world两次失败后停、没有第三次GET；INPUT_LIMIT分类真实，不充作数据无用或产品漏洞；该分类不抵消AC-02/03失败 |

## 独立反例与根因

**R1：混合列表的第一个元素不构成同一条链。**

`ep-09bafc6d1c7e`：原turns调用seq32/call-32与其结果相关；另有seq34/call-34，wire seq35的source_call_id是call-34。MEASURE.py:355–357分别取calls[0]、results[0]、matching_wires[0]，三个摘要都是真的，但值为`call-32, call-32, call-34`。没有引用显式父子关系就不能说三者“share explicit native call IDs”。应按每个call id分别建立链；父/子可以同时存在，不能合池后冒充精确相等。若完整链缺失，保留PARTIAL（部分）而非伪造PRESENT。

**R2：保留已观察金额，单独记录仍缺的绑定条件。**

`ep-172fbb8cce5b`：用户seq64明确说44.25美元；pay调用call-68在seq68，协议响应seq69，位于wire原行组1/行2632，source_call_id=call-68。响应包含checkout-3766021cd113、total=4425、currency=usd、status=completed。它是**模拟协议报告的付款结果**，并非独立清算事实，但已经存在，不能一律写payment=None。

MEASURE.py:384–389把所有确认checkout_id设None、所有payment设None、所有exact_link设False；因此不论源里有没有金额与id，纯函数都只能NOT_JUDGEABLE（不可判定）。这没有检验全部源的可用性。金额单位、确认到checkout绑定和实际后端状态可以分别UNKNOWN（未知）；即使最终仍不可判定，也应先提取已观察字段并给出具体缺失维度。

源messages还提供consent_seq/payment_seq/completion_seq，可用作定位线索，但不是授权真值，须与用户原文、显式业务id/挑战id/原生调用记录相互核对。本包不要求用户自然语言自己包含密码学签名或字面checkout id；也不允许仅因消息相邻就认定绑定。修复不能为追求正结果把exact_link直接改True。

## 访问失败与合同门槛的解释

固定env-bd45a7e9be19的envpack两次GET均失败且未生成文件；其余5个world对完整，6个manifest存在。评估者未重试；只能确认客户端记录的访问失败，不能宣称源文件不存在/损坏。INPUT_LIMIT可保留。

原合同AC-04正向表述“至少一例完整跨表/world关联”，冻结CHECK另要求所有所选world文件存在；本次没有修改门禁来追认正结论。后续设计须明确“某例可用于下一实验”和“六例全部齐备”是不同指标，不能仅因一个文件失败就跳过其余已取得材料的语义分析。新修复包继承访问受限，不新增下载，也不提前改判回放就绪。

## Project impact verdict / 项目影响裁决

Impact verdict: INCONCLUSIVE

新增完整材料获取、固定选样和访问边界证据可以保留；金额可判定性尚被测量缺陷混淆，不能声称六例事实均不足，更不能声称本仓控制改善/失效。缺陷位于来源测量，不是已发现支付产品漏洞。B-18优先级不变，眼前阻塞细化为“已获取源事实的正确关联与无损清点”。

## Iteration value and continuation decision / 下一步

Continuation decision: CONTINUE

下一包：`docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/CONTRACT.md`，H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1，repair（修复），CONTRACT_FROZEN/Executor。仅离线复用同六例、同四Parquet/11个world和现有解码器，另产逐调用链、原始金额字段及逐维缺失判断；90主动分钟/2L2，网络/安装/回放/模型/产品/支付0。原H64提交、失败、证据、预算与冻结文件保留。

修复预算比先恢复缺失world更有价值：5例材料已经完整，下载补齐并不会修正混合id和恒空金额输入；比更换数据集或扩H62成本更低。修复通过后再评估金额是否可比较、哪些world足够及回放基线是否值得另冻；允许保持不可判定，不能预设数据合格。发现新的零容忍产品反例才切换能力建设。

签收拒收结果后归档冻结r103并更新地图r104/新路由；属于治理边界，不回写本合同、BASELINE、报告、数据或L2/L3。历史保护复现使用原地图与工作区快照，不在新增修复包后重跑旧全工作区checker。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；对象=金额来源资格合同；代码=本任务测量/纯函数；Test=4VP+8用例+6源语义审阅；Evidence=L3/RV-EV-05/06；产品成熟度before/after不变；身份/清算/控制效果/商业价值/合规unknown。

## Final verdict

REJECTED

## RV-EV-01 — VP-01

- AC: AC-01
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-01.stderr.log
- Observed result: 0 / PASS.

## RV-EV-02 — VP-02

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-02.stderr.log
- Observed result: 0 / structure PASS, AC-02/03 semantic failure separately documented.

## RV-EV-03 — VP-03

- AC: AC-03
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-03.stderr.log
- Observed result: 0 / eight pure-function cases PASS; does not validate the source-to-input extraction.

## RV-EV-04 — VP-04

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l3_evaluator_20261108/RV-EV-04.stderr.log
- Observed result: 0 / PASS.

## RV-EV-05 — 六源独立清点与接受快照

- AC: AC-01, AC-02, AC-03
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-05.stderr.log
- Observed result: 0 / source inventory captured, no upstream/product execution.

## RV-EV-06 — 两项原源反例

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/independent_evaluator_20261108/RV-EV-06.stderr.log
- Observed result: 0 / reproduced call-id mismatch and omitted reported amount; no live GET retried.
