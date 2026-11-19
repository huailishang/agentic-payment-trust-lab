# H74 Evaluator Review

Task ID: H74_DURABLE_AUTHORITY_CONTEXT_V1
Reviewed baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e

## Project context before review

目标是授权→执行前治理→支付→恢复→审计可独立复核。r125：A–D本地关闭、E受控本地代表闭合、F受控Stripe切片关闭；真实身份/凭据/签名信任源未知。B-22的三个原事实引用断点已有测量，优先于继续付款扩例；真实认证尚缺来源与授权条件。H74建设本地原上下文保存/冷载入/adapter消费；所有强制AC与原回归通过才关闭该代表切片，反例出现先最小修复。

## Pre-review checks

| Check | Result | Evidence |
| --- | --- | --- |
| 合同、地图r125、八项计划 | 通过 | 冻结20文件一致 |
| 提交资格 | 通过 | L2八项PASS，命令/AC/退出码与raw摘要独立重算 |
| 接受字节 | 通过 | 147任务文件、4源码/测试文件及冻结文件，ACCEPTED_SNAPSHOT |
| 历史/范围/权限 | 通过 | 2687保护项一致；仅允许源变更；外部动作0 |
| 成本完整性 | 不通过 | END早于SUBMISSION，报告/提交后续修改时间也晚于END；COST_EVIDENCE |

接受快照包含Task与Repo两个根下的原字节摘要。执行者原报告、账本、SUBMISSION和全部L2不修改。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/evidence/l3_review/gate_001/L3-GATE.json
- Validation plan: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE；唯一一次L3，八项全退出0，原19/9/74回归通过。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/evidence/l3_review/gate_001/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/evidence/l3_review/gate_001/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/evidence/l3_review/gate_001/RV-EV-01.stderr.log
- Observed result: 退出0；RV-EV-02至08同目录原编号三件套，AC与命令映射见L3-GATE.json。结构门禁PASS不替代下面的独立反例验收。

## Acceptance matrix

| AC | Decision | Executor EV | Independent RV-EV | Specific basis |
| --- | --- | --- | --- | --- |
| AC-01 | 通过 | EV-01/08 | RV-EV-01/08 | 输入/冻结/源码与提交摘要保持、仅允许范围、原生隔离与权限通过 |
| AC-02 | 不通过 | EV-03 | RV-EV-03及独立探针 | 正常冷进程原图保持，但同原ctx下一秒重存被拒；未注册同名枚举被静默转换，闭集类型/原图保真不成立 |
| AC-03 | 通过 | EV-04 | RV-EV-04及独立探针 | 自写fake client在callback内确认DB原件先存在；stored create/get/browser计数分别1/1/1 |
| AC-04 | 通过 | EV-05 | RV-EV-05及独立探针 | 缺引用/错引用/payload篡改/版本金额收款方资源/future/expired/revoked等冻结负例拒绝；拒绝未增加fake副作用 |
| AC-05 | 通过 | EV-04 | RV-EV-04及独立探针 | R01过期后仍只读原付款恢复，C01取消后零付款，D01仅一成功收据；无额外付款 |
| AC-06 | 通过 | EV-06 | RV-EV-06 | 原Stripe三模块19、安全9、业务74通过，旧断言保持 |
| AC-07 | 通过（限正常原生类型三单元） | EV-02/07 | RV-EV-02/07及独立冷进程 | 初始原src不支持API，实际新合成三单元有冷进程与fake消费证据；不升级旧历史。全部产品增量仍受AC-02失败约束 |
| AC-08 | 不通过 | EV-08 | RV-EV-08及独立成本审阅 | 窗口提前关闭，不能把20.825250分钟当覆盖报告/最终提交的完整上界；未证明超105分钟，需要追加保守收尾账 |

独立程序INDEPENDENT_PROBES.py仅复用旧固定输入工厂，不使用执行者的新测试断言或codec生成原图摘要；自己的typed graph包含枚举真实module/qualname。9组对照为7通过/2失败，结果见INDEPENDENT_PROBES.json。首次辅助脚本误用8765回调端口，按冻结原入口要求改为8768后重算；初次输出另存INITIAL_HELPER，非产品反例。正式L3只有一次。

## Findings

### F-01 / P2 — 同一原授权的正常重试被记录时间阻断

原GateContext、operation、resource完全相同，首次recorded_at=T，重试T+1秒且仍在所有有效期内：第一次与同T重复都成功，T+1秒抛authority_original_fact_immutable。原因是recorded_at参与payload/digest，existing分支直接比较新payload，而没有区分原授权事实与本次尝试的记账时刻。违反AC-02同事实幂等。应保留首次记录时刻和原引用，比较实际原事实；不能更新原时间或借重试续期。

### F-02 / P2 — 未注册同名Enum被当成白名单类型

构造独立Enum("PaymentStatus", {"PENDING": 原值})，置入ctx.execution.status。record_authority接受，load_authority把它还原成项目内置PaymentStatus；原类型已经改变。codec的_enum入口只查__name__，不像dataclass检查真实class身份；执行者原图摘要复用同一_encode，掩盖此类变化。违反闭集codec和AC-02原图保真。应按注册真实类型校验，外来同名类型必须在持久化前拒绝。未证明真实支付越权，不夸大为真实身份攻击。

### F-03 / P2 — 收尾在工作窗关闭之后

原账本END=06:19:48.363008Z，SUBMISSION自身声明06:19:49.279966Z，最少已有0.916958秒晚于END；RUN_CLOSE也在写END后生成COST_SUMMARY和SUBMISSION。接受时报告mtime=06:21:53.184423Z、SUBMISSION mtime=06:22:20.508806Z，支持后续收尾发生。mtime不是精确主动时长证据，但足以反对将原窗口声称为完整覆盖。实际主动时间仍UNKNOWN；这里不判定超预算。补列从旧END到首次Evaluator保守工作窗边界06:24:00Z的收尾上界，可与现有证据相容、避免角色重叠且仍远低于105；原账本/报告不回写。

## Final verdict

REJECTED

- Failed AC: AC-02, AC-08
- Specific fact: F-01/F-02原事实幂等与类型保真反例，F-03收尾成本缺口。
- Minimum repair task: H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1。
- Required rerun: 两条反例+原合法冷进程/双消费者/生命周期守护、原13测试及追加回归、原19/9/74；新修复任务独立L3。禁止重跑或追认原H74门禁。
- Missing human fact or authorization: NONE for bounded local repair；无新增外部权限。

## Project impact verdict

Impact verdict: INCONCLUSIVE

原生类型正常路径已有本地可运行增量证据，但强制AC-02/08未过，不能最终签收为IMPROVED。B-22仍第一瓶颈，未阶段关闭；A–F声明边界及原H72/H73结论保持。不是回退到只换环境，也不能把新接口支持直接当全部保真安全完成。

## Iteration value and continuation decision

Continuation decision: CONTINUE

下一包只修F-01/F-02并追加F-03成本说明，不扩新功能/来源/续授/认证。只允许ledger、codec与新增测试的最小改动，adapter和全部旧测试继续保护，原接受源码逐字节归档。两问题有定位明确、可复算的独立反例，先修比再测环境、付款或增加平台价值高。

新修复包另冻45执行/15评估分钟、1实现/1L2/1L3；原H74计数不重置，保留累计成本及150分钟主线限额。先将旧Executor按到06:24Z的25.019200分钟保守上界补账，实际UNKNOWN；本轮Evaluator最终数见COST/FINAL_RECEIPT，后继制包另列。若父评估+修复制包+未来评估触及累计45分钟、执行触及105或总150，即停止重评，不能自动续期。

## Bottleneck movement after review

B-22从“缺原事实持久化”推进到“正常存储/消费已接线，但幂等与类型保真仍有断点”。已有新增代码和运行证据，当前需要小范围修正原事实语义，不需要扩大支付环境。修复通过后再判断该本地代表切片是否关闭及下一真实来源资格测量；不预授权真实认证/生产网络。
