# Task Contract

Task ID: `P9-AUTHORITATIVE-TRACE-READ-MODEL-PLAYER-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Contract owner: Evaluator  
Contract state: `FROZEN`  
Frozen date: `2026-08-10`  
Baseline HEAD: `c18a24066973b3fb33742a0c5c59a0bd8a35e1ae`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-10-r13`  
Active bottleneck: `B-08`  
Hypothesis: `H-08`  
Measurement status: `measured`  
Metric baseline: `UI-ready representative families=0/4; Consumer-ready=4/4; Product Trace=9/12; GESR=8/12`  
Estimated affected scope: `4 representative families: T01/T02/T07/T10`  
Expected project impact: `UI-ready 0/4 -> 4/4 while Consumer-ready remains 4/4, Product Trace remains 9/12, GESR remains 8/12`  
Rollback condition: `any frozen source/UI/trace hash changes; Consumer-ready drops below 4/4; Product Trace or GESR regresses; forbidden side effect appears; or the Player requires family-specific/business/network execution`

```yaml
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-10-r13
active_bottleneck_id: B-08
hypothesis_id: H-08
```

### Project outcome

在本地、离线、可重置的实验边界内，让智能体购物与支付过程不仅能够生成机器可验证的权威轨迹，还能通过一个协议中立、只读、可回指证据的用户界面被普通用户逐步查看，而 UI 本身不重新执行购买、支付或业务判断。

### Current bottleneck

H-07 已独立复核通过：T01/T02/T07/T10 四个代表结构族可以由同一个 Authoritative Trace Consumer 转成 deterministic Read Model。

当前 B-08 的最早失败点已经下移为：

```text
VALID ProductAuthoritativeTrace
→ generic Consumer
→ deterministic Trace Read Model（4/4 已完成）
→ 用户可见 UI 尚未真正消费 Read Model（0/4）
```

本任务不再验证“能否读取轨迹”，而只验证“同一个 UI 数据契约能否正确展示四类 Read Model”。

## Frozen hypothesis

如果第一版轨迹播放器只消费 `Trace Read Model`，前端只接收该 Read Model 的 deterministic primitive/JSON，不直接解析 `ProductAuthoritativeTrace`、family 产品对象、日志或业务运行结果，那么 T01/T02/T07/T10 四个代表结构族都可以被同一个只读播放器正确展示，并且每个事件都能机械回指 source binding，而无需重新执行任何业务规则或副作用。

### Principal change

Exactly one principal change:

```text
Trace Read Model
→ generic read-only Trace Player HTML
```

本任务不得顺带改造现有 Interactive Lab、WebShop runtime、trace producer 或业务决策链。

## Frozen baseline

Observed repository HEAD at contract freeze:

```text
c18a24066973b3fb33742a0c5c59a0bd8a35e1ae
```

当前工作区包含上一任务已经 Evaluator `PASS / IMPROVED`、但尚未 commit 的 accepted snapshot。该 snapshot 是本任务的冻结前置，不得被本任务修改：

```text
src/agentic_payment_experiment/authoritative_trace_consumer.py
sha256 = 6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5

tests/test_authoritative_trace_consumer.py
sha256 = dfa4a7717020819c96fdc0c21a8c7e68a9aee043a4fb02932b4d8252026100fc
```

Existing UI files are also frozen and out of scope:

```text
src/agentic_payment_experiment/html_report.py
sha256 = b93aeb6f18b59bac195e624b7acf10c20e6ed46338796735a3bfc1017f93164a

src/agentic_payment_experiment/interactive_lab.py
sha256 = cb083a9fee9c21e5d87e49f097b1ce33d0546c1b0fb79bb59f7b5b7da6308150

src/agentic_payment_experiment/interactive_server.py
sha256 = d0be3aa65cca715845d3c41e38a75cb251764e2287cf49c3eb5efef1019b718f
```

Measured project baseline:

```text
Product Trace = 9/12
GESR = 8/12
callback count match = 12/12
duplicate / forbidden side effect = 0/12
Consumer-ready representative families = 4/4
UI-ready representative families = 0/4
formal entrypoint = 13/13 PASS
full unittest = 557/557 PASS
```

Representative families remain frozen as:

```text
T01 = Sidecar
T02 = Prepayment
T07 = Attack Overlay
T10 = Duplicate / Preflight
```

## Observable objective

Build one generic, deterministic, self-contained, read-only Trace Player that takes the accepted `AuthoritativeTraceReadModel` contract as its only product-data input and produces an HTML evidence player for all four representative families.

The player must make the following observable to a user without reconstructing business facts:

- trace metadata;
- exact event sequence;
- event type, entity type/role/ref;
- decision/status/reason codes already present in the Read Model;
- relations already present in the Read Model;
- `source_binding_ref` for the current event;
- the referenced source binding type/ref/schema/projection;
- previous / next / reset / play-pause controls;
- an explicit offline/read-only notice stating that playback does not execute WebShop, Buy Now or payment.

User-facing fixed labels should be Chinese-first; code identifiers and raw technical fields may remain English.

## Required production shape

Add exactly one new production module:

```text
src/agentic_payment_experiment/authoritative_trace_player.py
```

The production module may import only Python stdlib plus the accepted generic Consumer module. It must not import any family/profile producer or any business execution module.

Recommended public boundary:

```text
AuthoritativeTraceReadModel
→ trace_read_model_to_primitive(...)
→ build deterministic player payload
→ render self-contained HTML string/bytes
```

Exact public function names are implementation-owned, but tests must prove the boundary above.

### Frontend facts boundary

The browser-side script embedded in the returned HTML may see only the serialized Read Model payload. It must not contain hidden family fixtures, hard-coded T task data, reconstructed order/payment facts, or a second copy of business truth.

For user-supplied/read-model data:

- use DOM `textContent` or equivalent safe text insertion;
- do not inject Read Model strings through `innerHTML`;
- escape embedded JSON so values containing `</script>` cannot break the script boundary;
- no external JavaScript, CSS, fonts, images, APIs or CDN dependencies.

## Acceptance criteria

### AC-01 — Generic Read-Model-only production boundary

Production player must:

- accept the generic `AuthoritativeTraceReadModel` / its generic primitive only;
- have no literal T01/T02/T07/T10 handling branches;
- have no profile/family-specific imports or branches;
- not import `ProductAuthoritativeTrace` producers or WebShop/Attack Overlay toolkits;
- not call Policy, Lineage, validation, payment, runner or evaluator business logic.

Expected: static source audit passes.

### AC-02 — Same player supports all four representative families

For T01/T02/T07/T10:

```text
VALID ProductAuthoritativeTrace
→ accepted Consumer
→ AuthoritativeTraceReadModel
→ same Trace Player renderer
→ self-contained HTML
```

Expected:

```text
UI-ready representative families: 0/4 -> 4/4
```

No task/profile-specific rendering path is allowed.

### AC-03 — Exact payload preservation

For each representative family, extract the deterministic payload embedded in the generated HTML and compare it mechanically with `trace_read_model_to_primitive(read_model)`.

Must be exactly equal for:

- top-level metadata;
- event count and order;
- every event field;
- relations and relation assertions;
- source bindings;
- source binding projection values;
- reason codes.

The player may add UI-only state outside the source payload, but must not mutate or enrich the frozen evidence payload.

### AC-04 — Source binding drill-down is resolvable

Every event with `source_binding_ref` must resolve to exactly one source binding in the embedded payload.

The UI must expose the referenced binding's existing:

```text
binding_ref
source_object_type
source_object_ref
projection_schema
projection
```

No inferred or generated evidence value may be labeled as source evidence.

### AC-05 — Read-only playback controls

Generated HTML must contain deterministic, generic controls for:

```text
上一步
下一步
回到起点
自动播放 / 暂停
```

Controls may only change local playback index/state. They must not:

- mutate evidence payload;
- issue HTTP/fetch/XHR/WebSocket calls;
- call a backend evaluation endpoint;
- execute WebShop/Buy Now/payment/order/fulfilment actions.

Tests must statically prove the absence of network/business execution hooks in the player document.

### AC-06 — Deterministic rendering

For each T01/T02/T07/T10 Read Model:

- render the player 3 times;
- exact HTML bytes or a contract-defined canonical HTML SHA must be identical all 3 times;
- embedded payload SHA must be identical all 3 times.

No timestamps, random IDs, object repr, environment-specific paths or runtime-generated values may enter the player output.

### AC-07 — Fail closed at player boundary

Wrong input types or missing/invalid Read Model objects must not produce a normal evidence player.

Player must raise a deterministic local error or return an explicit rejected result; it must not fabricate missing events/source bindings or silently fall back to mock data.

This is a structural UI boundary only. Do not add a second business validator.

### AC-08 — Safe evidence rendering

Dedicated tests must include at least one Read Model-compatible hostile display string containing HTML/script-like text and prove:

- payload round-trips exactly;
- generated HTML keeps the script boundary intact;
- frontend rendering uses safe text insertion for evidence values;
- hostile display text is not interpreted as executable markup.

Do not modify the source trace producer merely to create this test; use a read-model-level frozen test object or structurally valid local test value.

### AC-09 — Existing capability and measurement invariance

After implementation:

```text
Consumer-ready representative families = 4/4
Product Trace = 9/12
GESR = 8/12
callback count match = 12/12
duplicate / forbidden side effect = 0/12
formal entrypoint = 13/13 PASS
```

Also prove:

- accepted Consumer source/test hashes unchanged;
- existing task-start source files unchanged;
- accepted product trace hashes unchanged;
- project-impact repeat=3 remains stable.

### AC-10 — Test and workflow gate

Required minimums:

```text
new player dedicated tests >= 14, all pass
existing consumer suite = 19/19 PASS
project-impact suite = 21/21 PASS
full unittest >= 570, all pass
formal entrypoint = 13/13 PASS
workflow validator = OK
```

## Impact comparison

```text
Before
UI-ready representative families = 0/4
Consumer-ready representative families = 4/4
Product Trace = 9/12
GESR = 8/12

Expected After
UI-ready representative families = 4/4
Consumer-ready representative families = 4/4
Product Trace = 9/12
GESR = 8/12
```

Project impact may be `IMPROVED` only if all four representative Read Models use the same generic player and every product/measurement guardrail remains frozen.

A visually attractive page alone is not measurable project gain if it consumes mock/manual data or bypasses the accepted Read Model.

## Allowed scope

May change only:

- `src/agentic_payment_experiment/authoritative_trace_player.py` (new);
- `tests/test_authoritative_trace_player.py` (new);
- this task `REPORT.md`;
- this task `evidence/EV-*`;
- `CURRENT.md` only `CONTRACT_FROZEN -> EXECUTING` after implementation begins.

Task evidence may include generated HTML/JSON samples under this task's `evidence/` directory.

## Exclusions

Do not modify:

- `src/agentic_payment_experiment/authoritative_trace_consumer.py`;
- `src/agentic_payment_experiment/authoritative_trace.py`;
- any trace assembler/producer/profile/family toolkit;
- `src/agentic_payment_experiment/html_report.py`;
- `src/agentic_payment_experiment/interactive_lab.py`;
- `src/agentic_payment_experiment/interactive_server.py`;
- `__init__.py` merely to export the player;
- fixture, runner, registry or project-impact measurement code;
- existing accepted task artifacts.

Also excluded:

- no T05/T06/T11 trace work;
- no WebShop search/click/product-selection journey integration yet;
- no autonomous Agent work;
- no browser automation;
- no WebShop runtime execution;
- no Buy Now;
- no payment/order/wallet/fulfilment/callback side effects;
- no network/API call;
- no dependency installation or environment creation;
- no LLM-generated explanation;
- no commit, push, reset, clean or history rewrite.

## Authorization

```yaml
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_network_call: false
authorization_data_download: false
authorization_dependency_install: false
authorization_create_environment: false
authorization_webshop_runtime_execution: false
authorization_buy_now_execution: false
authorization_payment_or_order_side_effect: false
```

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | freeze task-start accepted Consumer/UI hashes and existing src manifest | accepted prior snapshot reproducible |
| VP-02 | dedicated T01/T02/T07/T10 player positive tests | one generic renderer, UI-ready 4/4 |
| VP-03 | embedded payload vs `trace_read_model_to_primitive()` exact comparison | exact equality |
| VP-04 | source-binding resolution / relations audit | every displayed ref resolvable, no synthesized evidence |
| VP-05 | player render repeat=3 per family | stable HTML and payload SHA |
| VP-06 | hostile display-string / script-boundary tests | safe deterministic text rendering |
| VP-07 | static import/call/network audit | no family/business/network/browser-runtime behavior |
| VP-08 | existing Consumer suite | 19/19 |
| VP-09 | project-impact suite + repeat=3 | 21/21; Product Trace 9/12; GESR 8/12 |
| VP-10 | formal entrypoint | 13/13 |
| VP-11 | full regression | >=570, all pass |
| VP-12 | workflow validator | OK |

## Stop conditions

Stop and submit `BLOCKED` rather than expanding scope if:

- the UI cannot render the four representative Read Models without family-specific knowledge;
- the accepted Read Model lacks evidence required by this frozen minimal player contract;
- existing Consumer or trace producer semantics must change;
- existing `html_report.py` / Interactive Lab must change to prove this first slice;
- player requires task ID/profile hard-coding;
- exact payload/source-binding equality cannot be preserved;
- Product Trace/GESR/old trace hashes move;
- full regression fails;
- browser/network/WebShop execution appears necessary.

## Required report

`REPORT.md` must include:

- exact new files and SHA-256;
- task-start accepted snapshot hashes and current comparison;
- public player boundary;
- 4/4 representative UI-ready evidence;
- exact embedded payload equality evidence;
- source-binding drill-down evidence;
- deterministic HTML/payload SHA x3 for each representative family;
- safe hostile-string rendering evidence;
- static no-family/no-business/no-network audit;
- unchanged Consumer/Product Trace/GESR/non-trace/old trace hashes;
- dedicated/full/formal test counts;
- workflow validator result;
- `project_impact_candidate: IMPROVED` only if UI-ready reaches 4/4 with every guardrail unchanged.

Executor must save raw command triplets as `EV-*` under this task `evidence/` directory and submit with `Executor status: SUBMITTED_FOR_REVIEW`. `CURRENT.md` remains Executor-owned `EXECUTING` until Evaluator accepts the snapshot.

## Amendments

- `2026-08-10` Evaluator governance-only normalization after Executor `EV-11` exposed validator incompatibility: renamed the strategic section to the v2.1 machine-readable heading and added `Baseline HEAD / Project map / Map revision / Active bottleneck / Hypothesis / Measurement status / Metric baseline / Estimated affected scope / Expected project impact / Rollback condition` labels. These labels restate facts and thresholds already frozen elsewhere in this contract; objective, hypothesis semantics, principal change, ACs, allowed scope, exclusions, validation thresholds, authorization, and product implementation are unchanged.
