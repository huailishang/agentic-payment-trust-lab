"""Recompute the closure table from this attempt's raw outputs, never self-PASS."""
import argparse
import json
import CHECK
from COMPARE import compare
from RUN_SUPPORT import P, ROOT, active, json_lines, save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    phase = parser.parse_args().phase
    tag = active(phase)
    out = P / "evidence" / (phase + "_closure_" + tag)
    paired = CHECK.read(out / "RESULT.json")
    for label in ("BEFORE", "AFTER"):
        meta = CHECK.read(out / (label + ".meta.json"))
        CHECK.need(meta["exit_code"] == 0, "paired child unsuccessful")
        for stream in ("stdout", "stderr"):
            CHECK.need(CHECK.sha(out / (label + "." + stream + ".log")) == meta[stream + "_sha256"], "paired raw drift")
    before = json_lines((out / "BEFORE.stdout.log").read_bytes())[0]
    after = json_lines((out / "AFTER.stdout.log").read_bytes())
    CHECK.need(compare(before, after) == paired["metric"], "cannot reproduce pair metric")
    CHECK.need(before == paired["before"] and [row for row in after if "case_id" in row] == paired["after_rows"] and after[-1] == paired["after_summary"], "summary must match exact child evidence")
    CHECK.need(paired["source_lock_sha256"] == CHECK.sha(P / "SOURCE.json"), "source lock drift")
    for rel, value in {**paired["after_product_sha256"], **paired["test_sha256"]}.items():
        CHECK.need(CHECK.sha(ROOT / rel) == value, "paired current input drift")
    prefix = "RV-EV" if phase == "evaluator" else "EV"
    raw = []
    for index in range(1, 5):
        stem = prefix + "-" + str(index).zfill(2)
        meta_path = P / "evidence" / tag / (stem + ".meta.json")
        meta = CHECK.read(meta_path)
        CHECK.need(meta["exit_code"] == 0, "prior VP failed; no closure claim")
        for stream in ("stdout", "stderr"):
            path = meta_path.with_name(stem + "." + stream + ".log")
            CHECK.need(CHECK.sha(path) == meta[stream + "_sha256"] and path.stat().st_size == meta[stream + "_bytes"], "prior EV raw drift")
        raw.append(meta_path.relative_to(ROOT).as_posix())
    regression_path = P / "evidence" / tag / (prefix + "-03.stdout.log")
    regression = json_lines(regression_path.read_bytes())[-1]
    expected = {"original_regressions": 130, "original_payment_binding": 18, "new_tests": 6, "original_source_guards": 16, "protocol_positive": 4, "protocol_negative": 21, "original_offline_gates": 8, "parent_physical_source_runs": 0}
    CHECK.need(regression == expected, "incomplete required regressions")
    CHECK.preservation()
    rows = {row["case_id"]: row for row in paired["after_rows"]}
    closure = {"schema": "h81-b23-closure-table/v1", "phase": phase, "attempt": tag, "pair_metric": paired["metric"], "same_context_positive": rows["M01"]["assurance"], "agent_provider_executor_mismatch": {key: {"assurance": rows[key]["assurance"], "reasons": rows[key]["identity_reasons"]} for key in ("M02", "M03", "M04")}, "revoked_callback_count": rows["M06"]["callbacks"], "after_original_observations": 33, "original_crypto_negatives": 10, "regressions": regression, "raw_prior_meta": raw, "parent_h80_formal_l2_failed": 2, "superseded_h80r_formal_attempts": 0, "source_is_current_authentication": False, "actual_payment_calls": 0, "new_issuer_runs": 0, "decision_authority": "EVALUATOR_ONLY_AFTER_ACCEPTANCE_AND_UNIQUE_L3", "active_minutes": "UNKNOWN"}
    save(out / "CLOSURE.json", closure)
    print(json.dumps(closure, ensure_ascii=False))


if __name__ == "__main__":
    main()
