from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from agentic_payment_experiment.interactive_lab import (
    build_interactive_catalog,
    evaluate_interactive_scenario,
)
from agentic_payment_experiment.interactive_server import create_interactive_server


class InteractiveLabTest(unittest.TestCase):
    def test_catalog_covers_all_current_scenarios_with_small_field_sets(self) -> None:
        catalog = build_interactive_catalog()

        self.assertEqual(
            [f"S{index:02d}" for index in range(1, 14)],
            sorted(catalog["scenarios"]),
        )
        self.assertTrue(
            all(len(item["fields"]) <= 3 for item in catalog["scenarios"].values())
        )

    def test_core_pre_payment_inputs_are_recomputed(self) -> None:
        self.assertEqual(
            "ALLOW",
            evaluate_interactive_scenario("S02", {"request.amount": "480"})["decision"]["code"],
        )
        self.assertEqual(
            "ALLOW",
            evaluate_interactive_scenario("S05", {"request_seen": False})["decision"]["code"],
        )
        self.assertEqual(
            "ALLOW",
            evaluate_interactive_scenario("S08", {"request.amount": "480"})["decision"]["code"],
        )
        self.assertEqual(
            "ALLOW",
            evaluate_interactive_scenario(
                "S13", {"request.agent_id": "agent-shop-001"}
            )["decision"]["code"],
        )

    def test_s09_price_edit_keeps_simple_order_consistent(self) -> None:
        result = evaluate_interactive_scenario(
            "S09", {"final_order_and_request.total_amount": "480"}
        )
        self.assertEqual("ALLOW", result["decision"]["code"])
        matrix = result["presentation"]["lifecycle_teaching_view"]["matrix"]
        self.assertEqual("NONE", matrix["failure_type_code"])
        self.assertEqual("L4", matrix["primary_stage"])

    def test_matrix_projection_moves_with_recomputed_result(self) -> None:
        safe_budget = evaluate_interactive_scenario("S02", {"request.amount": "480"})
        self.assertEqual(
            "NONE",
            safe_budget["presentation"]["lifecycle_teaching_view"]["matrix"][
                "failure_type_code"
            ],
        )

        completed = evaluate_interactive_scenario(
            "S10", {"fulfillment.status": "SUCCEEDED"}
        )
        completed_matrix = completed["presentation"]["lifecycle_teaching_view"]["matrix"]
        self.assertEqual("NONE", completed_matrix["failure_type_code"])
        self.assertEqual("L9", completed_matrix["primary_stage"])

        duplicate_risk = evaluate_interactive_scenario(
            "S12",
            {
                "payment_status_observation.status": "FAILED",
                "parallel_attempt_status": "SUCCEEDED",
            },
        )
        duplicate_matrix = duplicate_risk["presentation"]["lifecycle_teaching_view"][
            "matrix"
        ]
        self.assertEqual("F4", duplicate_matrix["failure_type_code"])
        self.assertEqual("L5", duplicate_matrix["primary_stage"])
        self.assertEqual("L6", duplicate_matrix["detection_stage"])

    def test_lifecycle_inputs_are_recomputed(self) -> None:
        s10 = evaluate_interactive_scenario(
            "S10", {"fulfillment.status": "SUCCEEDED"}
        )
        self.assertEqual("SUCCEEDED", s10["lifecycle"]["task_status"])

        s11 = evaluate_interactive_scenario("S11", {"refund.status": "PENDING"})
        self.assertEqual("PENDING", s11["lifecycle"]["refund_status"])
        self.assertEqual("IN_PROGRESS", s11["lifecycle"]["remediation_status"])

    def test_s12_recovery_changes_with_status_idempotency_and_attempts(self) -> None:
        retry_candidate = evaluate_interactive_scenario(
            "S12", {"payment_status_observation.status": "FAILED"}
        )["payment_recovery"]
        self.assertEqual("RETRY_CANDIDATE", retry_candidate["recovery_status"])
        self.assertTrue(retry_candidate["retry_allowed"])

        existing_success = evaluate_interactive_scenario(
            "S12",
            {
                "payment_status_observation.status": "FAILED",
                "parallel_attempt_status": "SUCCEEDED",
            },
        )["payment_recovery"]
        self.assertEqual("BLOCKED", existing_success["recovery_status"])
        self.assertFalse(existing_success["retry_allowed"])

        missing_boundary = evaluate_interactive_scenario(
            "S12",
            {
                "payment_status_observation.status": "FAILED",
                "payment_recovery_initial.idempotency_key": "",
            },
        )["payment_recovery"]
        self.assertEqual("BLOCKED", missing_boundary["recovery_status"])
        self.assertFalse(missing_boundary["retry_allowed"])

    def test_unknown_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported interactive fields"):
            evaluate_interactive_scenario("S01", {"raw_secret": "x"})

    def test_local_http_api_recomputes_s13(self) -> None:
        with TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.html"
            report.write_text("<html><body>lab</body></html>", encoding="utf-8")
            server = create_interactive_server(report, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address[:2]
                payload = json.dumps(
                    {
                        "sample_id": "S13",
                        "overrides": {"request.agent_id": "agent-shop-001"},
                    }
                ).encode("utf-8")
                request = urllib.request.Request(
                    f"http://{host}:{port}/api/evaluate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=3) as response:
                    body = json.loads(response.read().decode("utf-8"))
                self.assertEqual("ALLOW", body["decision"]["code"])
                self.assertTrue(body["simulation_only"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
