# H71R独立复核：矩阵修复有效，整包仍拒收

Task ID: H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1
Reviewed baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Review date: 2026-11-13

## Project context before review / 全局位置

项目要闭合授权→绑定→执行/恢复→可消费审计的信任链。r116：A–D本地阶段关闭、E受控本地闭合、F当前。B-21先修外部测量可信性，再讨论下载/监听/支付；已关闭本地扩例与延期H67不优先。H71R是离线repair，验收标准包括矩阵/历史诚实性、整个采集失败链及公共门禁，不是仅让原11探针通过。

## Submission eligibility / 交接资格与格式修正

CURRENT已由Executor置READY_FOR_REVIEW，原报告缺少标准字段。Evaluator先保存原报告原字节及摘要到`evidence/l3_review/pre_accept/ORIGINAL_REPORT.md`和PRE_ACCEPT.json，再追加可核实的格式/证据索引，不删除原正文或修改现场事实。

补齐L2引用后，结构校验暴露真正的BLOCKING：两轮所谓完整L2由`evidence/run_l2.py`自建，未使用合同要求的公共run_validation.py/capture_evidence.py。摘要缺schema/mode/gate_level/plan/AC等字段，元数据缺label/command_argv/working_directory等必要字段；解释器也被该脚本改写。原日志的执行结果可以独立核查，但不能把自建门禁追认为公共门禁。

首轮只有FAILURE.md，无完整原始三件套；按预算保守计一次，不补造。第2/3轮12份自定义三件套的stdout/stderr大小、摘要和退出码已独立复算相符。这保留实际离线测试成果，不能修复交接协议不合格。

Evaluator在结构校验失败后仍捕获候选快照并执行独立复现，顺序不正确；因此名为ACCEPTED_SNAPSHOT.json的文件仅是67文件的**候选审计快照，不是合法接受交接**。澄清见SNAPSHOT_CLASSIFICATION.json。独立结果不追认缺失的L2，不转写旧元数据；候选文件与原账本字节前缀保持，见RETENTION.json。

## L3 Independent Gate / 独立复现结果

- Gate result: PASS
- Gate summary: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/L3-GATE.json
- Validation plan: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE。

公共runner在原生Windows独立执行冻结六项均0，包含11/11传输探针、9/9安全、74/74回归。这消除了Executor仅有WSL执行的宿主不确定性；由于L2交接不合格，本次只作为预算内独立诊断复现，不构成最终验收。没有网络、API、下载、浏览器、服务或付款。

## RV-EV-01

- AC: AC-01, AC-06
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-01.stderr.log

## RV-EV-02

- AC: AC-01, AC-02, AC-03
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-02.stderr.log

## RV-EV-03

- AC: AC-04, AC-05
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-03.stderr.log

## RV-EV-04

- AC: AC-05
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-04.stderr.log

## RV-EV-05

- AC: AC-05
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-05.stderr.log

## RV-EV-06

- AC: AC-06
- Meta: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/evidence/l3_review/gate/RV-EV-06.stderr.log

## Independent findings / 独立发现

### F-01 已完成的修复

三GET200、空/完整分页与金标摘要一致，最终矩阵已消费实测。两段来源引用确为原文正文，支持通用API权限与CLI转发语义，没有外推匿名key权限。历史下载阶段/状态/接收量仍UNKNOWN，归档0与接收0已分开，保证可用下载余额仍0。原H71/产品/旧测试与冻结输入保持。

### F-02 归档摘要失败仍使结果整体丢失

新采集原语在finally关闭流后，于异常处理之外重读目标文件计算SHA。如果正文已成功读取/保存3字节、原状态200，而此处rb打开抛PermissionError，函数直接向外抛异常，没有返回HTTP状态、观察量、归档量或失败阶段。独立临时文件故障已复现，见INDEPENDENT_BOUNDARIES.json的archive_digest_read_failure。

这是冻结合同“读/写失败保留状态、字节、失败阶段及异常类型”的遗漏，属于原AC-04；不是为了增加测试而新增业务要求。正文输出打开失败可正确返回BODY_WRITE/PermissionError，说明修复确有进展，但归档收尾仍未被统一保护。不能用已通过原11探针覆盖这一断点。

### F-03 输出归属的剩余风险

若目标文件预先有OLD_EVIDENCE而本次opener超时，函数返回observed=0但archived=12及旧文件摘要，未说明该文件不属于本次尝试。这个接口前置条件未在原驱动冻结，单独作为后续归属边界收紧，不另判一个原AC失败；应与收尾异常在同一最小修复包处理，避免多轮逐点修补。

### F-04 公共L2缺失

原L2“PASS”是自定义脚本的字段，并非合同要求的公共门禁；原始摘要/元数据不能被结构验证器接受。不得只补schema或改名把这些输出升级为公共证据。Python命令不可用时可在任务环境修正PATH或用已可用原生Python，不能以此为由自建另一套验证器。

## Acceptance matrix / 逐AC裁决

| AC | 裁决 | 独立依据 |
| --- | --- | --- |
| AC-01 | 通过 | 1596保护文件/11冻结输入核验，旧产品/证据保持；报告格式修正前原件另存，候选67文件保持。 |
| AC-02 | 通过 | 历史两个HTTP200、下载阶段/状态/接收量UNKNOWN与保守余额0准确保留，无23字节倒填。 |
| AC-03 | 通过 | 三GET实测已消费，两个正文引用逐字/来源摘要与支持关系均核实，未测能力继续保留。 |
| AC-04 | 不通过 | 归档后摘要读取异常从函数抛出，整份状态/字节结果丢失；F-02独立反例。 |
| AC-05 | 不通过 | 原11探针/9安全/74回归独立通过，但要求的公共L2未执行，不能统一签收；F-04。 |
| AC-06 | 通过（声明及可核范围） | 1实现/3次保守预算预留/1次独立复现，无外部动作；没有已证明超预算。公共门禁不合格另归AC-05。 |

## Final verdict

REJECTED

矩阵与原部分读取修复成果保留，整包不能签收。原自定义证据、格式修正原件、候选快照及诊断复现全部保留，不合成缺失的公共L2，不声称原H71已通过。

## Project impact verdict / 项目影响

Impact verdict: NOT_APPLICABLE

本包是repair，外部合格支付旅程仍0。不能从离线修复推导监听/Checkout写入/Stripe前端、主体认证或合规成熟度。原H68运行截止2026-11-13T00:59:06Z已经过期，不由本次复核恢复。

## Iteration value and continuation decision / 后续决策

Continuation decision: CONTINUE

Next task ID: H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1
Next task path: docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/CONTRACT.md
Next task state: CONTRACT_FROZEN / Executor

下一有界离线长包复用已正确的矩阵/历史投影，只修采集文件归属与收尾全生命周期，并使用原公共runner完成真实L2/结构验证。把输出准备、短写/flush、摘要/属性读取、关闭以及原11探针一次核完，避免每个文件异常单开一轮。它比继续对当前阶段已正确矩阵加字段、重开H67或直接下载更有价值。

## Bottleneck movement / 瓶颈变化

历史诚实性与矩阵消费已修好；B-21本地前提缩小为归档收尾可靠性与合法门禁。下一包不增加网络、下载或支付，不延长过期授权。修复与公共门禁都闭合后停止同类扩例，再具体核后续运行所需资源与授权。
