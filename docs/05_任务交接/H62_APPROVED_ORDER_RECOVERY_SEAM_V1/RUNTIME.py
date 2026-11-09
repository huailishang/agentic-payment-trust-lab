"""Existing libraries, full merchant app, offline HTTP only."""
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
READY=False
def bootstrap():
    global READY
    if READY: return
    sys.dont_write_bytecode=True
    for p in (ROOT,ROOT/'src',ROOT/'local_sources/third_party/ap2-v0.2.0/code/sdk/python',TASK/'merchant'):
        sys.path.insert(0,str(p))
    sys.path.append(str(ROOT/'.task_envs/h37_ap2_crypto/lib/python3.12/site-packages'))
    from ap2.sdk import mandate
    scratch=ROOT/'.task_envs/H62/runs'; scratch.mkdir(parents=True,exist_ok=True)
    mandate.LOG_FILE_PATH=str(scratch/'synthetic-sdk.log')
    original=socket.socket.connect
    def denied(*a,**kw):
        caller=sys._getframe(1)
        if caller.f_code.co_name=='socketpair' and Path(caller.f_code.co_filename).resolve()==Path(socket.__file__).resolve(): return original(*a,**kw)
        raise AssertionError('H57 external network budget zero')
    socket.socket.connect=denied; socket.create_connection=denied; socket.getaddrinfo=denied
    READY=True
def preflight():
    bootstrap()
    assert sys.version_info[:2]==(3,12) and sys.prefix!=sys.base_prefix
    wanted=json.loads((TASK.parent/'H47_UCP_COMMERCE_APPLICABILITY_V1/ENVIRONMENT.json').read_text(encoding='utf-8'))['packages']
    assert all(importlib.metadata.version(n)==v for n,v in wanted.items())
    for n,v in {'jwcrypto':'1.5.6','sd-jwt':'0.10.4'}.items(): assert importlib.metadata.version(n)==v
    print(json.dumps({'runtime':'READY','h47_packages':len(wanted),'packages_installed':0}))
if __name__=='__main__':
    preflight()
    if sys.argv[1:] == ['regression']:
        import unittest
        suite=unittest.TestLoader().loadTestsFromNames(['tests.test_ap2_protocol_boundary','tests.test_ap2_sdk_bridge','tests.test_ap2_official_verification'])
        assert suite.countTestCases()==25
        sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    assert sys.argv[1:]==['preflight']
