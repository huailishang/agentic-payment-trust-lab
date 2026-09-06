# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-UNCERTAINTY-GATE-V1`  
Task name: Autonomous WebShop option-grounding uncertainty gate  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_UNCERTAINTY_GATE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r24`  
Active bottleneck: `B-04`  
Hypothesis: `H-15`  
Dispatch: `SINGLE`

Metric baseline: Evaluator-frozen H-15 uncertainty-gate probe `2/5 PASS`；H-14 option-grounding probe `5/5`；H-12 real five-goal WebShop regression `5/5`。  
Estimated affected scope: Systematic Discovery 的 5 个 FAIL 全部落在 `INV-06 UNCERTAINTY_BOUNDARY`；其中 `AMBIGUOUS_OPTION_GUESSED=3` 跨 `2` 个 independent seeds，另有 `MISSING_REQUIRED_OPTION_GUESSED=2` 但只来自 1 个 seed。该范围是 failure-mechanism estimate（失败机制范围估算），不是 fresh-unseen 提分承诺。  
Expected project impact: H-15 主探针 `2/5 → 5/5`，同时保持 H-14 `5/5`、Systematic Discovery 原 `19` 个 PASS 不回归、H-12 real WebShop `5/5`，以及 Product Trace `9/12`、GESR `8/12`、callback `12/12`、duplicate/forbidden side effect `0/12`。  
Rollback condition: H-15 probe 不能稳定到 `5/5`、正向控制回归、Systematic 原 19 PASS 回归、H-12 或项目守护线退化、需要第二个 principal change、需要 revealed/probe exact values、需要修改 search/ranking 或 numeric option semantics。

## Why this package exists / 为什么现在做

Systematic Metamorphic Discovery 已完成 Evaluator 独立复核：

```text
24 fixed cases
→ 19 PASS / 5 FAIL
→ 48 observations all reproducible
→ safety hits = 0

AMBIGUOUS_OPTION_GUESSED
→ 3 FAIL
→ 2 independent seeds
→ repeated-family candidate

MISSING_REQUIRED_OPTION_GUESSED
→ 2 FAIL
→ 1 independent seed
→ observe-only
```

5 个 FAIL 全部属于 `INV-06 UNCERTAINTY_BOUNDARY（不确定边界）`。当前策略允许仅凭 partial lexical roots（部分文本词根）形成候选并排序，但缺少动作前的 evidence sufficiency / uniqueness gate（依据充分性 / 唯一性门）：

- 多个候选只共享同一泛化词根时，仍会挑一个；
- 用户存在更具体修饰要求、但没有任何候选满足时，仍可能因为共享通用词根而挑一个。

这不是五个独立小问题，而是一个重复机制边界。

## Frozen accepted product snapshot / 冻结产品快照

| File | H-15 baseline SHA-256 |
|---|---|
| `src/agentic_payment_experiment/webshop_agent_behavior.py` | `6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f` |
| `tests/test_webshop_agent_behavior.py` | `36f51bbec44313e8e6fde98ec35d2d0a16ee2730e81e0e2b6916387da2e28b20` |

Evaluator pre-change snapshots:

- `evaluator_baseline/H15_BASELINE_webshop_agent_behavior.py.snapshot`
- `evaluator_baseline/H15_BASELINE_test_webshop_agent_behavior.py.snapshot`

## Frozen evaluator probe / 冻结评估探针

Evaluator 在首次 H-15 产品修改前冻结了与 Blind Holdout、24-Case Systematic Discovery 不同取值的 probe：

- checker: `evaluator_checks/uncertainty_gate_probe.py`
- checker SHA-256: `0acd714b427b3b445aea8fae619117fd2131642f9edf45927eff2069e0bcd2d3`
- baseline artifact: `evaluator_baseline/BASELINE_UNCERTAINTY_GATE.json`
- baseline artifact SHA-256: `5c5642cf27e70cb112dc7b176fa1af496a039c0bfb0e874ab9333f406ad919e0`
- baseline: `2/5 PASS`
- target: `5/5 PASS`

Probe 含两个正向控制和三个 uncertainty failure：

1. exact unique lexical（明确唯一文本规格）—— baseline PASS；
2. single unique partial extension（唯一可解释扩展）—— baseline PASS；
3. ambiguous shared root（多个候选只共享同一词根）—— baseline FAIL；
4. missing specific modifier（用户具体修饰词没有候选满足）—— baseline FAIL；
5. second independent ambiguity seed（第二个独立歧义 seed）—— baseline FAIL。

因此不能通过“一律拒绝文本规格”来达到 `5/5`。

## Single objective / 单一目标

只实现一个 principal change（唯一主要变化）：

> 在 lexical option selection（文本规格选择）前增加通用 grounding sufficiency / uniqueness（依据充分性 / 唯一性）判断：只有用户依据足够且候选可区分时才允许点击；证据不足或候选无法区分时不猜选。

允许围绕 `_instruction_option` 修改，并新增只直接服务于该判断的通用 helper。不得扩成搜索、商品排序、数值规格解析或完整自然语言理解重构。

## Acceptance criteria / 验收标准

### AC-01 — Five-field / source boundary

- `AgentPolicyInput` 保持五字段：`instruction_text / observation / available_actions / step_index / previous_actions`；
- 不读取 hidden truth（隐藏真值）、WebShop truth files、网络/runtime 外部数据；
- H-15 source audit PASS。

### AC-02 — H-15 primary metric

- frozen uncertainty-gate probe 从 `2/5 → 5/5`；
- 两个正向控制继续 PASS；
- 三个 uncertainty case 全部从“猜选”变为冻结预期；
- 该 probe 是 H-15 唯一 primary capability metric（主能力指标）。

### AC-03 — One general mechanism

- 所有改善必须来自同一 evidence sufficiency / uniqueness rule family；
- 不得为 probe case、Systematic case、goal index、ASIN 或 exact option value 写专用分支；
- dedicated tests 必须使用与 evaluator probe / revealed failure 不同的合成值。

### AC-04 — Anti-overfit / protected semantics

`evaluator_checks/uncertainty_gate_source_audit.py` 必须 PASS：

- 禁止 revealed Blind Holdout literals；
- 禁止 Systematic Discovery revealed failure literals；
- 禁止 H-15 evaluator probe literals 进入 product policy / dedicated tests；
- `_search_query / _significant_terms / _budget / _choose_result` byte-equivalent to H-15 baseline；
- `_dimension_signature / _measurement_pairs / _count_amount / _requested_cardinal_amounts / _numeric_option_matches_instruction` byte-equivalent to H-15 baseline。

### AC-05 — Scope discipline

主要产品变化仅限：

- `_instruction_option`；
- 新增/调整直接服务 lexical uncertainty gate 的通用 helper；
- `tests/test_webshop_agent_behavior.py` 中使用不同取值的 dedicated regression tests。

不得修改 search/product ranking、numeric option semantics、runtime driver / validator、WebShop upstream、Journey、Trace、payment/protocol/x402 产品链。

### AC-06 — Existing option-grounding capability preserved

- H-14 frozen option-grounding probe 保持 `5/5`；
- Systematic Discovery 原来 `19` 个 PASS Case 全部仍 PASS；
- 已揭晓 5 个 Systematic FAIL 只作为 secondary diagnostic（次级诊断），不要求为 Task PASS 而逐题修复。

### AC-07 — Revealed systematic regression boundary

Executor 运行同一冻结 24-Case matrix 到 H-15 独立 output：

`evidence/POST_H15_SYSTEMATIC_RESULT.json`

`systematic_regression_guard.py` 只要求：

- 原 19 PASS 不回归；
- measurement complete / reproducible；
- safety hits / external side effects = 0；
- 可以报告 5 个旧 FAIL 中哪些自然改善，但这些不是 primary target。

### AC-08 — Real / project guardrails

- H-12 five-goal real WebShop regression 保持 `5/5`、repeat=2；
- Journey focused regression PASS；
- formal `run_experiment.py` PASS；
- project-impact baseline repeat=3 一致，保持 Product Trace `9/12`、GESR `8/12`、callback `12/12`、duplicate/forbidden side effect `0/12`；
- full unittest 无新增失败；
- Buy Now / purchase / payment / order / network side effect = 0。

### AC-09 — v2.2 evidence handoff

- frozen Validation Plan `11/11` mandatory checks PASS；
- REPORT.md 映射 AC-01..09 → EV；
- 记录 before/after 主指标、product/test hash、bounded cycle count、Systematic regression summary 与 deviations；
- Executor 只提交 `SUBMITTED_FOR_REVIEW`，不自签 Task PASS / project-impact verdict。

## Exclusions / 明确排除

- 不修改 `_choose_result`、search query、商品 ranking；
- 不修改 numeric option semantics；
- 不修改 evaluator probe / source audit / baseline / Validation Plan；
- 不把 `navy / sage / forest green / mint green` 等当前 24-Case failure values 写成产品专用逻辑；
- 不把 H-15 probe 的 `burgundy / turquoise blue / olive green / olive brown / smoky violet / deep violet / light violet / matte silver / polished silver` 等 exact values 写进 product policy / dedicated tests；
- 不执行 Buy Now、真实购买、支付、订单、网络或履约；
- 不调用外部 API/network；
- 不安装依赖、不创建新环境；
- 不 commit、push、history rewrite。

## Allowed scope / 允许范围

Executor 仅可修改：

- `src/agentic_payment_experiment/webshop_agent_behavior.py`
- `tests/test_webshop_agent_behavior.py`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_UNCERTAINTY_GATE_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_UNCERTAINTY_GATE_V1/evidence/**`

以下只读：

- 本任务 `CONTRACT.md`
- 本任务 `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- `evaluator_baseline/**`
- Systematic Discovery contract/matrix/result/review/evidence
- H-14 evaluator probe / evidence
- project map / project control / CURRENT
- runtime driver / validator / WebShop upstream / Journey / Trace / payment / protocol/x402 产品代码

## Bounded execution / 有界执行

- max implementation→L2 cycles: `3`；
- cheap L1 checks 可在同一 cycle 内重复；
- 每次完整 L2 都必须保留 evidence，不得覆盖前一轮事实；
- principal change、hypothesis、AC、Validation Plan、授权和 measurement boundary 全程冻结。

推荐 L1：

```text
python3 -m unittest tests.test_webshop_agent_behavior -v
python3 .../uncertainty_gate_probe.py --require-all
python3 .../uncertainty_gate_source_audit.py
python3 .../option_grounding_probe.py --require-all
```

## Stop conditions / 停止条件

出现以下任一情况立即停止并回 Evaluator：

- 需要第二个 principal change；
- 需要改 search/product ranking 或 numeric option semantics；
- 需要使用 revealed/probe exact literals；
- H-15 probe 不能到 `5/5`，或两个正向控制出现回归；
- Systematic 原 19 PASS 发生回归；
- H-12 real regression / project guardrails 退化；
- 出现 Buy Now / purchase / payment / order / network side effect；
- 3 个完整 implementation→L2 cycles 用尽仍不满足冻结 AC。

此时不得继续堆规则；Evaluator 需要重新评估 `SWITCH（换方向）` 或新的架构假设。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- local WebShop regression: true
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Executor instructions / 执行者说明

直接执行冻结 H-15，不重新设计任务：

```text
read CURRENT / Contract / Validation Plan / evaluator checks
→ implement one uncertainty-gate principal change
→ cheap L1
→ frozen L2
→ REPORT.md with AC-01..09 / EV mapping
→ workflow validator
→ SUBMITTED_FOR_REVIEW
```

若出现 Systematic 旧 5 个失败仍未全部修复，不要为了追求 24/24 越界调参；H-15 primary target 是新 probe `2/5→5/5`，Systematic 24 Case 只守住原 19 PASS 并作为 secondary diagnostic。
