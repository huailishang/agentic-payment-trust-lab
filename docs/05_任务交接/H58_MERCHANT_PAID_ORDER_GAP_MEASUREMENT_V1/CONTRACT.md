# H58 测量已付款但无订单的持久证据与补救责任

Task ID: H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Task mode: measurement-only
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置与为何现在测

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-02-r95
Active bottleneck: B-17
Hypothesis: NONE（只读测量，不是能力实验）

A–D本地代表性阶段已完成，E仅本地，F当前。H57R已独立接受六例正常工厂HTTP及首商城进程退出后查询不重扣，停止继续工厂/日志修复。M06模拟付款成功但订单0、库存5，原恢复只QUERY/SUCCEEDED。此状态是已知业务边界，不是新多付或新安全漏洞。本轮只回答现存持久输入和责任是否足以支持一个未来安全补救包；不重复支付/恢复实验，不预设自动补单正确。

比H56未执行非标准披露支线，此处有现成商城业务断点；比真实PSP/客户，此处不依赖外部授权。只读测量成本低、避免直接建错业务。不研究新外部材料，不引入第二套工作流。

## Single objective / 唯一目标及主要变更

对固定H57R正式L3的M01正常对照和M06失败材料，完成一次可独立复算的“持久证据—仅实验交接—缺失事实—补救责任”测量，比较保留查询、未来订单完成、补偿/人工三机制，输出唯一下一决策。主要变更只有本包MEASURE.py只读提取器；不会改变已观察商城状态。

## Inputs / 输入及口径

INPUTS.json冻结HEAD、工作区保护文件、正式L3原始材料、两份M06交易库/模拟PSP库hash和源码。只用evaluator/run_0002，不用LATEST漂移输入、不用首轮预签收诊断代替正式观察。

M01对照只有已接受观察快照；不声称本轮重新执行。M06数据库以mode=ro&immutable=1读取，禁止checkpoint/写PRAGMA/写事务/复制成可写库/修改原数据。固定库已正常关闭且无活动写入；缺库、hash漂移或伴随活动WAL则停止，不补造库。

测量产物MEASUREMENT.json的精确事实结构由冻结CHECK.expected独立重算：两例case/http_statuses/payment_calls/orders/inventory/attempts/recovery/authorization_records，以及M06两库所有表的规范行。MEASURE.py不得导入或调用CHECK.expected（检验器不能成为被测实现）；只能从INPUTS定位固定原始材料、自己解析JSON和只读SQL。两次同输入输出必须相同；不得用冻结观测结果常量替代读取。

ANALYSIS.json按CHECK.TOPICS顺序逐项记录12个主题：结账身份、付款引用/状态、金额币种收款方、明细与履约、回滚后库存、确认与撤销、授权证据、原请求/幂等、订单ID/结束状态、重启信任配置、补偿权限、审计责任。每主题给availability=PERSISTED/TEST_HANDOFF_ONLY/MISSING/MIXED、basis=measured/estimated/unknown、sufficient_for_automatic_action布尔、finding、residual_risk、evidence数组。每证据有path、locator、observed；locator必须精确到JSON路径、表/列/主键或源码行，不能只列整个文件。描述“缺失”须有检索范围和源码依据，不能把没看到写成不存在。

特别区分：h50_attempts仍IN_FLIGHT不等于PSP失败；测试传给第二worker的token/可信上下文不自动成为生产持久事实；GET200不等于订单完成；SDK验签、已记录摘要与真实补偿授权不能互换；M01成功不证明M06能安全重建订单；库存此刻可用不保证未来重试仍可用。不得把可生成新order_id当原订单身份已持久。

ANALYSIS.json包含三个固定mechanisms（KEEP_QUERY_ONLY、ORDER_COMPLETION_CANDIDATE、COMPENSATION_OR_MANUAL_CANDIDATE），分别给ABSORB/REFERENCE_ONLY/REJECT、未执行=true、前提、安全条件、权限、复杂度/成本、失败或停止条件。最后唯一next_decision为BOUNDED_RECOVERY_CANDIDATE / MISSING_DURABLE_INPUT / HUMAN_POLICY_REQUIRED；给依据和missing_facts。没有缺项时missing_facts用明确NONE及依据，不能伪造人工阻塞。候选可行不是已实现。

ANALYSIS.md用中文解释业务意义，比较以上三者、停止不做的代价、H56最强替代、预计工程/人工成本与可证伪的下一边界。仅是设计建议，无执行自动补单/退款/联系客户的授权。

## Allowed scope / 范围

只可新建/修改本包MEASURE.py、MEASUREMENT.json、ANALYSIS.json、ANALYSIS.md、RESULT.json、ATTEMPT_LEDGER.json、REPORT.md、evidence/。输入、CHECK.py、PREPARE.py、合同、计划、入口及INPUTS冻结。旧任务、38商家、src/tests、SDK、地图均只读。CURRENT仅可改同任务EXECUTING/Executor和精确phase，提交仍Executor；不得改历史或权限。

## Exclusions / 排除与禁止副作用

只用已有系统Python标准库。任何HTTP/ASGI/商城应用启动/端口/外部DNS/网络/SDK或Provider调用、付款/退款、订单或库存写入、recover调用、测试patch、安装、模型、外部联系、Git提交/推送/历史改写全0。不得用H57R剩余HTTP额度。代码审查会独立检查只读性，schema检查成功不替代内容验收。

## Acceptance criteria

### AC-01 — 固定输入与全仓保护
Given INPUTS固定来源；When VP-01/06；Must observe所有保护/冻结/两库hash不变、正式L3/HEAD一致、无越界写入。不得改旧报告/证据、商家/SDK或补造输入。Mandatory: yes。

### AC-02 — 原始状态可复算
Given M01/M06；When VP-02/03；Must observe两次独立读取相同，MEASUREMENT与冻结CHECK独立只读重算逐值相同，包括全部表行和原HTTP、1付款1订单对照及1付款0订单失败。不得把仅查询变成补救成绩或运行新业务。Mandatory: yes。

### AC-03 — 持久性、信任与缺失分开
Given12主题；When VP-03及人工源码/证据审查；Must observe每主题都有准确定位和真实observed值、证据类型/充分性/残余风险；区分实验交接和库内事实、IN_FLIGHT和SUCCEEDED、缺订单与重试权限；记录重启后还需什么可信配置。不得以哈希存在冒充可独立重验完整授权。Mandatory: yes。

### AC-04 — 单一决策和完整机制比较
Given三机制；When VP-03及独立内容审查；Must observe三者前提、安全/权限/成本/停止条件完整，单一next_decision与RESULT一致，明确对H56/停止的比较；自动恢复/生产/客户结论false。只允许形成未来候选或精确缺事实，不实施。Mandatory: yes。

### AC-05 — 完整提交及预算诚实
Given冻结六VP；When L2/L3；Must observe全部固定门禁通过、六种损坏自测拒绝、原始输出/失败保留、REPORT逐AC索引和ATTEMPT_LEDGER精确工作起止区间。执行者不得签最终PASS。Mandatory: yes。

## Validation plan / 验证

VP-01输入保护；VP-02 MEASURE.py按role连读两遍并留measurement_1/2.json；VP-03独立事实/分析schema检查（内容另人工审查）；VP-04六负向schema判别自测；VP-05编译MEASURE.py（不用py_compile写缓存）；VP-06保护复查。精确argv见VALIDATION_PLAN，Evaluator只用冻结role差异。

L2使用公共run_validation.py --mode executor，输出evidence/l2_executor_01，失败下一目录02，禁止覆盖。L3由Evaluator签收未变快照后--mode evaluator。VP-03不包含授权业务的自动正确性证明。

## Budget / 停止与费用

Executor<=120主动分钟、<=2正式L2，MEASURE.py每次两遍，全部L1/失败/正式运行合计<=8次测量数据集读取；Evaluator另<=4次。输入hash检查、CHECK独立重算和schema自测不是MEASURE尝试。建议L1一次（2遍）+L2一次（2遍），足够即停；不为了用满预算重复读取。

ATTEMPT_LEDGER记录active_work_minutes、measurement_passes（每次读取前追加evidence/executor/MEASUREMENT_ATTEMPTS.jsonl，失败也计）、formal_l2_attempts及work_intervals_utc=[{start,end}]；HTTP/payment/recovery/network/model/packages_installed/git_write_operations全0。总工时按闭合起止区间并如实区分等待，不用“onwards”代替结束。RESULT含task_id、classification与next_decision相同、measurement_only=true、business_recovery_executed=false、customer_demand=UNKNOWN。REPORT含来源/范围/变更、每AC、每VP、失败、预算、真实边界和L2证据索引。

发现输入漂移/未闭合状态、预算不足、需改商家或信任合同、需任何业务副作用/外部权限、无法只读、证据不充分则保留并停止交回Evaluator；不得靠编造事实过门禁。发现数据不足是允许的有效测量结果，不要求自动恢复候选。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY。已读开发映射。PCAC-12/18/20 CORE：本轮只测证据/补救边界，不升级实现成熟度；PCAC-07/09/10现有控制保持，08真实意愿未知。Contract=AC01–05；Test=六VP/只读复算/六负向自测；Evidence=固定原始材料+新测量/分析/L2/L3。before/after业务能力保持，本轮只增加独立可审查的就绪结论；不是监管合规证明。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
