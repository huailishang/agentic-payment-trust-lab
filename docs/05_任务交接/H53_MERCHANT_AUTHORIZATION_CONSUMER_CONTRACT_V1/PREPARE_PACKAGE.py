"""Evaluator preparation only: preserve draft, copy fixed sources, inspect existing artifacts."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from RUNTIME import TASK, ROOT, PARENT, preflight, bootstrap

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    target = TASK / name
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), name
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    assert sys.argv[1:] == ["prepare"]
    preflight()
    original = TASK / "DRAFT_BEFORE_FREEZE_20261031.md"
    assert not original.exists()
    shutil.copy2(TASK / "CONTRACT.md", original)
    lock = json.loads((PARENT / "INHERITED_COPY.json").read_text(encoding="utf-8"))
    copied = {}
    for name, expected in lock["files"].items():
        source = PARENT / name
        assert sha(source) == expected, name
        target = TASK / name
        assert target.resolve().is_relative_to(TASK.resolve()) and not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied[name] = sha(target)
    assert len(copied) == 36
    shutil.copy2(PARENT / "UPSTREAM_LICENSE", TASK / "UPSTREAM_LICENSE")
    save("INHERITED_COPY.json", {"source_task": PARENT.name, "files": copied})
    observed = json.loads((PARENT / "evidence/http_l3.json").read_text(encoding="utf-8"))
    normal = next(c for c in observed["cases"] if c["case"] == "C01_NORMAL_REPLAY")
    checkout = next(c["response_body"] for c in normal["calls"] if c["method"] == "POST" and c["path"] == "/checkout-sessions")
    assert {"id", "ucp", "currency", "line_items", "totals", "fulfillment"} <= set(checkout)
    save("SAMPLE_CHECKOUT.json", checkout)
    from FIXTURES import keys, public, envelope, independent_materials
    registry = keys()
    fixture = envelope(checkout, "h53-preparation-only", registry)
    raw, verified = independent_materials(fixture, public(registry), "h53-preparation-only")
    assert raw == checkout and len(verified) == 2
    candidates = {name: importlib.util.find_spec(name) is not None for name in
                  ("jcs", "rfc8785", "canonicaljson", "json_canonicalization")}
    save("evidence/preparation_20261031/READINESS.json", {
        "phase": "EVALUATOR_PREPARATION_NOT_EXECUTOR_RESULT", "copied_merchant_files": len(copied),
        "sample_origin": "H51 accepted HTTP L3 C01 create response", "sample_sha256": sha(TASK / "SAMPLE_CHECKOUT.json"),
        "sample_top_level_fields": sorted(checkout), "full_raw_jws_and_two_hop_smoke": "PASS",
        "jcs_named_modules_found": candidates, "jcs_conformance": "NOT_ESTABLISHED",
        "private_keys_persisted": False, "merchant_method_calls": 0, "network_calls": 0,
        "asgi_requests": 0, "provider_calls": 0, "payment_calls": 0, "packages_installed": 0,
        "note": "Named-module absence is not an exhaustive proof that no JCS code exists; exact-byte local slice does not require JCS."
    })
    print(json.dumps({"copied": len(copied), "full_raw_jws_two_hop_smoke": "PASS", "merchant_execution": "NOT_RUN", "named_jcs_modules": candidates}))
