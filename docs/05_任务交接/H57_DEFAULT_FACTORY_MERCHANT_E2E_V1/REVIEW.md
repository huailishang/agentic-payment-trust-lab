# H57 复核：商城接线有进展，交付不通过；日志及进程退出证明需修复

Task ID: H57_DEFAULT_FACTORY_MERCHANT_E2E_V1
Task kind: capability_experiment
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review boundary: PRE_ACCEPTANCE / NOT_SUBMITTED; no accepted snapshot or L3 rerun

## 全局位置

目标仍是外部商城正常交易及异常时不越权、不多付。A–D已有本地代表成果，E仅本地，F当前。B-17优先于H56字段支线及延期的支付宝/比赛：H57默认工厂接线已形成候选和本地业务观测，下一步是使这条商城链可独立复核，而不是增加协议功能。

## Pre-review checks / 评估前检查

Executor主动说明未提交正式验收，未伪造L2。CURRENT仍CONTRACT_FROZEN/Executor且phase未更新，和实际已实施状态不一致；本次按未签收交付检查，不当作正式L3。独立审计见 `evidence/preacceptance/AUDIT.py`、`AUDIT.json` 及 `H57-PREACCEPT-01.meta.json`/stdout.log/stderr.log。

审计独立执行旧baseline/scope、重新验证已保存六例及18次HTTP观察的原始CASE文件和后续预留映射。1680保护、52冻结、其余36商家源和签名/路由/原生工厂范围检查通过；复算不是新跑商城，也不算独立HTTP成绩。新HTTP请求0、正式L2目录0、L3未运行。RESULT与ATTEMPT_LEDGER均缺失。

## Acceptance matrix / AC 逐条裁决

| AC | 本次判定 | 独立证据及限制 |
|---|---|---|
| AC-01 | 来源/范围局部通过，正式整体验收未到位 | 默认工厂仅增加app.state控制注入，guarded_app保留原生生命周期，36源未改；尚无正式L2/L3 |
| AC-02 | 已存材料语义复算通过，尚未最终通过 | M01完成/重放/查询、1模拟付款/1单/库存4及真实签名材料可复算；没有独立新HTTP复跑 |
| AC-03 | 已存材料语义复算通过，尚未最终通过 | M02–M05拒绝及零副作用记录一致；同上 |
| AC-04 | 不通过 | RUN_JOURNEY.py run_case先在自身PID运行NativeProbe，再于第211行同步subprocess.run启动恢复进程；父进程必须活着等待子进程并拼接结果。仅关闭应用lifespan，不满足合同“真正退出该应用进程”。不同PID本身不足以证明原进程已退出。付款总1等材料不被否认，但不能升级为真实退出恢复证明 |
| AC-05 | 不通过 | 原HTTP_ATTEMPTS有25个对象、0真实换行、2个ID，其中h57-2重复24次；materials实际抛JSONDecodeError；正式L2、RESULT、预算账本缺失 |

旧CHECK.validate只检查两个不同PID，没有检查第一个PID已退出，属于本轮判别器对合同AC-04约束不足；不能因为旧校验通过就验收。这里没有发现商城重复付款，也没有把测量脚本错误当作支付业务漏洞。

## L3 Independent Gate / L3 独立复核门禁

未启动：Executor没有完整L2/提交，不能签收快照或把本次只读审计伪装L3。当前交付门禁不通过，保持全部原始失败材料；不伪造L3-GATE文件。

## Project impact verdict / 项目影响裁决

Impact verdict: INCONCLUSIVE

原生默认工厂接线已由源码及18请求材料获得本地进展；完整恢复/成本与正式独立验证仍未闭合，不能声称项目能力已验收提升。历史57请求（损坏25+后续32）全部计费，不改旧wire ID、不清零预算。后续32条中失败run_0001为14、成功run_0002为18，逐字节保留。假付款只是本地模拟；真实身份、商户部署、标准互通、PSP和客户价值仍unknown。

## Final verdict

REJECTED

这是未签收交付的拒收，不是伪称正式L3跑失败。保留H57候选、合同、Checker、失败日志及所有既有接受/拒收结果。

## Continuation decision

CONTINUE — 冻结 `H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1` / repair / SINGLE / CONTRACT_FROZEN / Executor。

唯一主要修复是商城验收的证据忠实性：所有38商家候选源只读，只允许两个HTTP/旅程脚本修复预留日志及由监督进程先等首进程退出、再开恢复进程的安排；保留原六例/验签/业务要求，正式L2后独立L3。新包不接受旧受损日志为合格请求证据，而把原始哈希和57历史成本作为冻结继承输入，新规范日志重新执行。

共用原预算160请求：已花57，Executor余103，正式L2合计最多2次（已0）。此前主动用时精确值unknown；已观察执行会话2026-11-01T01:48:17.019Z至末次执行响应02:48:30.990224Z的整个窗口上界向上收61分钟，历史保守收取120分钟，另给最多90主动分钟，不超过240分钟总包。等待和Evaluator准备不伪装为Executor主动用时。若发现更早/未报执行成本应停报，不隐瞒。Evaluator仍总80，当前HTTP使用0。相比停止丢弃已完成接线，或只放宽日志Checker，这个修复能检验关键“进程退出后不多付”，收益更直接；相比回H56，仍针对真实商城旅程。

新包入口 `../H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/EXECUTOR_START.md`；业务六例及真实进程退出通过后STOP此接线切片，再根据商城实际证据选后续。四项授权仍false，零外部网络/真实支付/安装/Git写操作。PCAC-07/09业务候选保留，12/20证据及18恢复仍待修复和独立验收；无合规结论。

本轮辅助检查还包含数次不存在路径的只读查询（错误的旧review路径/日志扩展名）；不影响候选或HTTP预算，最终使用实际meta列出的stdout.log完成复核。
