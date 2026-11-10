# H66独立复核：研究通过，IronClaw接入停留在参考

Task ID: H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1
Task kind: one_off
Reviewed baseline HEAD: f3e3235e2cd220f1b03cdc217c49820cdebf02b0
Review date: 2026-11-10
Reviewer: Evaluator
Task verdict: PASS
Impact verdict: NOT_APPLICABLE
Continuation decision: SWITCH

## 全局位置

目标是交易授权、绑定、执行前治理、恢复与审计能够独立复核。冻结地图r108：A–D本地阶段关闭，E受控本地代表闭合，F当前；B-19只测IronClaw是否已有具体金融消费者，不能从通用宿主推断金融接入价值。本轮为资格研究，不建设产品能力。H62无新商户反例、B-06真实支付仍后置，均不重开。

继续门槛是固定主分支具体金融消费者、逐边代码链及新增独立判据同时成立。本次没有达到，停止IronClaw接入方向，保留机制参考。下一方向转为已定位的ACP REST到MCP绑定幂等要求差异，只测固定公开契约，不安装上游或执行付款。

## Pre-review checks / 评估前检查

收到时CURRENT为EXECUTING/Executor，REPORT为SUBMITTED_FOR_REVIEW，公共校验OK；接受至READY_FOR_REVIEW/Evaluator后锁定10个顶层文件、14个L2文件、15个来源归档和4个辅助文件。独立复跑原四VP，另写来源/预算审计，不运行执行者辅助脚本或上游代码。全部接受摘要保持。

收到时Git只显示本任务新增REPORT/RESULT及CURRENT；未对执行者报告的历史目录改动观察作归因。冻结5控制文件与194公开历史/产品文件摘要通过。版本化发布后的HEAD不同于观察基线不是输入漂移；本包依精确摘要保护，不使用旧HEAD相等门禁。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/L3-GATE.json
- Validation plan: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE；逐源审计RV-EV-05单列，不改冻结计划。

独立L3四项通过，七类合成损坏被拒。评估者另向官方GitHub固定提交复核全部9个成功源码文件的Git blob归属，未请求或绕过S07被拦截内容；动态Issue仅按其观察时点解释。

## Acceptance matrix / AC 逐条裁决

| AC | 裁决 | 独立证据与理由 |
| --- | --- | --- |
| AC-01 来源/许可/保护 | 通过 | RV-EV-01/04/05：5冻结、194保护一致；9文件内容Git blob与固定提交官方返回一致，11处引用复算；根Cargo仅声明MIT OR Apache-2.0，不冒充逐依赖法律尽调 |
| AC-02 具体消费者与六边 | 通过 | RV-EV-02/05与逐行审阅：通用入口/审批/凭据暂存有静态来源；金融准备对象、执行权消费和金融恢复保持UNKNOWN，consumer=NOT_FOUND_IN_VIEW。没有用通用代码或Issue冒充金融消费者 |
| AC-03 本仓对照与去留 | 通过 | RV-EV-02/05：6项本仓文件对照与已关闭本地能力边界相符；确认/绑定参照H48、HTTP接缝参照H51、恢复参照H62既有审阅。未建立新增金融边界，STOP_REFERENCE_ONLY有足够有界依据 |
| AC-04 预算/失败/副作用 | 通过 | RV-EV-03/04/05：15次来源请求=11成功+4失败，重试同目标≤2，全部闭合，顺序1，归档304999字节；请求/L2账本763.844秒、1L2、1版；失败保留，不以不同文件数替代累计请求数 |

## Independent source findings / 独立来源判断

固定提交为b0b999d96781516ee05e6ba961d6f3ead900da96。独立复核全部9文件的官方blob，并核对结果中的11处原文引用。HostRuntime/CapabilityHost是通用执行边界，ApprovalResolver发放权限租约，WASM凭据提供器在宿主内取得和消费秘密租约。这些局部静态机制有参考价值，但不证明一次资金执行权、金融账户主体、支付签名、实际扣款或PSP恢复。

六阶段中STATIC_PROVEN只表示通用机制的静态证据，不能改写为金融链路已证明。审批重试产生新grant id不是重复扣款漏洞证明；通用CapabilityLease包含Claimed/Dispatching/Consumed等状态也不是资金恰好执行一次的运行证据。未沿实际资金工具证明效果，因此不冻IronClaw适配或漏洞修复包。

停止结论只约束已读九文件和两Issue构成的有界视图。未读完整目录树、插件市场或所有旧PR，不能推断整个上游没有金融能力，也不能因剩余预算而无限追踪同一未知。

## Budget and failed attempts / 预算与失败

S07为安全落盘拦截、S08为路径404、S11/S12为Issue返回解析错误；失败已计入15次访问，后续成功请求使用新预留。未修改源全文以伪造blob，也未绕过安全拦截。两个Issue各2次目标访问，正式L2单独预留/封存，所有33条账本事件的哈希链接及归档摘要复算一致。

763.844秒是init至最后L2封存的账本时长，不是全部报告收尾工时；收到时报告末写时间距init约22分钟，仍在90分钟内。账本证明已记录请求的次数/顺序/归档，不声称提供操作系统级全部网络遥测。评估者独立9次固定文件版本复核及下一方向准备另计，不回写执行者账本。

## Final verdict

PASS

## Project impact verdict

Impact verdict: NOT_APPLICABLE

资格研究完成，不代表产品安全能力或真实支付成熟度提高。H65R原预算拒收保持；A–E原边界不扩张，真实身份、签名信任源、部署、独立控制效果、商业需求和合规仍未证明。

## Iteration value and continuation decision

Continuation decision: SWITCH

停止本IronClaw有界接入研究。更强的具体线索是ACP官方Issue #295：REST要求所有变更请求带幂等键，而MCP绑定将该键列为可选。评估者另核官方HEAD 7fdd78df677a94dce04c770644b0fbbb1401272b的规范、MCP文档、OpenRPC和示例，差异仍可定位；这涉及零容忍重扣边界，比扩大通用运行时研究更值得先测。

这仍是规范/生成客户端风险，不是已复现重复扣款；实际MCP服务端可能自行拒绝缺键或稳定复用键。UCP samples #277的悬空履约引用/报价差异作为次选保留，未独立运行；它更偏价格/引用正确性，需要运行时成本，暂不重开H62。公开问题单不证明客户购买意愿。

## Next execution package

- Dispatch mode: SINGLE
- Next task ID: H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1
- Next contract: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/CONTRACT.md
- Initial state and role: CONTRACT_FROZEN / Executor
- Principal change: 固定五个工具，仅测幂等键必填契约从REST映射到MCP元数据时是否弱化。
- Budget: 45分钟墙钟、最多2分析尝试/2正式L2；冻结10个成对元数据探针及5个示例元数据观察；网络/安装/上游运行/产品/模型服务/钱包/付款0。
- Readiness: 一个可证伪问题、四AC、固定公开来源投影、许可、范围和验证计划齐备；只使用标准库。只测meta字段，不验证完整RPC请求、业务payload或服务端付款行为。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/18/20；对象=金融消费者资格；代码=无产品改动；Test=四VP/七损坏/9官方blob及11引用复核；Evidence=独立L3/原源审计/追加账本；before/after产品成熟度不变，身份/签名/清算/采用/合规unknown。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-01.stderr.log
- Observed result: exit 0；保护通过。

## RV-EV-02

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-02.stderr.log
- Observed result: exit 0；六阶段/六对照/引用结构通过。

## RV-EV-03

- AC: AC-04
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-03.stderr.log
- Observed result: exit 0；七损坏被拒。

## RV-EV-04

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/gate/RV-EV-04.stderr.log
- Observed result: exit 0；最终检查通过。

## RV-EV-05

- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/semantic/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/semantic/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l3_evaluator_20261110/semantic/RV-EV-05.stderr.log
- Observed result: exit 0；9官方blob/11引用/15请求/4失败/归档字节与双时钟复核通过；全部接受快照保持。
