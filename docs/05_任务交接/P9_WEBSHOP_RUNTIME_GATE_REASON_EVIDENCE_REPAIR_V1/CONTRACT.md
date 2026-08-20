# Task Contract

Task ID: `P9-WEBSHOP-RUNTIME-GATE-REASON-EVIDENCE-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

父任务 `P9-WEBSHOP-BUY-NOW-RUNTIME-GATE-V1` 被评估者打回，原因不是错误放行，而是共享 Runtime Gate 在两类 P4 失败关闭分支中没有生成因果 reason code：

```text
p4_stale_wrong_action
p4_value_digest_mismatch
```

现状：

```text
final decision = INDETERMINATE
callback_count = 0
context_policy_status = VALID
reason_codes = p4:context_policy_valid
```

这会导致 Evidence / Replay 和后续 P9-E UI 无法解释为什么停止。

父任务复核：

- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/REVIEW.md`
- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/evidence/RV-EV-07.stdout.log`
- `docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/evidence/EV-02.runtime_mismatch_matrix.json`

## 2. Single objective

Repair the shared P2/P3/P4 runtime-gate evidence so every non-ALLOW branch exposes at least one stable, machine-readable causal gate reason.

The repair must not change the existing decision or callback behavior.

Expected examples:

```text
current_action != execute_payment
→ final INDETERMINATE
→ callback_count = 0
→ reason includes p4:current_action_mismatch

source coverage digest != current request values
→ final INDETERMINATE
→ callback_count = 0
→ reason includes p4:source_coverage_value_mismatch
```

The WebShop Buy Now outcome must consume these shared RuntimeGateRecord reasons without implementing a second WebShop-specific P4 rule engine.

## 3. Acceptance criteria

### AC-01 — causal reason for every shared runtime-gate branch

The shared runtime gate must expose explicit gate reasons for at least:

```text
upstream_prepayment_non_allow
p2_binding_missing
p2_binding_invalid
p3_identity_missing
p3_identity_invalid
p3_assurance_insufficient
p4_context_missing
p4_context_invalid
p4_policy_version_mismatch
p4_current_action_mismatch
p4_required_source_paths_mismatch
p4_covered_source_paths_mismatch
p4_missing_source_paths
p4_source_coverage_value_mismatch
runtime_gate_allow
```

Exact names may differ, but they must be stable, stage-prefixed and unambiguous.

For a non-ALLOW final decision, `RuntimeGateRecord.reason_codes` must not contain only success/match codes.

### AC-02 — reproduce and repair the two evaluator counterexamples

Independently test the fixed P9-B2 fixture with:

1. `ContextPolicyFact.current_action = refund_payment` while the expected action is `execute_payment`;
2. complete and otherwise valid source coverage whose amount digest belongs to `999.00` instead of the current `877.80` request.

Both must remain:

```text
final decision = INDETERMINATE
callback_count = 0
checkout_executed = false
```

Additionally, each must expose its actual causal reason. `p4:context_policy_valid` alone is forbidden.

### AC-03 — no duplicated WebShop policy logic

The decision remains owned by the existing shared runtime gate.

The WebShop wrapper may only forward or merge shared gate reasons. It must not reimplement:

- binding rules;
- identity rules;
- context trust/source rules;
- expected digest construction;
- authorization policy.

If exact causal reasons require a shared change, implement them in `payment_execution.py`, not as WebShop-only comparisons.

### AC-04 — preserve callback and decision semantics

All existing behavior must remain unchanged:

- final `ALLOW` calls the injected callback exactly once;
- P1/P2/P3/P4 non-ALLOW calls it zero times;
- callback exception is attempted once, never retried, never reported as checkout success;
- P2/P3 invalid cases remain `DENY` or `INDETERMINATE` according to existing rules;
- P4 wrong action and digest mismatch remain `INDETERMINATE`.

### AC-05 — evidence and replay consumability

`RuntimeGateRecord.to_dict()` and `WebShopBuyNowGateOutcome.reason_codes` must contain the same causal gate reason for the repaired P4 cases.

The evidence must be sufficient for a UI or replay consumer to display a plain-language explanation without reading the original ContextPolicyFact object or source code.

### AC-06 — regressions

Add tests covering:

- every newly added gate reason branch;
- the two evaluator counterexamples;
- no success-only reasons on a non-ALLOW outcome;
- WebShop outcome forwards shared reasons;
- existing 14 WebShop runtime-gate tests remain green;
- callback count remains unchanged.

Required commands:

```text
python3 -m unittest tests.trusted_execution.test_payment_binding -v
python3 -m unittest tests.test_webshop_runtime_gate -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

The full suite must exceed the current 336-test baseline and the formal entrypoint must remain 13/13.

### AC-07 — scope and handoff

Report exact changed files and SHA-256. Confirm:

- no WebShop runtime or real Buy Now;
- no payment/fulfilment/UI/network/environment side effect;
- no change to `models.py`, `validator.py`, P9-B1 adapter/fixture/helper or ContextPolicy rule construction;
- no commit or push.

## 4. Allowed scope

- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/webshop_runtime_gate.py`（only if needed to forward shared reasons）
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_webshop_runtime_gate.py`
- `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md`（factual status only）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（factual status only）
- `docs/05_任务交接/P9_WEBSHOP_RUNTIME_GATE_REASON_EVIDENCE_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_RUNTIME_GATE_REASON_EVIDENCE_REPAIR_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 5. Exclusions

- 不修改 `models.py`、`validator.py`、`trusted_execution/context_policy.py`；
- 不修改 P9-B1 adapter、fixture 或 export helper；
- 不改变 P1—P4 决策含义；
- 不新增 WebShop 专属授权规则；
- 不运行 WebShop、`webshop38`、Flask、浏览器或后台服务；
- 不执行 `click[buy now]` 或 `SimServer.done()`；
- 不开始 P9-C、P9-D 或 P9-E；
- 不调用网络、API、LLM、钱包、测试网、真实支付或履约；
- 不安装依赖或修改环境；
- 不 commit、不 push、不 rewrite history。

## 6. Authorization

```yaml
network_call: false
api_call: false
data_download: false
dependency_install: false
create_environment: false
background_process: false
webshop_runtime_execution: false
buy_now_execution: false
payment_or_order_side_effect: false
commit: false
push: false
history_rewrite: false
```

## 7. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | shared gate branch reason matrix | each non-ALLOW has causal stage-prefixed reason | AC-01 |
| VP-02 | wrong-action evaluator counterexample | INDETERMINATE, zero callback, explicit current-action reason | AC-02 |
| VP-03 | digest-mismatch evaluator counterexample | INDETERMINATE, zero callback, explicit coverage/digest reason | AC-02 |
| VP-04 | WebShop outcome forwarding | outcome and RuntimeGateRecord expose same causal reason | AC-03、AC-05 |
| VP-05 | callback and decision regression matrix | no decision/callback behavior changes | AC-04 |
| VP-06 | targeted shared + WebShop tests | all pass | AC-01—AC-06 |
| VP-07 | full regression and formal entrypoint | suite >336; 13/13 | AC-06 |
| VP-08 | scope/hash/workflow validator | no scope creep, no commit/push, no BLOCKING | AC-07 |

## 8. Required evidence

For each VP save complete `EV-*` meta/stdout/stderr triplets.

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- before/after machine-readable output for both evaluator counterexamples;
- complete shared gate reason matrix;
- explicit proof that every non-ALLOW branch has a causal reason;
- WebShop outcome / RuntimeGateRecord reason equality;
- callback counts and decisions before/after;
- test counts and formal entrypoint output;
- changed files and hashes;
- explicit no-runtime/no-Buy-Now/no-payment/no-UI/no-network/no-commit/no-push statement;
- AC-01 through AC-07 and VP-01 through VP-08 mappings.

## 9. Stop conditions

Stop and report without broadening scope if:

- a fix requires changing the ContextPolicy decision model or `models.py`;
- a fix would duplicate P4 expected-value logic inside the WebShop wrapper;
- existing decisions or callback counts change;
- any validation requires WebShop runtime, real Buy Now, network, payment, environment changes or UI.
