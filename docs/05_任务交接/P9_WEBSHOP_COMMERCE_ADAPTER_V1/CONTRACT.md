# Task Contract

Task ID: `P9-WEBSHOP-COMMERCE-ADAPTER-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P9-A2 已由独立评估者裁决 `PASS`：

```text
固定 WebShop commit: 64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd
独立环境: webshop38 / Python 3.8.13 / OpenJDK 11
small runtime: reset → search → product click → pre-Buy-Now → reset
buy_now_available: true
buy_now_executed: false
```

P9-A2 只证明外部运行时和购买动作前接点稳定，不证明：

- WebShop human instruction 与当前选中商品匹配；
- human instruction 已形成授权 mandate；
- WebShop reward 是支付安全结论；
- 到达 Buy Now 等于允许购买；
- 支付项目已经接入 WebShop。

路线图下一步是 P9-B1：先做 Commerce Adapter，把外部商城事实转换为现有协议中立对象；P9-B2 才负责 Buy Now 拦截与 Runtime Authorization Gate。

Primary references:

- `docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/REVIEW.md`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`
- `src/agentic_payment_experiment/models.py`
- `src/agentic_payment_experiment/adapters/acp.py`
- `src/agentic_payment_experiment/adapters/ap2.py`
- `docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/evidence/rv_webshop_small_smoke.json`

## 2. Single objective

Create one deterministic, offline WebShop Commerce Adapter that converts a minimal pre-Buy-Now WebShop snapshot into:

```text
human instruction text
+ selected product / options / price
+ explicit experiment context
        ↓
WebShopCommerceAdaptation
        ├─ user_intent_text
        ├─ Order
        ├─ TransactionRequest
        ├─ source/provenance metadata
        ├─ missing_fields
        ├─ unmapped_fields
        └─ limitations
```

The adapter must use the existing protocol-neutral `Order`, `OrderItem` and `TransactionRequest` models. It must not execute WebShop, intercept Buy Now, call authorization policy, or perform payment.

## 3. Acceptance criteria

### AC-01 — minimal, traceable pre-Buy-Now fixture

Create exactly one small committed fixture:

```text
samples/external/webshop/pre_buy_now_candidate_v1.json
```

It must be reproducibly derived from the P9-A2 local evidence and fixed WebShop data, using a tracked export helper. The fixture must contain only the facts required for adapter tests:

- fixture schema/version;
- fixed WebShop commit;
- source asset hashes;
- source smoke-result hash;
- session/task identifier;
- original `instruction_text` kept verbatim as data;
- executed actions up to, but excluding, `click[buy now]`;
- `buy_now_available == true`;
- `buy_now_executed == false`;
- selected ASIN, title, selected options and quantity;
- exact unit price and order total as decimal-safe strings;
- explicit `experiment_context` for fields WebShop does not natively establish: merchant, payee, category, currency, quote expiry, fulfilment terms, mandate reference, authority version and request timestamp.

Rules:

- the export helper may read only the existing local P9-A2 evidence and the three approved small data files;
- no WebShop environment step, network call or download is allowed;
- do not copy the 1,000-product file, index or human-goal dataset into `samples/`;
- the committed fixture must contain one product candidate only;
- context bridge fields must be clearly labeled as experiment context, not as WebShop-verified facts.

### AC-02 — protocol-neutral adapter output

Implement:

```python
adapt_webshop_purchase_candidate(snapshot) -> WebShopCommerceAdaptation
```

The adaptation result must be an immutable dataclass and expose at least:

```text
user_intent_text: str | None
order: Order | None
payment_request: TransactionRequest | None
source_commit: str
missing_fields: tuple[str, ...]
unmapped_fields: tuple[str, ...]
limitations: tuple[str, ...]
ready: bool
```

Required mappings:

```text
instruction_text                  -> user_intent_text only
asin + title + category           -> OrderItem
selected_options                  -> preserved deterministically in item name or explicit adapter metadata
quantity × unit_price             -> Order.total_amount
merchant / payee / currency       -> Order and TransactionRequest
session + asin + fixture version  -> deterministic order_id / request_id
Order.order_id                    -> TransactionRequest.order_ref
Order.total_amount                -> TransactionRequest.amount
Order.currency                    -> TransactionRequest.currency
Order.merchant                    -> TransactionRequest.merchant
Order.payee                        -> TransactionRequest.payee
mandate_ref                        -> Order.mandate_ref and TransactionRequest.authority_ref
```

Decimal rules:

- parse prices through `Decimal` from strings, never binary float arithmetic;
- quantity must be a positive integer;
- computed total must equal the fixture total exactly;
- preserve uppercase currency.

No change to `models.py` is allowed. If the existing neutral models cannot represent the required mapping without semantic distortion, stop and report rather than modifying the model layer.

### AC-03 — preserve semantic separation

The adapter must not convert or infer:

```text
instruction_text -> IntentMandate
WebShop reward -> Decision
buy_now_available -> ALLOW
selected product -> instruction satisfied
experiment merchant/payee -> externally verified identity
```

`limitations` must include at least:

- `instruction_product_match_not_assessed`;
- `instruction_is_not_authorization_mandate`;
- `merchant_and_payee_from_experiment_context`;
- `no_runtime_authorization_decision`;
- `no_purchase_or_payment_executed`.

The happy-path fixture is allowed to contain an instruction and product that are semantically unrelated. The adapter must faithfully preserve both and must not claim alignment.

### AC-04 — fail-closed validation

The adaptation must return `ready == false`, with no `Order` and no `TransactionRequest`, for at least:

1. missing or empty instruction;
2. missing ASIN/title/price/currency/context bridge;
3. malformed or negative price;
4. zero, negative or non-integer quantity;
5. total inconsistent with quantity × unit price;
6. missing `selected_options` field, while an explicitly empty mapping is allowed;
7. source commit not equal to `64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`;
8. mutable or missing source provenance;
9. `buy_now_available != true`;
10. `buy_now_executed != false`;
11. action sequence contains `click[buy now]`;
12. order/request binding fields cannot be made identical.

Unknown top-level fields must be reported in `unmapped_fields`, not silently treated as trusted facts.

### AC-05 — side-effect and dependency boundary

The production adapter must:

- import only main-project modules and Python standard-library modules;
- not import `gym`, `web_agent_site`, `pyserini`, spaCy, Torch or the WebShop checkout;
- not read files, write files, call network, spawn processes or access environment variables;
- not call policy evaluation, payment execution, recovery, fulfilment or UI code;
- not execute or construct an executable `click[buy now]` call;
- be deterministic for the same input mapping.

The export helper is validation tooling only and must not be imported by product code.

### AC-06 — tests and regressions

Add deterministic offline tests covering:

- one full happy-path mapping from the committed fixture;
- deterministic IDs and Decimal totals;
- exact Order ↔ TransactionRequest bindings;
- all AC-03 semantic limitations;
- every AC-04 fail-closed case;
- unknown-field reporting;
- adapter has no network/WebShop/payment side effects;
- repeated adaptation produces equal immutable results.

Required regressions:

```text
python3 -m unittest tests.test_webshop_adapter -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Full suite count must be at least the current 302-test baseline plus the new WebShop adapter tests.

### AC-07 — roadmap and handoff consistency

Update only factual status lines to show:

```text
P9-A1 source preflight                         PASS
P9-A2 isolated small runtime                  PASS
P9-B1 Commerce Adapter                        this task / READY_FOR_REVIEW
P9-B2 Buy Now interception + authorization    not started
P9-C payment / fulfilment sidecar             not started
```

The report must explicitly state that P9-B1 is an offline mapping layer and that WebShop has still not executed a purchase or entered payment flow.

## 4. Allowed scope

- `src/agentic_payment_experiment/adapters/webshop.py`
- `src/agentic_payment_experiment/adapters/__init__.py`
- `scripts/validation/webshop/export_webshop_commerce_fixture.py`
- `samples/external/webshop/pre_buy_now_candidate_v1.json`
- `tests/test_webshop_adapter.py`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`（only factual P9-B1 status/boundary update）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（only factual P9-B1 status/boundary update）
- `docs/05_任务交接/P9_WEBSHOP_COMMERCE_ADAPTER_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_COMMERCE_ADAPTER_V1/evidence/EV-*`
- `CURRENT.md` only for atomic review handoff

No other tracked path is allowed.

## 5. Exclusions

- 不修改 `models.py`、runner、UI、HTML 报告、现有 ACP/AP2/x402 adapter 或 P1—P6 逻辑；
- 不修改固定 WebShop checkout 或 P9-A2 runtime/data/index；
- 不运行 WebShop 环境、Flask、浏览器、ChromeDriver 或后台服务；
- 不执行 `click[buy now]`，不调用 `SimServer.done()`；
- 不实现 P9-B2 拦截器、Runtime Authorization Gate、支付或履约；
- 不把 `instruction_text` 变成 `IntentMandate`，不产生 `ALLOW/DENY`；
- 不下载数据，不调用网络/API/LLM/测试网/钱包；
- 不修改 Conda 环境或安装依赖；
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
| VP-01 | Run fixture export helper against fixed P9-A2 local evidence; verify fixture hash, one-item scope and provenance | Deterministic minimal fixture; no runtime/network | AC-01 |
| VP-02 | Happy-path adapter test and machine-readable mapping dump | `ready=true`; `Order` and `TransactionRequest` consistent | AC-02 |
| VP-03 | Semantic-separation assertions | No mandate, reward decision, alignment or authorization inference | AC-03 |
| VP-04 | Negative/fail-closed test matrix | Every invalid case returns no neutral objects | AC-04 |
| VP-05 | Static import/side-effect audit | No WebShop/network/payment/runtime dependency in adapter | AC-05 |
| VP-06 | `python3 -m unittest tests.test_webshop_adapter -v` | All adapter tests pass | AC-02—AC-05 |
| VP-07 | Full unittest and `run_experiment.py` | Full suite ≥302 + new tests; 13/13 entrypoint remains green | AC-06 |
| VP-08 | Task-scoped Git/diff/hash and workflow validation | No scope creep, no commit/push, no `BLOCKING` | AC-07 |

## 8. Required evidence

For every VP, save complete triplets:

```text
EV-xx.meta.json
EV-xx.stdout.log
EV-xx.stderr.log
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- fixture path, SHA-256, source smoke hash and fixed WebShop commit;
- exact mapping table into `Order` and `TransactionRequest`;
- happy-path machine-readable output;
- every negative case and its `missing_fields`/failure result;
- static side-effect/import audit;
- exact changed files and SHA-256;
- full test count and `run_experiment.py` result;
- explicit statement that no WebShop runtime, Buy Now action, authorization decision, payment, network, API, environment change, commit or push occurred;
- AC-01 through AC-07 and VP-01 through VP-08 mappings.

## 9. Stop conditions

Stop and report without broadening scope if:

- required mapping needs a change to `models.py`;
- product code would need to import WebShop or read the local checkout;
- fixture cannot be derived without copying bulk data;
- price/currency/title/ASIN cannot be obtained as explicit source or experiment-context fields;
- adapter would need to infer user authorization, product-goal match or merchant identity;
- any test requires network, `webshop38`, WebShop runtime or Buy Now execution;
- existing full regression fails because of this task;
- any file outside allowed scope must change.

## 10. Atomic handoff

Do not request review until:

1. all VP evidence triplets exist and are truthful;
2. every AC maps to evidence;
3. `executor_state: READY_FOR_REVIEW` is declared;
4. adapter tests, full tests and `run_experiment.py` pass;
5. workflow validator reports no `BLOCKING` finding;
6. `CURRENT.md` is routed to `READY_FOR_REVIEW / Evaluator` only after the complete package exists.
