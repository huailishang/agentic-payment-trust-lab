"""Frozen same-input comparison plus the unchanged H80 after-behavior oracle."""
import argparse
import json
import os
import subprocess
import sys
import CHECK
from RUN_SUPPORT import P, ROOT, active, json_lines, save


def compare(before, observations):
    rows = [row for row in observations if "case_id" in row]
    paired = [row for row in rows if row["case_id"] in {"M01", "M02"}]
    CHECK.need([row["case_id"] for row in paired] == ["M01", "M02"], "missing after pair")
    CHECK.need([row["case_id"] for row in before["rows"]] == ["M01", "M02"], "missing before pair")
    for old, new in zip(before["rows"], paired):
        CHECK.need(old["consumer"] == new["consumer"], "comparison input changed")
        for key in ("identity_status", "decision", "callbacks", "binding", "context_policy"):
            CHECK.need(old[key] == new[key], "existing payment/base policy changed: " + key)
    CHECK.need([row["assurance"] for row in before["rows"]] == ["VERIFIED", "VERIFIED"], "baseline fact mismatch")
    CHECK.need([row["assurance"] for row in paired] == ["VERIFIED", "BOUND"], "original attribution counterexample not repaired")
    CHECK.need("credential_possession_context_mismatch" in paired[1]["identity_reasons"], "after reason missing")
    summary = observations[-1]
    CHECK.need(summary["consumer_observations"] == len(rows) == 33 and summary["original_crypto_negatives"] == 10, "incomplete original after matrix")
    source = observations[0]
    CHECK.need(source["source_run"] == before["source_run_id"] and source["time_mode"] == before["time_mode"], "source mismatch")
    CHECK.need(source["source_observed_at_epoch"] == before["observed_at_epoch"] and source["challenge_payload_sha256"] == before["challenge_payload_sha256"], "observation or signed payload changed")
    return {"same_inputs": True, "wrong_verified_before": 1, "wrong_verified_after": 0, "positive_verified_before": 1, "positive_verified_after": 1, "source_run_id": before["source_run_id"], "source_observed_at_epoch": before["observed_at_epoch"], "after_observations": len(rows), "after_original_crypto_negatives": summary["original_crypto_negatives"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    phase = parser.parse_args().phase
    tag = active(phase)
    CHECK.preservation()
    out = P / "evidence" / (phase + "_closure_" + tag)
    out.mkdir(parents=True, exist_ok=False)
    outputs = {}
    env = os.environ.copy()
    env.update(PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    for label, argv in (("BEFORE", [sys.executable, "-B", str(P / "BEFORE.py"), "--phase", phase]), ("AFTER", [sys.executable, "-B", str(P / "CHECK.py"), "behavior"])):
        proc = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=240)
        for stream in ("stdout", "stderr"):
            (out / (label + "." + stream + ".log")).write_bytes(getattr(proc, stream))
        save(out / (label + ".meta.json"), {"argv": argv, "exit_code": proc.returncode, "stdout_sha256": CHECK.sha(out / (label + ".stdout.log")), "stderr_sha256": CHECK.sha(out / (label + ".stderr.log"))})
        CHECK.need(proc.returncode == 0, "paired child failed; preserve raw evidence: " + label)
        outputs[label] = json_lines(proc.stdout)
    CHECK.need(len(outputs["BEFORE"]) == 1, "ambiguous before output")
    before = outputs["BEFORE"][0]
    metric = compare(before, outputs["AFTER"])
    source, source_data, _ = CHECK.proof_values()
    CHECK.need(before["observed_at_epoch"] == source_data["observed_at_epoch"] and before["challenge_payload_sha256"] == CHECK.sha(source / "payload.bin"), "historical observation or signed input changed")
    mutable = CHECK.read(P / "BASELINE.json")["mutable"]
    after_origins = {rel: CHECK.sha(ROOT / rel) for rel in CHECK.read(P / "BASELINE.json")["inherited_product_sha256"]}
    result = {"schema": "h81-paired-closure/v1", "phase": phase, "attempt": tag, "metric": metric, "before": before, "after_rows": [row for row in outputs["AFTER"] if "case_id" in row], "after_summary": outputs["AFTER"][-1], "after_product_sha256": after_origins, "test_sha256": {rel: CHECK.sha(ROOT / rel) for rel in mutable}, "source_lock_sha256": CHECK.sha(P / "SOURCE.json"), "actual_payment_calls": 0, "new_issuer_runs": 0, "time_mode": before["time_mode"]}
    save(out / "RESULT.json", result)
    print(json.dumps({"result_path": (out / "RESULT.json").relative_to(ROOT).as_posix(), "metric": metric, "formal_role": phase}, ensure_ascii=False))


if __name__ == "__main__":
    main()
