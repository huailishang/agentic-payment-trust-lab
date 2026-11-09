<!-- Public display copy; original SHA-256: 687c5a990161276d79c7875a92a55a57715eaed67085e4cbe833f9b48ad56a64; only trailing whitespace/line endings normalized. -->

# H57R Executor Report — 商城验证账本与真实进程退出修复

Task ID: H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1
Task kind: repair
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: SUBMITTED_FOR_REVIEW
Executor handoff: COMPLETE; independent L3 must be performed by Evaluator
Git commit/push: NOT AUTHORIZED / NOT PERFORMED

## 全局位置与修复目标

A–D已有本地代表性可信支付能力，E只形成离线代表性闭环，F聚焦真实外部商城与Provider；第一瓶颈B-17是正常默认商家工厂接入后的可信交易链可验证性。父H57的六条本地业务观察可复算，但历史请求日志不规范，且M06父进程仍承载第一商城生命周期，父任务REJECTED / INCONCLUSIVE。本包只修复证据记录和首OS进程退出后的恢复实验，不能据此宣称真实商户或生产付款可用。

## 实施范围、来源和保护

- 仅修改本包HTTP_RUNTIME.py与RUN_JOURNEY.py；前者把新HTTP预约写到本包唯一HTTP_ATTEMPTS.jsonl，真实换行、请求前flush/fsync、ID加h57r-前缀、按role检验剩余额度。
- 后者添加独立M06 first worker/second worker与不承载商城的supervisor，等待第一worker彻底返回之后才启动第二worker；保存实际worker PID、Windows venv launcher PID、4个单调时间事件、exit code及原始stdout/stderr SHA-256；只读聚合持久SQLite与模拟PSP结果；自动更新正式L2中VP-03后的账本新请求数/已创建正式L2目录数，保留历史费用与所有失败目录。
- 原始38个merchant候选源、受保护基线、RUNTIME、CHECK、CASE_SPEC、VALIDATION_PLAN、父H57与历史57条账本均未修改。没有dependency_overrides、真网络、安装、真实密钥或支付、模型、Git操作。
- 父历史25条损坏原始预留及后续32条保留；它们不是本任务有效请求证据，但57请求全部继承计费。

## 执行过程及不隐藏的失败

- baseline、scope及冻结12条自测初始通过，HTTP=0。
- run_0001：首次M06首商城实际返回201/500，2条新HTTP预留；Windows虚拟环境启动器Popen.pid不同于真实Python工作进程os.getpid，原实现将启动器PID当工作PID导致断言失败。保留ERROR、进程流和2条计费，不冒充业务失败。
- run_0002：改成live worker PID handshake后单独M06成功，4条新HTTP预留；此为诊断波次，不冒充完整六场景。
- run_0003：完整六场景18请求，原冻结旧业务oracle的validate(observations)通过；本包独立materials executor本地运行成功，打印six journeys、18 requests、24 new reservations及first_process_exit_required=true。完整波次模拟付款M01=1、M06=1，M06独立模拟PSP查询1；所有其他拒绝零付款、零订单。
- M06真实监督PID与两工作PID彼此不同；启动器与工作PID分别记录；严格先first exited(0)后second started，并有first/second原始stdout、stderr、hash、exit 0，第二worker用相同持久DB查询到已成功付款，拒绝新键完成，没有二次扣款。本实验不保证断电级原子性，不自动补单。

## AC逐项执行者证据（非评估结论）

| AC | 执行者观测 | Evidence |
| --- | --- | --- |
| AC-01 | 只修改2个验证脚本，38个merchant只读，历史57全部计费 | EV-01 baseline / SOURCE_COPY / history |
| AC-02 | L1六条原生HTTP旅程18次观察符合旧oracle，签名与授权/库存/PSP绑定可独立复算 | EV-02 run_0003/observations.json及M01–M06.json |
| AC-03 | 监督者等待首OS worker实际退出后才启动第二worker，三PID、原始流、持久状态一致 | EV-03 run_0003/M06_processes.json + M06_first/second.stdout/stderr.log |
| AC-04 | 旧25+32保留，新请求有规范请求前预留及唯一ID，历史不洗白 | EV-04 HTTP_ATTEMPTS.jsonl / ATTEMPT_LEDGER.json / run_0001失败 |
| AC-05 | 原6计数+新6负向自测、25项AP2回归及正式L2 7/7均通过；L3仍待独立执行 | EV-05、EV-06与正式L2 Gate Summary |

## 验证计划（VP）记录

- EV-01 / VP-01：PASS；运行环境、1775保护文件、58冻结文件及历史57请求校验通过。
- EV-02 / VP-02：PASS；38商家文件只读、两验证脚本在授权范围内。
- EV-03 / VP-03：PASS；正式L2重新执行完整六例18请求，原生业务校验通过；产物run_0004。
- EV-04 / VP-04：PASS；签名、原生交易、规范账本、真实进程退出、RESULT、ATTEMPT_LEDGER全部检查成功。
- EV-05 / VP-05：PASS；原25项AP2回归全部通过。
- EV-06 / VP-06：PASS；原6计数及新6负向进程/账本自测全部通过。
- EV-07 / VP-07：PASS；最终保护基线复查通过。

## 计费、预算和授权

- 父H57旧预留57条（25原损坏+32后续），父正式L2=0，历史主动时间精确UNKNOWN并按冻结合同保守收费120分钟。
- 新H57R诊断失败2、单例4、完整L1波次18、正式L2波次18，共新增42次规范请求；加上继承历史57次合计99/160，剩余61。正式L2已用1/2，Evaluator独立HTTP预算仍0/80。所有失败请求保留并计费；正式L2采用run_0004（18请求）。
- 新工作从2026-11-02T12:34:32Z附近开始，保守计费30分钟（精确主动用时未单独计时）；连同历史120分钟共计150/240，符合本轮新增<=90分钟上限。该计费是保守额度而非精准工时。
- network/model/provider/real-payment/install/git-write均0；commit/push/history rewrite/API四授权仍false。

## PCAC外部要求与残余风险

external_requirement_impact profile=PCAC-AGENTPAY。PCAC-12/20关注日志及可复算证据；PCAC-18关注真正退出后查询不多付；PCAC-07/09既有本地授权控制不变，PCAC-08仅合成根，PCAC-10撤销不变。不能推断监管合规、真实人/代理人身份、真实支付Provider、CheckoutMandate标准互通或生产部署。H56为未执行安全支线。商业客户需求和真实部署责任UNKNOWN。

## L2摘要及下一交接

正式 L2 已完成：evidence/l2_executor_01，result=PASS，checks_total=7，mandatory_failures=0。该门禁固定七VP均返回exit=0，原始EV-01至EV-07 meta/stdout/stderr保存在对应目录；正式运行的LATEST=run_0004。执行者候选证据已齐，提请Evaluator核对未变快照，切READY_FOR_REVIEW后独立运行L3；Executor不自行签发最终PASS或执行Git commit/push。

## Workspace snapshot / 工作区快照

- 基线HEAD与origin/main：7831d232530c91825bb507a2a6d95b1de6a02c3b；HEAD未改变。
- CURRENT仍为EXECUTING / Executor，报告状态SUBMITTED_FOR_REVIEW；等待Evaluator验收文件快照后再切换READY_FOR_REVIEW / Evaluator。
- 改动文件 (Changed files)：本轮只修改CURRENT.md及本H57R下HTTP_RUNTIME.py、RUN_JOURNEY.py；本任务新增REPORT.md、RESULT.json、ATTEMPT_LEDGER.json和evidence。仓库原有其他未提交的无关文件全部保留，未暂存/提交/推送。
- 偏差与未解决项 (Deviations and unresolved items)：run_0001的2条请求已真实执行但首次PID断言错误，全部原始失败材料保留。Windows venv launcher PID不同于实际worker PID，修复后用工作进程live handshake确认其PID，supervisor顺序等待launcher/worker退出；L3需独立核查进程退出语义。真实Provider、商家部署、标准互通、客户需求仍UNKNOWN。

## Impact comparison / 影响对比

- Before: 父H57仅留下可复算本地六旅程，但首M06商城仍运行在监督进程、历史25条损坏预留及后32条不能作为本任务规范材料，正式L2为0，父包REJECTED。
- After: 本H57R原生商城完整六例经正式L2重跑，7/7检查PASS，新42条请求均前置预约；M06存在三个不同实际PID、严格退出后恢复、原始退出流可验。
- Delta: 从没有合格的真实进程退出+规范账本验收，推进为1套符合冻结判别器的正式L2证据包；没有把业务模拟交易误称为Provider真实支付或自动补单。
- Measurement evidence: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/L2-GATE.json；docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/executor/run_0004/observations.json；docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/executor/run_0004/M06_processes.json；docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/executor/HTTP_ATTEMPTS.jsonl
- Guardrail result: 1775个受保护文件、58个冻结文件和38商家候选hash保持；原25项AP2、原6个计数自测、新6个进程/日志负向自测通过；HTTP计数99/160、L2尝试1/2、收费工时150/240；无网络、Provider、生产款、Git副作用。
- Scope caveat: 仅本地ASGI真实路由、离线合成身份签名/公开profile、可持久假PSP与SQLite；进程退出模拟不是断电保障、订单自动恢复或外部协议/客户生产验证。

## L2 Task Gate / L2 任务门禁

- Executor status: SUBMITTED_FOR_REVIEW
- Gate result: PASS
- Gate summary: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/L2-GATE.json
- Validation plan: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/VALIDATION_PLAN.yaml
- Gate level: L2
- Checks total: 7
- Mandatory failures: 0
- Reviewer action: Evaluator核对候选快照，确认后独立执行L3；正式结论由Evaluator签发。

## EV-01 — 保护与环境
- AC: AC-01
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-01.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-01.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-01.stderr.log

## EV-02 — 范围和只读商城
- AC: AC-01
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-02.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-02.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-02.stderr.log

## EV-03 — 六个原生HTTP旅程
- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-03.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-03.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-03.stderr.log

## EV-04 — 日志及进程退出材料
- AC: AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-04.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-04.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-04.stderr.log

## EV-05 — AP2回归
- AC: AC-05
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-05.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-05.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-05.stderr.log

## EV-06 — 12条负向/计数自测
- AC: AC-05
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-06.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-06.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-06.stderr.log

## EV-07 — 最终基线保护
- AC: AC-01, AC-05
- Meta: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-07.meta.json
- Stdout: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-07.stdout.log
- Stderr: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01/EV-07.stderr.log
