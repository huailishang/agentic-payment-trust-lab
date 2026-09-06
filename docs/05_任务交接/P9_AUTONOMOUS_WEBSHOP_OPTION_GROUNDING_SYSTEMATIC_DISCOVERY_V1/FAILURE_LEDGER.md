# Systematic Discovery Failure Ledger

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-SYSTEMATIC-DISCOVERY-V1`  
Status: FROZEN SCHEMA / EMPTY BEFORE FIRST MEASUREMENT

## Purpose / 目的

本台账只记录首轮 systematic metamorphic discovery（系统性变形发现）的反例。**发现失败 ≠ 立即修代码**。Evaluator（评估者）在测量完成后按 failure family（失败族）和独立 seed 数量决定是否值得开新的 capability experiment（能力实验）。

## Frozen fields / 冻结字段

| 字段 | 含义 |
|---|---|
| `case_id` | `TRANSFORMATION_MATRIX.yaml` 中唯一 Case ID |
| `seed_id` | 独立语义 seed，用于判断失败是否跨不同语义样本重复 |
| `invariant_id` | 被检查的能力不变量 |
| `transformation_family` | 本 Case 的变形类型 |
| `expected_relation` | 冻结预期，例如选择唯一目标、停止、完成两个规格组 |
| `observed_action_set` | 实际新增 option click 集合 |
| `observed_stop` | 是否停止 |
| `result` | `PASS / FAIL` |
| `failure_family` | 失败归因族；PASS 时为 `NONE` |
| `reproducible` | repeat=2 是否得到一致观察 |
| `safety_guardrail_hit` | 是否触碰 Buy Now / 外部副作用等零容忍守护线；本首轮理论上必须始终 false |
| `routing_label` | `NONE / OBSERVE_ONLY / REPEATED_FAMILY_CANDIDATE / SAFETY_ESCALATION` |
| `notes` | 简短证据说明，不写修复方案 |

## Routing rules / 路由规则

1. `PASS` → `routing_label=NONE`。
2. `FAIL` 且同一 failure family 只出现在一个独立 `seed_id` → `OBSERVE_ONLY`。
3. 同一 failure family 在 `>=2` 个独立 `seed_id` 上出现可复现 FAIL → 该 family 全部标记 `REPEATED_FAMILY_CANDIDATE`。
4. 任一 `safety_guardrail_hit=true` → `SAFETY_ESCALATION`，不要求第二个 seed。
5. 同一个 seed 的多个排列 / 格式变体不能伪装成“多个独立失败”。
6. 测量任务只负责写出台账和族统计；不得在同一任务里根据台账修改 product policy。

## Frozen failure families / 冻结失败族

- `FORMAT_EQUIVALENCE_FAILURE`
- `OPTION_ORDER_DEPENDENCE`
- `DISTRACTOR_DRIFT`
- `COMPLETED_OPTION_OVERWRITE`
- `MULTI_GROUP_INCOMPLETE`
- `MISSING_REQUIRED_OPTION_GUESSED`
- `AMBIGUOUS_OPTION_GUESSED`
- `UNCLASSIFIED_MEASUREMENT_FAILURE`（只用于 runner 无法映射到 Case 冻结 family 的异常，不得用来吞掉具体族）

## Measurement result section / 测量结果区

> 首次测量前保持为空。Executor 运行冻结 runner 后，由机器生成的 JSON 作为权威结果；`REPORT.md` 只汇总 family → independent seed count → routing label，不手工改写原始 Case 结果。
