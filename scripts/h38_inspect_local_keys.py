"""Read an explicitly supplied local key file; emit metadata only, never values."""
import argparse
import base64
import re
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def inspect(path, *, return_keys=False):
    raw = Path(path).read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeError:
            pass
    if text is None:
        print("BLOCKED unsupported file encoding")
        return 1
    labels = re.compile(r"(应用私钥|应用公钥|支付宝公钥|AIPAY_PRIVATE_PKCS_KEY|AIPAY_ALIPAY_PUBLIC_KEY)\s*[:：=]?", re.I)
    matches = list(labels.finditer(text))
    keys = {}
    aliases = {"应用私钥": "app_private", "应用公钥": "app_public", "支付宝公钥": "alipay_public",
               "AIPAY_PRIVATE_PKCS_KEY": "app_private", "AIPAY_ALIPAY_PUBLIC_KEY": "alipay_public"}
    for index, match in enumerate(matches):
        name = aliases.get(match.group(1), aliases.get(match.group(1).upper()))
        if name in keys:
            print("BLOCKED duplicate key labels")
            return 1
        section = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        pem = re.search(r"-----BEGIN ([A-Z ]+KEY)-----.*?-----END \1-----", section, re.S)
        try:
            if pem:
                value = pem.group(0).encode("ascii")
                key = (serialization.load_pem_private_key(value, password=None)
                       if name == "app_private" else serialization.load_pem_public_key(value))
            else:
                candidates = re.findall(r"[A-Za-z0-9+/=]{100,}", section)
                if len(candidates) != 1:
                    print(name + "=unrecognized_format")
                    return 1
                value = base64.b64decode(candidates[0], validate=True)
                key = (serialization.load_der_private_key(value, password=None)
                       if name == "app_private" else serialization.load_der_public_key(value))
            expected = rsa.RSAPrivateKey if name == "app_private" else rsa.RSAPublicKey
            if not isinstance(key, expected) or key.key_size < 2048:
                print(name + "=unsupported_key_type_or_size")
                return 1
            keys[name] = key
            print(name + "=valid_RSA_" + str(key.key_size))
        except Exception:
            # Crypto exceptions may include input details; never echo them.
            print(name + "=parse_failed")
            return 1
    if not {"app_private", "alipay_public"} <= keys.keys():
        print("BLOCKED required labeled keys missing")
        return 1
    private = keys["app_private"]
    if "app_public" in keys:
        if private.public_key().public_numbers() != keys["app_public"].public_numbers():
            print("BLOCKED application key pair mismatch")
            return 1
        print("application_key_pair=matched")
    if private.public_key().public_numbers() == keys["alipay_public"].public_numbers():
        print("BLOCKED Alipay public key equals application public key")
        return 1
    message = b"H38 local configuration check - no payment"
    signature = private.sign(message, padding.PKCS1v15(), hashes.SHA256())
    private.public_key().verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
    print("local_RSA2_sign_verify=PASS")
    print("provider_key_provenance=NOT_VERIFIED")
    print("network_calls=0; secret_values_printed=false; secret_copies_written=false")
    return keys if return_keys else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        raise SystemExit(inspect(args.path))
    except (OSError, ValueError):
        print("BLOCKED file unavailable or invalid")
        raise SystemExit(1)
