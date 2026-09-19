from __future__ import annotations

from importlib import metadata
import sys

EXPECTED = {
    "pydantic": "2.12.5",
    "jwcrypto": "1.5.6",
    "sd-jwt": "0.10.4",
    "cryptography": "46.0.5",
}


def main() -> int:
    observed: dict[str, str] = {}
    for package, expected in EXPECTED.items():
        try:
            actual = metadata.version(package)
        except metadata.PackageNotFoundError:
            print(f"missing dependency: {package}=={expected}", file=sys.stderr)
            return 1
        observed[package] = actual
        if actual != expected:
            print(f"version mismatch: {package} expected {expected}, got {actual}", file=sys.stderr)
            return 1

    try:
        from ap2.sdk.mandate import MandateClient
        from jwcrypto.jwk import JWK
        from sd_jwt.verifier import SDJWTVerifier
    except Exception as exc:
        print(f"official verifier import failed: {exc}", file=sys.stderr)
        return 1

    if MandateClient is None or JWK is None or SDJWTVerifier is None:
        print("official verifier imports unresolved", file=sys.stderr)
        return 1

    print("OK")
    for package in sorted(observed):
        print(f"{package}={observed[package]}")
    print("official_mandate_client=present")
    print("official_sdjwt_verifier=present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
