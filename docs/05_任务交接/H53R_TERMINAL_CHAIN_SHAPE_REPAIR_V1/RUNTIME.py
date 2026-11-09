"""Frozen H53 runtime: existing libraries, no network or installation."""
import importlib.metadata
import json
from pathlib import Path
import runpy
import socket
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1"
AP2 = ROOT / "local_sources/third_party/ap2-v0.2.0/code/sdk/python"
LEGACY = ROOT / ".task_envs/h37_ap2_crypto/lib/python3.12/site-packages"
READY = False

def bootstrap():
    global READY
    if READY:
        return
    sys.dont_write_bytecode = True
    for path in (ROOT, ROOT / "src", AP2, TASK / "merchant"):
        sys.path.insert(0, str(path))
    sys.path.append(str(LEGACY))
    from ap2.sdk import mandate
    scratch = ROOT / ".task_envs/H53R/runs"
    scratch.mkdir(parents=True, exist_ok=True)
    mandate.LOG_FILE_PATH = str(scratch / "synthetic-sdk.log")
    original = socket.socket.connect
    def denied(*args, **kwargs):
        caller = sys._getframe(1)
        if caller.f_code.co_name == "socketpair" and Path(caller.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
            return original(*args, **kwargs)
        raise AssertionError("H53 network budget is zero")
    socket.socket.connect = denied
    socket.create_connection = denied
    socket.getaddrinfo = denied
    READY = True

def preflight():
    bootstrap()
    assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix
    import cryptography
    import pydantic
    import jwcrypto.jwk
    import sd_jwt.verifier
    for module in (cryptography, pydantic):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    for module in (jwcrypto.jwk, sd_jwt.verifier):
        assert Path(module.__file__).resolve().is_relative_to(LEGACY.resolve())
    wanted = {"cryptography": "46.0.7", "pydantic": "2.13.4", "jwcrypto": "1.5.6",
              "sd-jwt": "0.10.4", "ucp-sdk": "0.4.6", "PyYAML": "6.0.3"}
    assert {k: importlib.metadata.version(k) for k in wanted} == wanted
    print(json.dumps({"runtime": "READY", "packages": wanted, "installs": 0}))

def load_parent_tests():
    import importlib.util
    spec = importlib.util.spec_from_file_location("h53_parent_fixtures", PARENT / "FROZEN_TESTS.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    preflight()
    if sys.argv[1:] == ["focused"]:
        import unittest
        suite = unittest.TestLoader().loadTestsFromNames([
            "tests.test_ap2_protocol_boundary", "tests.test_ap2_sdk_bridge", "tests.test_ap2_official_verification",
            "tests.trusted_execution.test_confirmation", "tests.test_webshop_runtime_gate"])
        assert suite.countTestCases() == 76
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    elif sys.argv[1:] == ["official"]:
        runpy.run_path(str(ROOT / "docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/evaluator_checks/official_two_hop_cases.py"), run_name="__main__")
    else:
        assert sys.argv[1:] == ["preflight"]
