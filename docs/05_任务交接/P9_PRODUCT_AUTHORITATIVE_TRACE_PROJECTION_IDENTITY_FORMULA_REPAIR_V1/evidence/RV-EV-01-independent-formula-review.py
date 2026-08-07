from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
PARENT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence"

CURRENT_COVERAGE = EVIDENCE / "EV-01-coverage-projection-identity-formula.json"
VECTORS = EVIDENCE / "EV-01-projection-identity-vectors.json"
PARENT_COVERAGE = PARENT / "EV-01-coverage-reference-grounding.json"
PARENT_REFS = PARENT / "EV-01-reference-examples.json"
PARENT_T10 = PARENT / "EV-01-t10-grounded-instance.json"
PARENT_T12 = PARENT / "EV-01-t12-sidecar-examples.json"
DESIGN = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
ADAPTER = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
CURRENT = ROOT / "CURRENT.md"

checks: list[dict[str, Any]] = []


def check(name: str, condition: bool, detail: Any = None) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        raise ValueError("float forbidden")
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise ValueError("non-string key")
        return {k: canonicalize(v) for k, v in value.items()}
    raise ValueError(f"unsupported type: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def projection_ref(source_type: str, schema: str, projection: dict[str, Any]) -> str:
    if not schema:
        raise ValueError("projection_schema required")
    payload = {"projection_schema": schema, "projection": projection}
    return f"{source_type}:projection-sha256:{digest(payload)}"


def binding_ref(binding: dict[str, Any]) -> str:
    payload = {
        "source_object_type": binding["source_object_type"],
        "source_object_ref": binding["source_object_ref"],
        "projection_schema": binding["projection_schema"],
        "projection": binding["projection"],
    }
    return f"TraceSourceBinding:sha256:{digest(payload)}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_ref(spec: dict[str, Any], projection: dict[str, Any]) -> str:
    template = spec["source_identity"]["template"]
    if not template:
        raise ValueError("missing native template")
    return template.format(**projection)


coverage = json.loads(CURRENT_COVERAGE.read_text(encoding="utf-8"))
vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
parent_coverage = json.loads(PARENT_COVERAGE.read_text(encoding="utf-8"))
parent_refs = json.loads(PARENT_REFS.read_text(encoding="utf-8"))
parent_t10 = json.loads(PARENT_T10.read_text(encoding="utf-8"))
parent_t12 = json.loads(PARENT_T12.read_text(encoding="utf-8"))
design = DESIGN.read_text(encoding="utf-8")
adapter = ADAPTER.read_text(encoding="utf-8")
next_slice = NEXT_SLICE.read_text(encoding="utf-8")
current = CURRENT.read_text(encoding="utf-8")

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
}
expected_formula_registry = {
    **expected_formula,
    "payload_excludes": ["binding_ref", "source_object_ref"],
    "source_object_type_in_payload": False,
    "source_object_type_in_prefix": True,
}
formula_registry = coverage["projection_identity_formula_registry"]
check("formula registry has one formula", set(formula_registry) == {"PROJECTION_HASH_IDENTITY_V1"})
check("formula registry exact", formula_registry["PROJECTION_HASH_IDENTITY_V1"] == expected_formula_registry, formula_registry)
check("coverage schema v4", coverage["schema_version"] == "product-authoritative-trace-coverage/v4")
check("coverage baseline remains 0/12", coverage["current_product_observed_valid"] == "0/12")
check("coverage GESR remains 0/12", coverage["gesr"] == "0/12")
check("no new business rule", coverage["new_business_rule_required"] is False)

current_registry = coverage["projection_registry"]
parent_registry = parent_coverage["projection_registry"]
hash_schemas = [
    name for name, spec in current_registry.items()
    if spec["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY"
]
check("exactly 9 hash schemas", len(hash_schemas) == 9, hash_schemas)
check("same registry schema names as parent", set(current_registry) == set(parent_registry))

for schema, spec in current_registry.items():
    parent_spec = parent_registry[schema]
    mode = spec["source_identity"]["mode"]
    if mode == "PROJECTION_HASH_IDENTITY":
        check(f"{schema} formula exact", spec["source_identity"] == expected_formula, spec["source_identity"])
        current_without_identity = {k: v for k, v in spec.items() if k != "source_identity"}
        parent_without_identity = {k: v for k, v in parent_spec.items() if k != "source_identity"}
        check(f"{schema} non-identity fields unchanged", current_without_identity == parent_without_identity)
        check(f"{schema} parent mode was hash", parent_spec["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY")
    else:
        check(f"{schema} native identity unchanged", spec["source_identity"] == parent_spec["source_identity"])
        check(f"{schema} native schema unchanged", spec == parent_spec)

# The task must only enrich the registry formula, not rewrite task profiles.
check("T01-T12 tasks unchanged from parent", coverage["tasks"] == parent_coverage["tasks"])
for key in ("canonical_decimal", "forbidden_projection_fields", "reference_model"):
    check(f"coverage {key} unchanged", coverage[key] == parent_coverage[key])

for token in (
    "formula_id = PROJECTION_HASH_IDENTITY_V1",
    '"projection_schema": <exact schema string>',
    '"projection": <exact canonical primitive projection>',
    'separators=(",", ":")',
    "ensure_ascii=false",
    "allow_nan=false",
    "lowercase_hex(SHA-256(payload_bytes))",
    '":projection-sha256:"',
):
    check(f"design freezes {token}", token in design)
check("design excludes circular fields", "不包含 `binding_ref` 或 `source_object_ref`" in design)
check("design separates binding digest", "两个独立公式" in design)
for token in (
    "NATIVE_TEMPLATE",
    "PROJECTION_HASH_IDENTITY_V1",
    "adapter 只读取 envelope 和内置冻结 registry",
    "禁止读取 EV builder",
    "两者任一不一致都不能得到 `VALID`",
):
    check(f"adapter contains {token}", token in adapter)

# Parent fixed artifacts must still have the accepted hashes.
expected_parent_hashes = coverage["parent_fixed_artifact_hashes"]
parent_paths = {
    "EV-01-coverage-reference-grounding.json": PARENT_COVERAGE,
    "EV-01-reference-examples.json": PARENT_REFS,
    "EV-01-t10-grounded-instance.json": PARENT_T10,
    "EV-01-t12-sidecar-examples.json": PARENT_T12,
}
for name, path in parent_paths.items():
    check(f"parent artifact {name} hash unchanged", sha256_file(path) == expected_parent_hashes[name], sha256_file(path))
check("vectors before/after parent hashes equal", vectors["parent_fixed_artifact_hashes_before"] == vectors["parent_fixed_artifact_hashes_after"] == expected_parent_hashes)

# Build the set of concrete parent bindings; derived vectors must not masquerade as fixed history.
parent_bindings: list[dict[str, Any]] = list(parent_t10["bindings"])
parent_bindings.extend([parent_t12["conflict_fact"], parent_t12["sidecar_result"]])
parent_bindings.extend(parent_refs["fixed_binding_examples"].values())
parent_binding_keys = {
    (b["projection_schema"], b["source_object_ref"], b["binding_ref"])
    for b in parent_bindings
}
positive_vectors = vectors["positive_vectors"]
check("positive vectors cover 9 schemas", len(positive_vectors) == 9 and {v["projection_schema"] for v in positive_vectors} == set(hash_schemas))
check("7 parent fixed vectors", sum(v["parent_fixed"] for v in positive_vectors) == 7)
check("2 derived conformance vectors", sum(not v["parent_fixed"] for v in positive_vectors) == 2)
for vector in positive_vectors:
    schema = vector["projection_schema"]
    source_ref = projection_ref(vector["source_object_type"], schema, vector["projection"])
    binding = {
        "source_object_type": vector["source_object_type"],
        "source_object_ref": source_ref,
        "projection_schema": schema,
        "projection": vector["projection"],
    }
    computed_binding = binding_ref(binding)
    check(f"{schema} source ref independently recomputes", source_ref == vector["expected_source_object_ref"], source_ref)
    check(f"{schema} binding ref independently recomputes", computed_binding == vector["expected_binding_ref"], computed_binding)
    key = (schema, vector["expected_source_object_ref"], vector["expected_binding_ref"])
    if vector["parent_fixed"]:
        check(f"{schema} fixed vector exists in parent JSON", key in parent_binding_keys)
    else:
        check(f"{schema} derived vector not claimed as parent fixed", key not in parent_binding_keys)

# Recompute every parent T10 binding using only the current registry.
check("T10 remains 12 events", len(parent_t10["events"]) == parent_t10["event_count"] == 12)
check("T10 remains 11 bindings", len(parent_t10["bindings"]) == parent_t10["unique_binding_count"] == 11)
for binding in parent_t10["bindings"]:
    spec = current_registry[binding["projection_schema"]]
    if spec["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY":
        computed_source = projection_ref(binding["source_object_type"], binding["projection_schema"], binding["projection"])
    else:
        computed_source = native_ref(spec, binding["projection"])
    check(f"T10 {binding['projection_schema']} source ref unchanged", computed_source == binding["source_object_ref"], computed_source)
    computed_binding = binding_ref({**binding, "source_object_ref": computed_source})
    check(f"T10 {binding['projection_schema']} binding ref unchanged", computed_binding == binding["binding_ref"], computed_binding)
check("T10 shared order binding unchanged", parent_t10["authorized_and_current_order_share_binding"] is True)
check("T10 relations remain resolved", parent_t10["relations_resolved"] is True and all(r["target_resolved"] and r["all_binding_assertions_equal"] for r in parent_t10["relation_resolution"]))

# T12 fixed examples.
for key in ("conflict_fact", "sidecar_result"):
    binding = parent_t12[key]
    computed_source = projection_ref(binding["source_object_type"], binding["projection_schema"], binding["projection"])
    check(f"T12 {key} source ref unchanged", computed_source == binding["source_object_ref"], computed_source)
    check(f"T12 {key} binding ref unchanged", binding_ref({**binding, "source_object_ref": computed_source}) == binding["binding_ref"])
check("T12 sidecar decision stays null", parent_t12["sidecar_decision_extraction"] is None)

# Independent tamper checks and exact vector matrix coverage.
base = next(v for v in positive_vectors if v["parent_fixed"])
base_ref = projection_ref(base["source_object_type"], base["projection_schema"], base["projection"])
try:
    projection_ref(base["source_object_type"], "", base["projection"])
    missing_schema_failed = False
except ValueError:
    missing_schema_failed = True
check("negative missing schema fails closed", missing_schema_failed)
projection_only = f"{base['source_object_type']}:projection-sha256:{digest(base['projection'])}"
check("negative projection-only ref differs", projection_only != base_ref)
check("negative changed schema changes ref", projection_ref(base["source_object_type"], base["projection_schema"] + "-tampered", base["projection"]) != base_ref)
changed_projection = dict(base["projection"])
first_key = next(iter(changed_projection))
changed_projection[first_key] = str(changed_projection[first_key]) + "-tampered"
check("negative changed projection changes ref", projection_ref(base["source_object_type"], base["projection_schema"], changed_projection) != base_ref)
check("negative changed source type changes prefix", projection_ref(base["source_object_type"] + "Tampered", base["projection_schema"], base["projection"]) != base_ref)
ref_pattern = re.compile(r"^[A-Za-z][A-Za-z0-9]*:projection-sha256:[0-9a-f]{64}$")
check("base ref exact format", bool(ref_pattern.fullmatch(base_ref)), base_ref)
check("uppercase digest invalid format", not bool(ref_pattern.fullmatch(base_ref.rsplit(":", 1)[0] + ":" + base_ref.rsplit(":", 1)[1].upper())))
check("63 hex invalid format", not bool(ref_pattern.fullmatch(base_ref[:-1])))
for bad in (1.1, float("nan"), float("inf")):
    try:
        projection_ref(base["source_object_type"], base["projection_schema"], {"bad": bad})
        rejected = False
    except (ValueError, TypeError):
        rejected = True
    check(f"bad numeric {bad!r} fails closed", rejected)
extra_payload_ref = f"{base['source_object_type']}:projection-sha256:{digest({'projection_schema': base['projection_schema'], 'projection': base['projection'], 'source_object_ref': base_ref})}"
check("payload with source_object_ref differs", extra_payload_ref != base_ref)
expected_case_verdicts = {
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
actual_case_verdicts = {c["case_id"]: c["verdict"] for c in vectors["negative_matrix"]}
check("negative matrix exact cases/verdicts", actual_case_verdicts == expected_case_verdicts, actual_case_verdicts)
check("parent builder explicitly forbidden", vectors["independent_checker_forbidden_input"] == "EV-01-build-grounded-reference-model.py")

# Next-slice and workflow/scope boundary.
for token in ("State: `CONDITIONAL_NOT_FROZEN`", "TBD_AFTER_ADAPTER_ACCEPTANCE", "12 events", "11 unique bindings"):
    check(f"next slice contains {token}", token in next_slice)
check("next slice still requires adapter acceptance", "measurement adapter accepted" in next_slice)
check("current accepted for review", "state: READY_FOR_REVIEW" in current and "current_role: Evaluator" in current)
baseline_head = "979ffc505bec0b626858d0d186f655867b5491bf"
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
range_commits = subprocess.check_output(
    ["git", "rev-list", "--reverse", f"{baseline_head}..{head}"],
    cwd=ROOT,
    text=True,
).splitlines()
range_files = subprocess.check_output(
    ["git", "diff", "--name-only", f"{baseline_head}..{head}"],
    cwd=ROOT,
    text=True,
).splitlines()
head_subject = subprocess.check_output(
    ["git", "show", "-s", "--format=%s", head],
    cwd=ROOT,
    text=True,
).strip()
head_commit_time = int(
    subprocess.check_output(["git", "show", "-s", "--format=%ct", head], cwd=ROOT, text=True).strip()
)
report_path = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/REPORT.md"
ev04_path = EVIDENCE / "EV-04.stdout.log"
concurrent_commit_accepted = (
    head != baseline_head
    and range_commits == [head]
    and range_files == ["AGENTS.md"]
    and head_subject == "docs: add shared CodexPro shell safety rules"
    and head_commit_time > int(report_path.stat().st_mtime)
    and "?? AGENTS.md" in ev04_path.read_text(encoding="utf-8")
)
check(
    "HEAD is baseline or one audited post-submission concurrent commit",
    head == baseline_head or concurrent_commit_accepted,
    {
        "baseline_head": baseline_head,
        "live_head": head,
        "range_commits": range_commits,
        "range_files": range_files,
        "head_subject": head_subject,
        "report_mtime": int(report_path.stat().st_mtime),
        "head_commit_time": head_commit_time,
        "AGENTS_was_inherited_untracked_at_submission": "?? AGENTS.md" in ev04_path.read_text(encoding="utf-8"),
    },
)
ev04_text = ev04_path.read_text(encoding="utf-8")
hash_start = ev04_text.index("=== EXECUTOR ARTIFACT SHA256 / SIZE ===") + len("=== EXECUTOR ARTIFACT SHA256 / SIZE ===")
hash_end = ev04_text.index("=== COMPLETE TRACKED DIFF ===", hash_start)
executor_hash_rows: list[tuple[str, str]] = []
for line in ev04_text[hash_start:hash_end].strip().splitlines():
    parts = line.split("\t", 2)
    if len(parts) == 3 and len(parts[0]) == 64:
        executor_hash_rows.append((parts[2], parts[0]))
for relative_path, expected_hash in executor_hash_rows:
    if relative_path == "CURRENT.md":
        continue
    path = ROOT / relative_path
    check(
        f"submitted artifact unchanged: {relative_path}",
        path.is_file() and sha256_file(path) == expected_hash,
        sha256_file(path) if path.is_file() else "MISSING",
    )
tracked = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
protected = ("src/", "tests/", "scripts/", "samples/")
check("protected tracked unchanged", not any(p.startswith(protected) for p in tracked), tracked)
check("protected untracked unchanged", not any(p.startswith(protected) for p in untracked), untracked)
producer = subprocess.run(["grep", "-R", "-n", "authoritative_trace", "src"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
check("no product trace producer", producer.returncode == 1, producer.stdout)
contract_paths = [p for p in ROOT.glob("docs/05_任务交接/**/CONTRACT.md") if "MEASUREMENT_ADAPTER" in str(p) or "T10_DUPLICATE_PREFLIGHT_SLICE" in str(p)]
check("no adapter/T10 implementation contract frozen", not contract_paths, [str(p.relative_to(ROOT)) for p in contract_paths])

failed = [c for c in checks if not c["passed"]]
result = {
    "task_id": "P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1",
    "checks_total": len(checks),
    "checks_passed": len(checks) - len(failed),
    "checks_failed": len(failed),
    "failed": failed,
    "summary": {
        "formula_id": "PROJECTION_HASH_IDENTITY_V1",
        "hash_schema_count": len(hash_schemas),
        "parent_fixed_vectors": sum(v["parent_fixed"] for v in positive_vectors),
        "derived_conformance_vectors": sum(not v["parent_fixed"] for v in positive_vectors),
        "t10_events": len(parent_t10["events"]),
        "t10_bindings": len(parent_t10["bindings"]),
        "baseline_head": baseline_head,
        "live_head": head,
        "concurrent_commit_accepted": concurrent_commit_accepted,
        "concurrent_commit_files": range_files if concurrent_commit_accepted else [],
        "submitted_artifact_hashes_checked": len(executor_hash_rows) - 1,
    },
    "verdict": "PASS" if not failed else "BLOCKING_FINDINGS_PRESENT",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if not failed else 1)
