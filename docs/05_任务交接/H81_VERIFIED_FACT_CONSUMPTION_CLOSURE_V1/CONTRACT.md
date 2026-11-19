# H81：B-23 已验证身份事实消费闭环

Task ID: H81_VERIFIED_FACT_CONSUMPTION_CLOSURE_V1
Task kind: capability_experiment
Workflow: evaluator-executor-workflow/v2.2
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-18-r137
Active bottleneck: B-23
Hypothesis: H-81
Parent: H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1
Replaces unexecuted package: H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1
Dispatch mode: SINGLE
Validation plan file: docs/05_任务交接/H81_VERIFIED_FACT_CONSUMPTION_CLOSURE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

项目要证明授权→可信主体→交易治理→支付→恢复→审计可独立回放。A–D本地阶段关闭；E的来源代表切片闭合，但已验证事实可能被跨主体错误使用，B-23仍是最前端已证缺口；F受控外部切片关闭，未来真实接入受授权约束。

H79已独立证明：同一实际来源证明在跨Agent自洽消费场景仍被晋级VERIFIED（凭据已验证）。H80已经实现一个三元上下文传递/核对机制，但两次L2各3/4，完整回归和独立验收缺失，故REJECTED/INCONCLUSIVE（拒收/整体效果未定）。H80R有执行前原生入口阻塞报告，正式实现/L2/L3均0；旧报告保留。新增测试的小输入错误及启动问题属于本包前置修复，不再作为单独执行目标。

Metric baseline: H79原签收M01同上下文VERIFIED，M02跨Agent仍VERIFIED；原observed时点有效，无真实支付。H80原2实现/2L2失败、L3=0。修复前源码由H80的before_h80原字节别名锁定；修复后为当前继承的两产品文件，不是HEAD代表的源码。
Hypothesis: H-81
Falsifiable hypothesis: 在同一捕获证明/同一消费者输入上，继承H80的已验签Agent/Provider/Executor传递与精确消费核对，可将原M02错误晋级从1降为0，保持M01正对照，且三维错用、缺失/失效、密码学负例及原支付政策不退化。
Principal change: 沿用H80尚未签收的唯一产品变化——已验证三元上下文传递/消费核对。H81不叠加第二机制；测试输入纠错、原生启动、同输入前后对照、全量回归和证据汇总是该变化的一次完整验证包。
Estimated affected scope: 一个共享身份消费者、一个验证事实类型；本次新增可改实现仅一条回归测试输入；原支付门禁直接消费结果，不新增产品模块。
Expected project impact: 全部独立成立后关闭B-23本地代表消费切片，并停止同类扩例；不升级E整体，不把测试修好或报告完成计为能力提升。
Why first: 已有独立反例、可复算实际公开来源及实现；比未系统测量的轮换/撤销或第二平台有更高证据置信度和更低外部成本。H78同来源发行已足够，继续发行收益低。无须额外Skill讨论或外部调研。
Rollback condition: 修复后新错误晋级、失效仍有callback、来源/冻结漂移、必要回归失败且超出限定修复范围，立即停止，不扩大本包。父失败不追认。

## Single objective / 唯一目标

一包闭合“原始验签上下文→身份保证等级→既有支付治理结果→可独立对照的证据”。完成后只能给出有边界的闭合/未闭合结论；不以孤立测试修复代替项目瓶颈推进。

## Steps and dependency branches / 执行步骤与分支

| 步骤 | 依赖及工作 | 成功去向 | 失败处理 |
| --- | --- | --- | --- |
| S0 原样保全与前置修复 | 先核本会话原生PowerShell/现有Windows Python可用，保留H80R入口阻塞；核父摘要、登记实现；只纠正已知新测试输入；首测试前固定子进程导入环境 | 自动继续S1–S3，不单独交Human复核 | 仅Bash入口则在正式预算前停止；已知输入/导入问题可在本包剩余额度内修复；漂移或权限变化即停止 |
| S1 同输入前后对照 | 在独立子进程用锁定的原两产品源码重现H79 M01/M02；修复后使用当前源码跑原完整行为矩阵；来源/输入严格相同 | 自动继续S2 | 原基线不复现则证据资格失败；修复后仍有错误晋级或其他新零容忍反例立即停止 |
| S2 原必要回归 | 原28/18/新增6及原130、来源16、协议4正21负、8离线门禁；不skip/删断言 | 自动继续S3 | 已知一条测试前提或冷启动导入故障可用剩余一次有界修复；其他业务/安全失败停止，不改产品/旧测试 |
| S3 证据闭环和统一提交 | 核前后源码来源、同输入差异、原文三件套、回归结果、父失败与成本；形成CLOSURE.json和一次REPORT/SUBMISSION | 成功后停止重跑，交Evaluator | 只修报告/证据引用等不改变事实的格式；不靠重跑成功门禁补格式 |
| S4 独立验收 | Evaluator核不变提交后接受；唯一独立离线L3重做前后对照/原矩阵/全部回归/证据一致性 | 全AC通过才可关闭B-23代表切片，再比较下一瓶颈 | 不追认旧失败、不续跑L3；回Evaluator重新判断 |

## Frozen behavior and boundaries / 冻结行为与边界

1. 小修仅限tests/trusted_execution/test_credential_context_consumption.py的test_existing_credential_reference_precedence_is_preserved，在原self.consume调用追加identity=replace(self.identity, credential_ref="different-credential")。原证明仍credential-1、当前引用仍different-credential；基础身份绑定有效后才隔离证明引用不匹配。全部断言/其余方法/6项数量保持。
2. 两产品文件及原test_payment_binding.py按当前摘要锁定；旧两产品和原fixture按before_h80摘要锁定。仅在独立基线子进程的导入解析中指定旧两模块路径，禁止修改/回写工作树，禁止在同一进程混用两版枚举/事实；确认两个模块实际来源路径/摘要。既有其他模块与fixture保持原样。基线只重放原已证M01/M02，不扩充H79未测槽位。
3. 修复后完整原六槽M01–M06、缺失/空白/旧对象、无证明、inactive、基础主体冲突、十密码学负例及原status/四布尔/重放守护按H80原检查运行；不重复加新案例凑包。
4. 原BOUND/VERIFIED采用相同支付策略保持；身份无效/撤销仍阻止callback。原证明按原observed时点重算，不能充作当前认证；callback只是原测试本地列表追加，没有付款接口。
5. 原生PowerShell使用已有Windows agent Python；BOOTSTRAP/CHECK非win32或非nt拒绝，首测试前设置子进程PYTHONPATH=仓库src、PYTHONDONTWRITEBYTECODE=1和同解释器PATH。无Bash/WSL/WSLENV中转。历史H80启动祖先边界UNKNOWN（未知）保持，不追认为无偏差。

## Acceptance criteria / 验收标准

### AC-01 范围、兼容与原件

HEAD、继承两产品/原支付fixture、共享工具、H80/H79/H78证据及H80R原冻结/就绪文件摘要不变。治理原件有明确旧字节别名。唯一允许测试改动是一项identity关键字，其余AST（语法树）和断言相同。H80R确为0实现/0L2/0L3，SUPERSESSION说明其被Human此次指示替换，非技术拒收或已完成。

### AC-02 同输入可归因改善

实际离线运行锁定before_h80两源码，确认原来源VALID、M01与M02均VERIFIED；再用当前两源码跑原矩阵，M01仍VERIFIED，M02为BOUND且context_mismatch。前后source_run、observed、credential_ref、Agent/Provider/Executor、identity status、基础P2/P4有效和本地callback语义相同。记录两个模块来源路径/摘要，禁止从既有报告抄结果冒充本次运行。原跨Agent错误晋级计数1→0，正对照1→1；此差异不代表真实付款减少或当前身份验证。

### AC-03 完整消费安全边界

原六槽与三维错用/缺失/旧对象/无证明/失效/请求冲突/十密码学负例和合成晋级守护全部按原H80断言成立；三字段与原签名上下文一致。INVALID/MISSING事实不输出已验证上下文，缺失或不匹配只保留BOUND并给原原因；基础无效/撤销callback0。保留原始逐行精确输入、原因与门禁结果，不能用汇总替代。

### AC-04 原必要回归与环境

原28、支付18、新增6全部通过；原130与来源16/4正21负/8门禁全部实际执行通过，无skip/断言删除。原130包含前置重复保护，不把它们相加称独立覆盖。原生环境标记及原始输出完整，无新服务/发行/外部API/真实支付。

### AC-05 可独立消费的闭合证据

本包五项L2全PASS，CLOSURE.json能从本次原文重算AC-02改善和AC-03/04保持；源/模块/输入摘要及EV三件套长度/退出码一致。一次统一报告/提交，保留父2实现/2L2失败和本包增量，实际主动时间未知不估造。Evaluator接受不变快照后唯一L3五项独立通过，逐AC签收。L2/L3或CLOSURE.json自身不能自动宣布项目PASS，Evaluator另给产品影响与瓶颈决策。

## Allowed scope / 允许范围

- tests/trusted_execution/test_credential_context_consumption.py，仅上述一项identity关键字。
- 本包REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl、evidence/executor_*、evidence/l2或l2_retry_02、runtime及启动器生成标记；CURRENT仅执行阶段/状态/报告路由。
- Evaluator拥有ACCEPTED/REVIEW/独立L3/后续地图；Executor不能改本包CONTRACT/PLAN/CHECK/BEFORE/COMPARE/EVIDENCE/BOOTSTRAP/SEAL/PREPARE/SOURCE/BASELINE/BEFORE_LOCK/FREEZE/READINESS/SUPERSESSION/REPORT_TEMPLATE/references。

## Exclusions / 明确排除

无新增产品机制、支付策略/状态机/保证等级要求、凭据生命周期服务、信任根、新平台/新真实来源；无WSL/Bash、服务、私钥读写/新凭据、网络/下载/安装/API/浏览器/真实付款/提交推送/历史重写。进程内事实仍有可信调用者边界，不宣称防任意dataclass伪造、持久化篡改、实时撤销或组织/用户强认证。

## Validation plan / 验证计划

VP-01 CHECK preservation→AC-01；VP-02 COMPARE executor/evaluator（原基线2槽+修复后完整原矩阵）→AC-02/03；VP-03 CHECK regressions→AC-04；VP-04 CHECK preservation→AC-01；VP-05 EVIDENCE executor/evaluator（本次原文与闭合表）→AC-05。具体argv与独立evaluator_command见VALIDATION_PLAN。比较器原始stdout/stderr和CLOSURE.json附于正式EV，不引入第二工作流。

## Cost and bounded budget / 预算

低成本纯离线，基线仅两槽，不重新发行。新包最多2实现cycle/2正式L2/1独立L3，串行并发1；每cycle廉价目标L1最多1次，成功即停。第二cycle仅原同一测试前提/原生导入环境故障且不需改产品/冻结checker时可用，已知小修自动纳入，不逐步交Human。原回归子进程240秒上限保持，无自设总墙钟时限。

父H80已耗2实现/2L2/0L3，H80R0/0/0被替换，H81上限2/2/1；合计上界4实现/4L2/1L3。不得并行执行旧H80R或把本包视为旧失败额度自动续期。报告记录原始时间窗、尝试数和主动分钟UNKNOWN（如未独立计时），不推算系统网络字节/付费成本。

## Authorization / 授权

Human本次要求“这个小的错 可以放到下一执行包，新的包要围绕 项目瓶颈，继续整理”，授权将未执行H80R替换为本完整包并保全旧冻结，非授权实际执行、外部接入或权限升级。执行范围为后续本地可逆限定修复及离线验证；reference_read=true，其余提交/推送/历史重写/API/网络/安装/下载/WSL/服务/新凭据/浏览器/真实付款全部false。

## Stop conditions / 停止与下一步

修复后新错误晋级/失效仍执行、冻结/输入漂移、需要新产品变化、权限/范围/AC/预算变化即停止交Evaluator；原基线已证反例仅用于对照，不属于新副作用权限。普通已知测试/导入修复仅在本包限定额度内继续。

全部独立AC成立→可判IMPROVED（本地代表归因能力改善），关闭B-23该切片、STOP同类扩例；再比较真实生命周期的只读测量与其他最前端未知，不自动执行下一阶段。证据不足→INCONCLUSIVE（整体效果未定）；修复假设不成立或更高优先新反例→重新评估CONTINUE/STOP/SWITCH，不把测试错误包装成新能力。

## External requirement impact / 外部指标

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-03/05/06/09/12/20。03/05/09/12为CORE，06为CORE/ADAPTER，20为CORE/EVIDENCE_ONLY；仅身份事实消费窄对象。maturity_before=M2（实现未完整签收），maturity_after=待验收，仅原代表切片独立成立后才记录对应证据成熟度，不升级整个条款。对象/Contract=CredentialPossessionVerificationFact与身份消费晋级；代码=继承H80两产品文件；Test=同输入对照/原矩阵/全部原回归；Evidence=H78公开历史、H79反例、H80失败及本包未来L2/L3/CLOSURE。残余为历史非当前认证、可信进程对象、未测生命周期/强用户身份/生产采用；不作监管合规结论。
