# H65R：只修结构化确认与字段单位的漏读

Task ID: H65R_STRUCTURED_CONSENT_UNIT_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 04d86b3c277e6f21f7a902a28ff0364df4b4941b
Validation plan file: docs/05_任务交接/H65R_STRUCTURED_CONSENT_UNIT_REPAIR_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-10-r107
Active bottleneck: B-18
Hypothesis: H-65R
Metric baseline: H65独立L3结构4/4，但源审阅发现4条arguments.consent直接确认与1项额度单位定义被遗漏，AC-02/03/04不通过，REJECTED（拒收）。
Estimated affected scope: 原六episode及H65已获输入；只修已定位的两类漏读。
Expected project impact: 恢复来源测量有效性，不新增产品安全成绩。
Rollback condition: 需新来源、运行时、依赖、签名/身份假设或扩大单位适用范围时保留未知并提交。
Expected material cost: 45主动分钟、8次完整episode读取、1版结果、2L2；其它外部/运行费用0。
Bounded retry / iteration budget: 同一修复内允许引用/格式纠正；不得第二分析策略、扩样或续开静态探索。

目标仍是交易信任链可独立复核。A–D本地关闭、E受控本地代表闭合、F当前。B-18优先于已关闭的H62、未找到新执行消费者的IronClaw和受授权限制的真实支付。已知直接反例应先修，不以新模块或测试数量代替可信测量。

## Single objective / 唯一目标

按原六例恢复结构化确认和字段单位的真实清点，撤销或更正H65因漏读形成的缺失声明，再给出一个有边界的去留结论。EXPECTED.json只锁定已知反例位置，不代替逐源引用，不预定最终必须继续或停止。

本包是H65拒收后的显式最小修复例外：原停止规则针对有效测量后仍缺证据，不适用于已经复现的漏提取。H65原件保持；修复不能成为第三轮开放式找证据。修复后即收束，不能因为仍未知而再开同六例的静态研究。

## Allowed scope / 允许范围

只写本任务ANALYZE.py、RESULT.json、ATTEMPT_LEDGER.json、REPORT.md、derived/和新evidence/；CURRENT只更新本任务执行状态/阶段。CONTRACT、CHECK、INPUTS、EXPECTED、计划和入口冻结只读。INPUTS锁定原49只读输入、H65完整提交/拒收/L2/L3及产品177文件；发布治理元数据不改变这些输入，不要求HEAD永远等于旧提交。

允许标准库及已有固定PyArrow解码器；只读原四Parquet、已获world、静态参考和原报告。不得运行H65/H64R分析器、产品、上游或旧全工作区checker。原金额/调用链可作比较输入，不作免读新字段的依据。禁止新GET、安装、模型、支付、回放、适配器、src/tests修改、联系他人或公开发布。

## Acceptance criteria

### AC-01 — 原件、来源和边界

Given INPUTS；When VP-01/04；Must observe冻结文件、全部只读/历史/产品摘要保持，缺原始输入明确INPUT_LIMIT（输入受限）；无新增网络/安装/模型/产品/上游回放/付款。原拒收及失败保留，不改旧门禁。Mandatory: yes。

### AC-02 — 四条结构化确认不能再被漏读

Given EXPECTED定位的四条shopper（用户角色）message（消息）；When VP-02及独立源审阅；Must observe同一行原文text与arguments.consent的引用、given、checkout_id、amount、currency和seq。绑定判定范围固定为published_episode_consent_record_to_checkout；须引用同episode原生checkout观察并比较值，不能跨episode借用重复编号。缺真实身份或签名不是该来源记录绑定的拒收理由，也不能据此声称真实人已认证。其余两例显式记录无该确认，不凭H65旧UNKNOWN代填。Mandatory: yes。

### AC-03 — 单位按具体字段、工具、调用适用

Given 第4例tools[8]的allowance.max_amount说明与原call-32/34；When VP-02及独立逐边复核；Must observe实际工具名、字段路径、单位定义及适用的原调用引用。把此字段写为已获直接定义，不得由final_cart单位或同额替代，也不能推广到所有response.total。call-32/34仍分开，call-68的4425/usd保留，token/额度签发不记作已付。逐例保留原金额和缺失维度；完整链须逐边引用“确认→checkout→该调用金额及单位→协议报告结果”，并写明结果类型。Mandatory: yes。

### AC-04 — 防假阴性、声明和有界决策

Given VP-03/04和账本；Must observe遗漏结构化确认、跨episode复用、遗漏额度单位、把额度当实付、无完整例却继续、伪称回放这六类损坏被拒。输出仅CONTINUE_TO_REPLAY_BASELINE/STOP_SOURCE_VIEW/INPUT_LIMIT；继续至少一例完整直接链，仍只建议另冻回放基线。停止必须承认已存在的确认/字段单位，不能重复H65错误。账本≤45主动分钟/8源读取/1版/2L2，所有实质尝试含起止时间及状态。Mandatory: yes。

## Output and validation / 输出与验证

RESULT结构由CHECK.py固定：samples依INPUTS.episode_ids顺序；每例consent_records、native_checkout_citations、field_units、binding、unit、complete_chain、chain_citations、protocol_result_kind；保留source_payment_observations、source_request_allowances并区分额度/实付；顶层classification=REFERENCE_ONLY、replay_executed=false、product_effect_measured=false及verdict。引用格式与H65一致，新增校验会比对原字段值；完整性仍由独立语义审阅决定，不能仅靠机器PASS。

四VP：source→analysis→guards→final。正式L2使用公共run_validation.py；提交时保持EXECUTING/Executor。Evaluator另作原源审阅和独立L3。package仅验证远端公开任务文件，不代表输入齐备；source通过后才开工。

## Authorization / Exclusions

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

以上约束Executor。Human既有统一推送授权仅供Evaluator按中央安全Hook发布本轮可公开治理文件，不转授执行者。原始数据/日志/环境保留本地；远端缺输入不能下载或改门禁。

## Stop conditions

预算任一上限、输入摘要不符、缺已锁定输入、需新来源/假设/运行时或权限即停对应工作并记录；足够修正两类漏读即提交，不消耗余额扩展。没有完整链则停止当前源视图；若修复尚有错误交回Evaluator，禁止自行续开研究或以付款/强身份标准变更AC。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；适用性=CORE/ADAPTER/EVIDENCE_ONLY沿原来源测量；对象=确认/单位修复合同；代码=本任务分析；Test=四VP/六损坏/独立源审阅；Evidence=新L2/L3；before/after产品成熟度不变，真实身份/清算/控制效果/合规unknown。
