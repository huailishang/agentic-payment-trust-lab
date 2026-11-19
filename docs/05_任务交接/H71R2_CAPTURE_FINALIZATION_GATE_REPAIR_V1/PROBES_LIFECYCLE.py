"""Frozen independent archive ownership/finalization fault probes; temporary files only."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PACK=Path(__file__).resolve().parent
item=importlib.util.spec_from_file_location("h71r2_legacy_loader",PACK/"PROBES_LEGACY.py")
legacy=importlib.util.module_from_spec(item); sys.modules[item.name]=legacy; item.loader.exec_module(legacy)
SECRET="synthetic-private-path-do-not-echo"

class Response:
    status=200; headers={}
    def __init__(self,read_error=False,close_error=False):
        self.parts=[b"a" if read_error else b"abc",TimeoutError(SECRET) if read_error else b""]
        self.closed=False; self.close_error=close_error
    def read(self,n):
        value=self.parts.pop(0)
        if isinstance(value,Exception): raise value
        return value
    def close(self):
        if self.close_error: raise OSError(SECRET)
        self.closed=True

class Writer:
    def __init__(self,inner,short=False,flush_error=False): self.inner=inner; self.short=short; self.flush_error=flush_error
    def write(self,value): return self.inner.write(value[:2] if self.short else value)
    def flush(self):
        if self.flush_error: raise OSError(SECRET)
        return self.inner.flush()
    def close(self): return self.inner.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def __getattr__(self,name): return getattr(self.inner,name)

class Lifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.runner=legacy.load_runner()
    def call(self,path,response=None):
        calls=[]
        def opener(): calls.append(1); return response or Response()
        result=self.runner.capture_attempt(opener,body_path=path,byte_limit=64,chunk_size=8)
        self.assertNotIn(SECRET,str(result)); self.assertIsInstance(result["errors"],list)
        self.assertIn(result["body_sha256_state"],{"KNOWN","UNAVAILABLE","NOT_OWNED"})
        return result,calls
    def not_owned(self,result,calls):
        self.assertEqual(calls,[]); self.assertFalse(result["body_artifact_owned"])
        self.assertEqual(result["body_sha256_state"],"NOT_OWNED"); self.assertIsNone(result["body_sha256"])
        self.assertEqual(result["body_bytes_archived"],0); self.assertEqual(result["body_bytes_observed"],0)
        self.assertEqual(result["failure_phase"],"OUTPUT_PREPARE"); self.assertFalse(result["body_complete"])
    def owned(self,result,response):
        self.assertTrue(result["body_artifact_owned"]); self.assertEqual(result["http_status"],200)
        self.assertEqual(result["response_closed"],response.closed)
    def test_existing_destination_never_opens_response_or_claims_old_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; path.write_bytes(b"OLD_EVIDENCE")
            result,calls=self.call(path); self.not_owned(result,calls)
            self.assertEqual(path.read_bytes(),b"OLD_EVIDENCE")
    def test_output_parent_failure_precedes_opener(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"missing"/"body.bin"; original=Path.mkdir
            def fail(target,*args,**kwargs):
                if target==path.parent: raise PermissionError(SECRET)
                return original(target,*args,**kwargs)
            with patch.object(Path,"mkdir",fail): result,calls=self.call(path)
            self.not_owned(result,calls)
    def test_output_open_failure_precedes_opener(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; original=Path.open
            def fail(target,mode="r",*args,**kwargs):
                if target==path and ("w" in mode or "x" in mode): raise PermissionError(SECRET)
                return original(target,mode,*args,**kwargs)
            with patch.object(Path,"open",fail): result,calls=self.call(path)
            self.not_owned(result,calls)
    def test_short_write_is_completed_or_reported_with_actual_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; original=Path.open; response=Response()
            def inject(target,mode="r",*args,**kwargs):
                value=original(target,mode,*args,**kwargs)
                return Writer(value,short=True) if target==path and ("w" in mode or "x" in mode) else value
            with patch.object(Path,"open",inject): result,_=self.call(path,response)
            raw=path.read_bytes(); self.owned(result,response)
            self.assertEqual(result["body_bytes_observed"],3); self.assertEqual(result["body_bytes_archived"],len(raw))
            self.assertEqual(result["body_sha256"],hashlib.sha256(raw).hexdigest())
            if result["body_complete"]: self.assertEqual(raw,b"abc")
            else: self.assertEqual(result["failure_phase"],"BODY_WRITE"); self.assertIsNone(result["body_bytes_total"])
    def test_flush_failure_retains_status_observation_and_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; original=Path.open; response=Response()
            def inject(target,mode="r",*args,**kwargs):
                value=original(target,mode,*args,**kwargs)
                return Writer(value,flush_error=True) if target==path and ("w" in mode or "x" in mode) else value
            with patch.object(Path,"open",inject): result,_=self.call(path,response)
            self.owned(result,response); self.assertEqual(result["body_bytes_observed"],3)
            self.assertEqual(result["body_bytes_archived"],len(path.read_bytes()))
            self.assertFalse(result["body_complete"]); self.assertEqual(result["failure_phase"],"BODY_WRITE")
    def test_digest_read_failure_is_contained_or_reread_is_unnecessary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; original=Path.open; response=Response(); attempted=[]
            def fail(target,mode="r",*args,**kwargs):
                if target==path and mode=="rb": attempted.append(1); raise PermissionError(SECRET)
                return original(target,mode,*args,**kwargs)
            with patch.object(Path,"open",fail): result,_=self.call(path,response)
            self.owned(result,response); self.assertEqual(result["body_bytes_observed"],3)
            if attempted:
                self.assertIsNone(result["body_sha256"]); self.assertEqual(result["body_sha256_state"],"UNAVAILABLE")
                self.assertEqual(result["failure_phase"],"BODY_HASH"); self.assertFalse(result["body_complete"])
            else: self.assertEqual(result["body_sha256"],hashlib.sha256(b"abc").hexdigest())
    def test_post_close_stat_failure_never_escapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/"body.bin"; original=Path.stat; response=Response()
            def fail(target,*args,**kwargs):
                if target==path and response.closed: raise OSError(SECRET)
                return original(target,*args,**kwargs)
            with patch.object(Path,"stat",fail): result,_=self.call(path,response)
            self.owned(result,response); self.assertEqual(result["body_bytes_observed"],3)
            if result["body_sha256_state"]=="KNOWN": self.assertEqual(result["body_sha256"],hashlib.sha256(b"abc").hexdigest())
            else: self.assertIsNone(result["body_sha256"]); self.assertFalse(result["body_complete"])
    def test_close_failure_is_not_reported_as_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            response=Response(close_error=True); result,_=self.call(Path(tmp).resolve()/"body.bin",response)
            self.owned(result,response); self.assertFalse(result["response_closed"]); self.assertFalse(result["body_complete"])
            self.assertTrue(any(e["phase"]=="CLOSE" and e["type"]=="OSError" for e in result["errors"]))
    def test_read_and_close_errors_are_both_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            response=Response(read_error=True,close_error=True); result,_=self.call(Path(tmp).resolve()/"body.bin",response)
            self.owned(result,response); self.assertEqual(result["body_bytes_observed"],1)
            self.assertEqual(result["error_type"],"TimeoutError"); self.assertIsNone(result["body_bytes_total"])
            self.assertTrue(any(e["phase"]=="BODY_READ" and e["type"]=="TimeoutError" for e in result["errors"]))
            self.assertTrue(any(e["phase"]=="CLOSE" and e["type"]=="OSError" for e in result["errors"]))

if __name__=="__main__": unittest.main(verbosity=2)
