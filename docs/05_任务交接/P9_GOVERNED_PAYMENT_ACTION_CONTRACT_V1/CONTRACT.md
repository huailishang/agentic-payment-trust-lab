# Task Contract

Task ID: `P9-GOVERNED-PAYMENT-ACTION-CONTRACT-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P9-C1 支付与履约 Sidecar 已通过，P9-C2 的结账快照连续性切片也已通过。

当前 Runtime Gate 已能检查：

```text
P1 授权与订单变化
P2 Order → Request → Execution 绑定
P3 Agent / Executor 身份
P4 Context Policy / current_action
```

但“Agent 准备执行什么动作”仍分散在：

```text
current_action = "execute_payment"
declared_agent_id
current_executor_instance_ref
mandate / order / request / payment references
```

这些字段由多个参数分别传入，没有形成一个可记录、可验证、可进入后续权威轨迹的动作对象。

`docs/reference/03_身份与治理/ArbiterOS治理机制与项目吸收方案_20260802.md` 已声明下一步为：

```text
P9-C2-A 支付动作契约
→ P9-C2-B Source Lineage / Taint Propagation
→ P9-C2-C 外部异常与提示注入组合测试
```

本任务只完成第一个最小动作类型：`EXECUTE_PAYMENT`，并让 WebShop Runtime Gate 成为第一个真实消费者。

## 2. Single objective

Create one immutable, protocol-neutral governed payment action contract and verifier so that:

```text
Agent / WebShop intends to execute payment
        ↓
GovernedPaymentAction
        ↓
verify action type + authority + order + request + payment + agent + executor + context action
        ↓
only a valid action contract may continue through existing P2—P4 and the injected callback
```

The contract describes and binds an intended action. It must never execute the action.

## 3. Required domain contract

Implement immutable types equivalent to:

```python
class GovernedActionType(str, Enum):
    EXECUTE_PAYMENT = "execute_payment"


class SideEffectClass(str, Enum):
    PAYMENT_EXECUTION = "PAYMENT_EXECUTION"


class ActionReversibility(str, Enum):
    COMPENSATABLE_NOT_REVERSIBLE = "COMPENSATABLE_NOT_REVERSIBLE"


@dataclass(frozen=True)
class GovernedPaymentAction:
    action_id: str
    action_type: GovernedActionType
    subject_ref: str
    agent_ref: str
    executor_ref: str
    authority_ref: str
    authority_version: str
    order_ref: str
    order_version: str
    request_ref: str
    payment_ref: str
    source_refs: tuple[str, ...]
    side_effect_class: SideEffectClass
    reversibility: ActionReversibility
    occurred_at: datetime

    def to_dict(self) -> dict[str, object]: ...
```

Exact internal names may differ, but the observable contract must contain the same governance information.

Version 1 must not add speculative action types. Only `EXECUTE_PAYMENT` is in scope.

## 4. Required verification result

Implement an immutable verification fact equivalent to:

```python
@dataclass(frozen=True)
class GovernedActionBindingFact:
    status: VerificationStatus
    action_id: str | None
    reason_codes: tuple[str, ...]
    checked_action_type: str | None
    checked_order_ref: str | None
    checked_request_ref: str | None
    checked_payment_ref: str | None

    def to_dict(self) -> dict[str, object]: ...
```

And one pure verifier equivalent to:

```python
def verify_governed_payment_action(
    action,
    *,
    mandate,
    order,
    request,
    execution,
    agent_identity,
    current_executor_instance_ref,
    context_policy_fact,
) -> GovernedActionBindingFact:
    ...
```

The verifier only classifies evidence. It must not call a callback, payment function, network, file or environment API.

## 5. Acceptance criteria

### AC-01 — immutable and primitive-only action contract

`GovernedPaymentAction` and its verification fact must be frozen dataclasses or equivalent immutable objects.

`to_dict()` must contain only:

```text
null / string / number / boolean / list / dict
```

Datetime values must be stable ISO-8601 strings; enums must use stable values; `source_refs` must serialize as a list.

The action object must not contain natural-language instructions, executable functions, arbitrary tool arguments or mutable dictionaries.

### AC-02 — mandatory evidence and exact action semantics

The verifier must fail closed when any mandatory field is missing, blank or has an invalid enum/type.

A valid v1 action must satisfy:

```text
action_type      = EXECUTE_PAYMENT
side_effect_class = PAYMENT_EXECUTION
reversibility     = COMPENSATABLE_NOT_REVERSIBLE
source_refs       = at least one nonblank explicit reference
```

Missing evidence returns `VerificationStatus.MISSING_EVIDENCE` with stable reason codes. Invalid or unsupported values return `VerificationStatus.INVALID`.

Do not silently coerce arbitrary strings into trusted enums.

### AC-03 — authority and subject binding

Verify:

```text
subject_ref       == mandate.user_id
authority_ref     == mandate.mandate_id
authority_version == mandate.authority_version
```

Any mismatch must be `INVALID` with separate stable reasons for subject, authority and authority-version mismatch.

The action contract does not expand or replace the mandate.

### AC-04 — order, request and payment binding

Verify:

```text
order_ref     == order.order_id
order_version == order.order_version
request_ref   == request.request_id
payment_ref   == execution.payment_id
```

Also require the supplied request and execution to remain the existing continuous chain:

```text
execution.request_id == request.request_id
execution.order_id   == order.order_id
```

The verifier may reuse existing binding helpers. It must not duplicate or weaken P2 business rules.

At minimum test independent mismatches for order ref, order version, request ref and payment ref.

### AC-05 — Agent, executor and context-action binding

Verify:

```text
action.agent_ref    == request.agent_id
                    == mandate.expected_agent_id
                    == agent_identity.agent_id

action.executor_ref == current_executor_instance_ref
                    == agent_identity.executor_instance_id

action.action_type.value == context_policy_fact.current_action
```

At minimum test:

- action Agent mismatch;
- action executor mismatch;
- current executor mismatch;
- context `current_action` mismatch;
- missing Agent or executor evidence.

A valid action contract cannot repair or override an invalid P3/P4 fact.

### AC-06 — temporal and identity boundaries

Require:

```text
request.occurred_at <= action.occurred_at <= execution.occurred_at
```

Reject an action recorded before the request or after the execution candidate.

`action_id` must be nonblank and must not equal the order, request or payment identifier.

Duplicate detection across multiple actions is not in scope; only local identity collision is required.

### AC-07 — WebShop Runtime Gate consumer

Extend `gate_webshop_buy_now(...)` with one optional keyword-only input equivalent to:

```python
governed_action: GovernedPaymentAction | None = None
```

Backward compatibility:

- when omitted, all existing Runtime Gate decisions and callback counts remain unchanged;
- no existing caller is forced to construct the action contract in this task.

When supplied:

1. run the existing prepayment/order-continuity check;
2. verify the governed action before the existing controlled callback;
3. preserve the action binding fact in `WebShopBuyNowGateOutcome` or an equivalent structured field;
4. `VALID` continues to existing P2—P4;
5. `MISSING_EVIDENCE` produces `INDETERMINATE`, zero callback;
6. `INVALID` produces `DENY`, zero callback;
7. reason codes are prefixed or otherwise namespaced as stable action-contract reasons.

A supplied invalid action must never be ignored or replaced by values reconstructed from other inputs.

### AC-08 — valid action does not replace P1—P4

With an otherwise valid `GovernedPaymentAction`:

```text
P1/order continuity failure → existing non-ALLOW, zero callback
P2 binding mismatch         → existing DENY, zero callback
P3 identity mismatch        → existing DENY/INDETERMINATE, zero callback
P4 context mismatch         → existing DENY/INDETERMINATE, zero callback
all checks valid            → ALLOW, exactly one injected callback
```

The action contract is a new governed intent boundary, not a substitute for existing business and trust facts.

### AC-09 — machine-readable action matrix

Add a deterministic offline matrix covering at least:

```text
valid_execute_payment
missing_action_id
unsupported_action_type_or_invalid_type
subject_mismatch
authority_mismatch
authority_version_mismatch
order_ref_mismatch
order_version_mismatch
request_ref_mismatch
payment_ref_mismatch
agent_mismatch
executor_mismatch
context_action_mismatch
action_before_request
action_after_execution
identifier_collision
```

Each case must expose:

- expected and actual verification status;
- expected and actual gate decision when consumed by WebShop;
- callback count;
- reason codes;
- action/order/request/payment references;
- explicit `no_real_buy_now` and `no_real_payment` limitations.

Do not execute WebShop or payment.

### AC-10 — side-effect, scope and regressions

Production code must import only main-project modules and Python standard library. It must not:

- parse natural language into an action;
- execute a callback from the verifier;
- read/write files, call network, spawn processes or access environment variables;
- run WebShop, Buy Now, payment, retry, query, fulfilment, refund or dispute;
- modify mandate, order, request, execution, identity, context or action inputs;
- implement Source Lineage / Taint Propagation;
- modify existing P1—P6 decision rules.

Required commands:

```text
python3 -m unittest tests.trusted_execution.test_governed_action -v
python3 -m unittest tests.test_webshop_runtime_gate -v
python3 -m unittest tests.trusted_execution.test_payment_binding tests.trusted_execution.test_context_policy -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Expected:

```text
governed-action tests all PASS
Runtime Gate tests > 23 and all PASS
full suite > 375 and all PASS
formal entrypoint 13/13 PASS
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact public contract and verifier API;
- exact WebShop consumer behavior;
- action matrix output;
- valid action + P1—P4 regression results;
- primitive-only serialization example;
- exact changed files and SHA-256;
- complete EV triplets and AC-01 through AC-10 mapping;
- explicit no-WebShop/no-Buy-Now/no-payment/no-network/no-environment/no-commit/no-push statement;
- workflow validator with no `BLOCKING` finding.

## 6. Allowed scope

- `src/agentic_payment_experiment/trusted_execution/governed_action.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`（only export new API）
- `src/agentic_payment_experiment/__init__.py`（only export new public API）
- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `tests/trusted_execution/test_governed_action.py`
- `tests/test_webshop_runtime_gate.py`
- `samples/external/webshop/governed_payment_action_matrix_v1.json`（optional matrix specification）
- `scripts/validation/webshop/run_governed_payment_action_matrix.py`（optional deterministic runner）
- `docs/reference/03_身份与治理/ArbiterOS治理机制与项目吸收方案_20260802.md`（factual status only）
- `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md`（factual status only）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（factual status only）
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/REPORT.md`
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 7. Exclusions

- 不修改 `models.py`；
- 不修改 `validator.py`、`order_validation.py`、`payment_execution.py`、P1—P6 共享规则；
- 不实现 OBSERVE、SEARCH、退款、争议等其他动作类型；
- 不实现 FactLineage、DerivedFact、taint propagation 或 trust upgrade；
- 不实现页面提示注入组合测试；
- 不修改 UI、M5 或 Replay；
- 不执行 WebShop、真实 Buy Now、支付、状态查询、履约、退款或争议；
- 不调用网络、API、LLM、钱包或测试网；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理工作区继承改动。

## 8. Authorization

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

## 9. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | action contract immutability and serialization | frozen; primitive-only stable output | AC-01 |
| VP-02 | mandatory fields and enums | missing → MISSING_EVIDENCE; invalid → INVALID | AC-02 |
| VP-03 | subject/authority binding | exact refs required | AC-03 |
| VP-04 | order/request/payment binding | exact refs and existing chain preserved | AC-04 |
| VP-05 | Agent/executor/context action binding | exact P3/P4-related refs required | AC-05 |
| VP-06 | temporal and identifier boundaries | before/after/collision invalid | AC-06 |
| VP-07 | WebShop consumer | valid continues; invalid/missing zero callback | AC-07 |
| VP-08 | valid action + P1—P4 regressions | action does not replace existing gates | AC-08 |
| VP-09 | machine-readable action matrix | stable status/decision/callback/reasons/refs | AC-09 |
| VP-10 | side-effect/scope/full regression/workflow | no external action; all tests pass; validator no BLOCKING | AC-10 |

## 10. Stop conditions

Stop and report without broadening scope if:

- a useful action contract requires modifying `models.py` or existing P1—P6 rules;
- WebShop cannot consume the action contract without breaking old callers;
- action verification would need natural-language parsing, Source Lineage or policy redesign;
- a validation requires WebShop runtime, network, environment changes or payment execution;
- unrelated inherited workspace changes prevent objective verification.
