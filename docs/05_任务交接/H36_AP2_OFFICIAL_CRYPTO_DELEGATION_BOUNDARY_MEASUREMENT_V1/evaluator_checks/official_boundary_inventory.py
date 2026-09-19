from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
AP2 = REPO / "local_sources" / "third_party" / "ap2-v0.2.0" / "code" / "sdk" / "python" / "ap2" / "sdk"

REQUIRED = {
    "mandate.py": ["MandateClient"],
    "checkout_mandate_chain.py": ["CheckoutMandateChain"],
    "payment_mandate_chain.py": ["PaymentMandateChain"],
    "receipt_wrapper.py": ["ReceiptClient"],
}


def symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
    return out


def methods(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def main() -> int:
    for rel, class_names in REQUIRED.items():
        path = AP2 / rel
        if not path.exists():
            print(f"missing official file: {path}")
            return 1
        found = symbols(path)
        for name in class_names:
            if name not in found:
                print(f"missing official symbol: {rel}:{name}")
                return 1

    mandate_methods = methods(AP2 / "mandate.py", "MandateClient")
    if "verify" not in mandate_methods:
        print("MandateClient.verify missing")
        return 1
    if "verify" not in methods(AP2 / "checkout_mandate_chain.py", "CheckoutMandateChain"):
        print("CheckoutMandateChain.verify missing")
        return 1
    if "verify" not in methods(AP2 / "payment_mandate_chain.py", "PaymentMandateChain"):
        print("PaymentMandateChain.verify missing")
        return 1
    if "verify_receipt" not in methods(AP2 / "receipt_wrapper.py", "ReceiptClient"):
        print("ReceiptClient.verify_receipt missing")
        return 1

    local = REPO / "src" / "agentic_payment_experiment" / "trusted_execution" / "signed_instruction.py"
    text = local.read_text(encoding="utf-8")
    if "ES256_ALGORITHM" not in text or "ec.ECDSA(hashes.SHA256())" not in text:
        print("local generic ES256 verifier evidence missing")
        return 1

    mandate_text = (AP2 / "mandate.py").read_text(encoding="utf-8")
    if "_chain.verify_chain(" not in mandate_text:
        print("MandateClient.verify -> verify_chain boundary missing")
        return 1

    print("OK")
    print("MandateClient.verify=present")
    print("verify_chain_call=present")
    print("CheckoutMandateChain.verify=present")
    print("PaymentMandateChain.verify=present")
    print("ReceiptClient.verify_receipt=present")
    print("local_ES256_verifier=present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
