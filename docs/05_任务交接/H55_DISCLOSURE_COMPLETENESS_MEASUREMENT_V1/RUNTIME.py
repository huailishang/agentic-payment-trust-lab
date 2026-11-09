"""Frozen runtime. Existing H47/H37 dependencies plus task-local reviewed source."""
import importlib.metadata
import json
from pathlib import Path
import socket
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
AP2 = ROOT / 'local_sources/third_party/ap2-v0.2.0/code/sdk/python'
LEGACY = ROOT / '.task_envs/h37_ap2_crypto/lib/python3.12/site-packages'
NODE = Path('D:/SoftWare/nodejs/install/node.exe')
READY = False
def bootstrap():
    global READY
    if READY: return
    sys.dont_write_bytecode = True
    for path in (ROOT, ROOT/'src', AP2, TASK/'sources/python/src'):
        sys.path.insert(0,str(path))
    sys.path.append(str(LEGACY))
    from ap2.sdk import mandate
    scratch = ROOT/'.task_envs/H55/runs'
    scratch.mkdir(parents=True,exist_ok=True)
    mandate.LOG_FILE_PATH = str(scratch/'synthetic-sdk.log')
    def denied(*a,**kw): raise AssertionError('H54 runtime network budget zero')
    socket.socket.connect = denied
    socket.create_connection = denied
    socket.getaddrinfo = denied
    READY = True
def preflight():
    bootstrap()
    assert sys.version_info[:2] == (3,12) and sys.prefix != sys.base_prefix
    wanted={'cryptography':'46.0.7','pydantic':'2.13.4','jwcrypto':'1.5.6','sd-jwt':'0.10.4','ucp-sdk':'0.4.6','PyYAML':'6.0.3'}
    assert {k:importlib.metadata.version(k) for k in wanted} == wanted
    import rfc8785
    assert rfc8785.__version__ == '0.1.4'
    assert Path(rfc8785.__file__).is_relative_to(TASK/'sources/python/src')
    version = subprocess.check_output([str(NODE),'--version'],text=True).strip()
    assert version == 'v24.12.0', version
    print(json.dumps({'runtime':'READY','python_packages':wanted,'node':version,'installs':0}))
if __name__ == '__main__':
    preflight()
    if sys.argv[1:] == ['regression']:
        import unittest
        suite=unittest.TestLoader().loadTestsFromNames(['tests.test_ap2_protocol_boundary','tests.test_ap2_sdk_bridge','tests.test_ap2_official_verification'])
        assert suite.countTestCases() > 0
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    assert sys.argv[1:] == ['preflight']
