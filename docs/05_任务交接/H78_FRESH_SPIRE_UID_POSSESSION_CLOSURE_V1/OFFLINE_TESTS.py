"""Candidate gate tests: historical data/ordinary fixtures, no new credentials."""
import ast
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import CONTROL as C
import CHECK
import QUALIFY

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
R2 = P.parent / "H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1"


class GateTests(unittest.TestCase):
    def sample(self):
        return {"run_id": "a" * 32, "nonce": "b" * 32, "status": "ISSUER_FETCH_SIGNATURE_CAPTURED", "started_utc": "2026-11-17T00:10:00+00:00", "finished_utc": "2026-11-17T00:11:00+00:00", "issued_at_epoch": int(datetime(2026, 11, 17, 0, 10, 20, tzinfo=timezone.utc).timestamp()), "observed_at_epoch": int(datetime(2026, 11, 17, 0, 10, 21, tzinfo=timezone.utc).timestamp())}

    def test_source_clock_accepts_host_offset_without_widening_freshness(self):
        data = self.sample()
        for offset in (-600, 0, 600):
            marker = {"run_id": data["run_id"], "nonce": data["nonce"], "begin_epoch": data["issued_at_epoch"] + offset}
            result = C.check_window(data, marker, marker["begin_epoch"] + 100)
            self.assertEqual(result["challenge_age_seconds"], 1)
            self.assertIs(result["cross_clock_comparison_used"], False)

    def test_source_order_staleness_nonce_and_completion_fail_closed(self):
        original = self.sample()
        marker = {"run_id": original["run_id"], "nonce": original["nonce"], "begin_epoch": original["issued_at_epoch"]}
        mutations = {"wrong_nonce": {"nonce": "c" * 32}, "wrong_run": {"run_id": "d" * 32}, "failed": {"status": "FAILED"}, "reversed": {"observed_at_epoch": original["issued_at_epoch"] - 1}, "before_source": {"issued_at_epoch": original["issued_at_epoch"] - 50}, "after_source": {"observed_at_epoch": original["observed_at_epoch"] + 100}, "bool_epoch": {"issued_at_epoch": True}, "naive_source": {"started_utc": "2026-11-17T00:10:00"}}
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                C.check_window({**original, **mutation}, marker, marker["begin_epoch"] + 100)
        stale = {**original, "finished_utc": "2026-11-17T00:20:00+00:00", "observed_at_epoch": original["issued_at_epoch"] + 301}
        with self.assertRaisesRegex(ValueError, "stale"):
            C.check_window(stale, marker, marker["begin_epoch"] + 100)

    def test_real_parent_clocks_are_recorded_without_inventing_success(self):
        meta = C.read(R2 / "evidence/l3/RV-EV-02.meta.json")
        result = C.read(R2 / "evidence/evaluator_runs/fef81b90a6594345b1212498ee52f90d/RESULT.json")
        self.assertGreater(datetime.fromisoformat(result["finished_utc"]), datetime.fromisoformat(meta["finished_at_utc"]))
        self.assertEqual(result["status"], "FAILED")
        self.assertNotIn("issued_at_epoch", result)

    def test_failure_run_resolves_without_success_pointer(self):
        self.assertFalse((R2 / "evidence/evaluator_current.json").exists())
        out = C.attempt_output(R2)
        result = C.cleanup_facts(out)
        self.assertTrue(result["cleanup_proven"])
        self.assertEqual(result["source_status"], "FAILED")

    def test_cleanup_missing_raw_and_false_flags_are_rejected(self):
        out = C.attempt_output(R2)
        original = C.read
        for field, value in (("owned_processes_alive", [123]), ("private_tmpfs_exists", True), ("public_private_key_files", 1), ("independent_check_exit_code", 1)):
            def changed(path, field=field, value=value):
                data = copy.deepcopy(original(path))
                if path.name == "CLEANUP.json":
                    data[field] = value
                return data
            with self.subTest(field=field), patch.object(C, "read", side_effect=changed), self.assertRaises(ValueError):
                C.cleanup_facts(out)

    def test_exact_accepted_collector_and_helpers_preserved(self):
        self.assertTrue(C.sources(P, ROOT)["byte_exact_collector"])

    def test_draft_route_cannot_start_live_or_preflight(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            task = root / P.name
            task.mkdir()
            (root / "CURRENT.md").write_text("```yaml\ntask_id: " + P.name + "\nstate: DRAFT_CONTRACT\ncurrent_role: Evaluator\n```\n", encoding="utf-8")
            for phase in ("executor", "evaluator"):
                with self.assertRaises(ValueError):
                    C.authority(task, root, phase)
        with patch.object(C, "authority", side_effect=ValueError("draft denied")), patch.object(CHECK.subprocess, "run") as launched, self.assertRaises(ValueError):
            CHECK.live()
        launched.assert_not_called()
        with patch.object(sys, "argv", ["QUALIFY.py", "--phase", "executor"]), patch.object(C, "authority", side_effect=ValueError("draft denied")), patch.object(QUALIFY.subprocess, "run") as launched, self.assertRaises(ValueError):
            QUALIFY.main()
        launched.assert_not_called()

    def test_windows_supervisor_does_not_timeout_cleanup(self):
        tree = ast.parse((P / "CHECK.py").read_text(encoding="utf-8"))
        live = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "live")
        launches = [node for node in ast.walk(live) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
        self.assertEqual(len(launches), 1)
        self.assertNotIn("timeout", [key.arg for key in launches[0].keywords])
        self.assertIn("signal.alarm(1100)", (P / "WORKLOAD.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
