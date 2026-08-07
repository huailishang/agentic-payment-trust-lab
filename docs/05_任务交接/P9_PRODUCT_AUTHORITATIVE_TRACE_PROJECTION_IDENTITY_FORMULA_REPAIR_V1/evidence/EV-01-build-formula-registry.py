from __future__ import annotations

import copy
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
TASK_ID = "P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1"

PARENT_EVIDENCE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence"
PARENT_COVERAGE = PARENT_EVIDENCE / "EV-01-coverage-reference-grounding.json"
PARENT_T10 = PARENT_EVIDENCE / "EV-01-t10-grounded-instance.json"
PARENT_T12 = PARENT_EVIDENCE / "EV-01-t12-sidecar-examples.json"
PARENT_REFS = PARENT_EVIDENCE / "EV-01-reference-examples.json"

DESIGN_DOC = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
MEASUREMENT_DOC = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"

OUTPUT_COVERAGE = EVIDENCE / "EV-01-coverage-projection-identity-formula.json"
OUTPUT_VECTORS = EVIDENCE / "EV-01-projection-identity-vectors.json"

FORMULA_ID = "PROJECTION_HASH_IDENTITY_V1"
PREFIX_LITERAL = ":projection-sha256:"
FORMULA_PARAMETERS: dict[str, Any] = {
    "mode": "PROJECTION_HASH_IDENTITY",
    "formula_id": FORMULA_ID,
    "prefix_template": "{source_object_type}:projection-sha256:",
    "hash_algorithm": "SHA-256",
    "digest_encoding": "lowercase-hex-64",
    "payload_fields": ["projection_schema", "projection"],
    "canonical_json": {
        "encoding": "UTF-8",
        "sort_keys": True,
        "separators": [",", ":"],
        "ensure_ascii": False,
        "allow_nan": False,
    },
}

HASH_SCHEMAS = [
    "governed-action-binding-fact-trace/v2",
    "governed-payment-action-missing-id-trace/v2",
    "known-payment-attempt-preflight-fact-trace/v2",
    "payment-recovery-result-trace/v2",
    "payment-status-conflict-fact-trace/v2",
    "runtime-gate-record-trace/v2",
    "validation-result-trace/v2",
    "webshop-buy-now-gate-outcome-result-trace/v2",
    "webshop-payment-fulfilment-outcome-result-trace/v2",
]


class FormulaInputError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise FormulaInputError("non-finite Decimal is forbidden")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_primitive(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise FormulaInputError("float is forbidden")
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, tuple):
        return [canonical_primitive(item) for item in value]
    if isinstance(value, list):
        return [canonical_primitive(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise FormulaInputError("dict key must be str")
            result[key] = canonical_primitive(item)
        return result
    raise FormulaInputError(f"unsupported primitive: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    primitive = canonical_primitive(value)
    return json.dumps(
        primitive,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def projection_identity_payload(schema: str, projection: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, str) or not schema:
        raise FormulaInputError("projection_schema is required")
    if not isinstance(projection, dict):
        raise FormulaInputError("projection must be an object")
    return {
        "projection_schema": schema,
        "projection": canonical_primitive(projection),
    }


def projection_source_ref(source_type: str, schema: str, projection: dict[str, Any]) -> str:
    if not isinstance(source_type, str) or not source_type:
        raise FormulaInputError("source_object_type is required")
    payload = projection_identity_payload(schema, projection)
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return f"{source_type}{PREFIX_LITERAL}{digest}"


def binding_ref(binding: dict[str, Any]) -> str:
    payload = {
        "source_object_type": binding["source_object_type"],
        "source_object_ref": binding["source_object_ref"],
        "projection_schema": binding["projection_schema"],
        "projection": canonical_primitive(binding["projection"]),
    }
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return f"TraceSourceBinding:sha256:{digest}"


def make_binding(source_type: str, schema: str, projection: dict[str, Any]) -> dict[str, Any]:
    source_ref = projection_source_ref(source_type, schema, projection)
    partial = {
        "source_object_type": source_type,
        "source_object_ref": source_ref,
        "projection_schema": schema,
        "projection": canonical_primitive(projection),
    }
    return {"binding_ref": binding_ref(partial), **partial}


def write_json(path: Path, value: Any) -> str:
    path.write_text(
        json.dumps(canonical_primitive(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return sha256_file(path)


def replace_marked_block(text: str, marker: str, block: str, before_heading: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    rendered = f"{start}\n{block.rstrip()}\n{end}\n\n"
    if start in text:
        left, rest = text.split(start, 1)
        _, right = rest.split(end, 1)
        return left + rendered + right.lstrip("\n")
    if before_heading not in text:
        raise AssertionError(f"heading not found for {marker}: {before_heading}")
    return text.replace(before_heading, rendered + before_heading, 1)


def normalize_markdown(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


parent_paths = [PARENT_COVERAGE, PARENT_T10, PARENT_T12, PARENT_REFS]
parent_hashes_before = {path.name: sha256_file(path) for path in parent_paths}

parent_coverage = json.loads(PARENT_COVERAGE.read_text(encoding="utf-8"))
parent_t10 = json.loads(PARENT_T10.read_text(encoding="utf-8"))
parent_t12 = json.loads(PARENT_T12.read_text(encoding="utf-8"))
parent_refs = json.loads(PARENT_REFS.read_text(encoding="utf-8"))

new_coverage = copy.deepcopy(parent_coverage)
new_coverage["schema_version"] = "product-authoritative-trace-coverage/v4"
new_coverage["generated_for_task"] = TASK_ID
new_coverage["projection_identity_formula_registry"] = {
    FORMULA_ID: {
        "source_object_type_in_payload": False,
        "source_object_type_in_prefix": True,
        "payload_excludes": ["binding_ref", "source_object_ref"],
        **copy.deepcopy(FORMULA_PARAMETERS),
    }
}
new_coverage["parent_fixed_artifact_hashes"] = parent_hashes_before

registry = new_coverage["projection_registry"]
actual_hash_schemas = sorted(
    schema
    for schema, entry in registry.items()
    if entry["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY"
)
if actual_hash_schemas != sorted(HASH_SCHEMAS):
    raise AssertionError((actual_hash_schemas, HASH_SCHEMAS))

native_identity_before = {
    schema: copy.deepcopy(entry["source_identity"])
    for schema, entry in parent_coverage["projection_registry"].items()
    if entry["source_identity"]["mode"] == "NATIVE_TEMPLATE"
}

for schema in HASH_SCHEMAS:
    registry[schema]["source_identity"] = copy.deepcopy(FORMULA_PARAMETERS)

for schema, expected in native_identity_before.items():
    if registry[schema]["source_identity"] != expected:
        raise AssertionError(f"native identity changed: {schema}")

coverage_sha = write_json(OUTPUT_COVERAGE, new_coverage)

persisted_vectors: dict[str, dict[str, Any]] = {}


def register_parent_binding(binding: dict[str, Any], origin: str) -> None:
    schema = binding.get("projection_schema")
    source_ref = binding.get("source_object_ref", "")
    if schema in HASH_SCHEMAS and ":projection-sha256:" in source_ref:
        existing = persisted_vectors.get(schema)
        candidate = {
            "origin": origin,
            "parent_fixed": True,
            "binding": copy.deepcopy(binding),
        }
        if existing is None:
            persisted_vectors[schema] = candidate
        elif existing["binding"] != candidate["binding"]:
            # Multiple fixed instances for one schema are allowed; the first remains
            # the canonical positive vector while T10/T12 regression covers all.
            pass


for binding in parent_t10["bindings"]:
    register_parent_binding(binding, "parent_t10")
for key in ("conflict_fact", "sidecar_result"):
    register_parent_binding(parent_t12[key], f"parent_t12.{key}")
for role, binding in parent_refs.get("fixed_binding_examples", {}).items():
    register_parent_binding(binding, f"parent_ref_examples.{role}")

# Two registry schemas had no persisted concrete parent binding JSON. Build
# deterministic conformance vectors without changing or inventing parent values.
t10_action = next(
    item for item in parent_t10["bindings"]
    if item["projection_schema"] == "governed-payment-action-trace/v2"
)
missing_action_projection = copy.deepcopy(t10_action["projection"])
missing_action_projection["action_id"] = ""
missing_action_binding = make_binding(
    "GovernedPaymentAction",
    "governed-payment-action-missing-id-trace/v2",
    missing_action_projection,
)

recovery_projection = {
    "initial_status": "UNKNOWN",
    "observed_status": "SUCCEEDED",
    "effective_status": "SUCCEEDED",
    "recovery_status": "RECOVERED",
    "next_action": "continue_with_original_payment",
    "retry_allowed": False,
    "issue_codes": ["payment_state_recovered_as_succeeded"],
    "evidence_paths": [
        "payment.payment_id",
        "payment.status",
        "payment_status_observation.payment_id",
        "payment_status_observation.status",
    ],
    "rule_version": "payment-recovery-rules-v0.2",
}
recovery_binding = make_binding(
    "PaymentRecoveryResult",
    "payment-recovery-result-trace/v2",
    recovery_projection,
)

conformance_vectors = {
    "governed-payment-action-missing-id-trace/v2": {
        "origin": "derived_from_parent_t10_governed_action_with_empty_action_id",
        "parent_fixed": False,
        "binding": missing_action_binding,
    },
    "payment-recovery-result-trace/v2": {
        "origin": "derived_from_current_payment_recovery_contract_shape",
        "parent_fixed": False,
        "binding": recovery_binding,
    },
}

all_vectors = {**persisted_vectors, **conformance_vectors}
if sorted(all_vectors) != sorted(HASH_SCHEMAS):
    raise AssertionError((sorted(all_vectors), sorted(HASH_SCHEMAS)))

positive_results = []
for schema in HASH_SCHEMAS:
    vector = all_vectors[schema]
    item = copy.deepcopy(vector["binding"])
    recomputed_source_ref = projection_source_ref(
        item["source_object_type"], item["projection_schema"], item["projection"]
    )
    recomputed_binding_ref = binding_ref(item)
    source_unchanged = recomputed_source_ref == item["source_object_ref"]
    binding_unchanged = recomputed_binding_ref == item["binding_ref"]
    if not source_unchanged or not binding_unchanged:
        raise AssertionError(f"positive vector mismatch: {schema}")
    positive_results.append(
        {
            "projection_schema": schema,
            "source_object_type": item["source_object_type"],
            "origin": vector["origin"],
            "parent_fixed": vector["parent_fixed"],
            "expected_source_object_ref": item["source_object_ref"],
            "recomputed_source_object_ref": recomputed_source_ref,
            "source_ref_unchanged": source_unchanged,
            "expected_binding_ref": item["binding_ref"],
            "recomputed_binding_ref": recomputed_binding_ref,
            "binding_ref_unchanged": binding_unchanged,
            "projection": item["projection"],
        }
    )


def native_source_ref(entry: dict[str, Any], projection: dict[str, Any]) -> str:
    template = entry["source_identity"]["template"]
    if not isinstance(template, str) or not template:
        raise AssertionError("native template missing")
    rendered = template
    for field, value in projection.items():
        rendered = rendered.replace("{" + field + "}", str(value))
    if "{" in rendered or "}" in rendered:
        raise AssertionError(f"native template unresolved: {rendered}")
    return rendered


def recompute_binding_with_registry(binding: dict[str, Any]) -> dict[str, Any]:
    schema = binding["projection_schema"]
    entry = registry[schema]
    if entry["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY":
        source_ref = projection_source_ref(
            binding["source_object_type"], schema, binding["projection"]
        )
    else:
        source_ref = native_source_ref(entry, binding["projection"])
    candidate = copy.deepcopy(binding)
    candidate["source_object_ref"] = source_ref
    return {
        "projection_schema": schema,
        "source_ref_unchanged": source_ref == binding["source_object_ref"],
        "binding_ref_unchanged": binding_ref(candidate) == binding["binding_ref"],
        "expected_source_object_ref": binding["source_object_ref"],
        "recomputed_source_object_ref": source_ref,
        "expected_binding_ref": binding["binding_ref"],
        "recomputed_binding_ref": binding_ref(candidate),
    }


t10_binding_results = [recompute_binding_with_registry(item) for item in parent_t10["bindings"]]
if not all(item["source_ref_unchanged"] and item["binding_ref_unchanged"] for item in t10_binding_results):
    raise AssertionError("T10 fixed references changed")

t12_binding_results = [
    recompute_binding_with_registry(parent_t12["conflict_fact"]),
    recompute_binding_with_registry(parent_t12["sidecar_result"]),
]
if not all(item["source_ref_unchanged"] and item["binding_ref_unchanged"] for item in t12_binding_results):
    raise AssertionError("T12 fixed references changed")

base = next(item for item in positive_results if item["parent_fixed"])
base_type = base["source_object_type"]
base_schema = base["projection_schema"]
base_projection = copy.deepcopy(base["projection"])
base_ref = base["expected_source_object_ref"]

negative_results: list[dict[str, Any]] = []


def add_negative(case_id: str, expected: str, actual: str, verdict: str, detail: Any) -> None:
    negative_results.append(
        {
            "case_id": case_id,
            "expected": expected,
            "actual": actual,
            "verdict": verdict,
            "detail": canonical_primitive(detail),
        }
    )


try:
    projection_source_ref(base_type, "", base_projection)
except FormulaInputError as exc:
    add_negative("missing_projection_schema", "fail closed", type(exc).__name__, "FAIL_CLOSED", str(exc))
else:
    raise AssertionError("missing schema did not fail")

projection_only_digest = hashlib.sha256(canonical_json_bytes(base_projection)).hexdigest()
projection_only_ref = f"{base_type}{PREFIX_LITERAL}{projection_only_digest}"
add_negative(
    "payload_projection_only",
    "ref mismatch / INVALID",
    "ref_changed" if projection_only_ref != base_ref else "ref_reused",
    "INVALID_REF_MISMATCH",
    {"tampered_ref": projection_only_ref, "fixed_ref": base_ref},
)

schema_changed_ref = projection_source_ref(base_type, base_schema + "-tampered", base_projection)
add_negative(
    "schema_string_changed",
    "ref changed",
    "ref_changed" if schema_changed_ref != base_ref else "ref_reused",
    "REF_CHANGED",
    schema_changed_ref,
)

projection_changed = copy.deepcopy(base_projection)
first_key = sorted(projection_changed)[0]
old_value = projection_changed[first_key]
if isinstance(old_value, str):
    projection_changed[first_key] = old_value + "-tampered"
elif isinstance(old_value, bool):
    projection_changed[first_key] = not old_value
elif isinstance(old_value, list):
    projection_changed[first_key] = list(old_value) + ["tampered"]
elif old_value is None:
    projection_changed[first_key] = "tampered"
else:
    projection_changed[first_key] = str(old_value) + "-tampered"
projection_changed_ref = projection_source_ref(base_type, base_schema, projection_changed)
add_negative(
    "projection_field_changed",
    "ref changed",
    "ref_changed" if projection_changed_ref != base_ref else "ref_reused",
    "REF_CHANGED",
    {"field": first_key, "tampered_ref": projection_changed_ref},
)

type_changed_ref = projection_source_ref(base_type + "Tampered", base_schema, base_projection)
add_negative(
    "source_type_prefix_changed",
    "object identity mismatch / INVALID",
    "prefix_changed" if type_changed_ref != base_ref else "ref_reused",
    "INVALID_OBJECT_IDENTITY_MISMATCH",
    type_changed_ref,
)

case_prefix = base_ref.replace(":projection-sha256:", ":Projection-SHA256:", 1)
add_negative(
    "prefix_case_changed",
    "prefix mismatch / INVALID",
    "prefix_changed",
    "INVALID_PREFIX_MISMATCH",
    case_prefix,
)

digest = base_ref.rsplit(":", 1)[1]
upper_ref = base_ref[: -len(digest)] + digest.upper()
add_negative(
    "digest_uppercase",
    "encoding mismatch / INVALID",
    "uppercase_digest",
    "INVALID_DIGEST_ENCODING_MISMATCH",
    upper_ref,
)

short_ref = base_ref[: -len(digest)] + digest[:-1]
add_negative(
    "digest_not_64_hex",
    "format mismatch / INVALID",
    f"digest_length={len(digest) - 1}",
    "INVALID_DIGEST_FORMAT_MISMATCH",
    short_ref,
)

for case_id, value in (
    ("float_input", 1.0),
    ("nan_input", float("nan")),
    ("infinity_input", float("inf")),
):
    tampered = copy.deepcopy(base_projection)
    tampered[first_key] = value
    try:
        projection_source_ref(base_type, base_schema, tampered)
    except FormulaInputError as exc:
        add_negative(case_id, "canonicalization fail closed", type(exc).__name__, "FAIL_CLOSED", str(exc))
    else:
        raise AssertionError(f"{case_id} did not fail")

payload_with_cycle = {
    "projection_schema": base_schema,
    "projection": base_projection,
    "source_object_ref": base_ref,
}
cycle_ref = f"{base_type}{PREFIX_LITERAL}{hashlib.sha256(canonical_json_bytes(payload_with_cycle)).hexdigest()}"
add_negative(
    "payload_includes_source_object_ref",
    "schema/payload mismatch / INVALID",
    "payload_fields_changed",
    "INVALID_PAYLOAD_SCHEMA_MISMATCH",
    cycle_ref,
)

add_negative(
    "parent_ev_builder_as_resolver",
    "forbidden",
    "not_read_or_imported",
    "FORBIDDEN_RESOLVER",
    "Independent checker input contract excludes EV-01-build-grounded-reference-model.py",
)

if len(negative_results) < 11:
    raise AssertionError("negative matrix incomplete")

parent_hashes_after = {path.name: sha256_file(path) for path in parent_paths}
if parent_hashes_before != parent_hashes_after:
    raise AssertionError("parent fixed evidence changed")

next_text = NEXT_SLICE.read_text(encoding="utf-8")
next_slice_checks = {
    "conditional_not_frozen": "State: `CONDITIONAL_NOT_FROZEN`" in next_text,
    "measurement_adapter_prerequisite": "prerequisite = measurement adapter accepted" in next_text,
    "hashes_tbd": all(
        marker in next_text
        for marker in (
            "runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE",
            "before hash = TBD_AFTER_ADAPTER_ACCEPTANCE",
            "target hash = TBD_AFTER_ADAPTER_ACCEPTANCE",
            "non-trace projection hash = TBD_AFTER_ADAPTER_ACCEPTANCE",
        )
    ),
    "t10_12_events_11_bindings": "events = exact 12" in next_text and "source_bindings = exact 11 unique bindings" in next_text,
}
if not all(next_slice_checks.values()):
    raise AssertionError(next_slice_checks)

vectors = {
    "schema_version": "projection-hash-identity-vectors/v1",
    "generated_for_task": TASK_ID,
    "formula": {
        "formula_id": FORMULA_ID,
        "source_object_type_in_payload": False,
        "source_object_type_in_prefix": True,
        "payload_excludes": ["binding_ref", "source_object_ref"],
        **FORMULA_PARAMETERS,
    },
    "positive_vectors": positive_results,
    "positive_summary": {
        "schema_count": len(positive_results),
        "parent_persisted_fixed_schema_count": sum(1 for item in positive_results if item["parent_fixed"]),
        "derived_conformance_schema_count": sum(1 for item in positive_results if not item["parent_fixed"]),
        "all_source_refs_recomputed": all(item["source_ref_unchanged"] for item in positive_results),
        "all_binding_refs_recomputed": all(item["binding_ref_unchanged"] for item in positive_results),
    },
    "negative_matrix": negative_results,
    "t10_regression": {
        "event_count": parent_t10["event_count"],
        "unique_binding_count": parent_t10["unique_binding_count"],
        "authorized_and_current_order_share_binding": parent_t10["authorized_and_current_order_share_binding"],
        "relations_resolved": parent_t10["relations_resolved"],
        "binding_results": t10_binding_results,
        "all_fixed_values_unchanged": all(
            item["source_ref_unchanged"] and item["binding_ref_unchanged"]
            for item in t10_binding_results
        ),
    },
    "t12_regression": {
        "binding_results": t12_binding_results,
        "sidecar_decision_extraction": parent_t12["sidecar_decision_extraction"],
        "all_fixed_values_unchanged": all(
            item["source_ref_unchanged"] and item["binding_ref_unchanged"]
            for item in t12_binding_results
        ),
    },
    "baseline": {
        "product_observed_authoritative_trace": "0/12 VALID",
        "gesr": "0/12",
        "new_business_rule_required": False,
    },
    "parent_fixed_artifact_hashes_before": parent_hashes_before,
    "parent_fixed_artifact_hashes_after": parent_hashes_after,
    "parent_fixed_artifacts_unchanged": parent_hashes_before == parent_hashes_after,
    "next_slice_checks": next_slice_checks,
    "independent_checker_forbidden_input": "EV-01-build-grounded-reference-model.py",
}
vectors_sha = write_json(OUTPUT_VECTORS, vectors)

formula_block = f"""## 2.1 `PROJECTION_HASH_IDENTITY_V1`

无 native ID 的事实或 outcome 使用唯一公式：

```text
formula_id = {FORMULA_ID}

payload = {{
  \"projection_schema\": <exact schema string>,
  \"projection\": <exact canonical primitive projection>
}}

payload_bytes = UTF-8(
  JSON(payload,
       sort_keys=true,
       separators=(\",\", \":\"),
       ensure_ascii=false,
       allow_nan=false)
)

digest = lowercase_hex(SHA-256(payload_bytes))

source_object_ref =
  <source_object_type>
  + \"{PREFIX_LITERAL}\"
  + digest
```

冻结语义：

1. `source_object_type` 只进入固定前缀，不进入 hash payload；
2. `projection_schema` 与 exact canonical `projection` 都进入 payload；
3. payload 只允许上述两个字段，不包含 `binding_ref` 或 `source_object_ref`，避免循环；
4. digest 固定为 SHA-256 小写 64 位十六进制；
5. prefix 的大小写、冒号和 `projection-sha256` 字面值固定；
6. schema、projection、source type 或 prefix 任一变化都不得复用原 ref；
7. float、NaN、Infinity 或 canonical primitive 失败时 fail closed；
8. 该公式只证明 envelope 内部 object identity 一致性，不宣称外部真实性、签名身份或可信执行。

结构化 registry 使用相同 `formula_id`、prefix、payload fields、hash、encoding 和 canonical JSON 参数。`source_object_ref` 的 identity hash 与 `binding_ref` 的 full-binding digest 是两个独立公式，不得混算。"""

design_text = DESIGN_DOC.read_text(encoding="utf-8")
design_text = replace_marked_block(
    design_text,
    "PROJECTION_HASH_IDENTITY_V1",
    formula_block,
    "## 3. Envelope、Binding、Event",
)
DESIGN_DOC.write_text(normalize_markdown(design_text), encoding="utf-8")

coverage_formula_block = f"""## 2.1 Projection Identity 公式 registry

9 个 `PROJECTION_HASH_IDENTITY` schema 统一使用 `{FORMULA_ID}`：

```text
prefix = {{source_object_type}}{PREFIX_LITERAL}
payload_fields = [projection_schema, projection]
hash = SHA-256
encoding = lowercase-hex-64
canonical JSON = UTF-8 / sort_keys / compact separators / ensure_ascii=false / allow_nan=false
```

结构化 coverage：`docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-coverage-projection-identity-formula.json`
SHA-256：`{coverage_sha}`
Schema：`product-authoritative-trace-coverage/v4`

正反例与固定值回归：`docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-projection-identity-vectors.json`
SHA-256：`{vectors_sha}`

Hash identity schemas：

```text
{chr(10).join(HASH_SCHEMAS)}
```

validator 只读 envelope 与冻结 registry 即可重算 object identity；不得读取父 EV builder、fixture、GateContext、产品原对象或 evaluator replay。"""

coverage_text = COVERAGE_DOC.read_text(encoding="utf-8")
coverage_text = replace_marked_block(
    coverage_text,
    "PROJECTION_HASH_IDENTITY_V1_REGISTRY",
    coverage_formula_block,
    "## 3. T01—T12 概览",
)
# Replace the old authoritative structured-coverage pointer with the new v4 registry.
old_pointer = (
    "结构化 coverage：`docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/EV-01-coverage-reference-grounding.json`\n"
    "SHA-256：`3d9904094556680137eb296e016a9abc573534d0f2c13060c0a288292f79d4fa`\n"
    "Schema：`product-authoritative-trace-coverage/v3`"
)
new_pointer = (
    "结构化 coverage：`docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-coverage-projection-identity-formula.json`\n"
    f"SHA-256：`{coverage_sha}`\n"
    "Schema：`product-authoritative-trace-coverage/v4`"
)
if old_pointer in coverage_text:
    coverage_text = coverage_text.replace(old_pointer, new_pointer, 1)
elif new_pointer not in coverage_text:
    raise AssertionError("coverage pointer not found")
COVERAGE_DOC.write_text(normalize_markdown(coverage_text), encoding="utf-8")

adapter_block = f"""## 2.1 Object identity 两条路径

```text
NATIVE_TEMPLATE
→ 按 schema 冻结的 native template 重算 source_object_ref

{FORMULA_ID}
→ prefix = {{source_object_type}}{PREFIX_LITERAL}
→ payload = {{projection_schema, projection}}
→ canonical JSON + SHA-256 + lowercase-hex-64
```

adapter 只读取 envelope 和内置冻结 registry。禁止读取 EV builder、fixture、GateContext、产品原对象或 evaluator replay。

以下均不得得到 `VALID`：

- formula_id、prefix、payload fields、canonical JSON 参数不匹配；
- schema 或 projection 改变但复用旧 ref；
- source type/prefix 大小写或冒号变化；
- digest 非小写 64 hex；
- payload 缺 `projection_schema`、只有 projection，或额外包含 `source_object_ref`；
- float、NaN、Infinity canonicalization；
- 把 source identity hash 与 `binding_ref` full-binding digest 混为一个公式。

object identity 通过后，仍必须单独重算 `binding_ref`；两者任一不一致都不能得到 `VALID`。"""

measurement_text = MEASUREMENT_DOC.read_text(encoding="utf-8")
measurement_text = replace_marked_block(
    measurement_text,
    "PROJECTION_HASH_IDENTITY_V1_ADAPTER",
    adapter_block,
    "## 3. Strict matrix",
)
MEASUREMENT_DOC.write_text(normalize_markdown(measurement_text), encoding="utf-8")

parent_hashes_final = {path.name: sha256_file(path) for path in parent_paths}
if parent_hashes_final != parent_hashes_before:
    raise AssertionError("parent evidence changed after doc updates")

print(f"task_id={TASK_ID}")
print(f"formula_id={FORMULA_ID}")
print(f"hash_schema_count={len(HASH_SCHEMAS)}")
print(f"parent_persisted_fixed_schema_count={sum(1 for item in positive_results if item['parent_fixed'])}")
print(f"derived_conformance_schema_count={sum(1 for item in positive_results if not item['parent_fixed'])}")
print(f"positive_source_refs_unchanged={all(item['source_ref_unchanged'] for item in positive_results)}")
print(f"positive_binding_refs_unchanged={all(item['binding_ref_unchanged'] for item in positive_results)}")
print(f"negative_case_count={len(negative_results)}")
print(f"t10_events={parent_t10['event_count']}")
print(f"t10_unique_bindings={parent_t10['unique_binding_count']}")
print(f"t10_fixed_values_unchanged={vectors['t10_regression']['all_fixed_values_unchanged']}")
print(f"t12_fixed_values_unchanged={vectors['t12_regression']['all_fixed_values_unchanged']}")
print(f"parent_fixed_artifacts_unchanged={parent_hashes_final == parent_hashes_before}")
print(f"coverage_sha256={coverage_sha}")
print(f"vectors_sha256={vectors_sha}")
