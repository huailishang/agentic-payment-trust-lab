"""Frozen independent fault driver. No network and no historical transport replay."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PACK=Path(__file__).resolve().parent

def blocked(*args,**kwargs): raise AssertionError("external_action_forbidden")

def load_runner():
    path=PACK/"RUN.py"
    tree=ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): names=[a.name.split(".")[0] for a in node.names]
        elif isinstance(node,ast.ImportFrom): names=[(node.module or "").split(".")[0]]
        else: continue
        if set(names)&{"socket","urllib","http","requests","httpx","aiohttp","subprocess","importlib"}:
            raise AssertionError("offline_module_has_external_or_dynamic_import")
    spec=importlib.util.spec_from_file_location("h71r_executor_capture",path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    with patch.object(socket.socket,"connect",blocked),patch.object(subprocess,"Popen",blocked): spec.loader.exec_module(mod)
    return mod

class Stream:
    def __init__(self,data=b"",status=200,error_after=None,headers=None):
        self.data=data; self.status=status; self.headers=headers or {}; self.error_after=error_after
        self.pos=0; self.calls=[]; self.closed=False
    def read(self,n):
        assert isinstance(n,int) and n>0,"unbounded_read"
        self.calls.append(n)
        if self.error_after is not None and self.pos>=self.error_after: raise TimeoutError("synthetic secret must not be echoed")
        end=min(len(self.data),self.pos+n)
        if self.error_after is not None: end=min(end,self.error_after)
        out=self.data[self.pos:end]; self.pos=end; return out
    def close(self): self.closed=True
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class Probes(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.runner=load_runner()

    def capture(self,stream,limit=128,chunk=32,clock=None):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp).resolve()/"body.bin"
            calls=[]
            def opener():
                calls.append(1); self.assertEqual(len(calls),1,"unexpected retry or redirect follow"); return stream
            with patch.object(socket.socket,"connect",blocked),patch.object(subprocess,"Popen",blocked):
                result=self.runner.capture_attempt(opener,body_path=target,byte_limit=limit,chunk_size=chunk,clock=clock,timeout_seconds=1)
            raw=target.read_bytes() if target.exists() else b""
            self.assertEqual(result["body_sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["body_bytes_observed"],len(raw))
            self.assertGreaterEqual(result["bytes_charged"],len(raw)); self.assertLessEqual(result["bytes_charged"],limit)
            self.assertEqual(result["http_status"],stream.status)
            self.assertTrue(stream.closed); self.assertTrue(result["response_closed"])
            self.assertNotIn("synthetic secret",str(result))
            observed=0
            for request in stream.calls:
                self.assertLessEqual(request,limit-observed)
                observed+=min(request,max(0,len(stream.data)-observed),max(0,stream.error_after-observed) if stream.error_after is not None else limit)
            return result,raw

    def test_full_multichunk_body(self):
        result,raw=self.capture(Stream(b"abcdefghijk"),chunk=4)
        self.assertEqual(raw,b"abcdefghijk"); self.assertTrue(result["body_complete"])
        self.assertEqual(result["body_bytes_total"],11); self.assertEqual(result["bytes_charged"],11)

    def test_empty_eof_is_legitimate_zero(self):
        result,raw=self.capture(Stream())
        self.assertTrue(result["body_complete"]); self.assertEqual(result["body_bytes_total"],0); self.assertEqual(raw,b"")

    def test_partial_200_timeout_preserves_status_and_prefix(self):
        stream=Stream(b"x"*23,status=200,error_after=23)
        result,raw=self.capture(stream,limit=128,chunk=32)
        self.assertEqual(raw,b"x"*23); self.assertFalse(result["body_complete"])
        self.assertIsNone(result["body_bytes_total"]); self.assertEqual(result["failure_phase"],"BODY_READ")
        self.assertEqual(result["error_type"],"TimeoutError"); self.assertEqual(result["bytes_charged"],55)

    def test_failed_200_first_read_does_not_claim_complete_zero(self):
        result,raw=self.capture(Stream(status=200,error_after=0),limit=64,chunk=16)
        self.assertEqual(raw,b""); self.assertFalse(result["body_complete"])
        self.assertIsNone(result["body_bytes_total"]); self.assertEqual(result["bytes_charged"],16)

    def test_403_body_failure_does_not_erase_status(self):
        result,raw=self.capture(Stream(b"denied",status=403,error_after=6),chunk=16)
        self.assertEqual(raw,b"denied"); self.assertEqual(result["failure_phase"],"BODY_READ")
        self.assertIsNone(result["body_bytes_total"])

    def test_complete_404_body_is_preserved(self):
        result,raw=self.capture(Stream(b"not found",status=404),chunk=4)
        self.assertTrue(result["body_complete"]); self.assertEqual(raw,b"not found")

    def test_redirect_is_captured_without_second_open(self):
        result,_=self.capture(Stream(status=302,headers={"Location":"https://example.invalid/forbidden"}))
        self.assertTrue(result["body_complete"])

    def test_exact_limit_requires_no_extra_eof_byte(self):
        stream=Stream(b"abcdefghijklmnop")
        result,raw=self.capture(stream,limit=16,chunk=5)
        self.assertEqual(raw,b"abcdefghijklmnop"); self.assertFalse(result["body_complete"])
        self.assertIsNone(result["body_bytes_total"]); self.assertEqual(result["failure_phase"],"LIMIT")
        self.assertEqual(stream.calls,[5,5,5,1])

    def test_declared_oversize_stops_before_body(self):
        stream=Stream(b"x"*32,headers={"Content-Length":"32"})
        result,raw=self.capture(stream,limit=16,chunk=4)
        self.assertEqual(stream.calls,[]); self.assertEqual(raw,b""); self.assertFalse(result["body_complete"])
        self.assertIsNone(result["body_bytes_total"])

    def test_remaining_budget_between_two_attempts(self):
        first,_=self.capture(Stream(b"12345"),limit=8,chunk=4)
        remaining=8-first["bytes_charged"]
        second,_=self.capture(Stream(b"abcdefgh"),limit=remaining,chunk=4)
        self.assertEqual(first["bytes_charged"]+second["bytes_charged"],8)
        self.assertFalse(second["body_complete"])

    def test_open_failure_has_no_fabricated_status_or_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            def opener(): raise TimeoutError("synthetic secret must not be echoed")
            result=self.runner.capture_attempt(opener,body_path=Path(tmp).resolve()/"body.bin",byte_limit=32,chunk_size=8,clock=None,timeout_seconds=1)
            self.assertIsNone(result["http_status"]); self.assertIsNone(result["body_bytes_total"])
            self.assertFalse(result["body_complete"]); self.assertEqual(result["failure_phase"],"OPEN")
            self.assertEqual(result["body_bytes_observed"],0); self.assertNotIn("synthetic secret",str(result))

if __name__=="__main__": unittest.main(verbosity=2)
