# Task Contract

Task ID: `P9-WEBSHOP-PAYMENT-FULFILMENT-SIDECAR-BINDING-DUPLICATE-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Parent rejection

Parent task:

```text
P9-WEBSHOP-PAYMENT-FULFILMENT-SIDECAR-V1
```

Parent review:

```text
docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_V1/REVIEW.md
```

Independent evidence `RV-EV-06` established two blocking defects:

```text
F-01 Adapter payment_request 与 Gate bound_request 可交叉拼接，仍 ready=true
F-02 无 query 时 known successful/unresolved attempt 未暴露 duplicate block
```

This repair inherits the rejected parent implementation. Observed starting hashes:

```text
src/agentic_payment_experiment/webshop_payment_sidecar.py
  a7950308864d71a25b36c43ff11aed8cfeef1f0fe4d373ab305849b770f95c3b

tests/test_webshop_payment_sidecar.py
  02b2a757f3d2656dbe38704d00001ef687c8935d70410c48669e1fb5ae832c74
```

The workspace contains inherited changes from earlier tasks. Do not clean, reformat, stage, commit, or modify unrelated paths.

## 2. Single objective

Repair only the two rejected Sidecar boundaries:

```text
1. bind the current Adapter TransactionRequest to the already-allowed Gate request;
2. expose duplicate-payment blocking from related known attempts even when no query observation is supplied.
```

Do not start P9-C2 and do not redesign the Sidecar API.

## 3. Acceptance criteria

### AC-01 — canonical Adapter/Gate request binding

Before producing an effective payment or lifecycle result, verify that:

```python
gate_outcome.bound_request
== replace(
    adaptation.payment_request,
    agent_id=gate_outcome.bound_request.agent_id,
)
```

A semantically equivalent full-field comparison is acceptable. The only intentional projection difference is the Gate-injected `agent_id`; all other `TransactionRequest` fields must match.

At minimum test mismatches in:

```text
request_id
amount
currency or merchant/category-related request content
```

Any mismatch must produce:

```text
ready = false
effective_payment = null
lifecycle = null
retry_allowed = false
duplicate_payment_blocked = false
reason_codes contains prerequisite:adapter_gate_request_mismatch
```

Do not accept partial field matching that allows two different requests to be cross-composed.

### AC-02 — known-attempt duplicate blocking without query

When `query_observation is None` and `known_attempts` contains an idempotency-related attempt for the same business request:

```text
related SUCCEEDED attempt       → duplicate_payment_blocked=true
related UNKNOWN/PENDING attempt → duplicate_payment_blocked=true
retry_allowed=false
reason_codes contains duplicate:payment_blocked
```

The result must also expose a stable reason distinguishing successful versus unresolved related attempts.

Use the existing Trusted Execution idempotency capability to determine related attempts. Do not treat a different request as related merely because it appears in `known_attempts`.

When no query is supplied:

```text
query_recovery remains null
retry_allowed can never become true
no PaymentExecutionRecord is created
no callback is invoked
```

### AC-03 — preserve existing recovery semantics

The existing query-based path must remain unchanged in meaning:

```text
trusted FAILED query + explicit idempotency boundary + no conflicting attempt
→ retry_allowed=true only as offline retry candidate
```

And:

```text
query + related SUCCEEDED/UNKNOWN/PENDING attempt
→ existing assess_payment_recovery result remains authoritative
```

Do not fabricate a query observation to reuse `assess_payment_recovery`.

Do not modify:

```text
payment_recovery.py
payment_status_conflict.py
lifecycle.py
remediation.py
trusted_execution idempotency implementation
```

### AC-04 — no side effects and immutable inputs

The repair remains deterministic and offline:

- no WebShop runtime;
- no Buy Now execution;
- no payment, retry, status query, callback, fulfilment, refund or dispute;
- no file/network/process/environment access from production Sidecar code;
- all caller-supplied records remain unchanged;
- effective status, when needed, still uses immutable copies.

### AC-05 — regression coverage

Add deterministic tests covering at least:

1. Adapter request-id mismatch fails closed;
2. Adapter amount mismatch fails closed;
3. full canonical Adapter/Gate projection passes;
4. no-query related successful attempt blocks duplicate payment;
5. no-query related UNKNOWN attempt blocks duplicate payment;
6. no-query related PENDING attempt blocks duplicate payment;
7. no-query unrelated attempt does not falsely set duplicate block;
8. no-query known attempts never produce retry candidate;
9. existing trusted FAILED query retry-candidate behavior remains unchanged;
10. existing query-based successful/unresolved attempt blocking remains unchanged.

Required commands:

```text
python3 -m unittest tests.test_webshop_payment_sidecar -v
python3 -m unittest tests.test_payment_recovery tests.test_payment_status_conflict tests.test_lifecycle -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Expected:

```text
Sidecar targeted tests > 21 and all PASS
full suite > 358 and all PASS
formal entrypoint 13/13 PASS
```

### AC-06 — evidence and handoff

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact changed files and SHA-256;
- before/after machine-readable outputs for F-01 and F-02;
- mapping AC-01 through AC-06;
- complete `EV-*` triplets for every validation command;
- explicit statement that no runtime/payment/network/environment/commit/push action occurred;
- workflow validator result with no `BLOCKING` finding.

## 4. Allowed scope

- `src/agentic_payment_experiment/webshop_payment_sidecar.py`
- `tests/test_webshop_payment_sidecar.py`
- `docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_BINDING_DUPLICATE_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_BINDING_DUPLICATE_REPAIR_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 5. Exclusions

- 不修改公共 API 名称或结果字段；
- 不修改 `__init__.py`；
- 不修改 Adapter、Runtime Gate、models 或共享 P1—P6/payment-domain 规则；
- 不开始 P9-C2、P9-D、P9-E；
- 不修改 UI、路线图或项目中控；
- 不运行 WebShop、Flask、浏览器或后台服务；
- 不调用网络、API、LLM、钱包或测试网；
- 不执行真实或模拟支付副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理或归档工作区其他继承改动。

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
| VP-01 | canonical Adapter/Gate projection | exact projection passes; mismatches fail closed | AC-01 |
| VP-02 | no-query successful known attempt | duplicate blocked, retry false | AC-02 |
| VP-03 | no-query unresolved known attempt | UNKNOWN/PENDING both blocked | AC-02 |
| VP-04 | unrelated known attempt | no false duplicate block | AC-02 |
| VP-05 | query recovery regression | existing recovery semantics unchanged | AC-03 |
| VP-06 | immutability and side-effect audit | no mutation or side effect | AC-04 |
| VP-07 | targeted/full/formal regressions | >21; >358; 13/13 | AC-05 |
| VP-08 | scope/hash/workflow | allowed scope only; validator no BLOCKING | AC-06 |

## 8. Stop conditions

Stop and report without broadening scope if:

- full Adapter/Gate binding cannot be expressed without changing Adapter or Runtime Gate;
- no-query duplicate detection would require changing shared recovery/idempotency modules;
- any required validation needs WebShop runtime, network, environment changes or payment execution;
- an unrelated inherited workspace change blocks objective verification.
