<!-- Public display copy; original SHA-256: 61d3202987ca096ae5d1225fca7e0c7f96e06dc3be7db113ea7979eeb6d11b55; only trailing whitespace/line endings normalized. -->

# H60 本地人工批准的对账处置登记入口

Task ID: H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-02-r97
Active bottleneck: B-17
Hypothesis: H-60
Metric baseline: measured ABSENT：本仓没有连接已接受M06持久交易/PSP来源的人工处置批准登记器；0个此类批准。本包APPROVAL_INBOX.py尚不存在，无候选成绩。
Estimated affected scope: estimated，固定本地已付款无订单这一类边界，1个接受M06来源及20个保护/反例；不外推总体交易覆盖率或真实商户。
Expected project impact: 从只有查询/防重扣和分析，增加明确操作员批准、证据绑定、可撤销、可重启读取的本地登记能力；不改变付款/订单结果。
Rollback condition: 误接受越权/错绑/失效批准、重放复活、任意原业务来源写入、账本不可恢复或预算超限即停，保留失败候选，不接入付款或旧商城。
Measurement status: measured（H57R/H58来源及缺口）；unknown（新批准能力）；estimated（维护成本中等、受影响业务范围）。

A–D本地代表完成、E仅本地、F当前。H58已PASS/STOP，同一M01/M06无需重复提取。Human明确选择“先建立人工批准的对账处置入口（推荐）”，见H59/DECISION.md。这个选择解除本地权限模式待定，不等于授权自动补单/退款、真实资金或身份验证。比回H56披露支线更贴近实际付款无订单断点；比直接自动完成订单更少副作用，且无需先找真实客户/PSP。成功后STOP此登记器方向，另评批准的真实消费者；不无限加字段/Case。

## Single objective / 唯一目标与一个主要变更

只新建APPROVAL_INBOX.py一个标准库模块，提供本地操作员显式批准、撤销、读取及CLI入口；直接读取已接受M06交易库与独立假PSP收据的只读副本，将批准绑定到原交易和当时证据。只有新批准账本可写。新能力是处置批准登记，不是订单完成或真实人认证。

采用本地可信进程配置模拟有权操作员；角色和身份由启动配置注入，不能由批准请求中的approved=true/operator_id代替。成熟度明确LOCAL_OPERATOR_ASSUMED（假设本地操作员可信），不是human_authentication_verified。私钥、普通签名、链均非最小必要机制，本轮不用。

## Public API / 冻结接口

APPROVAL_INBOX.py定义：
- ApprovalDenied(Exception)，有非空str属性code；业务拒绝不能泄漏为裸SQL异常。
- ApprovalInbox(*, transactions_path, psp_path, ledger_path, operator_context, now)。now是可信启动层注入的整数时钟函数；source两库只读，ledger单独SQLite，不得与任一source解析为相同路径。不得向原库建表或使用可写source连接。
- inspect(checkout_id)返回eligible、source_digest、checkout_id、payment_ref、execution_enabled=false。
- approve(request)、revoke(request)、show(approval_id)同步方法，返回下述读取结构。构造器允许失效上下文以读取“为何批准失效”；任何新批准/撤销都必须校验上下文。
- CLI：python -B APPROVAL_INBOX.py --transactions PATH --psp PATH --ledger PATH --operator-config JSON_FILE --now INT inspect|approve|revoke|show；从stdin读单个JSON。inspect body={checkout_id}、show body={approval_id}，其余为请求。成功stdout只输出结果JSON；业务拒绝JSON含error=code并exit=2，成功exit=0；上下文文件只属于可信启动配置，不能通过业务请求覆盖。无服务端、浏览器或端口。

固定操作员配置示例：{operator_id:"local-reviewer-01",active:true,roles:["RECONCILIATION_APPROVER"],policy_version:"h60-local-v1"}。审批请求没有operator_id/roles/approved等字段；发现未知字段直接拒绝。身份/角色/配置文件的真实性来自本地受信进程边界，未验证现实操作员身份。

approve请求字段恰为request_key、checkout_id、payment_ref、expected_source_digest、disposition、reason、expires_at；disposition仅ORDER_COMPLETION。该字段记录人工对原交易订单完成方向的处置意向，执行连接始终关闭；不是可用于旧complete付款接口的令牌。字符串非空，reason限1–500字符，expires_at必须为整数且now < expires_at <= now+600。不接受bool当整数、退款动作、任意扩权限字段。

revoke请求恰为approval_id、request_key、reason；只允许原批准的同操作员以当前有效上下文撤销。即使来源已变化仍可撤销，不能要求来源有效才能撤回。撤销不改变原付款/确认记录。

独立批准库至少有approvals、approval_events两张表，分别保存批准记录与只追加有效事件；额外幂等索引/表允许。冻结检验器直接读取两表，拒绝请求必须保持零批准/零事件，不能先写后抛异常假装拒绝。同一批准/撤销重复不得多行。字段内部布局由执行者选择，公开读取结构必须完整。

读取结构：
{record:{approval_id,request_key,checkout_id,payment_ref,source_digest,context_digest,operator_id,policy_version,disposition,reason,expires_at},events:[{seq,kind,approval_id,operator_id,source_digest,at,...}],current:bool,effective_state:str,execution_enabled:false}。
批准/撤销原始请求及其身份/绑定事实须持久可审计；额外字段允许但不得含完整旧授权token、私钥或虚构真实身份。events序号按单批准1递增，kind为APPROVED、REVOKED，at为可信时钟整数。状态投影可变，原有效事件不得覆盖。历史批准不是一次性执行凭证，不声称已实现consume（执行消费）或密码学不可抵赖。

## Source binding / 真实来源与有效性

源是INPUTS固定的H57R正式L3 M06交易库及独立假PSP库。HARNESS为每例复制到.task_envs/H60/runs下，负例只在这些一次性测试副本上叠加SQL变化。旧H57R/H58及原库全部只读。原M01只作历史背景，不重跑商城。

source_view精确字段/排序见冻结HARNESS.source_view：
- 原checkout整行（data保留数据库原始JSON字符串）；
- checkout_id对应h50_attempts、h53_authorizations、由其confirmation_ref找到的h50_confirmations整行；
- payment_ref对应PSP receipts行或None；
- inventory全部行按product_id排序，orders全部行按id排序。
对这个对象使用UTF-8、ensure_ascii=false、sort_keys=true、separators=(",",":")、allow_nan=false编码，再SHA-256得到source_digest。这里是当前单交易固定来源的保守绑定，不声称多商户通用最小依赖；JSON原文空白变化也会保守失效。
context_digest用相同公式覆盖完整注入operator_context。摘要只是变化检测，不是数字签名或现实身份保证。

批准必须自己读源并核对请求的expected_source_digest，不能信任请求内自报PSP成功/金额/身份；候选不得导入HARNESS/CHECK来生成事实。至少要求：
1. checkout身份与attempt/确认/授权记录一致；状态ready_for_complete、attempt IN_FLIGHT，当前单交易库无订单行。
2. 付款引用与请求一致，PSP receipt存在且snapshot_json与冻结attempt/confirmation快照语义一致；checkout中的id、currency、line_items、totals、fulfillment与付款快照一致，merchant/payee非空。
3. 持久授权摘要记录decision=ALLOW且confirmation_ref/checkout_id绑定一致，原确认未撤销。原确认过期只作为历史事实；这里是新人工批准，不能将付款后旧确认过期等同于禁止任何新处置，C19须能新批准。本轮不重验旧token，也不声称旧摘要证明了新批准。
4. 当前操作员active=true、有固定角色、非空id和policy_version；请求目标不越过这组显式配置。

源均为静止、已关闭的SQLite副本，读取mode=ro&immutable=1，活动WAL/缺源/损坏即拒绝。新账本的写事务须原子保护幂等、唯一活跃批准及事件；两连接竞争最多一条活跃批准。此处不声称跨实时交易库/PSP的分布式原子性、生产撤销或TOCTOU已解决。

## Lifecycle / 幂等、撤销与失效

同操作员同request_key同完整批准请求重放：返回同approval_id、同原记录，不新增事件、不延长有效期。相同key改内容拒绝。撤销后重放旧批准只读返回REVOKED，不复活。不同key试图为同checkout_id/payment_ref再建活跃批准拒绝；失效/撤销后的重新签发不在本轮必做范围，不为测试自由扩新状态机。

show动态判断：
- 有撤销事件：APPROVAL_REVOKED。
- 当前上下文摘要不符或失去身份/角色/active：APPROVAL_STALE_CONTEXT。
- now >= expires_at：APPROVAL_EXPIRED。
- 当前来源不再可读/合格，或source_digest变化：APPROVAL_STALE_SOURCE。
- 全部成立：APPROVAL_CURRENT，current=true。
其他状态current=false；execution_enabled始终false。只读show不为“失效观察”追加事件。
同key同撤销请求重放保持两事件；冲突撤销key拒绝。不得通过重新构造对象、重启或请求approved=true绕过失效。只有批准/撤销的有效状态变化必须持久留痕；拒绝请求不要求额外持久事件，不声称完整生产审计链。

## Allowed scope / 允许范围

产品变更仅本包APPROVAL_INBOX.py；可写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json和evidence/。HARNESS.py、CHECK.py、PREPARE.py、INPUTS、合同/计划/入口和CASE_SPEC冻结。
可在.task_envs/H60/runs写新批准账本、候选CLI配置及一次性源副本；只允许冻结HARNESS对源副本执行列明的负向overlay，候选任何源写入都禁止。C11夹具插入假订单行仅用于“已有单必须拒绝”的输入，不是候选业务写入；new_order_writes等0副作用计数指候选，不隐去夹具变化，原始overlay由固定源码与case输入/结果留存。不得修改src/tests、旧商家38文件、旧报告/证据、SDK、根词汇或地图。CURRENT只可改同任务执行状态/phase，权限不变。

## Exclusions / 明确排除

不实现/触发补单、扣库存、退款、重新扣款、解锁旧claim、调用旧recover或改变h50/h53记录；不得将批准注入旧complete接口。无HTTP/ASGI、监听、DNS/外网/Provider/模型/安装/外部联系/Git操作。仅已有Python标准库；不创建通用审批平台、生产身份认证、密钥治理、自动补单状态机、UI或区块链。

## Acceptance criteria

### AC-01 — 来源/旧能力只读
Given冻结两库/全仓保护；When VP01/02/07及源码审查；Must observe旧源码与证据hash不变、仅一个新产品模块，候选只写独立批准库、无新付款/订单/库存/原表变更。Mandatory: yes。

### AC-02 — 显式人工批准与原交易绑定
Given原M06及C01/C04–C11/C19/C20；When VP03/04及源码审查；Must observe有权本地配置+实际原交易/收据/预期摘要才能批准，CLI直接读取新账本；身份不来自请求，原过期确认不被伪装成新授权，错误目标/无收据/错快照/已有单/退款均拒绝。Mandatory: yes。

### AC-03 — 幂等、失效与撤销
GivenC02/C03/C12–C16；When VP03/04；Must observe重放不增事件或延寿、冲突拒绝、变源/过期/失去上下文失效、撤销可持久且不被旧请求复活，全部execution_enabled=false。Mandatory: yes。

### AC-04 — 重启、竞争与可归责事件
GivenC17/C18；When VP03/04；Must observe首子进程退出后新进程仅凭持久库+独立启动配置可读同批准，无内存批准交接；两连接竞争恰一活跃批准；有效批准/撤销事件绑定actor/交易/摘要/时间，旧事件保留。不得宣称强认证/已消费/业务闭环。Mandatory: yes。

### AC-05 — 完整验证与诚实边界
Given固定20例/七VP；When正式L2/L3；Must observe全部通过、原始失败和case预留保留、6损坏判别自测拒绝、预算/工时区间完整、结果只称本地批准登记，真实身份/PSP/客户/生产与业务执行均false。Mandatory: yes。

## Validation plan / 验证与交付

七VP精确argv见VALIDATION_PLAN.yaml：VP01来源与保护；VP02单模块标准库范围；VP03固定20例含CLI/新进程/两连接；VP04材料/预算/结果；VP05六损坏自测；VP06候选编译不写缓存；VP07保护复查。Evaluator仅使用冻结role差异；固定命令不替代源码独立检查与任务裁决。

每次HARNESS写新run_NNNN，CASE_ATTEMPTS.jsonl每case之前唯一耐久预留；错误原始流保留，不覆盖失败目录。C01 CLI及C17两个worker原始stdout/stderr保存在该例独立scratch，case结果指向路径；完整正式结果保存evidence/<role>/run/results.json，LATEST仅成功整包。不以自造观察替换实际方法返回/数据库。

ATTEMPT_LEDGER：case_attempts为executor规范预留总行数，formal_l2_attempts为l2_executor_*目录数，active_work_minutes与work_intervals_utc闭合起止；http_requests/new_payment_calls/new_order_writes/recovery_calls/network_calls/model_calls/packages_installed/git_write_operations全0。初次运行前执行者建立成本账本，记已实际使用值；冻结RUN_AND_ACCOUNT.py在每次运行结束或失败后准确同步预留和正式门禁目录数，候选模块不承担费用记账。

RESULT：task_id本包、classification=LOCAL_OPERATOR_APPROVAL_ONLY、remaining_gaps非空；business_execution_enabled/human_authentication_verified/production_ready/provider_verified/customer_value_proven均false。REPORT逐AC/VP/所有EV/失败、原M06来源、合成人工身份与候选影响对比；任务通过不是原付款/订单问题已解决。

## Budget / 有界预算

Executor<=240主动分钟、<=2正式L2、总case预留<=160（20例最多8波，失败/L1/正式均计）；Evaluator另<=60。仅临时本地两worker/两线程属于冻结测试，不开常驻后台服务。已有充分证据即停，不用完预算再报。下一轮不沿用H58/H57剩余额度。新增单模块维护成本estimated中等；资金/API/模型成本0，最大机会成本为四小时本地实现与独立审查。

## Stop conditions / 停止条件

任何保护漂移、候选写来源、错误批准/重放复活、需要新产品文件/权限/依赖或改AC/计划、预算耗尽、无法保持新旧账本分离，立即保留失败停回Evaluator。合同内可修但不改主要变更/预算。成功后停止继续加登记器字段/Case，按是否有真实执行消费者再决定下一包；若一轮无净收益，不自动转通用身份或自动补单。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；已核对开发映射。PCAC-07/09 CORE：本地特定处置批准对象/绑定由M0目标M2/M3，只有独立证据后才记有界M4；PCAC-10 CORE：仅新批准自身撤销，不升级全项目撤销；PCAC-12/20 CORE：持久事件/评估证据；PCAC-18仅准备，未完成业务处置；PCAC-08真实人工身份/意愿仍unknown。Contract=AC01–05；代码=单模块；Test=20例/七VP/六负向自测；Evidence=真实SQLite读写、CLI、新进程/并发/L2/L3；残余真实身份/PSP/跨库竞争/订单执行/生产客户未覆盖，不作监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
