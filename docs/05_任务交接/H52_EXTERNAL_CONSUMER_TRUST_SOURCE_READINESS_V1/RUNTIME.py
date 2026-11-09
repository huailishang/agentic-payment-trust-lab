"""Frozen task-only bootstrap; no dependency installs or product patching."""
from pathlib import Path
import importlib.metadata
import json
import runpy
import socket
import sys
import tempfile

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
AP2 = ROOT / "local_sources/third_party/ap2-v0.2.0/code/sdk/python"
LEGACY = ROOT / ".task_envs/h37_ap2_crypto/lib/python3.12/site-packages"
_BOOTSTRAPPED = False
def bootstrap():
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(AP2))
    # Only jwcrypto and sd-jwt are reused from the old pure-Python dependency tree.
    # Compiled cryptography/pydantic continue to resolve from the H47 Windows venv.
    if str(LEGACY) not in sys.path:
        sys.path.append(str(LEGACY))
    from ap2.sdk import mandate
    scratch = ROOT / ".task_envs/H52/runs"
    scratch.mkdir(parents=True, exist_ok=True)
    mandate.LOG_FILE_PATH = str(scratch / "synthetic-sdk-operations.log")
    original_connect = socket.socket.connect
    def denied(*args, **kwargs):
        caller = sys._getframe(1)
        if caller.f_code.co_name == "socketpair" and Path(caller.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
            return original_connect(*args, **kwargs)
        raise AssertionError("H52 network budget is zero")
    socket.socket.connect = denied
    socket.create_connection = denied
    socket.getaddrinfo = denied
    _BOOTSTRAPPED = True

def preflight():
    bootstrap()
    import cryptography
    import pydantic
    import jwcrypto.jwk
    import sd_jwt.verifier
    import ap2.sdk.mandate
    assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix
    for name in ("cryptography", "pydantic"):
        module = sys.modules[name]
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), name
    for module in (jwcrypto.jwk, sd_jwt.verifier):
        assert Path(module.__file__).resolve().is_relative_to(LEGACY.resolve())
    assert Path(ap2.sdk.mandate.__file__).resolve().is_relative_to(AP2.resolve())
    value = {name: importlib.metadata.version(name) for name in ("cryptography", "pydantic", "jwcrypto", "sd-jwt", "ucp-sdk", "PyYAML")}
    assert value == {"cryptography": "46.0.7", "pydantic": "2.13.4", "jwcrypto": "1.5.6", "sd-jwt": "0.10.4", "ucp-sdk": "0.4.6", "PyYAML": "6.0.3"}
    print(json.dumps({"existing_runtime": "READY", "packages": value, "packages_installed": 0}))

if __name__ == "__main__":
    if sys.argv[1:] == ["preflight"]:
        preflight()
    elif sys.argv[1:] == ["official-regression"]:
        bootstrap()
        runpy.run_path(str(ROOT / "docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/evaluator_checks/official_two_hop_cases.py"), run_name="__main__")
    elif sys.argv[1:] == ["focused-regression"]:
        bootstrap()
        import unittest
        suite = unittest.TestLoader().loadTestsFromNames([
            "tests.test_ap2_protocol_boundary", "tests.test_ap2_sdk_bridge", "tests.test_ap2_official_verification",
            "tests.trusted_execution.test_confirmation", "tests.test_webshop_runtime_gate"])
        assert suite.countTestCases() == 76, "focused regression discovery drift"
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    else:
        raise SystemExit("Use preflight, official-regression or focused-regression")
