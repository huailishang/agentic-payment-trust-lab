from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
COVERAGE_PATH = EVIDENCE / "EV-01-coverage-reference-grounding.json"
REF_PATH = EVIDENCE / "EV-01-reference-examples.json"
SOURCE_PATH = EVIDENCE / "EV-01-source-grounding-manifest.json"
T10_PATH = EVIDENCE / "EV-01-t10-grounded-instance.json"
T12_PATH = EVIDENCE / "EV-01-t12-sidecar-examples.json"
TRACE_DOC = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
MEASUREMENT_DOC = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
NEXT_DOC = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
CONTRACT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/CONTRACT.md"

coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
refs = json.loads(REF_PATH.read_text(encoding="utf-8"))
sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
t10 = json.loads(T10_PATH.read_text(encoding="utf-8"))
t12 = json.loads(T12_PATH.read_text(encoding="utf-8"))
trace_text = TRACE_DOC.read_text(encoding="utf-8")
coverage_text = COVERAGE_DOC.read_text(encoding="utf-8")
measurement_text = MEASUREMENT_DOC.read_text(encoding="utf-8")
next_text = NEXT_DOC.read_text(encoding="utf-8")
contract_text = CONTRACT.read_text(encoding="utf-8")

checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: Any = "") -> None:
    checks.append((name, bool(condition), str(detail)))


def canonical(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise TypeError("float forbidden")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal")
        if value == 0:
            return "0"
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, tuple):
        return [canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical(item) for key, item in value.items()}
    raise TypeError(type(value).__name__)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def binding_ref(binding: dict[str, Any]) -> str:
    payload = {
        "source_object_type": binding["source_object_type"],
        "source_object_ref": binding["source_object_ref"],
        "projection_schema": binding["projection_schema"],
        "projection": binding["projection"],
    }
    return "TraceSourceBinding:sha256:" + digest(payload)


def projection_identity(source_type: str, schema: str, projection: dict[str, Any]) -> str:
    return f"{source_type}:projection-sha256:{digest({'projection_schema': schema, 'projection': projection})}"


def template_fields(template: str | None) -> set[str]:
    if not template:
        return set()
    return set(re.findall(r"\{(?:projection\.)?([A-Za-z_][A-Za-z0-9_]*)\}", template))


def render_entity(template: str, projection: dict[str, Any], ref: str) -> str:
    result = template.replace("{binding_digest}", ref.removeprefix("TraceSourceBinding:sha256:"))
    for field in re.findall(r"\{projection\.([A-Za-z_][A-Za-z0-9_]*)\}", result):
        result = result.replace(f"{{projection.{field}}}", str(projection[field]))
    return result


check("coverage schema v3", coverage.get("schema_version") == "product-authoritative-trace-coverage/v3")
check("coverage task id", coverage.get("generated_for_task") == "P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1")
check("product trace baseline", coverage.get("current_product_observed_valid") == "0/12")
check("GESR baseline", coverage.get("gesr") == "0/12")
check("no new business rule", coverage.get("new_business_rule_required") is False)
reference_model = coverage["reference_model"]
for key, expected in {
    "event_binding_lookup": "ProductTraceEvent.source_binding_ref",
    "duplicate_binding_ref_verdict": "INVALID",
    "unreferenced_binding_verdict": "INVALID",
    "missing_binding_verdict": "INDETERMINATE",
}.items():
    check(f"reference model {key}", reference_model.get(key) == expected, reference_model.get(key))
check("hidden resolver prohibited", reference_model.get("hidden_resolver_allowed") is False)
check("evaluator reconstruction prohibited", reference_model.get("evaluator_reconstruction_allowed") is False)
check("no external authenticity overclaim", reference_model.get("external_cryptographic_authenticity_claimed") is False)

registry = coverage["projection_registry"]
check("registry has 16 schemas", len(registry) == 16, len(registry))
check("source manifest schema count", sources.get("schema_count") == len(registry))
check("source manifest classes", sources.get("all_classes_exist") is True)
check("source manifest roots", sources.get("all_extraction_roots_exist") is True)
manifest_by_schema = {item["projection_schema"]: item for item in sources["schemas"]}
check("manifest exact schemas", set(manifest_by_schema) == set(registry))

for schema, spec in registry.items():
    prefix = f"registry:{schema}"
    check(prefix + ":module", isinstance(spec.get("source_module"), str) and bool(spec["source_module"]))
    check(prefix + ":class", isinstance(spec.get("source_class"), str) and bool(spec["source_class"]))
    check(prefix + ":binding-mode", spec.get("binding_ref_mode") == "EXACT_PROJECTION_DIGEST")
    check(prefix + ":projection-fields", set(spec.get("projection_fields", [])) == set(spec.get("field_extractions", {})))
    check(prefix + ":entity-template-no-plus", "+" not in spec["entity_ref_template"])
    check(prefix + ":entity-template-typed", ":" in spec["entity_ref_template"])
    manifest = manifest_by_schema[schema]
    check(prefix + ":manifest-class", manifest["source_class"] == spec["source_class"])
    check(prefix + ":manifest-module", manifest["source_module"] == spec["source_module"])
    source_file = ROOT / manifest["source_file"]
    check(prefix + ":source-file-exists", source_file.is_file(), source_file)
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    cls = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == spec["source_class"]), None)
    check(prefix + ":AST-class-exists", cls is not None)
    fields = {
        node.target.id
        for node in (cls.body if cls is not None else [])
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    for projected, extraction in spec["field_extractions"].items():
        root = re.split(r"\.|\[", extraction["path"], maxsplit=1)[0]
        check(prefix + f":field:{projected}:root", root in fields, f"{root} in {sorted(fields)}")
        check(prefix + f":field:{projected}:transform", isinstance(extraction["transform"], str) and bool(extraction["transform"]))
    identity = spec["source_identity"]
    check(prefix + ":identity-mode", identity["mode"] in {"NATIVE_TEMPLATE", "PROJECTION_HASH_IDENTITY"})
    if identity["mode"] == "NATIVE_TEMPLATE":
        check(prefix + ":native-template", isinstance(identity["template"], str) and bool(identity["template"]))
        check(prefix + ":native-template-no-plus", "+" not in identity["template"])
        check(prefix + ":native-template-fields", template_fields(identity["template"]).issubset(set(spec["projection_fields"])))
    else:
        check(prefix + ":hash-template-null", identity["template"] is None)

check("real conflict schema present", "payment-status-conflict-fact-trace/v2" in registry)
check("fake conflict schema absent", all("PaymentStatusConflictOutcome" not in json.dumps(spec) for spec in registry.values()))
sidecar_schema = registry["webshop-payment-fulfilment-outcome-result-trace/v2"]
check("sidecar decision absent", "decision" not in sidecar_schema["projection_fields"])
check("sidecar real fields", {"ready", "retry_allowed", "reason_codes", "lifecycle_task_status"}.issubset(sidecar_schema["projection_fields"]))
check("gate result decision present", "decision" in registry["webshop-buy-now-gate-outcome-result-trace/v2"]["projection_fields"])

expected_tasks = [f"T{i:02d}" for i in range(1, 13)]
tasks = coverage["tasks"]
check("exact T01-T12", [item["task_id"] for item in tasks] == expected_tasks)
for item in tasks:
    tid = item["task_id"]
    check(f"{tid}:not-available", item["current_status"] == "NOT_AVAILABLE")
    check(f"{tid}:no-new-rule", item["new_business_rule_required"] is False)
    events = item["events"]
    check(f"{tid}:continuous-sequence", [event["sequence_no"] for event in events] == list(range(1, len(events) + 1)))
    check(f"{tid}:roles-exact", item["entity_roles"] == [event["entity_role"] for event in events])
    role_keys = {(event["entity_type"], event["entity_role"]) for event in events}
    for event in events:
        ep = f"{tid}:{event['sequence_no']}"
        schema = event["projection_schema"]
        check(ep + ":known-schema", schema in registry, schema)
        spec = registry[schema]
        check(ep + ":source-module", event["source_module"] == spec["source_module"])
        check(ep + ":source-class", event["source_class"] == spec["source_class"])
        check(ep + ":source-type", event["source_object_type"] == spec["source_object_type"])
        check(ep + ":binding-required", event["source_binding_ref_required"] is True)
        check(ep + ":entity-no-plus", "+" not in event["entity_ref_template"])
        for name, path in event["value_paths"].items():
            check(ep + f":value-path:{name}:no-plus", path is None or "+" not in path)
            if path:
                field = path.removeprefix("projection.").removesuffix("[]")
                check(ep + f":value-path:{name}:field", field in spec["projection_fields"], field)
        for index, relation in enumerate(event["relations"]):
            rp = ep + f":relation:{index}"
            target = (relation["target_entity_type"], relation["target_entity_role"])
            check(rp + ":target-exists", target in role_keys, target)
            check(rp + ":target-template-no-plus", "+" not in relation["target_entity_ref_template"])
            source_field = relation["source_assertion_path"].removeprefix("projection.").removesuffix("[]")
            check(rp + ":source-field", source_field in spec["projection_fields"], source_field)
            check(rp + ":value-mode", relation["value_mode"] in {"SCALAR", "EACH_VALUE"})
            for assertion_index, assertion in enumerate(relation["target_binding_assertions"]):
                source_assertion_field = assertion["source_path"].removeprefix("projection.")
                check(rp + f":assert:{assertion_index}:source-field", source_assertion_field in spec["projection_fields"])

coverage_validation = coverage["coverage_validation"]
check("builder coverage 600 checks", coverage_validation.get("check_count") == 600, coverage_validation)
check("builder coverage zero failures", coverage_validation.get("failed_count") == 0, coverage_validation)

t10_profile = next(item for item in tasks if item["task_id"] == "T10")
expected_roles = [
    "AUTHORITY",
    "AUTHORIZED_ORDER_SNAPSHOT",
    "CURRENT_ORDER_SNAPSHOT",
    "CURRENT_REQUEST",
    "GOVERNED_ACTION",
    "CURRENT_PAYMENT_CANDIDATE",
    "ACTION_BINDING_FACT",
    "HISTORICAL_SUCCEEDED_PAYMENT",
    "KNOWN_PAYMENT_PREFLIGHT_FACT",
    "PREPAYMENT_VALIDATION",
    "RUNTIME_GATE_OBSERVATION",
    "FINAL_OUTCOME",
]
check("T10 profile 12", len(t10_profile["events"]) == 12)
check("T10 profile roles", [event["entity_role"] for event in t10_profile["events"]] == expected_roles)
check("T10 instance 12", t10["event_count"] == 12)
check("T10 instance 11 bindings", t10["unique_binding_count"] == 11)
check("T10 shared order binding", t10["authorized_and_current_order_share_binding"] is True)
check("T10 binding resolution", t10["event_binding_resolved"] is True)
check("T10 relation resolution", t10["relations_resolved"] is True)
check("T10 no hidden resolver", t10["hidden_resolver_used"] is False)
check("T10 runtime not executed", t10["fixture_basis"]["runtime_executed"] is False)
check("T10 literals only", t10["fixture_basis"]["objects_constructed_from_fixed_literals_only"] is True)

bindings = t10["bindings"]
binding_by_ref = {binding["binding_ref"]: binding for binding in bindings}
check("T10 binding refs unique", len(binding_by_ref) == len(bindings))
for index, binding in enumerate(bindings):
    bp = f"T10:binding:{index}:{binding['projection_schema']}"
    check(bp + ":known-schema", binding["projection_schema"] in registry)
    check(bp + ":digest", binding["binding_ref"] == binding_ref(binding))
    spec = registry[binding["projection_schema"]]
    check(bp + ":exact-fields", set(binding["projection"]) == set(spec["projection_fields"]), sorted(binding["projection"]))
    check(bp + ":source-type", binding["source_object_type"] == spec["source_object_type"])
    identity = spec["source_identity"]
    if identity["mode"] == "PROJECTION_HASH_IDENTITY":
        expected = projection_identity(binding["source_object_type"], binding["projection_schema"], binding["projection"])
        check(bp + ":projection-identity", binding["source_object_ref"] == expected)
    else:
        expected = identity["template"]
        for field in template_fields(expected):
            expected = expected.replace(f"{{{field}}}", str(binding["projection"][field]))
        check(bp + ":native-identity", binding["source_object_ref"] == expected, f"{binding['source_object_ref']} == {expected}")

instance_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
for event in t10["events"]:
    ep = f"T10-instance:{event['sequence_no']}:{event['entity_role']}"
    check(ep + ":binding-exists", event["source_binding_ref"] in binding_by_ref)
    binding = binding_by_ref[event["source_binding_ref"]]
    profile_event = t10_profile["events"][event["sequence_no"] - 1]
    check(ep + ":profile-event", event["event_type"] == profile_event["event_type"])
    check(ep + ":profile-type", event["entity_type"] == profile_event["entity_type"])
    check(ep + ":profile-role", event["entity_role"] == profile_event["entity_role"])
    expected_ref = render_entity(profile_event["entity_ref_template"], binding["projection"], binding["binding_ref"])
    check(ep + ":entity-ref", event["entity_ref"] == expected_ref, expected_ref)
    check(ep + ":source-object-ref", event["source_object_ref"] == binding["source_object_ref"])
    instance_by_key[(event["entity_type"], event["entity_role"], event["entity_ref"])] = event

for relation in t10["relation_resolution"]:
    rp = f"T10-relation:{relation['source_sequence_no']}:{relation['relation_type']}:{relation['target_entity_role']}"
    target_key = (relation["target_entity_type"], relation["target_entity_role"], relation["target_entity_ref"])
    check(rp + ":target-resolved", relation["target_resolved"] is True)
    check(rp + ":target-present", target_key in instance_by_key, target_key)
    check(rp + ":binding-assertions", relation["all_binding_assertions_equal"] is True)
    for idx, assertion in enumerate(relation["target_binding_assertions"]):
        check(rp + f":assert:{idx}", assertion["equal"] is True, assertion)

order_events = [event for event in t10["events"] if event["entity_role"] in {"AUTHORIZED_ORDER_SNAPSHOT", "CURRENT_ORDER_SNAPSHOT"}]
check("T10 exactly two order events", len(order_events) == 2)
check("T10 order same binding", len({event["source_binding_ref"] for event in order_events}) == 1)
check("T10 order same source ref", len({event["source_object_ref"] for event in order_events}) == 1)
check("T10 order same entity ref", len({event["entity_ref"] for event in order_events}) == 1)
current_payment = next(event for event in t10["events"] if event["entity_role"] == "CURRENT_PAYMENT_CANDIDATE")
history_payment = next(event for event in t10["events"] if event["entity_role"] == "HISTORICAL_SUCCEEDED_PAYMENT")
check("T10 payments differ", current_payment["entity_ref"] != history_payment["entity_ref"])
action = next(event for event in t10["events"] if event["entity_role"] == "GOVERNED_ACTION")
check("T10 action points current payment", any(rel["target_entity_ref"] == current_payment["entity_ref"] for rel in action["relations"]))
preflight = next(event for event in t10["events"] if event["entity_role"] == "KNOWN_PAYMENT_PREFLIGHT_FACT")
check("T10 preflight points history", any(rel["target_entity_ref"] == history_payment["entity_ref"] for rel in preflight["relations"]))

expected_decimal = {"0": "0", "-0": "0", "1": "1", "1.00": "1", "0.10": "0.1", "1000.000": "1000"}
check("Decimal examples", refs["decimal_examples"] == expected_decimal, refs["decimal_examples"])
check("Decimal examples digest", refs["decimal_examples_sha256"] == digest(expected_decimal))
for raw, expected in expected_decimal.items():
    check(f"Decimal:{raw}", canonical(Decimal(raw)) == expected)
for raw in ["NaN", "Infinity", "-Infinity"]:
    try:
        canonical(Decimal(raw))
    except ValueError:
        rejected = True
    else:
        rejected = False
    check(f"Decimal rejects {raw}", rejected)
try:
    canonical(1.0)
except TypeError:
    float_rejected = True
else:
    float_rejected = False
check("float rejected", float_rejected)
check("duplicate binding fixed verdict", refs["duplicate_binding_verdict"].startswith("INVALID"))
check("collision old equal", refs["collision_example"]["old_unsafe"]["ab+c"] == refs["collision_example"]["old_unsafe"]["a+bc"])
check("collision new distinct", refs["collision_example"]["new"]["first"] != refs["collision_example"]["new"]["second"])
for role, binding in refs["fixed_binding_examples"].items():
    check(f"fixed-binding:{role}:digest", binding["binding_ref"] == binding_ref(binding))

check("T12 conflict digest", t12["conflict_fact"]["binding_ref"] == binding_ref(t12["conflict_fact"]))
check("T12 sidecar digest", t12["sidecar_result"]["binding_ref"] == binding_ref(t12["sidecar_result"]))
check("T12 conflict real class", t12["conflict_fact"]["source_object_type"] == "PaymentStatusConflictFact")
check("T12 sidecar decision null", t12["sidecar_decision_extraction"] is None)
check("T12 decision separate runtime", "RuntimeGateRecord.final_decision" in t12["decision_source"])
check("T12 runtime not executed", t12["runtime_executed"] is False)

required_trace_markers = [
    "四类引用必须分开",
    "ProductTraceEvent.source_binding_ref",
    "任意重复 `binding_ref`",
    "Order:<order_id>",
    "-0→0",
    "PaymentStatusConflictFact",
    "WebShopPaymentFulfilmentOutcome` 不再伪造 `decision`",
    "12 events",
    "11 unique bindings",
    "hidden resolver = false",
    "0/12 VALID",
]
for marker in required_trace_markers:
    check(f"trace-doc:{marker}", marker in trace_text)
for marker in ["coverage checks = 600/600", "AttackOverlayResult", "PaymentStatusConflictFact", "11 unique bindings", "0/12 VALID"]:
    check(f"coverage-doc:{marker}", marker in coverage_text)
for marker in ["duplicate `binding_ref`", "Decimal", "source_object_ref identity", "sidecar RESULT", "0/12 VALID"]:
    check(f"measurement-doc:{marker}", marker in measurement_text)
for marker in ["CONDITIONAL_NOT_FROZEN", "exact 11 unique bindings", "两个 ORDER event 必须共享", "不构成执行合同"]:
    check(f"next-doc:{marker}", marker in next_text)
check("no measurement formal contract", not (ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/CONTRACT.md").exists())
check("no T10 formal contract", not (ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md").exists())

for finding in [f"F-0{i}" for i in range(1, 9)]:
    check(f"contract contains {finding}", finding in contract_text)

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")
