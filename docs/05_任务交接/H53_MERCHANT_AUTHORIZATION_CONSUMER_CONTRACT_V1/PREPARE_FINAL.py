"""Final evaluator scaffold check, without executing any merchant methods."""
import ast
import hashlib
import json
from RUNTIME import TASK, PARENT, bootstrap
bootstrap()
from CHECK import CASES

for path in TASK.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"))
original = json.loads((TASK / "INHERITED_COPY.json").read_text(encoding="utf-8"))["files"]
for name, expected in original.items():
    assert hashlib.sha256((TASK / name).read_bytes()).hexdigest() == expected
assert not (TASK / "merchant/services/ap2_authorization.py").exists()
import models
checkout = json.loads((TASK / "SAMPLE_CHECKOUT.json").read_text(encoding="utf-8"))
checkout["h53_unknown"] = {"terms": "synthetic-\u82b1\u5e97", "nested": [1, {"x": "keep"}]}
model = models.UnifiedCheckout(**checkout)
assert model.currency == checkout["currency"]
plan = json.loads((TASK / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
assert len(plan["checks"]) == 9
assert len(CASES) == 28
for check in plan["checks"]:
    assert check["mandatory"] and check["expected_exit_code"] == 0
    assert check["command"][0] == ".task_envs/H47/.venv/Scripts/python.exe"
    assert check["cwd"] == "."
print(json.dumps({"python_syntax": "PASS", "copied_source_files_unchanged": len(original),
    "full_model_with_unknown_member": "ACCEPTED", "frozen_scenarios": len(CASES),
    "validation_checks": len(plan["checks"]), "candidate_implemented": False,
    "candidate_scenarios_run": 0, "merchant_method_calls": 0}))
