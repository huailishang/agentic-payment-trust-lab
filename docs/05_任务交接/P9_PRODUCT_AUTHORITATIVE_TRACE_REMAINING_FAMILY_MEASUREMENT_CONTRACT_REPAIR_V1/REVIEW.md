# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-REMAINING-FAMILY-MEASUREMENT-CONTRACT-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Reviewed baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Task verdict: `PASS`  
Project impact verdict: `NOT_APPLICABLE`

```yaml
review_state: PASS
project_impact_verdict: NOT_APPLICABLE
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

本 repair 正式通过。

它只修正了剩余 T05/T06/T07/T08 的四个 stale measurement event names，并新增一条公共 registry 子集回归检查；没有新增任何产品轨迹，也没有改变项目能力指标。

独立复核确认：

- fixture 相对 task-start snapshot 精确只有 4 个 scalar replacement；
- `tests/test_project_impact_baseline.py` 相对 task-start snapshot 仅新增 1 个测试方法，既有测试方法 AST 全部不变；
- 新测试只使用 public `runtime_contract_primitive()`，12/12 fixture key-event 都属于对应 authoritative registry；
- T05/T06/T07/T08 仍为 `NOT_AVAILABLE`，gap 名称已全部切到 accepted registry 事件；
- Product Trace 保持 `7/12`；
- GESR 保持 `6/12`；
- repeat=3 完全一致；
- 12 项 actual 产品输出与上一轮 Evaluator accepted snapshot 完全一致；
- non-trace SHA 不变；
- 55 个 `src/**/*.py` 与上一轮 Evaluator accepted manifest 完全一致；
- project-impact `21/21`；
- full regression `523/523`；
- workflow validator `OK`。

因此这是一个合格的 measurement repair，而不是能力改善实验；项目影响必须记为 `NOT_APPLICABLE`。

## 2. 独立证据

### RV-EV-01 — 精确 diff / 测试边界 / registry / src 审计

独立输出：

```text
frozen_hashes=PASS
fixture_diff=tasks/4/expected_product_observed_trace_events/3:DECISION_RECORDED->ACTION_BINDING_DECISION_RECORDED
fixture_diff=tasks/5/expected_product_observed_trace_events/3:DECISION_RECORDED->ACTION_BINDING_DECISION_RECORDED
fixture_diff=tasks/6/expected_product_observed_trace_events/0:INPUT_SOURCE_RECORDED->LINEAGE_DECISION_RECORDED
fixture_diff=tasks/7/expected_product_observed_trace_events/0:INPUT_SOURCE_RECORDED->LINEAGE_DECISION_RECORDED
fixture_semantic_diff_count=4
test_scope=ONLY_ONE_NEW_METHOD
new_method=test_fixture_expected_product_events_are_subset_of_public_registry
registry_subset=12/12
src_python_file_count=55
src_matches_parent_accepted_manifest=True
RESULT=PASS
```

特别说明：src 不变量不是只和 Executor 本轮自己保存的 manifest 比，而是锚定上一轮 Evaluator accepted Prepayment completion manifest；两份 manifest byte-for-byte 一致。

证据：

- `evidence/RV-EV-01-independent-repair-audit.py`
- `evidence/RV-EV-01.meta.json`
- `evidence/RV-EV-01.stdout.log`
- `evidence/RV-EV-01.stderr.log`

### RV-EV-02 — Project-impact regression

```text
Ran 21 tests
OK
```

包含新增 public-registry subset regression test。

证据：`evidence/RV-EV-02.*`。

### RV-EV-03 — Same-baseline repeat=3

```text
repeat_count = 3
all_identical = true
normalized_sha256 = cef137ad7cc2db4c60954e3dbec778c14c7929a38bbfc6af7528472fe47660ca × 3

Product Trace = 7/12 = 0.583333
GESR          = 6/12 = 0.500000
```

修正后的剩余 gap：

```text
T05 NOT_AVAILABLE
missing: ACTION_BINDING_DECISION_RECORDED, AUTHORITY_RECORDED, ORDER_RECORDED, REQUEST_RECORDED

T06 NOT_AVAILABLE
missing: ACTION_BINDING_DECISION_RECORDED, AUTHORITY_RECORDED, ORDER_RECORDED, REQUEST_RECORDED

T07 NOT_AVAILABLE
missing: LINEAGE_DECISION_RECORDED, POLICY_DECISION_RECORDED

T08 NOT_AVAILABLE
missing: LINEAGE_DECISION_RECORDED, POLICY_DECISION_RECORDED
```

证据：

- `evidence/RV-EV-03.meta.json`
- `evidence/RV-EV-03-baseline.json`
- `evidence/RV-EV-03.stdout.log`
- `evidence/RV-EV-03.stderr.log`

### RV-EV-04 — 产品与业务不变量

```text
all_12_actual_outputs_equal_parent_evaluator_snapshot=True
non_trace_projection_sha256=6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
valid_product_tasks=T01,T02,T03,T04,T09,T10,T12
absent_product_tasks=T05,T06,T07,T08,T11
metrics_unchanged=7/12_product_trace,6/12_gesr
corrected_gap_names=T05,T06,T07,T08
T05_T08_business_guardrails=PASS
RESULT=PASS
```

关键业务状态仍为：

```text
T05 decision = DENY
T06 decision = INDETERMINATE
T07 decision = ALLOW
T08 decision = ALLOW

T07/T08 callback = 0
T07/T08 retry = 0
T07 trusted_state_changed = false
T07 blocked_paths = request.amount
T08 trusted_state_changed = false
T08 blocked_paths = request.payee
forbidden side effects = []
```

证据：`evidence/RV-EV-04-*`。

### RV-EV-05 — Full regression

```text
Ran 523 tests
OK
```

证据：`evidence/RV-EV-05.*`。

### RV-EV-06 — Workflow validator

```text
OK: v2.1 routing and required artifacts are structurally valid
```

证据：`evidence/RV-EV-06.*`。

## 3. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 Exact four semantic replacements | 通过 | RV-EV-01 递归 JSON diff 精确 4 项，无第五项 |
| AC-02 Registry-subset regression test | 通过 | RV-EV-01：仅新增一个测试；public API；12/12 subset |
| AC-03 Corrected remaining-family gap names | 通过 | RV-EV-03 / RV-EV-04：T05-T08 仍 NOT_AVAILABLE，旧事件名消失 |
| AC-04 No false project gain | 通过 | RV-EV-03：repeat=3；Product Trace 7/12；GESR 6/12 |
| AC-05 Actual product / business invariance | 通过 | RV-EV-04：12 actual 与 parent evaluator snapshot 完全一致；non-trace SHA 不变 |
| AC-06 Frozen implementation boundaries | 通过 | RV-EV-01：runner/registry frozen hash 命中；55 src 与上一轮 accepted manifest 一致 |
| AC-07 Tests | 通过 | RV-EV-02 21/21；RV-EV-05 523/523；无既有测试方法修改 |
| AC-08 Evidence and workflow | 通过 | Executor REPORT 完整；Evaluator RV-EV-01~06；validator OK |

## 4. Project impact

```text
Project impact verdict: NOT_APPLICABLE
```

本任务是 repair，不是 capability experiment。

同一 accepted baseline 前后：

```text
Before
Product Trace = 7/12
GESR          = 6/12

After
Product Trace = 7/12
GESR          = 6/12

Delta
Product Trace = 0
GESR          = 0
```

这里“没有提升”正是正确结果：如果修尺子后 T05-T08 突然变成 VALID，反而说明 measurement repair 越权制造了假能力。

## 5. Continuation

B-03 仍是第一瓶颈，剩余产品轨迹缺口：

```text
T05,T06,T07,T08,T11
```

按 `PROJECT_BOTTLENECK_MAP.md` revision `2026-08-07-r11`，下一组真实重复最明确的是 T07/T08 Attack Overlay Family。

执行前结构核对确认：

```text
T07 / T08
→ 都由 evaluate_attack_overlay 产出 AttackOverlayResult
→ Policy / Lineage / Final Result 已经是产品真实事实
→ accepted registry 都是同一个 3-event 结构
   POLICY_DECISION_RECORDED
   LINEAGE_DECISION_RECORDED
   RESULT_RECORDED
→ 三个事件都绑定同一个 AttackOverlayResult projection
```

因此下一包采用：

```text
一个 Attack Overlay Trace Toolkit
+ 两个固定 Profile
+ 一个共享 3-event 组装路径
```

不允许：

- 分别创建 T07/T08 专属 builder；
- 修改 runner、fixture、authoritative registry；
- 重新执行 Policy / Lineage 规则来“生成证据”；
- 改变攻击阻断结果、决策或可信状态。

Next task:

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-ATTACK-OVERLAY-FAMILY-TOOLKIT-V1
state = CONTRACT_FROZEN / Executor
```

预期同基线项目变化：

```text
Product Trace 7/12 -> 9/12
GESR          6/12 -> 8/12
```

只有 T07/T08 允许新增产品轨迹；其余 10 项 actual 必须不变。
