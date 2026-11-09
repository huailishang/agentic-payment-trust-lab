"""Evaluator-only repair snapshot; copies the rejected implementation unchanged."""
import hashlib
import json
from pathlib import Path
import shutil

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def copy(source, name, replacements=()):
    target = TASK / name
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    if replacements:
        text = source.read_text(encoding="utf-8")
        for old, new in replacements:
            assert old in text, old
            text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(source, target)
    return {"source": source.relative_to(ROOT).as_posix(), "source_sha256": sha(source), "copy_sha256": sha(target)}

manifest = {}
for name in sorted(json.loads((PARENT / "INHERITED_COPY.json").read_text(encoding="utf-8"))["files"]):
    manifest[name] = copy(PARENT / name, name)
name = "merchant/services/ap2_authorization.py"
manifest[name] = copy(PARENT / name, name)
assert len(manifest) == 37
for name in ("FIXTURES.py", "SAMPLE_CHECKOUT.json", "UPSTREAM_LICENSE"):
    manifest[name] = copy(PARENT / name, name)
manifest["RUNTIME.py"] = copy(PARENT / "RUNTIME.py", "RUNTIME.py", [(".task_envs/H53/runs", ".task_envs/H53R/runs")])
manifest["FROZEN_TESTS.py"] = copy(PARENT / "FROZEN_TESTS.py", "FROZEN_TESTS.py", [
    (".task_envs/H53/runs", ".task_envs/H53R/runs"),
    ("(112 if evaluator else 280)", "(102 if evaluator else 272)")])
manifest["sources/H53_CHECK.py"] = copy(PARENT / "CHECK.py", "sources/H53_CHECK.py")
manifest["sources/evaluator/INDEPENDENT_CASES.py"] = copy(
    PARENT / "evidence/review_20261031/INDEPENDENT_CASES.py", "sources/evaluator/INDEPENDENT_CASES.py")
(TASK / "SOURCE_COPY.json").write_text(json.dumps({"parent_task": PARENT.name, "files": manifest,
    "adaptations": "Only scratch path and lower repair budget in frozen inherited harness; original cases and semantic assertions unchanged."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"merchant_files_copied": 37, "implementation_repaired": False}))
