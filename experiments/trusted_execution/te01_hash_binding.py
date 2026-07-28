"""TE-01: demonstrate deterministic Hash-based object binding."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.trusted_execution import canonical_hash, verify_hash


def main() -> None:
    authorized_order = {
        "order_id": "order-demo-001",
        "merchant_id": "merchant-A",
        "currency": "CNY",
        "amount": "780.00",
        "category": "shoes",
    }

    authorized_hash = canonical_hash(authorized_order)
    unchanged_order = deepcopy(authorized_order)
    tampered_order = deepcopy(authorized_order)
    tampered_order["category"] = "membership"

    print("TE-01 Hash 对象绑定实验")
    print(f"授权订单摘要: {authorized_hash}")
    print(f"原对象验证: {verify_hash(authorized_hash, unchanged_order)}")
    print(f"篡改对象验证: {verify_hash(authorized_hash, tampered_order)}")
    print(f"篡改后摘要: {canonical_hash(tampered_order)}")

    assert verify_hash(authorized_hash, unchanged_order)
    assert not verify_hash(authorized_hash, tampered_order)


if __name__ == "__main__":
    main()
