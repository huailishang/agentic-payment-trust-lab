from __future__ import annotations

import base64
import json
import sys

from cryptography.hazmat.primitives.asymmetric import ec
from jwcrypto.jwk import JWK

from ap2.sdk.generated.open_payment_mandate import (
    AllowedPayees,
    AmountRange,
    OpenPaymentMandate,
)
from ap2.sdk.generated.payment_mandate import PaymentMandate
from ap2.sdk.generated.types.amount import Amount
from ap2.sdk.generated.types.merchant import Merchant
from ap2.sdk.generated.types.payment_instrument import PaymentInstrument
from ap2.sdk.mandate import MandateClient

from agentic_payment_experiment.adapters.ap2_official_verification import (
    verify_ap2_v020_official_two_hop_chain,
)
from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus

NOW = 1_800_000_000
AUD = "merchant"
NONCE = "tx_abc"


def jwk_with_kid(raw_key, kid: str) -> JWK:
    data = json.loads(JWK.from_pyca(raw_key).export())
    data["kid"] = kid
    return JWK(**data)


def public_mapping(jwk: JWK) -> dict[str, object]:
    return json.loads(jwk.export_public())


def make_open(agent_pub: dict[str, object], *, max_amount: int = 5000) -> OpenPaymentMandate:
    return OpenPaymentMandate(
        constraints=[
            AmountRange(currency="USD", min=0, max=max_amount),
            AllowedPayees(allowed=[Merchant(id="M-1", name="Cat Store")]),
        ],
        cnf={"jwk": agent_pub},
        iat=NOW,
        exp=NOW + 3600,
    )


def make_closed() -> PaymentMandate:
    return PaymentMandate(
        transaction_id=NONCE,
        payee=Merchant(id="M-1", name="Cat Store"),
        payment_amount=Amount(amount=2500, currency="USD"),
        payment_instrument=PaymentInstrument(
            type="card", id="stub", description="Demo"
        ),
        iat=NOW,
        exp=NOW + 3600,
    )


def build_chain(
    issuer_jwk: JWK,
    agent_jwk: JWK,
    *,
    root_agent_pub: dict[str, object] | None = None,
    max_amount: int = 5000,
) -> tuple[str, str]:
    client = MandateClient()
    pub = root_agent_pub if root_agent_pub is not None else public_mapping(agent_jwk)
    root = client.create(
        payloads=[make_open(pub, max_amount=max_amount)],
        issuer_key=issuer_jwk,
    )
    chain = client.present(
        holder_key=agent_jwk,
        mandate_token=root,
        payloads=[make_closed()],
        nonce=NONCE,
        aud=AUD,
    )
    return root, chain


def _decode_b64url(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _encode_b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def mutate_compact_signature(sd_segment: str) -> str:
    first, sep, rest = sd_segment.partition("~")
    parts = first.split(".")
    if len(parts) != 3 or not parts[2]:
        raise AssertionError("expected compact JWT at start of segment")

    original = _decode_b64url(parts[2])
    if not original:
        raise AssertionError("expected non-empty decoded signature")

    mutated_bytes = bytearray(original)
    mutation_index = len(mutated_bytes) // 2
    mutated_bytes[mutation_index] ^= 0x01
    mutated = bytes(mutated_bytes)
    if mutated == original:
        raise AssertionError("signature mutation did not change decoded bytes")

    parts[2] = _encode_b64url(mutated)
    compact = ".".join(parts)
    return compact + (sep + rest if sep else "")


def replace_root(chain: str, new_root: str) -> str:
    _old_root, sep, tail = chain.partition("~~")
    if not sep:
        raise AssertionError("expected two-hop chain")
    return new_root + sep + tail


def mutate_terminal_signature(chain: str) -> str:
    root, sep, tail = chain.partition("~~")
    if not sep:
        raise AssertionError("expected two-hop chain")
    return root + sep + mutate_compact_signature(tail)


def call(token: str, root_pub: dict[str, object], *, aud: str = AUD, nonce: str = NONCE):
    return verify_ap2_v020_official_two_hop_chain(
        token=token,
        root_public_jwk=root_pub,
        expected_aud=aud,
        expected_nonce=nonce,
        current_time=NOW,
    )


def expect(name: str, result, expected: VerificationStatus) -> None:
    if result.status != expected:
        raise AssertionError(
            f"{name}: expected {expected.value}, got {result.status.value}, reasons={result.reason_codes}"
        )
    if expected is VerificationStatus.VALID:
        if result.verified_hop_count != 2 or not result.official_verifier_completed:
            raise AssertionError(
                f"{name}: valid result did not prove two-hop official completion: {result}"
            )
    print(f"{name} PASS status={result.status.value}")


def main() -> int:
    issuer = jwk_with_kid(ec.generate_private_key(ec.SECP256R1()), "issuer-1")
    agent = jwk_with_kid(ec.generate_private_key(ec.SECP256R1()), "agent-1")
    wrong_root = jwk_with_kid(ec.generate_private_key(ec.SECP256R1()), "issuer-wrong")
    wrong_agent = jwk_with_kid(ec.generate_private_key(ec.SECP256R1()), "agent-wrong")

    root, chain = build_chain(issuer, agent)
    issuer_pub = public_mapping(issuer)

    expect("C01", call(chain, issuer_pub), VerificationStatus.VALID)
    expect("C02", call(chain, public_mapping(wrong_root)), VerificationStatus.INVALID)

    root_tampered = mutate_compact_signature(root)
    expect("C03", call(replace_root(chain, root_tampered), issuer_pub), VerificationStatus.INVALID)

    expect(
        "C04",
        call(mutate_terminal_signature(chain), issuer_pub),
        VerificationStatus.INVALID,
    )

    _bad_root, broken_cnf_chain = build_chain(
        issuer,
        agent,
        root_agent_pub=public_mapping(wrong_agent),
    )
    expect("C05", call(broken_cnf_chain, issuer_pub), VerificationStatus.INVALID)

    expect("C06", call(chain, issuer_pub, aud="wrong-aud"), VerificationStatus.INVALID)
    expect("C07", call(chain, issuer_pub, nonce="wrong-nonce"), VerificationStatus.INVALID)

    different_root = MandateClient().create(
        payloads=[make_open(public_mapping(agent), max_amount=5001)],
        issuer_key=issuer,
    )
    binding_tampered = replace_root(chain, different_root)
    expect("C08", call(binding_tampered, issuer_pub), VerificationStatus.INVALID)

    print("Summary: total=8 passed=8 failed=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
