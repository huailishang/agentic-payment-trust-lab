# H61 批准记录的订单补救消费者接缝：只读可行性测量

Task ID: H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-04-r99
Active bottleneck: B-17
Hypothesis: NONE（只读接缝测量，不是新能力实验）

最终目标是高风险交易的授权、执行与恢复信任链。A–D 本地代表完成，E 本地边界，F 当前。H60R 已 PASS/NOT_APPLICABLE/STOP，原 H60 拒收不回写；人工批准登记已被有界接受，但没有实际业务消费者，原 M06 仍付款1/订单0。该消费者缺口比回到 H56 非标准支线更直接；比直接编码自动补单更少副作用。H59 已明确人工批准模式，不重新索要同一业务选择，不以真实PSP/客户缺失阻塞所有本地研究。

## Single objective / 唯一目标

一次性只读核查：已接受的批准记录是否能在原商城的订单侧恢复中被安全消费；定位重用边界、阻断点、一次性执行/幂等/撤销与崩溃一致性义务。交付一个有证据的下一实现候选，或明确不可直接接线的合同变更/停止结论。不是重复 H58 盘点缺失数据，也不再次证明登记器的固定24例。

固定源为 INPUTS 的批准库及其对应 M06 交易/假PSP快照，和十份固定文件（批准模块/父合同/已验收复核、原商城 checkout_service/execution_control/db/models/dependencies、H58复核、H59决策）。批准记录时钟只用于历史材料，不根据真实当前时间重新授予或执行权限。来源仅能通过 mode=ro&immutable=1 查询；不创建新批准、不调用候选/商家函数、不运行服务器。

## Allowed scope / 允许范围

只允许新增本包一个标准库只读提取器 EXTRACT.py，可写 ASSESSMENT.json、ANALYSIS.md、REPORT.md、ATTEMPT_LEDGER.json、RESULT.json 和 evidence/。合同、INPUTS、CHECK、RUN_AND_ACCOUNT、计划、入口冻结。父 H60/H60R、原商城38文件、SDK、src/tests、其他任务和旧证据全部只读。CURRENT 只能同任务 state/phase 更新，不能改权限/历史。

EXTRACT.py --out PATH 的唯一写入为给定的本任务 evidence/<role>/run_NNNN/EXTRACTION.json；不能写DB、复制后执行商家、调用 ApprovalInbox、导入冻结测试器代替提取或为业务对象补字段。sqlite3.connect 必须只读不可变模式，SQL 仅 SELECT。只能已有Python标准库，无依赖安装。

## Deliverables / 精确交付

EXTRACTION.json：schema=h61-source-extraction/v1，task_id 本包，files 精确包含 INPUTS.source_files 的每个相对路径及 sha256/line_count；databases 精确包含三库的 sha256/tables（逐表逐行 dict，按 rowid 顺序），business_execution_enabled=false。固定 CHECK 独立读原件逐值比对，不能用报告自报替代事实。

ASSESSMENT.json：schema=h61-consumer-assessment/v1，task_id；topics 包含下列十个 id，每项有 observed/impact/refs；每条 refs={path,start,end,excerpt} 必须回指 INPUTS 中文件的真实1起始行和完整原文切片，范围最多40行。事实、设计推断及 unknown 在自然语言中明确区分。

主题：approval_currentness、source_snapshot、payment_no_recharge、old_claim_semantics、order_transaction、inventory_revalidation、approval_consumption、restart_idempotency、revocation_serialization、notification_boundary。

options 精确三个 id：KEEP_QUERY_ONLY（现状基线）、REUSE_COMPLETE（重调旧完成入口）、ORDER_ONLY_RECOVERY（显式订单侧恢复）。每项有 classification=ABSORB/REFERENCE_ONLY/REJECT、reason/refs/proposed_files/safety_obligations。不能仅凭新批准就绕过旧 claim 防重扣，也不能整段拷贝商家业务再称适配。

结论 classification 只能 BOUNDED_CONSUMER_CANDIDATE / CONTRACT_CHANGE_REQUIRED / NO_SAFE_CONSUMER_SEAM；selected_option 必须对应上述选项，rationale 非空，business_execution_enabled=false。若选择可实施候选，需列唯一主要变更/最小允许文件/已有订单逻辑复用点/同事务一次性消费或明确跨库限制/撤销与提交先后/不重复charge及订单唯一性；若缺证据，则明确哪条义务未闭合，不因真实生产凭据未知泛化为本地绝不可行。

future_cases 精确8项，id为G01_NORMAL_ORDER_ONLY、G02_NO_RECHARGE、G03_REPLAY_SINGLE_ORDER、G04_REVOKED_APPROVAL、G05_CHANGED_SOURCE、G06_INVENTORY_SHORTAGE、G07_CRASH_AFTER_COMMIT、G08_CONCURRENT_CONSUMERS；每项 status=DESIGN_ONLY、input/expected/forbidden 非空。它们是未来验证设计，不得写成已执行成绩。ANALYSIS.md 解释选择、反证、复用/不复用及与不变更/最强备选的成本比较。

## Acceptance criteria

### AC-01 — 已接受能力与来源只读

Given 冻结原件/三库；When VP01/02/06及源码审查；Must observe 只新增一个只读提取器，父全部hash保持，零候选调用/HTTP/网络/付款/订单/库存/批准写入。Mandatory: yes。

### AC-02 — 精确来源提取

Given 十文件/三库；When VP03/04；Must observe 原始行表及hash完全匹配，唯一耐久调用预留、失败保留，重复角色提取相同；历史批准不得被描述成当前可执行权限。Mandatory: yes。

### AC-03 — 消费接缝与单一决策

Given 十主题/三机制/八未来设计；When VP04及Evaluator语义审查；Must observe 每个关键结论有原文回指，正确区分旧complete/claim/recover与订单事务及新批准消费的工程责任；只形成一个候选或明确STOP/合同变更，不实现补救。Mandatory: yes。

### AC-04 — 验证、成本与诚实边界

Given 六VP及损坏自测；When 完整L2/L3；Must observe 预算/原始流/失败完整、八项仅设计、结果无生产/真实身份/PSP/业务处置虚报，旧H60/H60R结论不变。Mandatory: yes。

## Validation plan / 验证计划

VP01来源/父保护；VP02单提取器标准库及只读审查；VP03带预留的一次提取；VP04精确原值、十主题/三机制/八设计、费用与结论；VP05六种损坏提取自测；VP06保护复查。精确 argv 与角色差异见 VALIDATION_PLAN.yaml；结构通过不能代替独立语义审查。准备仅核路径/hash、判别器和计划，不运行执行者提取器或形成测量结论。

## Budget / 有界预算

Executor <=120主动分钟、<=2正式L2、<=4提取器调用（含L1/失败/正式，调用前耐久预留）；Evaluator <=2独立提取器调用，完整L3默认一次，足够即停。本任务为新的只读测量预算，不借用或清零H60R的53/60评估额度。源码/材料阅读和CHECK的只读真实性核验不是提取器调用，仍计主动工时；不假称只读库查询次数为零。

ATTEMPT_LEDGER：extraction_attempts=executor预留行数<=4，formal_l2_attempts=l2_executor_*目录数<=2，active_work_minutes<=120、work_intervals_utc闭合；network_calls/http_requests/model_calls/packages_installed/git_write_operations/payment_calls/order_writes/inventory_writes/approval_writes全0。RESULT含task_id、classification与ASSESSMENT一致、remaining_gaps非空，business_execution_enabled/human_authentication_verified/provider_verified/production_ready/customer_value_proven全false。REPORT逐AC/VP/EV、原件/设计区别、费用/失败。

## Exclusions / 明确排除

不调用旧 complete/claim/recover/payment；不写三库、不造新批准、不解锁旧占用、不建补单/退款/消费实现，不复制并运行商城，不改SDK/核心/旧报告，不联网/安装/真实身份/密钥/客户接触/比赛/Git。静态检查发现可能需要真实运行时才判定，报告精确缺项，不擅自运行。

## Authorization / 授权

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## Stop conditions / 停止条件

任何来源写入/保护漂移、候选或商家函数被调用、新权限/依赖/预算、需改冻结语义即停并保留失败。完成一次完整来源提取和比较后必须形成候选/合同变更/STOP，不派第二份同类泛化研究。若仅能重复H58缺口，明确无新增信息并STOP；只有实际消费边界闭合才由Evaluator另冻实现，不自动补单。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/18/20 CORE/ADAPTER，适用批准消费、撤销与补救责任的只读接缝测量；before=批准登记本地M3/M4、消费者unknown；after=仅测量/设计证据，不升级产品成熟度。Test=六VP/原文回指/三库原值/未来八设计；Evidence=L2/L3/ANALYSIS。PCAC-08现实身份、真实PSP/生产并发/订单执行/客户价值仍unknown，不作监管合规结论。
