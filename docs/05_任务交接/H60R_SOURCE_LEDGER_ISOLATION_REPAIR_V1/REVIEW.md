# H60R 评估者复核：来源文件身份隔离修复通过，停止扩展登记器

Task ID: H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1
Task kind: repair
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review date: 2026-11-04

## 全局位置

目标是证明高风险智能体支付的授权、执行、副作用与恢复证据链。地图 r98：A–D 本地代表完成、E 本地受控闭环、F 当前；B-17 仍是付款无订单后的处置责任链。本包只修父 H60 来源隔离的已实证零容忍缺陷，优先于未执行 H56 支线和需要更大权限的自动补单。父 H60 的 REJECTED/INCONCLUSIVE 不回写。

## Pre-review checks / 评估前检查

执行者提交正式 L2 7/7、24/24，状态 SUBMITTED_FOR_REVIEW。中央校验与冻结 baseline/scope 独立通过，七组 EV 的 14 份原始流逐一校验 hash/长度，24例引用的物理来源文件逐一核对。执行者 WSL /mnt/d 路径仅在评估者读取历史文件时映射到同一原生文件，不修改其元数据或报告。

`evidence/independent_review_20261104/ACCEPT.py` 在确认提交快照不变后，将 CURRENT 转 READY_FOR_REVIEW/Evaluator，再运行中央校验；之后按冻结计划在原生 Windows 发起正式 L3。109 个签收文件在 L3 和独立补充验证前后逐字节不变，2414 保护文件保持，详见 SUBMITTED_SNAPSHOT.json、ACCEPTANCE.json、POST_AUDIT.json。

源码差异仅在 ApprovalInbox.__init__ 增加已存在账本 stat/samefile 检查，发生 OSError 以业务拒绝失败关闭；检查在 mkdir、可写连接和建表之前。其他 AST 及构造函数签名与父一致，未新增导入或产品文件。候选检查不能阻止恶意管理员在检查后替换文件；该动态竞争已明确排除，不把本次结果外推到生产原子性。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/L3-GATE.json
- Validation plan: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/VALIDATION_PLAN.yaml
- Checks total: 7
- Mandatory failures: 0

正式独立门禁在原生 Windows 已有 Python 环境执行；固定24例完整通过，不安装依赖。执行者 WSL 与评估者 Windows 的逐例结果、批准行数、事件种类、别名拒绝码、执行开关和来源完整视图均一致。随机批准 ID、进程 PID 和物理路径不要求相同，不用这些不稳定标识伪造逐字节结果一致。

## Acceptance matrix / AC 逐条裁决

| AC | 裁决 | 独立证据与边界 |
|---|---|---|
| AC-01 最小范围/来源保护 | 通过 | RV-EV-01/02/06/07、构造器签名审查、109 签收文件及2414保护文件不变；只改构造函数，原两库保持 |
| AC-02 文件身份隔离 | 通过 | RV-EV-03/04 的四别名均在子进程构造期拒绝，退出后来源 hash/表集合不变；C01 新账本与 CLI 成功；另两身份查询故障检查均写前拒绝 |
| AC-03 原二十条行为 | 通过 | RV-EV-03/04，C01–C20 原授权、绑定、重放、撤销、失效、重启、竞争保持；L2/L3 来源视图逐值相同，始终 execution_enabled=false |
| AC-04 完整证据/预算 | 通过 | 七项正式L3、七损坏自测、28份L2/L3原始流核对、三独立补充检查、所有失败/历史费用保留；未声称真实身份/PSP/业务处置 |

## Independent counterexamples / 独立补充检查

POST_AUDIT.py 在每例调用候选前向 EXTRA_ATTEMPTS.jsonl 耐久预留，三例均通过：

1. X01 已存在且独立的批准库：重新构造可读同一批准，仍一事件，不误拒正常重启使用。
2. X02 账本文件 stat 检查不可用：测试层注入 PermissionError，候选转为 SOURCE_LEDGER_NOT_ISOLATED；账本和两来源 hash 不变。
3. X03 samefile 检查不可用：同样注入身份查询 OSError，业务拒绝且账本/来源不变。

故障注入只在独立测试进程的文件身份查询层进行，不修改候选文件、不替换业务判断或原固定测试。它证明已有合同的失败关闭分支，不代表模拟了真实主机权限体系。

## 费用与副作用

Executor 新24/72案例、1/2门禁、保守11/120分钟；继承后103/160案例、3/4门禁、41/150分钟。提交后的费用账本和 REPORT 不回写。

Evaluator 继承26（父自行重放20加独立6）+本次正式24+补充3=53/60；本新包使用27/34。没有清零父失败/诊断费用，剩余额度不用于继续堆登记器测试。来源原库未变，无新付款/订单/库存业务写入、HTTP、网络、Provider、模型、安装或 Git 写操作。父在一次性来源副本建表的失败事实仍保留。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

本包为 repair，不另包装成新能力实验的量化提升。已测得父文件别名隔离缺陷关闭，并在合法重冻结下首次完整接受这个本地批准登记切片；不倒改父 H60，不把它称为全项目安全或真实人身份保证。原 M06 仍付款1/订单0，批准执行消费没有实现，B-17 整体未关闭。

## Iteration value and continuation decision

Continuation decision: STOP

STOP 此构造器/登记器方向：代表性链路已闭合，继续加字段或别名用例的预期收益低于确认批准的实际消费者。下一有界任务 H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1 / one_off / measurement-only / CONTRACT_FROZEN / Executor；合同路径 docs/05_任务交接/H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1/CONTRACT.md。

H61 只读固定批准记录、原 M06 来源及现有 complete/claim/recover/订单事务代码，判断能否用原生业务形成不重复扣款的订单补救接缝；比较保持查询、重调旧 complete、显式订单侧恢复，形成一个可实施边界或有证据 STOP。它不能实现消费/解锁旧占用/补单/退款，不能重测 H58 的同一缺失输入或重新索要 H59 已解决的业务选择。它比回 H56 更贴近下一消费者，也比直接编码补单更能控制副作用。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/20 CORE，仅本地批准对象/隔离、撤销、事件与验证范围。before=父未接受M2候选；after=本地有界M3 TESTED/M4 EVIDENCED。对象=父批准合同和本修复合同；代码=APPROVAL_INBOX.py；Test=固定24例/七VP加独立3例；Evidence=L2/L3及POST_AUDIT。PCAC-18业务处置、PCAC-08现实人工身份与意愿仍未知；真实PSP/商户/客户/跨库原子性未覆盖，无监管合规结论。

## Final verdict

PASS

## RV-EV-01 — VP-01

- AC: AC-01
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-01.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-02 — VP-02

- AC: AC-01
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-02.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-03 — VP-03

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-03.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-04 — VP-04

- AC: AC-03, AC-04
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-04.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-05 — VP-05

- AC: AC-04
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-05.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-06 — VP-06

- AC: AC-01
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-06.stderr.log
- Observed result: PASS，exit_code=0。

## RV-EV-07 — VP-07

- AC: AC-01
- Meta: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l3_evaluator_01/RV-EV-07.stderr.log
- Observed result: PASS，exit_code=0。
