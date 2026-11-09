<!-- Public display copy; original SHA-256: bc0748933cfff14d2f5e604fdd4f38913df51ba180ad72839b2509500fc9f8d7; only trailing whitespace/line endings normalized. -->

# H63R 执行报告：P1–P5 固定六例合同映射纠偏

Task ID: H63R_CONTRACT_MAPPING_REPAIR_V1
Task kind: repair
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: SUBMITTED_FOR_REVIEW
Authorization: commit=false, push=false, history_rewrite=false, api_call=false

## Global position / 全局位置

项目目标是把智能体支付中的用户授权、交易绑定、可信执行、异常恢复和审计做成可回放的信任链。地图 r101：A–D 本地阶段闭合，E 只有受控代表性结果，F 外部协议/独立交易证据仍是当前阶段。第一可执行测量缺口 B-18 是外部模拟轨迹能否支持原有合同的有效观察；H62 本地恢复已签收关闭，真实服务方 B-06 仍待授权。H63 因 AC-03 的 P1–P5 **语义误映射**被评估者 REJECTED，结构 L3 4/4 不代表语义通过。本包只修测量映射，不修产品，也不声称付款能力/合规性提升。

## Root cause and correction / 根因和纠偏

H63 把五个既有合同误当成通用购物步骤：P1 误用用户请求，P2 误用价格确认，P3 误用交易关联，P4 误用付款工具结果，P5 误用订单工具结果。本包只读取 H63 固定六例 `MEASUREMENT.json` 的七类已有事实，并按冻结 `SPEC.json` 和既有权威代码合同重新映射。没有重新运行 H63 EXTRACT/产品/支付服务，没有改原样本和原证据。

| 合同 | 原有权威语义 | 修后判定边界 |
| --- | --- | --- |
| P1 | `confirmation.py`，确认记录绑定授权版本、订单摘要与有效期 | 可见确认文字或checkout仅为PARTIAL；不能替代持久确认记录 |
| P2 | `payment_binding.py`，Authority→Order→Request→Execution 连续绑定 | 工具调用/checkout关联仅PARTIAL；缺mandate/版本/agent/payee绑定 |
| P3 | `execution_facts.py`，Agent/Executor身份保证 | 无执行者身份/凭据持有证明，一律MISSING；支付call id不算身份 |
| P4 | `context_policy.py`，可信来源×事实域写入策略、上下文完整性 | 消息role不能证明来源认证或上下文变更历史，一律MISSING |
| P5 | `replay.py`，RuntimeGateRecord与受治理证据链回放 | 模拟get_order/付款工具回复不是治理收据，一律MISSING |

映射原件：`MAP.py`（仅标准库、纯读取旧事实、生成新文件）、`MAPPING.json`（6×5=30）、`ATTEMPT_LEDGER.json`。30项中 **PARTIAL=8，MISSING=22，OBSERVABLE=0**。S01/S02/S03/S06在P1/P2仅有部分输入；S04/S05不提供足够的P1/P2有意义输入；P3–P5全部缺权威输入。每一项的 `contract_name`、`contract_ref`、`fact_keys`、`missing_inputs`、`reason` 均在MAPPING内，并保留全部SPEC必需缺失条件。

## Decision / 是否继续这六例

**STOP_PREVIEW_VIEW（停止扩大研究这六条预览）**，候选仍为 `REFERENCE_ONLY`、证据等级 `TRANSCRIPT_ONLY`。

S03/S06的checkout/call id/订单工具输出可在模拟文本内关联；这点H63已观察到。但两者均没有可独立认证的用户授权绑定、支付主体、真实付款方状态、可信来源策略及RuntimeGateRecord。继续比较相同六条已见模拟会话只能复述调用关系，不能独立判定本仓P1–P5实际控制有效性。未来有新且经许可、可核验的真实消费者/服务方证据时再单独由评估者判断是否转向新来源；**不由本报告启动下一任务或获得新的权限**。

六项原限制仍在 `MAPPING.decision.limits`：仅预览、非新鲜留出集、无独立后端状态、无已证实身份、无本仓控制测量、无客户价值证据。没有更改H63旧测量事实、H63 REJECTED裁决、原地图或H62验收。

## Validation and evidence / 验证与原始证据

- L1 快速检查：`CHECK.py source` PASS（受保护文件2898、冻结文件5）；`CHECK.py mapping` PASS（30条，仍需独立语义审查）；`CHECK.py selftest` PASS（4个原错误变异全部拒绝）。
- 正式 L2 尝试 1：退出码2，误从本仓 `scripts/run_validation.py` 启动不存在的入口；未生成Gate、未执行VP，不计为通过。保留 `evidence/L2_INVOCATION_FAILURE_01.md`，预算照扣。
- 正式 L2 尝试 2：使用 `../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py`，严格运行原冻结计划。**Gate PASS 3/3，mandatory_failures=0**。摘要：`evidence/l2_executor_02/L2-GATE.json`。
- EV-01（VP-01 / AC-01）：`evidence/l2_executor_02/EV-01.{meta.json,stdout.log,stderr.log}`；原保护材料保留、无新增越界文件。
- EV-02（VP-02 / AC-02,AC-03）：`evidence/l2_executor_02/EV-02.{meta.json,stdout.log,stderr.log}`；30条映射结构、来源与保守结论通过。
- EV-03（VP-03 / AC-03,AC-04）：`evidence/l2_executor_02/EV-03.{meta.json,stdout.log,stderr.log}`；四个语义回归变异被判定器拒绝。
- 原始事实与反例：`docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/MEASUREMENT.json` 和该任务 `REVIEW.md`。**正式L3尚未运行；L2/Checker不等于Evaluator语义签收。**

## Scope / Budget / Impact

新增本任务允许的MAP/MAPPING/LEDGER/REPORT/evidence；`CURRENT.md`仅由CONTRACT_FROZEN切换至EXECUTING/Executor。没有修改旧H63、H62、原产品src/tests、地图、SPEC、CHECK、冻结CONTRACT/VALIDATION_PLAN/BASELINE和源文件。原不相关脏工作区保留。

预算：映射版本 **1/2**；正式 L2 启动 **2/2**（含失败一次）；主动工时保守记 **30/60分钟**，包含准备、核查、生成和验证；本轮网络/模型/付款/安装/产品调用均 **0**，没有Git提交或推送。

Before：H63 结构可以通过，但P1–P5语义全部错位，测量有效性拒收。
After：30项按冻结合同重分级，全部缺少权威合同完整输入，最小负例门禁能够拒绝原典型错误。
Delta：**测量合同解释与维护证据修复**，非支付产品安全提升；真实身份、服务方、资金结果、客户采用和监管合规仍未知。

## Workspace snapshot / 工作区快照

Changed files / 改动文件：
- 本任务新生成：`MAP.py`、`MAPPING.json`、`ATTEMPT_LEDGER.json`、`REPORT.md`、`evidence/L2_INVOCATION_FAILURE_01.md` 与 `evidence/l2_executor_02/` 中的原始门禁流。
- `CURRENT.md`仅改变本任务的state/phase，保持EXECUTING/Executor。既有H63/H62/产品及被冻结的本包判别器、SPEC、计划与BASELINE不改；原未提交无关改动保留。

Deviations and unresolved items / 偏差与未解决项：
- 首次正式L2命令使用了不存在的本仓 `scripts/run_validation.py`，退出2并保留失败原始记录；第二次走相邻公共runner执行，原计划和所有VP未改变。
- 这里的PARTIAL表示只有零散源观察，而不是确认/绑定事实成立；Evaluator独立30映射语义审查及L3尚未执行。
- `STOP_PREVIEW_VIEW` 是执行者建议，非Evaluator签收；公开模拟轨迹不证明实际用户授权或PSP结果。

## Impact comparison / 影响对比

Measurement evidence: `MAPPING.json` 6×5全部30项、`ATTEMPT_LEDGER.json`、`evidence/l2_executor_02/L2-GATE.json` 及其EV-01..03原始流；根因反例为H63 `REVIEW.md`。
Before: H63 L3结构4/4但AC-03六例P1–P5含义误映射，评估者正式拒收。
After: 原冻结合同含义恢复；8项PARTIAL、22项MISSING、0项OBSERVABLE，判定器拒绝四个原型错误。
Delta: 改善测量语义有效性及回溯能力；没有产品安全能力增量。
Guardrail result: 正式L2第二次PASS 3/3、mandatory_failures=0；2898受保护文件、5冻结文件保持，网络/模型/付款/安装/产品调用0。
Scope caveat: 六条已见模拟轨迹，不是未见留出集或独立商家/PSP事实；产品控制效果、生产安全、商业价值、监管合规均未测量。

## L2 Task Gate / 正式执行者门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/L2-GATE.json
- Validation plan: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/VALIDATION_PLAN.yaml
- 正式L2尝试2/2；首次启动失败已计成本、未充PASS，第二次三项必选验证通过。独立L3 NOT_RUN。

## EV-01 — VP-01 保护与来源连续性

- AC: AC-01
- Meta: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-01.meta.json
- Stdout: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-01.stdout.log
- Stderr: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-01.stderr.log
- Observed result: 0 / PASS；protected=2898，frozen=5。

## EV-02 — VP-02 30项映射及保守决策

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-02.meta.json
- Stdout: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-02.stdout.log
- Stderr: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-02.stderr.log
- Observed result: 0 / PASS；30条结构有效，语义仍需独立审阅。

## EV-03 — VP-03 原错误变异拒绝

- AC: AC-03, AC-04
- Meta: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-03.meta.json
- Stdout: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-03.stdout.log
- Stderr: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/evidence/l2_executor_02/EV-03.stderr.log
- Observed result: 0 / PASS；四类误映射负例正确拒绝。

## Executor handoff / 执行者交接

**SUBMITTED_FOR_REVIEW / L2 PASS 3/3 / L3 NOT_RUN。** Evaluator应先冻结本次提交快照，独立查阅 `confirmation.py/payment_binding.py/execution_facts.py/context_policy.py/replay.py` 的合同语义，再对六例共30项逐一核验部分输入与缺失输入是否真实；独立运行L3并判断STOP_PREVIEW_VIEW是否合理。发现任何语义不一致应REJECT/退修，而非改判别器迁就结果。执行者不能宣布任务PASS；CURRENT继续保持EXECUTING/Executor，等待评估者接受与独立裁决。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20；只修测量语义；产品成熟度before/after均不变，资金/身份/真实服务方/监管合规unknown。
