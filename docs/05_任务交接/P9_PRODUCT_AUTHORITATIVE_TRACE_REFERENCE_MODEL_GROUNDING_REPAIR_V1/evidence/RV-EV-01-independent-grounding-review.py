from __future__ import annotations

import hashlib
import importlib
import json
import re
import subprocess
import sys
import types
from dataclasses import fields, is_dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
COVERAGE_PATH = EVIDENCE / "EV-01-coverage-reference-grounding.json"
MANIFEST_PATH = EVIDENCE / "EV-01-source-grounding-manifest.json"
EXAMPLES_PATH = EVIDENCE / "EV-01-reference-examples.json"
T10_PATH = EVIDENCE / "EV-01-t10-grounded-instance.json"
T12_PATH = EVIDENCE / "EV-01-t12-sidecar-examples.json"
DESIGN_PATH = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
ADAPTER_PATH = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
NEXT_SLICE_PATH = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
CURRENT_PATH = ROOT / "CURRENT.md"

sys.path.insert(0, str(ROOT / "src"))

checks: list[dict[str, Any]] = []


def check(name: str, condition: bool, detail: Any = None) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def recompute_binding(binding: dict[str, Any]) -> str:
    payload = {
        "source_object_type": binding["source_object_type"],
        "source_object_ref": binding["source_object_ref"],
        "projection_schema": binding["projection_schema"],
        "projection": binding["projection"],
    }
    return "TraceSourceBinding:sha256:" + sha256_json(payload)


def recompute_projection_identity(binding: dict[str, Any]) -> str | None:
    marker = ":projection-sha256:"
    ref = binding["source_object_ref"]
    if marker not in ref:
        return None
    prefix = ref.split(marker, 1)[0]
    identity_payload = {
        "projection_schema": binding["projection_schema"],
        "projection": binding["projection"],
    }
    return f"{prefix}{marker}{sha256_json(identity_payload)}"


def binding_digest(binding_ref: str) -> str:
    return binding_ref.rsplit(":", 1)[-1]


def get_projection_value(projection: dict[str, Any], path: str) -> Any:
    if not path.startswith("projection."):
        raise ValueError(f"not a projection path: {path}")
    key = path[len("projection.") :]
    array = key.endswith("[]")
    if array:
        key = key[:-2]
    value = projection[key]
    return list(value) if array else value


def render_template(template: str, projection: dict[str, Any], digest: str, value: Any = None) -> str:
    rendered = template.replace("{binding_digest}", digest)
    for field_name in re.findall(r"\{projection\.([A-Za-z0-9_]+)\}", rendered):
        rendered = rendered.replace(f"{{projection.{field_name}}}", str(projection[field_name]))
    if "{value}" in rendered:
        rendered = rendered.replace("{value}", str(value))
    return rendered


def unwrap_type(annotation: Any) -> Any:
    while True:
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin in (list, tuple, set, frozenset):
            annotation = args[0] if args else Any
            continue
        if origin in (types.UnionType, getattr(__import__("typing"), "Union")):
            non_none = [a for a in args if a is not type(None)]
            annotation = non_none[0] if len(non_none) == 1 else annotation
            continue
        return annotation


@lru_cache(maxsize=None)
def cached_type_hints(cls: type[Any]) -> dict[str, Any]:
    return get_type_hints(cls)


@lru_cache(maxsize=None)
def cached_field_types(cls: type[Any]) -> dict[str, Any]:
    hints = cached_type_hints(cls)
    return {f.name: hints.get(f.name, f.type) for f in fields(cls)}


def resolve_dataclass_path(root_class: type[Any], path: str) -> tuple[bool, str]:
    current: Any = root_class
    clean = path.replace("[]", "")
    for segment in clean.split("."):
        current = unwrap_type(current)
        if not isinstance(current, type) or not is_dataclass(current):
            return False, f"{getattr(current, '__name__', current)!r} is not a dataclass before {segment}"
        field_types = cached_field_types(current)
        if segment not in field_types:
            return False, f"{current.__module__}.{current.__name__}.{segment} missing"
        current = field_types[segment]
    return True, str(current)


def decimal_canonical(raw: str) -> str:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(raw) from exc
    if not value.is_finite():
        raise ValueError(raw)
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
t10 = json.loads(T10_PATH.read_text(encoding="utf-8"))
t12 = json.loads(T12_PATH.read_text(encoding="utf-8"))
design = DESIGN_PATH.read_text(encoding="utf-8")
adapter = ADAPTER_PATH.read_text(encoding="utf-8")
next_slice = NEXT_SLICE_PATH.read_text(encoding="utf-8")
current = CURRENT_PATH.read_text(encoding="utf-8")
registry: dict[str, dict[str, Any]] = coverage["projection_registry"]
tasks: list[dict[str, Any]] = coverage["tasks"]

# Contract/document invariants.
for token in (
    "source_object_ref",
    "binding_ref",
    "entity_ref",
    "relation.target_entity_ref",
    "ProductTraceEvent.source_binding_ref",
    "TraceSourceBinding:sha256",
):
    check(f"design contains {token}", token in design)
check("design forbids source_object_ref binding lookup", "不得再用 `source_object_ref` 查找 binding" in design)
check("duplicate binding verdict unified", "任意重复 `binding_ref`" in design and "统一 `INVALID`" in design)
check("sidecar decision not fabricated", "WebShopPaymentFulfilmentOutcome` 不再伪造 `decision`" in design)
check("adapter envelope only", "source_binding_ref" in adapter and "唯一" in adapter and "envelope" in adapter.lower())
check("next slice conditional", "CONDITIONAL_NOT_FROZEN" in next_slice)
check("next slice TBD hashes", "TBD_AFTER_ADAPTER_ACCEPTANCE" in next_slice)
check("current accepted for review", "state: READY_FOR_REVIEW" in current and "current_role: Evaluator" in current)

# Coverage and registry structure.
check("exact T01-T12", [t["task_id"] for t in tasks] == [f"T{i:02d}" for i in range(1, 13)])
check("all tasks NOT_AVAILABLE", all(t["current_status"] == "NOT_AVAILABLE" for t in tasks))
check("all tasks no new business rule", all(t["new_business_rule_required"] is False for t in tasks))
check("coverage baseline 0/12", coverage["current_product_observed_valid"] == "0/12")
check("coverage GESR 0/12", coverage["gesr"] == "0/12")
check("registry count 16", len(registry) == 16)
projection_hash_specs = {
    name: spec
    for name, spec in registry.items()
    if spec["source_identity"]["mode"] == "PROJECTION_HASH_IDENTITY"
}
expected_projection_identity_formula = (
    "<SourceType>:projection-sha256:sha256(canonical-json({projection_schema,projection}))"
)
check(
    "projection hash identity formula frozen in structured registry",
    bool(projection_hash_specs)
    and all(
        spec["source_identity"].get("formula") == expected_projection_identity_formula
        for spec in projection_hash_specs.values()
    ),
    {
        name: spec["source_identity"]
        for name, spec in projection_hash_specs.items()
    },
)
check(
    "projection hash identity payload frozen in authoritative design",
    "projection_schema" in design
    and "projection-sha256" in design
    and "canonical-json({projection_schema,projection})" in design.replace(" ", ""),
    "exact source identity formula must be implementable without reading EV builder code",
)
check("obsolete conflict type absent", "PaymentStatusConflictOutcome" not in canonical_json(coverage).decode("utf-8"))
check(
    "real conflict type present",
    any(v["source_class"] == "PaymentStatusConflictFact" for v in registry.values()),
)

allowed_transforms = {
    "DIRECT",
    "Decimal.canonical_string",
    "Enum.value",
    "Enum.value_or_null",
    "datetime.isoformat",
    "datetime.isoformat_or_null",
    "tuple.to_list",
    "tuple.map",
    "tuple.flatten_enum_values",
    "optional.singleton_tuple",
}

for schema, spec in registry.items():
    module = importlib.import_module(spec["source_module"])
    cls = getattr(module, spec["source_class"], None)
    check(f"{schema} class exists", isinstance(cls, type), f"{spec['source_module']}.{spec['source_class']}")
    if not isinstance(cls, type):
        continue
    check(f"{schema} class is dataclass", is_dataclass(cls))
    extraction_fields = set(spec["field_extractions"])
    projection_fields = set(spec["projection_fields"])
    check(f"{schema} extraction fields equal projection fields", extraction_fields == projection_fields)
    for projection_field, extraction in spec["field_extractions"].items():
        ok, detail = resolve_dataclass_path(cls, extraction["path"])
        check(f"{schema}.{projection_field} full source path resolves", ok, detail)
        check(
            f"{schema}.{projection_field} transform closed",
            extraction["transform"] in allowed_transforms,
            extraction["transform"],
        )
    check(f"{schema} entity template has no plus", "+" not in spec["entity_ref_template"])

sidecar_schema = registry["webshop-payment-fulfilment-outcome-result-trace/v2"]
check("sidecar projection excludes decision", "decision" not in sidecar_schema["projection_fields"])
conflict_schema = registry["payment-status-conflict-fact-trace/v2"]
for required in ("resolution", "effective_status", "reason_codes"):
    check(f"conflict projection includes {required}", required in conflict_schema["projection_fields"])

for task in tasks:
    events = task["events"]
    check(
        f"{task['task_id']} contiguous sequence",
        [e["sequence_no"] for e in events] == list(range(1, len(events) + 1)),
    )
    check(
        f"{task['task_id']} role set exact",
        set(task["entity_roles"]) == {e["entity_role"] for e in events},
    )
    role_index = {(e["entity_type"], e["entity_role"]): e for e in events}
    for event in events:
        schema = event["projection_schema"]
        spec = registry[schema]
        check(f"{task['task_id']}#{event['sequence_no']} binding required", event["source_binding_ref_required"] is True)
        check(f"{task['task_id']}#{event['sequence_no']} schema grounded", event["source_class"] == spec["source_class"] and event["source_module"] == spec["source_module"])
        check(f"{task['task_id']}#{event['sequence_no']} entity template closed", "+" not in event["entity_ref_template"])
        for key, path in event["value_paths"].items():
            if path is None:
                continue
            check(f"{task['task_id']}#{event['sequence_no']} {key} projection path", path.startswith("projection."))
            field_name = path[len("projection.") :].replace("[]", "")
            check(f"{task['task_id']}#{event['sequence_no']} {key} field exists", field_name in spec["projection_fields"], field_name)
        for relation in event["relations"]:
            target = (relation["target_entity_type"], relation["target_entity_role"])
            check(f"{task['task_id']}#{event['sequence_no']} relation target role exists", target in role_index, target)
            check(f"{task['task_id']}#{event['sequence_no']} relation template closed", "+" not in relation["target_entity_ref_template"])
            check(f"{task['task_id']}#{event['sequence_no']} relation source projection path", relation["source_assertion_path"].startswith("projection."))

# Decimal and fixed digest examples.
expected_decimal = {"0": "0", "-0": "0", "1": "1", "1.00": "1", "0.10": "0.1", "1000.000": "1000"}
actual_decimal = {raw: decimal_canonical(raw) for raw in expected_decimal}
check("decimal examples independently canonicalize", actual_decimal == expected_decimal, actual_decimal)
check("decimal example artifact matches", examples["decimal_examples"] == expected_decimal)
check("decimal example digest recomputes", sha256_json(expected_decimal) == examples["decimal_examples_sha256"])
for bad in ("NaN", "Infinity", "-Infinity"):
    try:
        decimal_canonical(bad)
        failed_closed = False
    except ValueError:
        failed_closed = True
    check(f"Decimal {bad} fails closed", failed_closed)
check("duplicate verdict exact", examples["duplicate_binding_verdict"].startswith("INVALID"))
for name, binding in examples["fixed_binding_examples"].items():
    check(f"fixed binding {name} digest recomputes", recompute_binding(binding) == binding["binding_ref"])
    projection_ref = recompute_projection_identity(binding)
    if projection_ref is not None:
        check(f"fixed binding {name} projection identity recomputes", projection_ref == binding["source_object_ref"])

# T10 full independent recomputation.
bindings = t10["bindings"]
events = t10["events"]
check("T10 event count 12", len(events) == t10["event_count"] == 12)
check("T10 unique binding count 11", len(bindings) == t10["unique_binding_count"] == 11)
check("T10 binding refs unique", len({b["binding_ref"] for b in bindings}) == len(bindings))
binding_by_ref = {b["binding_ref"]: b for b in bindings}
for binding in bindings:
    check(f"T10 binding {binding['projection_schema']} digest recomputes", recompute_binding(binding) == binding["binding_ref"])
    projection_ref = recompute_projection_identity(binding)
    if projection_ref is not None:
        check(f"T10 binding {binding['projection_schema']} projection identity recomputes", projection_ref == binding["source_object_ref"])

coverage_t10 = next(t for t in tasks if t["task_id"] == "T10")
profile_event_by_seq = {e["sequence_no"]: e for e in coverage_t10["events"]}
actual_event_index = {(e["entity_type"], e["entity_role"], e["entity_ref"]): e for e in events}
for event in events:
    seq = event["sequence_no"]
    profile_event = profile_event_by_seq[seq]
    binding = binding_by_ref.get(event["source_binding_ref"])
    check(f"T10 event {seq} binding resolves", binding is not None)
    if binding is None:
        continue
    check(f"T10 event {seq} object ref equals binding", event["source_object_ref"] == binding["source_object_ref"])
    expected_entity_ref = render_template(
        profile_event["entity_ref_template"],
        binding["projection"],
        binding_digest(binding["binding_ref"]),
    )
    check(f"T10 event {seq} entity ref recomputes", event["entity_ref"] == expected_entity_ref, expected_entity_ref)
    for value_key, path_key in (("decision", "decision_path"), ("status", "status_path"), ("reason_codes", "reason_codes_path")):
        path = profile_event["value_paths"][path_key]
        expected = [] if value_key == "reason_codes" and path is None else None
        if path is not None:
            expected = get_projection_value(binding["projection"], path)
        check(f"T10 event {seq} {value_key} recomputes", event[value_key] == expected, {"actual": event[value_key], "expected": expected})

    expected_relations: list[tuple[str, str, str, str]] = []
    for relation in profile_event["relations"]:
        source_value = get_projection_value(binding["projection"], relation["source_assertion_path"])
        values = source_value if relation["value_mode"] in ("ARRAY_EACH", "EACH", "EACH_VALUE") else [source_value]
        for value in values:
            target_ref = render_template(relation["target_entity_ref_template"], {}, "", value)
            expected_relations.append((relation["relation_type"], relation["target_entity_type"], relation["target_entity_role"], target_ref))
    actual_relations = [
        (r["relation_type"], r["target_entity_type"], r["target_entity_role"], r["target_entity_ref"])
        for r in event["relations"]
    ]
    check(f"T10 event {seq} relation refs recompute", sorted(actual_relations) == sorted(expected_relations), {"actual": actual_relations, "expected": expected_relations})
    for relation in event["relations"]:
        target_key = (relation["target_entity_type"], relation["target_entity_role"], relation["target_entity_ref"])
        check(f"T10 event {seq} relation target event exists", target_key in actual_event_index, target_key)
        check(f"T10 event {seq} relation assertions true", all(a["equal"] for a in relation["target_binding_assertions"]))

order_events = [events[1], events[2]]
check("T10 two order roles differ", {e["entity_role"] for e in order_events} == {"AUTHORIZED_ORDER_SNAPSHOT", "CURRENT_ORDER_SNAPSHOT"})
check("T10 order binding shared", order_events[0]["source_binding_ref"] == order_events[1]["source_binding_ref"])
check("T10 order object ref shared", order_events[0]["source_object_ref"] == order_events[1]["source_object_ref"])
check("T10 order entity ref shared", order_events[0]["entity_ref"] == order_events[1]["entity_ref"])
check("T10 no hidden resolver", t10["hidden_resolver_used"] is False)
check("T10 relation summary true", t10["relations_resolved"] is True and all(r["target_resolved"] and r["all_binding_assertions_equal"] for r in t10["relation_resolution"]))

# T12/sidecar exact binding and field grounding.
for name in ("conflict_fact", "sidecar_result"):
    binding = t12[name]
    check(f"T12 {name} binding digest recomputes", recompute_binding(binding) == binding["binding_ref"])
    check(f"T12 {name} projection identity recomputes", recompute_projection_identity(binding) == binding["source_object_ref"])
check("T12 real conflict type", t12["conflict_fact"]["source_object_type"] == "PaymentStatusConflictFact")
check("T12 sidecar decision extraction null", t12["sidecar_decision_extraction"] is None)
check("T12 sidecar projection has no decision", "decision" not in t12["sidecar_result"]["projection"])
check("T12 runtime not executed", t12["runtime_executed"] is False)

# Scope, HEAD and producer boundary.
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
check("HEAD unchanged", head == "979ffc505bec0b626858d0d186f655867b5491bf", head)
tracked_diff = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
protected_prefixes = ("src/", "tests/", "scripts/", "samples/")
check("protected tracked scope unchanged", not any(p.startswith(protected_prefixes) for p in tracked_diff), tracked_diff)
check("protected untracked scope unchanged", not any(p.startswith(protected_prefixes) for p in untracked), untracked)
producer_search = subprocess.run(
    ["grep", "-R", "-n", "authoritative_trace", "src"],
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
check("no product authoritative_trace producer", producer_search.returncode == 1, producer_search.stdout)

failed = [c for c in checks if not c["passed"]]
result = {
    "task_id": "P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1",
    "check_count": len(checks),
    "passed_count": len(checks) - len(failed),
    "failed_count": len(failed),
    "failed": failed,
    "summary": {
        "registry_schemas": len(registry),
        "tasks": len(tasks),
        "t10_events": len(events),
        "t10_unique_bindings": len(bindings),
        "head": head,
        "protected_tracked_changes": [p for p in tracked_diff if p.startswith(protected_prefixes)],
        "protected_untracked_changes": [p for p in untracked if p.startswith(protected_prefixes)],
    },
    "verdict": "PASS" if not failed else "BLOCKING_FINDINGS_PRESENT",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if not failed else 1)
