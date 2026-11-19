"""One-time Evaluator correction before handoff; preserves the first frozen packet."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
target = P / "references/before_baseline_rebind"
if target.exists():
    raise RuntimeError("baseline correction already recorded")
target.mkdir(parents=True)
frozen = json.loads((P / "FREEZE.json").read_text(encoding="utf-8"))
for rel, expected in frozen["files"].items():
    source = P / rel
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise RuntimeError("prior freeze drift")
    destination = target / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
(target / "FREEZE.before.json").write_bytes((P / "FREEZE.json").read_bytes())
(target / "CURRENT.md").write_bytes((ROOT / "CURRENT.md").read_bytes())
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
names = subprocess.check_output(["git", "diff", "--name-only", "c6c617c9e20e227c7bfe967cc86ed9a102034036..HEAD", "-z"], cwd=ROOT).decode().strip("\0").split("\0")
record = {"at_utc": datetime.now(timezone.utc).isoformat(), "first_draft_baseline": "c6c617c9e20e227c7bfe967cc86ed9a102034036", "actual_head_at_input_lock": head, "changed_paths": names, "reason": "concurrent reference-only documentation commit; source digests and scope unchanged; align contract/router to already locked observed HEAD", "executor_started": False, "original_frozen_files_preserved": len(frozen["files"]), "formal_gates": 0, "commit_or_push_by_this_task": False}
(P / "BASELINE_REBIND.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# Only this explicit task-local file is removed after its bytes have been saved.
if hashlib.sha256((target / "FREEZE.before.json").read_bytes()).digest() != hashlib.sha256((P / "FREEZE.json").read_bytes()).digest():
    raise RuntimeError("freeze backup mismatch")
(P / "FREEZE.json").unlink()
print(json.dumps({"original_frozen_files_preserved": len(frozen["files"]), "observed_head": head, "changed_paths": len(names), "ready_to_correct_contract_router": True}))
