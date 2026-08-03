# Task Contract

Task ID: `P9-GOVERNED-PAYMENT-ACTION-OBJECT-TYPE-BOUNDARY-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Parent task: `P9-GOVERNED-PAYMENT-ACTION-CONTRACT-V1`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Repair objective

Repair only the governed-action outer object type boundary found by the evaluator:

```text
F-01 mutable lookalike object
     → currently VALID
     → WebShop ALLOW
     → callback = 1

F-02 dict object
     → currently AttributeError
```

Required outcome:

```text
Only the exact GovernedPaymentAction contract type
may enter field-level verification.

Any other supplied object
→ VerificationStatus.INVALID
→ stable reason code
→ WebShop DENY
→ callback = 0
→ no exception
```

Do not redesign the action contract or add new action types.

## 2. Acceptance criteria

### AC-01 — strict action object boundary

Before `_checked_values(...)` or any attribute access, `verify_governed_payment_action(...)` must distinguish:

```text
action is None
→ existing MISSING_EVIDENCE / governed_action_missing

exact GovernedPaymentAction object
→ continue existing field verification

all other supplied objects
→ INVALID / governed_action_invalid_type
```

Use a strict boundary equivalent to:

```python
type(action) is GovernedPaymentAction
```

A duck-typed object, dictionary, list, string, mock, proxy or subclass must not be accepted as the governed contract.

### AC-02 — no exception and stable fact

For every invalid outer object type, the verifier must return a `GovernedActionBindingFact` without raising.

Expected fact:

```text
status = INVALID
action_id = null
reason_codes = ("governed_action_invalid_type",)
checked_action_type = null
checked_order_ref = null
checked_request_ref = null
checked_payment_ref = null
```

No attributes may be read from the invalid object.

### AC-03 — WebShop fails closed before callback

When an invalid outer object is supplied through `governed_action=`:

```text
decision = DENY
checkout_executed = false
callback_count = 0
runtime_gate_record = null
governed_action_fact.status = INVALID
reason_codes = ("action:governed_action_invalid_type",)
```

No exception may escape the Runtime Gate.

The existing omitted-action behavior remains unchanged:

```text
governed_action=None
→ backward-compatible old path
```

### AC-04 — fixed evaluator counterexamples

Add direct regression tests for at least:

1. `SimpleNamespace(**valid_action.__dict__)`;
2. `valid_action.to_dict()`;
3. list or string input;
4. subclass or proxy object that otherwise carries valid-looking fields.

For the mutable lookalike, prove it is not accepted even though all field values match a valid action.

For dict and other invalid objects, prove no exception is raised.

### AC-05 — matrix coverage

Extend the deterministic action matrix with at least:

```text
mutable_lookalike_action_object
serialized_dict_action_object
```

Expected for both:

```text
verification = INVALID
gate = DENY
callback = 0
reason = governed_action_invalid_type
```

Existing 16 matrix cases must remain unchanged and passing. New matrix total must be at least 18.

### AC-06 — preserve all prior behavior

The repair must not change:

- valid exact `GovernedPaymentAction` → VALID;
- missing `None` semantics;
- field-level missing/invalid/mismatch reasons;
- authority/order/request/payment/Agent/executor/context/time binding;
- P1—P4 behavior;
- one-callback valid WebShop behavior;
- public serialization format.

### AC-07 — bounded scope and regression evidence

Required commands:

```text
python3 -m unittest tests.trusted_execution.test_governed_action -v
python3 -m unittest tests.test_webshop_runtime_gate -v
PYTHONPATH=src python3 scripts/validation/webshop/run_governed_payment_action_matrix.py
python3 -m unittest tests.trusted_execution.test_payment_binding tests.trusted_execution.test_context_policy -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Expected:

```text
governed-action tests > 12 and all PASS
Runtime Gate tests > 30 and all PASS
action matrix >= 18/18 matched
full suite > 394 and all PASS
formal entrypoint 13/13 PASS
```

`REPORT.md` must include the exact evaluator counterexample output before/after, changed-file SHA-256, complete EV triplets, AC-01 through AC-07 mapping, and workflow validation with no `BLOCKING` finding.

## 3. Allowed scope

- `src/agentic_payment_experiment/trusted_execution/governed_action.py`
- `tests/trusted_execution/test_governed_action.py`
- `tests/test_webshop_runtime_gate.py`
- `samples/external/webshop/governed_payment_action_matrix_v1.json`
- `scripts/validation/webshop/run_governed_payment_action_matrix.py`
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_OBJECT_TYPE_BOUNDARY_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_OBJECT_TYPE_BOUNDARY_REPAIR_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 4. Explicit exclusions

- 不修改 `webshop_runtime_gate.py`，除非现有 verifier 返回 INVALID 后无法满足 AC-03；如必须修改，报告中单独证明原因；
- 不修改公开动作字段、枚举值或序列化结构；
- 不增加新动作类型；
- 不修改 P1—P6、订单规则、支付生命周期或 Sidecar；
- 不实现 Source Lineage、Taint Propagation、提示注入、UI；
- 不执行 WebShop、Buy Now、支付、查询或网络；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理继承工作区改动。

## 5. Authorization

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

## 6. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | exact type gate before attribute access | only exact `GovernedPaymentAction` continues | AC-01 |
| VP-02 | dict/list/string/proxy/subclass verifier inputs | INVALID fact, stable reason, no exception | AC-02, AC-04 |
| VP-03 | invalid object through WebShop Gate | DENY, zero callback, no runtime record | AC-03 |
| VP-04 | evaluator mutable lookalike reproduction | no longer VALID or ALLOW | AC-04 |
| VP-05 | extended machine matrix | at least 18/18 matched | AC-05 |
| VP-06 | original 16 cases and valid action path | unchanged decisions, reasons and serialization | AC-06 |
| VP-07 | targeted, P2/P4, full, formal and workflow | all counts exceed parent baseline; no BLOCKING | AC-07 |

## 7. Stop conditions

Stop and report without broadening scope if:

- exact type enforcement requires changing the public action fields or P1—P4 APIs;
- invalid object handling cannot be made exception-free inside the pure verifier;
- any required proof needs WebShop runtime, payment, network or environment changes;
- unrelated inherited changes prevent objective validation.
