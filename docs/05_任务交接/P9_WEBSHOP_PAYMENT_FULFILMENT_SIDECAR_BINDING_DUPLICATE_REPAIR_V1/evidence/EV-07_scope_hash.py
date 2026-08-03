import hashlib
import json
from pathlib import Path


SOURCE_PATH = Path("src/agentic_payment_experiment/webshop_payment_sidecar.py")
TEST_PATH = Path("tests/test_webshop_payment_sidecar.py")
EVIDENCE_PATH = Path(
    "docs/05_任务交接/"
    "P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_BINDING_DUPLICATE_REPAIR_V1/"
    "evidence"
)

EXPECTED_PARENT_SOURCE = "a7950308864d71a25b36c43ff11aed8cfeef1f0fe4d373ab305849b770f95c3b"
EXPECTED_PARENT_TEST = "02b2a757f3d2656dbe38704d00001ef687c8935d70410c48669e1fb5ae832c74"
EXPECTED_CURRENT_SOURCE = "32c2428e3ff56fd4576a3265636b566cc63c5e1296cf3b1a63a0725eee8435e2"
EXPECTED_CURRENT_TEST = "06910d4c833cba21e973f87315e945fbdc6ed0b15736d6a49a45132b85c859e5"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


source = SOURCE_PATH.read_text(encoding="utf-8")
test_source = TEST_PATH.read_text(encoding="utf-8")
current_source_sha = sha256_text(source)
current_test_sha = sha256_text(test_source)

start = test_source.index("    def test_adapter_request_id_mismatch_fails_closed")
end = test_source.index(
    "    def test_payment_success_and_fulfillment_success_complete_user_task"
)
reconstructed_parent_test_sha = sha256_text(test_source[:start] + test_source[end:])

before_output = json.loads((EVIDENCE_PATH / "EV-01.stdout.log").read_text(encoding="utf-8"))
reconstructed_parent_source_sha = before_output["reconstructed_parent_sha256"]

checks = {
    "current_source_sha_matches": current_source_sha == EXPECTED_CURRENT_SOURCE,
    "current_test_sha_matches": current_test_sha == EXPECTED_CURRENT_TEST,
    "parent_source_sha_reconstructed": (
        reconstructed_parent_source_sha == EXPECTED_PARENT_SOURCE
    ),
    "parent_test_sha_reconstructed": (
        reconstructed_parent_test_sha == EXPECTED_PARENT_TEST
    ),
}
if not all(checks.values()):
    raise RuntimeError(json.dumps(checks, sort_keys=True))

print(
    json.dumps(
        {
            "checks": checks,
            "current": {
                str(SOURCE_PATH): current_source_sha,
                str(TEST_PATH): current_test_sha,
            },
            "reconstructed_parent": {
                str(SOURCE_PATH): reconstructed_parent_source_sha,
                str(TEST_PATH): reconstructed_parent_test_sha,
            },
            "authorizations_used": {
                "network_call": False,
                "api_call": False,
                "dependency_install": False,
                "create_environment": False,
                "webshop_runtime_execution": False,
                "buy_now_execution": False,
                "payment_or_order_side_effect": False,
                "commit": False,
                "push": False,
                "history_rewrite": False,
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
)
