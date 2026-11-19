# H80R：回归输入与原生Windows门禁最小修复

Task ID: H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1
Task kind: repair
Workflow: evaluator-executor-workflow/v2.2
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-18-r136
Active bottleneck: B-23
Hypothesis: H-80
Parent: H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1
Dispatch mode: SINGLE
Validation plan file: docs/05_任务交接/H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

目标为授权→可信主体→交易治理→支付→恢复→审计。A–D本地阶段关闭，E的B-23归因修复待验收，F受控代表切片关闭、未来真实接入受授权约束。H79跨Agent错误VERIFIED（凭据已验证）独立成立；H80两轮L2均3/4，产品实现已有局部信号，但新增测试前提错误阻断必要回归。H80拒收且预算耗尽，未提交、未接受、L3=0；不追认旧失败或历史WSL式启动。

Metric baseline: 原新增6项为5通过1失败，错误输入实际INVALID/DECLARED（基础身份绑定无效）；Evaluator在内存隔离该前提后为VALID/BOUND（引用绑定有效）且凭据事实引用不符原因正确。原130与来源16/4正21负/8门禁在第二轮中未执行。
Hypothesis: 继承H-80，不增加产品机制。纠正唯一测试输入并在第一项测试前固定原生Windows导入环境，可以完成原合同完整验证。
Principal change: H80完整门禁的最小可执行修复；仅测试输入可变，启动环境在本包冻结，不准改产品以迎合测试。
Estimated affected scope: 一个测试方法的一项identity关键字；两个产品文件及原支付fixture按当前摘要锁定。
Expected project impact: 消除验收阻塞；全部独立验收成立后才考虑B-23本地代表消费切片闭合，E整体不升级。
Why first: 明确的非安全机制反例和独立输入对照，成本低于未测生命周期/第二平台；H78来源已代表闭合，不重开发行。
Rollback condition: 产品需改、新安全反例、冻结/父输入漂移或业务断言失败立即停止，不扩大此包。

## Single objective / 唯一目标

保全H80失败与当前未提交实现→登记一次测试修复→纠正输入→原生Windows完整L2→统一报告/封包→Evaluator接受不变快照后唯一独立离线L3。Evaluator本轮仅制包和复核，不执行产品/测试实现。

## Frozen behavior / 冻结行为

1. 唯一可改测试是tests/trusted_execution/test_credential_context_consumption.py中test_existing_credential_reference_precedence_is_preserved：在原self.consume调用中只追加identity=replace(self.identity, credential_ref="different-credential")。原current_credential_ref与证明均保持原值，所有原断言/其他方法/测试数量6不变。基础身份引用匹配、证明引用不符须为VALID/BOUND，且保留原凭据引用原因优先；不得削弱断言。
2. H80两个产品文件、原test_payment_binding.py及父证据按新基线当前字节锁定；原H80前字节别名也保护。不得以“继承改动”为由再改产品。
3. BOOTSTRAP与CHECK必须由现有Windows agent Python原生执行；非win32或非nt立即拒绝。启动器在第一测试之前设置子进程PYTHONPATH=仓库src、PYTHONDONTWRITEBYTECODE=1，并把同解释器目录置PATH首位。无需WSL、Bash、WSLENV、安装或全局配置更改。工具入口若仅能用WSL/Bash，停止并交Evaluator。
4. 复用H80原行为检查及全部回归，不改密码学检查、原十负例、同支付策略或失效/撤销守护。原证据仅按原observed时点重算，不是当前认证；ALLOW与本地列表callback不是实际付款。

## Acceptance criteria / 验收标准

### AC-01 范围、原样继承与历史

HEAD、H80全部原始证据/报告/冻结工具/REVIEW、H79/H78接受与失败材料、共享工具保持。治理旧路由/地图/交接有逐字快照及别名。两个产品和原支付fixture当前摘要不变，唯一新测试只允许上述一项关键字，其他AST（语法树）完全相同，仍6项，无skip/删断言。

### AC-02 正反行为完整保持

完整复跑H80原六槽M01–M06：原H78历史事实三字段等于签名上下文；M01为VALID/VERIFIED且callback1；三维不符为VALID/BOUND及context_mismatch；凭据引用不符保留ref_mismatch；revoked为INVALID/DECLARED且callback0。缺失/空白/旧鸭子对象、无证明、inactive、基础请求冲突、原十密码学负例上下文None、原status/四布尔/重放合成守护全部按原断言成立。保留精确输入/原因，不制造新实际来源。

### AC-03 必要回归与原生环境

原28、支付18、新增6项全部通过；随后原130及来源16、协议4正21负、8离线门禁全部通过，不能因为前面通过就跳后面。首项测试前已固定原生Windows环境，子进程全用同解释器，无WSL式中转；保留真实stdout/stderr和进程环境标记。原130包含原28的重复保护，数量不相加冒充独立覆盖。

### AC-04 完整提交及唯一独立验收

4项L2全部PASS后停止重跑；统一REPORT/SUBMISSION/EV原文/测试修复diff/源摘要/父失败和新增累计成本，结构校验通过。Evaluator先核不变快照并接受，后唯一离线L3，逐AC审阅；未提交/未接受不能运行正式L3。失败保留全部原文，不造PASS。

## Allowed scope / 允许范围

- tests/trusted_execution/test_credential_context_consumption.py，仅上述一项identity关键字。
- 本包REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl、ENVIRONMENT_RETRY.json（仅环境重试理由）、evidence/executor_*、evidence/l2与l2_retry_02、runtime及BOOTSTRAP生成标记。
- Executor只改CURRENT的执行状态/阶段/报告路由。Evaluator拥有ACCEPTED/REVIEW/L3与后续治理。

本包CONTRACT/PLAN/CHECK/BOOTSTRAP/SEAL/PREPARE/REPORT_TEMPLATE/SOURCE/BASELINE/FREEZE/READINESS/references只读。其它未提交工作保持，不暂存。

## Exclusions / 明确排除

无产品/支付政策改动，无新案例/断言放宽/父报告改写；无WSL/Bash工作负载、服务、私钥读取或生成、新凭据/签发、网络、下载、安装、外部API、浏览器、真实付款、提交/推送/历史重写。H78物理许可不继承；不证明任意调用者不能伪造进程内dataclass、当前实时有效性、用户强认证、真实轮换/撤销或监管合规。

## Steps and bounded branches / 有界执行包

原生PowerShell按EXECUTOR_README启动现有agent Python，先将CURRENT改EXECUTING，再BOOTSTRAP --mode implementation --attempt 1。只做上述一次测试修复，廉价目标L1最多1次。BOOTSTRAP --mode executor --attempt 1运行全部L2。

PASS→停止实现/重跑，报告→SEAL统一提交。纯导入启动故障且产品/测试字节与首轮L2相同→保全失败，写ENVIRONMENT_RETRY.json解释，仅允许一次attempt2同代码环境重试；第二次不登记implementation。启动器仅接受VP-03唯一失败、原始stderr含明确缺少agentic_payment_experiment导入且无新增测试业务失败，并要求人工归因保存在该JSON。业务断言/安全失败、保护漂移或产品需改→立即停止，不使用环境额度。第二次FAIL→停止交Evaluator，不自行续期。

## Validation plan / 验证计划

VP-01原样继承/测试AST/冻结/父保护→AC-01；VP-02完整原行为→AC-02；VP-03原28+18+6及130/16/4正21负/8门禁→AC-03；VP-04最终保护→AC-01/04。正式argv见VALIDATION_PLAN。CHECK的原行为和回归复用H80，新增的仅为精确测试范围检查与原生环境前置。独立L3使用同冻结命令，不能靠执行方自报代替。

## Cost and bounded budget / 预算

本地低成本。新包最多1实现、2正式L2（第二次仅同代码纯启动环境错误）、1独立L3、0发行；L1最多1次；顺序、并发1、成功即停。单回归子进程原240秒超时保持，无自设总体墙钟时限。H80已耗2实现/2L2/0L3保留；合计上界3实现/4L2/1L3，不把父失败移出账本。主动分钟UNKNOWN则明记；编排窗和工具调用单列，不推算主动时间/系统网络字节。

## Authorization / 授权

reference_read=true；api_call/install/download/local_service/existing_wsl/ephemeral_test_credentials/browser/test_payments/commit/push/history_rewrite全部false。仅本地可逆测试修复和原生Python验证，无缺失Human事实或外部权限；用户“再次复核”与仓库评估后制包规则足以制包，不自动执行产品修复。

## Stop conditions / 停止条件与下一步

范围/AC/假设/预算/权限变化、任一新零容忍反例、业务失败或漂移→停止交Evaluator。全部AC独立成立→才可关闭B-23本地代表消费切片、STOP同类扩例，再比较生命周期等下一缺口。否则保持INCONCLUSIVE（整体效果未定），不自动转外部身份/钱包/付款。

## External requirement impact / 外部指标

external_requirement_impact：profile=PCAC-AGENTPAY；PCAC-03/05/06/09/12/20，CORE为03/05/09/12，06为CORE/ADAPTER，20为CORE/EVIDENCE_ONLY。maturity_before=M2；maturity_after=待独立验收。对象/Contract为CredentialPossessionVerificationFact及消费晋级合同；代码继承H80两个产品文件；Test为本包冻结原行为与全部原回归；Evidence为H78公开历史/H79反例/H80失败审计及未来L2/L3。残余为进程内事实可信边界、历史非当前认证、未测生命周期/强用户身份/生产采用。历史启动未知不追认，无监管合规结论。
