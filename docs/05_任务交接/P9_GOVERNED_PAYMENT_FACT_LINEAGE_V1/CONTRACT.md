# Task Contract

Task ID: `P9-GOVERNED-PAYMENT-FACT-LINEAGE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

支付动作契约和外层类型边界已通过。当前项目已有 `SourceType`，能够说明一个事实直接来自用户、协议、商户、网页、LLM 或外部工具，但仍不能表达：

```text
网页价格 WEB_UNTRUSTED
        ↓ Agent 摘要
LLM_GENERATED
        ↓ 形成候选支付金额
最终金额依赖了哪些上游来源
```

当前缺口不是再增加一个来源标签，而是保留完整的事实来源链，防止经过 Agent 或 LLM 转换后，上游不可信来源静默消失。

本任务对应 P9-C2-B，只建立最小 Fact Lineage / Source Propagation 能力，并让现有不可信输入覆盖测试成为第一个消费者。

## 2. Single objective

Create one immutable, protocol-neutral fact-lineage graph and deterministic resolver so that every derived payment fact retains all direct and upstream source types:

```text
direct fact sources
+ upstream fact references
+ transformation reference
        ↓
resolved lineage
        ↓
effective source-type set
+ untrusted ancestry indicator
+ stable verification reasons
```

This task records provenance. It does not by itself authorize payment or replace existing P1—P4 policy decisions.

## 3. Required domain contract

Implement immutable types equivalent to:

```python
@dataclass(frozen=True)
class FactLineageNode:
    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None = None
    trust_upgrade_evidence_ref: str | None = None

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class ResolvedFactLineage:
    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    effective_source_types: tuple[SourceType, ...]
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None
    trust_upgrade_evidence_ref: str | None
    contains_untrusted_ancestry: bool

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class FactLineageResult:
    status: VerificationStatus
    reason_codes: tuple[str, ...]
    resolved_facts: tuple[ResolvedFactLineage, ...]
    unresolved_fact_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]: ...
```

Exact names may differ, but observable information and behavior must be equivalent.

## 4. Acceptance criteria

### AC-01 — immutable, exact-type and primitive-only contracts

All public lineage objects must be frozen dataclasses or equivalent immutable objects.

The resolver must accept only exact `FactLineageNode` objects. Dictionary, list, string, mutable lookalike, proxy and subclass inputs must return a stable `INVALID` result without attribute access or exception.

`to_dict()` output must contain only null, string, number, boolean, list and dictionary values. Enums use stable values and tuples serialize as lists.

### AC-02 — mandatory fields and stable identity

Each node requires nonblank:

```text
fact_ref
fact_path
value_digest
```

`direct_source_type` must be an exact `SourceType`, not an arbitrary string silently converted into an enum.

`upstream_fact_refs` must be an exact tuple of unique, nonblank strings. A node cannot reference itself.

Missing required evidence returns `MISSING_EVIDENCE`; invalid object or field types return `INVALID`, with stable reason codes.

### AC-03 — graph integrity

The resolver must deterministically detect:

- duplicate `fact_ref` values;
- missing upstream references;
- direct self-reference;
- multi-node cycles;
- duplicate upstream references;
- invalid transformation or upgrade-evidence references.

Expected classification:

```text
missing upstream node → MISSING_EVIDENCE
cycle / duplicate / invalid structure → INVALID
```

No recursion error or partial silent resolution is allowed.

### AC-04 — source propagation preserves every ancestor

For a root node:

```text
effective_source_types = {direct_source_type}
```

For a derived node:

```text
effective_source_types
= direct_source_type
+ union(all upstream effective_source_types)
```

The output order must be deterministic.

At minimum prove:

```text
WEB_UNTRUSTED
→ LLM_GENERATED summary
→ effective contains WEB_UNTRUSTED + LLM_GENERATED
```

and:

```text
USER_CONFIRMED + WEB_UNTRUSTED
→ derived fact
→ effective contains both sources
```

No transformation may remove an upstream source type.

### AC-05 — no silent trust upgrade

`trust_upgrade_evidence_ref` may be recorded as evidence, but V1 must not erase ancestry or rewrite effective source types.

At minimum prove:

```text
upstream = WEB_UNTRUSTED
direct node label = USER_CONFIRMED
trust_upgrade_evidence_ref present or absent
→ effective sources still contain WEB_UNTRUSTED
```

The resolver is a provenance engine, not a business authorization engine. It must not convert a lineage into ALLOW/DENY by itself.

### AC-06 — untrusted ancestry classification

`contains_untrusted_ancestry` must be true when any effective source is one of:

```text
AGENT_INFERRED
EXTERNAL_TOOL_UNTRUSTED
WEB_UNTRUSTED
LLM_GENERATED
```

It must remain false for a root or derived chain composed only of:

```text
USER_CONFIRMED
SYSTEM_POLICY
MERCHANT_PROVIDED
PROTOCOL_VERIFIED
PAYMENT_PROVIDER_OBSERVED
```

`AGENT_DECLARED` must be preserved as a source but must not be silently classified as authoritative. Its exact ancestry classification must be explicitly documented and tested.

### AC-07 — existing untrusted-input overlay becomes first consumer

Extend the existing offline untrusted-input overlay result with structured lineage facts for each proposed override.

For every override path, the consumer must expose at least:

```text
fact_ref
fact_path
value_digest
direct_source_type
effective_source_types
contains_untrusted_ancestry
source_ref
```

The consumer must use the shared lineage resolver. It must not implement a second propagation algorithm.

Existing overlay policy behavior must remain unchanged:

- no trusted-state mutation from blocked untrusted writes;
- no decision drift;
- existing reason codes and pass/fail results preserved;
- lineage is additional evidence, not a replacement for Context Policy.

### AC-08 — deterministic lineage matrix

Add a machine-readable offline matrix covering at least:

```text
root_user_confirmed
root_web_untrusted
web_to_llm_summary
multi_source_user_and_web
claimed_user_confirmation_with_web_ancestor
claimed_upgrade_with_evidence_and_web_ancestor
missing_upstream
self_reference
multi_node_cycle
duplicate_fact_ref
duplicate_upstream_ref
invalid_direct_source_type
mutable_lookalike_node
serialized_dict_node
overlay_untrusted_amount_override
overlay_untrusted_payee_override
```

Each case must expose expected/actual status, effective source types, untrusted ancestry, reason codes, resolved/unresolved refs and explicit no-LLM/no-network/no-payment limitations.

### AC-09 — side-effect and scope boundary

Production lineage code must not:

- call an LLM, network, file, process or environment API;
- parse natural language into facts or actions;
- modify input nodes or trusted state;
- execute WebShop, Buy Now, payment, query, fulfilment, refund or dispute;
- change P1—P6, Context Policy, order rules or payment lifecycle decisions;
- implement prompt-injection success measurement or UI.

The existing overlay report writer may continue writing its explicit report file; the pure lineage resolver itself must have no I/O.

### AC-10 — regressions and evidence

Required commands:

```text
python3 -m unittest tests.trusted_execution.test_fact_lineage -v
python3 -m unittest tests.test_attack_overlay -v
PYTHONPATH=src python3 scripts/validation/run_fact_lineage_matrix.py
python3 -m unittest tests.trusted_execution.test_context_policy -v
python3 -m unittest tests.trusted_execution.test_governed_action tests.test_webshop_runtime_gate -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 run_experiment.py
```

Expected:

```text
fact-lineage tests all PASS
overlay tests > current count and all PASS
lineage matrix all matched
full suite > 396 and all PASS
formal entrypoint 13/13 PASS
```

`REPORT.md` must include public APIs, propagation examples, overlay consumer output, matrix summary, proof old overlay results are unchanged, changed-file SHA-256, complete EV triplets, AC-01 through AC-10 mapping, explicit no-WebShop/no-Buy-Now/no-payment/no-network/no-environment/no-commit/no-push statement, and workflow validation with no `BLOCKING` finding.

## 5. Allowed scope

- `src/agentic_payment_experiment/trusted_execution/fact_lineage.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`（new exports only）
- `src/agentic_payment_experiment/__init__.py`（new exports only if required）
- `src/agentic_payment_experiment/attack_overlay.py`（lineage evidence consumer only）
- `tests/trusted_execution/test_fact_lineage.py`
- `tests/test_attack_overlay.py`
- `samples/attacks/fact_lineage_matrix_v1.json`
- `scripts/validation/run_fact_lineage_matrix.py`
- factual status updates to existing P9 roadmap/reference documents
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/REPORT.md`
- `docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff

No other tracked path is allowed.

## 6. Exclusions

- 不修改 `context_policy.py`、`governed_action.py` 或 `webshop_runtime_gate.py`；
- 不让 lineage 直接作出支付 ALLOW/DENY；
- 不改变 `SourceType` 枚举；
- 不实现提示注入组合测试、个人信息最小化、P9-D 或 P9-E UI；
- 不执行 WebShop、Buy Now、支付或网络；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理继承工作区改动。

## 7. Authorization

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

## 8. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | exact-type and primitive serialization | immutable exact nodes; invalid outer types fail closed | AC-01 |
| VP-02 | mandatory fields and identities | missing vs invalid classifications stable | AC-02 |
| VP-03 | graph integrity | duplicates, missing refs and cycles deterministic | AC-03 |
| VP-04 | root and derived propagation | all upstream source types retained | AC-04 |
| VP-05 | claimed trust upgrades | ancestry never erased | AC-05 |
| VP-06 | untrusted ancestry classifier | deterministic documented source classes | AC-06 |
| VP-07 | overlay consumer | structured lineage added; old policy behavior unchanged | AC-07 |
| VP-08 | machine-readable matrix | all required cases and fields matched | AC-08 |
| VP-09 | static/dynamic side-effect audit | pure resolver has no I/O or external action | AC-09 |
| VP-10 | targeted/full/formal/workflow | all regressions pass; validator no BLOCKING | AC-10 |

## 9. Stop conditions

Stop and report without broadening scope if:

- provenance propagation requires changing `SourceType` or Context Policy decisions;
- the overlay consumer cannot expose lineage without changing its prior decisions;
- a validation requires LLM, WebShop runtime, network or payment execution;
- unrelated inherited workspace changes prevent objective verification.
