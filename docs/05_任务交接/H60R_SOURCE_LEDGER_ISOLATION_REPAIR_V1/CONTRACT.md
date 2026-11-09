# H60R 来源与批准账本文件身份隔离修复

Task ID: H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-04-r98
Active bottleneck: B-17
Hypothesis: H-60（继承，非新增能力假设）
Measurement status: measured（父硬链接来源写入反例）；unknown（修复后的独立验收）。

目标仍是高风险交易信任链。A–D 本地代表、E 本地、F 当前；H59 人工批准方向已明确，H57R/H58 已验收。H60 未签收交付 REJECTED/INCONCLUSIVE：构造器允许新账本与交易/PSP 来源为同一文件的不同硬链接，并写入来源。该零容忍缺陷比未执行 H56 支线更优先，比真实身份/自动补单更有界。原 M06 付款 1/订单 0 不变，不以本修复声称业务处置闭环。

## Single objective / 唯一目标

在不改批准、撤销、读取、绑定或 CLI 业务语义的前提下，仅修复 ApprovalInbox.__init__，在任何可写 SQLite 连接/建表前拒绝来源与新账本的相同文件身份（包括路径别名和硬链接）。独立新账本的原二十条行为必须保持。一个产品主变更；验证夹具由本合同冻结，不交给 Executor 自改。

## Allowed scope / 允许范围

仅可改本包 APPROVAL_INBOX.py 的 ApprovalInbox.__init__ 函数体；除该方法外 AST 必须与父候选完全相同，包括导入。已有 os/Path 足够；不得改方法签名。必须在任何可能触及来源的写连接之前进行隔离检查，不能写后检查或只比较解析路径。不存在的新独立账本必须仍能创建；无法可靠确认已存在文件隔离时按失败关闭，业务拒绝用 ApprovalDenied.code。

可写本包 REPORT.md、RESULT.json、ATTEMPT_LEDGER.json、evidence/ 及 .task_envs/H60R/runs 下临时夹具/账本。父 H60 全部只读（含 REVIEW、全部失败、测试、报告、自重放和本轮独立证据），原商家/SDK/src/tests/其他任务不改。CURRENT 仅同任务 state/phase 可变，不能改权限或全局历史。合同、计划、INPUTS、CHECK、HARNESS、RUN_AND_ACCOUNT、PREPARATION、入口均冻结。

受信本地静止文件/配置边界保持；不引入动态文件替换/恶意管理员/生产文件系统竞争的新架构义务。不得据此声称已解决生产 TOCTOU 或跨库原子性。

## Frozen validation fidelity / 冻结验证修正

本新包合法采纳已由 Evaluator 源码与纯夹具复核的两个修正：源副本 SQL overlay 关闭连接后才记录摘要；C17 同步 subprocess.run 返回后启动下一 worker，三个 PID 与退出码保持，允许相邻单调时钟采样相等。原父 HARNESS/PLAN 不改、不追溯通过。

二十例原批准/撤销/过期/变源/上下文/旧确认/CLI/重启/竞争行为逐条保留；新增 R21 交易库硬链接、R22 PSP 硬链接、R23 同交易路径、R24 同 PSP 路径。新四例在隔离子进程构造候选，退出后必须业务拒绝且来源 hash/表集合不变；不只观察连接尚未关闭的主文件。硬链接仅测试准备层建立在一次性来源副本，候选无创建硬链接功能。

每例前耐久唯一预留；失败和原始子进程 stdout/stderr 保存，LATEST 仅完整成功后更新。修复代码未实施，父候选当前会在别名例失败；准备检查不得伪装为本包成绩。

## Acceptance criteria

### AC-01 — 最小范围与来源保护

Given 冻结父快照/原两库/单产品模块；When VP01/02/06/07 与源码审查；Must observe 父全部 hash 不变、仅构造函数体变化、无其他产品模块/依赖/外部副作用；候选写入仅独立新账本。Mandatory: yes。

### AC-02 — 文件身份隔离

Given R21–R24 的相同文件别名及 C01 独立新账本；When VP03/04 和独立复核；Must observe 四别名均在写连接前被 ApprovalDenied 拒绝，进程退出后来源 hash/表集合不变；C01 真批准并由 CLI 读取成功。不得只检查路径字符串或写后回滚。Mandatory: yes。

### AC-03 — 原二十条行为保持

Given 父固定 C01–C20 及合法修正夹具；When VP03/04；Must observe 原授权/绑定/幂等/撤销/变源/过期/上下文/真实重启/两连接竞争均通过，事件持久且 execution_enabled=false。不得自动补单/退款或将旧确认当新批准。Mandatory: yes。

### AC-04 — 完整证据与诚实预算

Given 24 例/七 VP/七损坏自测；When 完整正式 L2 后签收并独立 L3；Must observe 所有原始流、失败和预留完整，父 79 案例/两次修复版门禁/自重放 20 例/独立六例均不清零；REPORT 逐 AC/VP/EV 和原件边界清楚；不冒充真实身份/PSP/订单完成/生产/合规。Mandatory: yes。

## Validation plan / 验证计划

VP01 保护与原库；VP02 仅构造函数变化；VP03 完整二十四例；VP04 材料、预留、成本、结果；VP05 七种损坏证据拒绝；VP06 不落 pycache 的编译；VP07 保护复查。精确 argv/角色差异见 VALIDATION_PLAN.yaml。准备只能运行不调用候选的 baseline/scope/selftest/编译及计划解析；实际修复与 L2 属 Executor。

## Budget / 费用不可重置

继承 Executor 案例 79/160、保守工时 30 分钟；新包最多 72 案例（最多三波二十四例，含 L1/失败/正式），累计不超过 151/160。新 Executor 主动分钟最多 120，累计收费不超过 150，工作区间闭合；等待不算主动工时。

父原计划正式 L2=0 不代表没有费用：v2/v3 两次门禁全部计费，原两次已耗尽。本修复明确新分配最多两次正式 L2，父子门禁总数最多四；非原合同余额恢复。新门禁目录只能 l2_executor_01/_02，创建即计次，失败保留，不换目录逃预算。

父 self-replay（执行者自行重放）20 例加本次独立 6 例，保守占 Evaluator 26/60；新包最多 34，父子累计不超过 60，其中完整 L3 用 24，余最多 10 独立反例。Executor 不得再自行使用 evaluator 模式；Evaluator 只在正式签收后使用。已有充分证据即停。

ATTEMPT_LEDGER 必须含 inherited_executor_cases=79、case_attempts=本包 Executor 规范预留数、total_executor_cases=79+新数、inherited_gate_attempts=2、formal_l2_attempts=本包 l2_executor_* 目录数、total_gate_attempts=2+新数、inherited_evaluator_charge=26、active_work_minutes、charged_minutes_total=30+新工时、work_intervals_utc。http_requests/new_payment_calls/new_order_writes/recovery_calls/network_calls/model_calls/packages_installed/git_write_operations 均 0。固定负向夹具准备与候选实际副作用分开报告，不把父别名写来源事实改成零。

RESULT 必须 task_id 本包、classification=LOCAL_OPERATOR_APPROVAL_ONLY、remaining_gaps 非空；business_execution_enabled/human_authentication_verified/production_ready/provider_verified/customer_value_proven 全 false。

## Exclusions / 明确排除

不建设自动补单、退款、扣库存、重新扣款、旧 claim 解锁、批准消费、身份认证、密钥治理或通用审批平台；不调用 HTTP/ASGI/网络/Provider/模型，不安装依赖、不对外联系、不提交或推送 Git。不改父包、原商家、SDK、src/tests 或构造器以外产品方法。

## Authorization / 授权

四项授权全 false；本包仅允许冻结范围内本地修复与一次性测试副本写入。

## Stop conditions / 停止条件

保护漂移、需改构造器以外方法/合同/计划/权限/依赖、来源副本写入、假批准、重放复活、费用耗尽即保留失败返回 Evaluator。实现中已知父反例的首次验证失败可以在冻结范围/预算内修复；不得反复跑缺陷原样候选消耗预算。通过后 STOP 此登记器，不继续加字段/用例；批准消费、补单、退款、真实身份或实时数据竞争均另立合同。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/20 CORE，before=未接受 M2 候选、AC-01 失败；after=仅独立通过后才记本地有界 M3/M4。对象=原批准/事件合同；代码=单构造函数修复；Test=24例/七VP；Evidence=L2/L3、子进程原始流/来源摘要。PCAC-18 业务处置、PCAC-08 现实身份/意愿仍未覆盖；真实PSP、跨库原子性、商户/客户价值 unknown，不作监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
