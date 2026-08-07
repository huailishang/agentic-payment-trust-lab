from __future__ import annotations

import ast
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
PARENT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence"

DESIGN = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
MEASUREMENT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
NEW_COVERAGE = EVIDENCE / "EV-01-coverage-projection-identity-formula.json"
VECTORS = EVIDENCE / "EV-01-projection-identity-vectors.json"
PARENT_COVERAGE = PARENT / "EV-01-coverage-reference-grounding.json"
PARENT_T10 = PARENT / "EV-01-t10-grounded-instance.json"
PARENT_T12 = PARENT / "EV-01-t12-sidecar-examples.json"
PARENT_REFS = PARENT / "EV-01-reference-examples.json"

STATIC_ALLOWED = {
    DESIGN.resolve(),
    COVERAGE_DOC.resolve(),
    MEASUREMENT.resolve(),
    NEXT_SLICE.resolve(),
    NEW_COVERAGE.resolve(),
    VECTORS.resolve(),
    PARENT_COVERAGE.resolve(),
    PARENT_T10.resolve(),
    PARENT_T12.resolve(),
    PARENT_REFS.resolve(),
}
READ_PATHS: list[str] = []


def read_allowed(path: Path) -> str:
    resolved = path.resolve()
    if resolved not in STATIC_ALLOWED and not (
        resolved.is_relative_to((ROOT / "src").resolve()) and resolved.suffix == ".py"
    ):
        raise AssertionError(f"disallowed project input: {resolved}")
    READ_PATHS.append(resolved.relative_to(ROOT).as_posix())
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_allowed(path))


def canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("non-finite Decimal")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise TypeError("float forbidden")
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, tuple):
        return [canonical(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("dict key must be str")
        return {key: canonical(item) for key, item in value.items()}
    raise TypeError(type(value).__name__)


def canonical_bytes(value: Any, parameters: dict[str, Any]) -> bytes:
    cfg = parameters["canonical_json"]
    if cfg != {
        "encoding": "UTF-8",
        "sort_keys": True,
        "separators": [",", ":"],
        "ensure_ascii": False,
        "allow_nan": False,
    }:
        raise AssertionError(f"unsupported canonical JSON parameters: {cfg}")
    return json.dumps(
        canonical(value),
        sort_keys=cfg["sort_keys"],
        separators=tuple(cfg["separators"]),
        ensure_ascii=cfg["ensure_ascii"],
        allow_nan=cfg["allow_nan"],
    ).encode(cfg["encoding"].lower())


def source_ref_from_registry(
    source_type: str,
    schema: str,
    projection: dict[str, Any],
    identity: dict[str, Any],
) -> str:
    if identity["mode"] == "NATIVE_TEMPLATE":
        rendered = identity["template"]
        for field, value in projection.items():
            rendered = rendered.replace("{" + field + "}", str(value))
        if "{" in rendered or "}" in rendered:
            raise AssertionError(f"native template unresolved: {rendered}")
        return rendered

    if identity["mode"] != "PROJECTION_HASH_IDENTITY":
        raise AssertionError(identity["mode"])
    if identity["formula_id"] != "PROJECTION_HASH_IDENTITY_V1":
        raise AssertionError(identity["formula_id"])
    if identity["payload_fields"] != ["projection_schema", "projection"]:
        raise AssertionError(identity["payload_fields"])
    payload = {
        identity["payload_fields"][0]: schema,
        identity["payload_fields"][1]: projection,
    }
    if identity["hash_algorithm"] != "SHA-256":
        raise AssertionError(identity["hash_algorithm"])
    digest = hashlib.sha256(canonical_bytes(payload, identity)).hexdigest()
    if identity["digest_encoding"] != "lowercase-hex-64":
        raise AssertionError(identity["digest_encoding"])
    if len(digest) != 64 or digest.lower() != digest:
        raise AssertionError(digest)
    prefix = identity["prefix_template"].replace("{source_object_type}", source_type)
    return prefix + digest


def binding_ref(binding: dict[str, Any], formula: dict[str, Any]) -> str:
    payload = {
        "source_object_type": binding["source_object_type"],
        "source_object_ref": binding["source_object_ref"],
        "projection_schema": binding["projection_schema"],
        "projection": binding["projection"],
    }
    digest = hashlib.sha256(canonical_bytes(payload, formula)).hexdigest()
    return f"TraceSourceBinding:sha256:{digest}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


coverage = load_json(NEW_COVERAGE)
vectors = load_json(VECTORS)
parent_coverage = load_json(PARENT_COVERAGE)
t10 = load_json(PARENT_T10)
t12 = load_json(PARENT_T12)
parent_refs = load_json(PARENT_REFS)
design_text = read_allowed(DESIGN)
coverage_text = read_allowed(COVERAGE_DOC)
measurement_text = read_allowed(MEASUREMENT)
next_text = read_allowed(NEXT_SLICE)

checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: Any = "") -> None:
    checks.append((name, bool(condition), str(detail)))


formula_registry = coverage["projection_identity_formula_registry"]
check("one formula", list(formula_registry) == ["PROJECTION_HASH_IDENTITY_V1"], list(formula_registry))
formula = formula_registry["PROJECTION_HASH_IDENTITY_V1"]
expected_formula = {
    "mode": "PROJECTION_HASH_IDENTITY",
    "formula_id": "PROJECTION_HASH_IDENTITY_V1",
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
    "source_object_type_in_payload": False,
    "source_object_type_in_prefix": True,
    "payload_excludes": ["binding_ref", "source_object_ref"],
}
for key, expected in expected_formula.items():
    check(f"formula:{key}", formula.get(key) == expected, formula.get(key))

registry = coverage["projection_registry"]
parent_registry = parent_coverage["projection_registry"]
hash_schemas = sorted(
    schema for schema, entry in registry.items()
    if entry["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY"
)
expected_hash_schemas = sorted(
    [
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
)
check("exact 9 hash schemas", hash_schemas == expected_hash_schemas, hash_schemas)
for schema in hash_schemas:
    identity = registry[schema]["source_identity"]
    for key in (
        "mode",
        "formula_id",
        "prefix_template",
        "hash_algorithm",
        "digest_encoding",
        "payload_fields",
        "canonical_json",
    ):
        check(f"registry:{schema}:{key}", identity.get(key) == expected_formula[key], identity.get(key))
    check(f"registry:{schema}:not-null-template-only", set(identity) != {"mode", "template"})
    check(f"registry:{schema}:no-builder-reference", "builder" not in json.dumps(identity).lower())

native_schemas = sorted(set(registry) - set(hash_schemas))
for schema in native_schemas:
    check(
        f"native-unchanged:{schema}",
        registry[schema]["source_identity"] == parent_registry[schema]["source_identity"],
    )

# Validate source class and extraction roots using only current source type boundaries.
for schema, entry in registry.items():
    source_file = ROOT / "src" / (entry["source_module"].replace(".", "/") + ".py")
    source_text = read_allowed(source_file)
    tree = ast.parse(source_text)
    cls = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == entry["source_class"]),
        None,
    )
    check(f"source-class:{schema}", cls is not None, source_file)
    fields = {
        node.target.id
        for node in (cls.body if cls is not None else [])
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    for projected, extraction in entry["field_extractions"].items():
        root = re.split(r"\.|\[", extraction["path"], maxsplit=1)[0]
        check(f"source-field:{schema}:{projected}", root in fields, root)

positive = vectors["positive_vectors"]
check("9 positive vectors", len(positive) == 9, len(positive))
check("7 parent persisted vectors", vectors["positive_summary"]["parent_persisted_fixed_schema_count"] == 7)
check("2 derived conformance vectors", vectors["positive_summary"]["derived_conformance_schema_count"] == 2)
check("positive schemas exact", sorted(item["projection_schema"] for item in positive) == hash_schemas)
for item in positive:
    schema = item["projection_schema"]
    identity = registry[schema]["source_identity"]
    source_ref = source_ref_from_registry(
        item["source_object_type"], schema, item["projection"], identity
    )
    candidate = {
        "source_object_type": item["source_object_type"],
        "source_object_ref": source_ref,
        "projection_schema": schema,
        "projection": item["projection"],
    }
    computed_binding = binding_ref(candidate, formula)
    check(f"positive-source:{schema}", source_ref == item["expected_source_object_ref"], source_ref)
    check(f"positive-binding:{schema}", computed_binding == item["expected_binding_ref"], computed_binding)
    check(f"positive-prefix:{schema}", source_ref.startswith(item["source_object_type"] + ":projection-sha256:"))
    digest = source_ref.rsplit(":", 1)[1]
    check(f"positive-digest-format:{schema}", len(digest) == 64 and digest == digest.lower() and bool(re.fullmatch(r"[0-9a-f]{64}", digest)))

# T10 and T12 fixed instances must remain byte-for-byte equivalent in their refs.
t10_results = []
for binding in t10["bindings"]:
    schema = binding["projection_schema"]
    source_ref = source_ref_from_registry(
        binding["source_object_type"], schema, binding["projection"], registry[schema]["source_identity"]
    )
    candidate = dict(binding)
    candidate["source_object_ref"] = source_ref
    computed_binding = binding_ref(candidate, formula)
    ok_source = source_ref == binding["source_object_ref"]
    ok_binding = computed_binding == binding["binding_ref"]
    t10_results.append(ok_source and ok_binding)
    check(f"T10-source:{schema}:{binding['source_object_ref'][-8:]}", ok_source, source_ref)
    check(f"T10-binding:{schema}:{binding['binding_ref'][-8:]}", ok_binding, computed_binding)
check("T10 event count", t10["event_count"] == 12)
check("T10 unique bindings", t10["unique_binding_count"] == 11)
check("T10 shared order", t10["authorized_and_current_order_share_binding"] is True)
check("T10 relations", t10["relations_resolved"] is True)
check("T10 all refs unchanged", all(t10_results))

for label, binding in (("conflict", t12["conflict_fact"]), ("sidecar", t12["sidecar_result"])):
    schema = binding["projection_schema"]
    source_ref = source_ref_from_registry(
        binding["source_object_type"], schema, binding["projection"], registry[schema]["source_identity"]
    )
    candidate = dict(binding)
    candidate["source_object_ref"] = source_ref
    check(f"T12-{label}-source", source_ref == binding["source_object_ref"], source_ref)
    check(f"T12-{label}-binding", binding_ref(candidate, formula) == binding["binding_ref"])
check("T12 sidecar decision null", t12["sidecar_decision_extraction"] is None)

expected_negative_verdicts = {
    "missing_projection_schema": "FAIL_CLOSED",
    "payload_projection_only": "INVALID_REF_MISMATCH",
    "schema_string_changed": "REF_CHANGED",
    "projection_field_changed": "REF_CHANGED",
    "source_type_prefix_changed": "INVALID_OBJECT_IDENTITY_MISMATCH",
    "prefix_case_changed": "INVALID_PREFIX_MISMATCH",
    "digest_uppercase": "INVALID_DIGEST_ENCODING_MISMATCH",
    "digest_not_64_hex": "INVALID_DIGEST_FORMAT_MISMATCH",
    "float_input": "FAIL_CLOSED",
    "nan_input": "FAIL_CLOSED",
    "infinity_input": "FAIL_CLOSED",
    "payload_includes_source_object_ref": "INVALID_PAYLOAD_SCHEMA_MISMATCH",
    "parent_ev_builder_as_resolver": "FORBIDDEN_RESOLVER",
}
actual_negative = {item["case_id"]: item for item in vectors["negative_matrix"]}
check("negative cases exact", set(actual_negative) == set(expected_negative_verdicts), sorted(actual_negative))
for case_id, verdict in expected_negative_verdicts.items():
    check(f"negative:{case_id}:verdict", actual_negative[case_id]["verdict"] == verdict, actual_negative[case_id])
    check(f"negative:{case_id}:actual-present", bool(actual_negative[case_id]["actual"]))

# Re-execute canonicalization fail-closed boundaries independently.
for case_id, value in (("float", 1.0), ("nan", float("nan")), ("inf", float("inf"))):
    try:
        canonical({"x": value})
    except TypeError:
        failed_closed = True
    else:
        failed_closed = False
    check(f"canonical-fail-closed:{case_id}", failed_closed)

for marker in (
    "formula_id = PROJECTION_HASH_IDENTITY_V1",
    '"projection_schema": <exact schema string>',
    '"projection": <exact canonical primitive projection>',
    "source_object_type` 只进入固定前缀，不进入 hash payload",
    "lowercase_hex(SHA-256(payload_bytes))",
    ":projection-sha256:",
    "不包含 `binding_ref` 或 `source_object_ref`",
):
    check(f"design-marker:{marker}", marker in design_text)
for marker in (
    "PROJECTION_HASH_IDENTITY_V1",
    "EV-01-coverage-projection-identity-formula.json",
    "product-authoritative-trace-coverage/v4",
    "不得读取父 EV builder",
):
    check(f"coverage-doc:{marker}", marker in coverage_text)
for marker in (
    "Object identity 两条路径",
    "NATIVE_TEMPLATE",
    "PROJECTION_HASH_IDENTITY_V1",
    "只读取 envelope 和内置冻结 registry",
    "source identity hash 与 `binding_ref` full-binding digest",
):
    check(f"measurement:{marker}", marker in measurement_text)
for marker in (
    "State: `CONDITIONAL_NOT_FROZEN`",
    "prerequisite = measurement adapter accepted",
    "runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE",
    "events = exact 12",
    "source_bindings = exact 11 unique bindings",
):
    check(f"next-slice:{marker}", marker in next_text)

# Parent fixed evidence hashes must remain unchanged.
recorded_hashes = vectors["parent_fixed_artifact_hashes_before"]
for path in (PARENT_COVERAGE, PARENT_T10, PARENT_T12, PARENT_REFS):
    check(f"parent-hash:{path.name}", sha256(path) == recorded_hashes[path.name], sha256(path))
check("parent hashes before/after equal", vectors["parent_fixed_artifacts_unchanged"] is True)
check("baseline product trace", vectors["baseline"]["product_observed_authoritative_trace"] == "0/12 VALID")
check("baseline GESR", vectors["baseline"]["gesr"] == "0/12")
check("no new business rule", vectors["baseline"]["new_business_rule_required"] is False)

# No formal next implementation contracts are allowed.
formal_contracts = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V2/CONTRACT.md",
]
check("no next formal contracts", not any(path.exists() for path in formal_contracts))

src_text = "\n".join(read_allowed(path) for path in sorted((ROOT / "src").rglob("*.py")))
check("no product trace producer", "authoritative_trace=ProductAuthoritativeTrace" not in src_text.replace(" ", ""))

# The project-input allowlist proves the parent builder was not read. Its basename
# is not in READ_PATHS, and every project file read went through read_allowed().
forbidden_basename = "EV-01-build-grounded-reference-model.py"
check("forbidden builder not read", all(forbidden_basename not in path for path in READ_PATHS), READ_PATHS)
check("forbidden builder not imported", forbidden_basename not in " ".join(READ_PATHS))

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
print(f"project_input_count={len(set(READ_PATHS))}")
print("allowed_inputs=")
for path in sorted(set(READ_PATHS)):
    print(f"- {path}")
print("forbidden_parent_builder_read=false")
print("forbidden_parent_builder_imported=false")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")
