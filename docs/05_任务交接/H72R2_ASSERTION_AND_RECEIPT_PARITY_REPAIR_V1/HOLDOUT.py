"""Independent H72R2 holdout: separate from NEGATIVE_TESTS and parser suite."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
H72=ROOT/"docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1"
PY=Path(sys.executable)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parser_holdout():
 sys.path.insert(0,str(PACK))
 import NATIVE_NEGATIVES
 cls=NATIVE_NEGATIVES.ParserCases
 if cls.fail is not unittest.TestCase.fail:
  raise RuntimeError("ParserCases still shadows unittest.TestCase.fail")
 case=cls("test_01_english_original_positive")
 try:case.assertEqual({"tag":1},{"tag":2})
 except AssertionError:dict_assertion="REJECTED_AS_EXPECTED"
 else:raise RuntimeError("false_dictionary_assertion_was_accepted")
 try:case.fail("holdout intentional fail")
 except AssertionError:fail_method="RAISED_AS_EXPECTED"
 else:raise RuntimeError("unittest_fail_did_not_raise")
 return {"status":"PASS","fail_method_inherited":True,
         "false_dictionary_assertion":dict_assertion,"fail_method":fail_method}
def receipt_holdout():
 with tempfile.TemporaryDirectory(prefix="_h72r_negative_h72r2_holdout_") as temp:
  root=Path(temp)/"agentic-payment-trust-lab";root.mkdir()
  pack=root/PACK.relative_to(ROOT);pack.mkdir(parents=True)
  shutil.copy2(PACK/"CHECK.py",pack/"CHECK.py")
  receipt=json.loads((H72/"P0_RECEIPT.json").read_text(encoding="utf-8"))
  (pack/"P0_RECEIPT.json").write_text(json.dumps(receipt),encoding="utf-8")
  expected={k:receipt[k] for k in ("baseline_head","baseline_sha256","authorization_sha256","source_sha256","test_counts")}
  expected["commands"]=[{k:item[k] for k in ("label","meta_sha256","exit_code","test_count")} for item in receipt["commands"]]
  fixture={"schema":"h72r2-nonadmitting-fixture/v1","receipt":expected}
  (pack/"NEG_FIXTURE.json").write_text(json.dumps(fixture),encoding="utf-8")
  env=os.environ.copy();env["H72R2_NEGATIVE_FIXTURE"]="1";env["PYTHONDONTWRITEBYTECODE"]="1"
  cmd=[str(PY),"-B",str(pack/"CHECK.py"),"historical-receipt","--fixture-mode"]
  good=subprocess.run(cmd,cwd=root,env=env,capture_output=True,timeout=20)
  if good.returncode!=0:raise RuntimeError("original_receipt_positive_control_failed:"+good.stderr.decode("utf-8",errors="replace")[-500:])
  receipt["commands"][3]["test_count"]=99
  (pack/"P0_RECEIPT.json").write_text(json.dumps(receipt),encoding="utf-8")
  bad=subprocess.run(cmd,cwd=root,env=env,capture_output=True,timeout=20)
  error=bad.stderr.decode("utf-8",errors="replace")
  if bad.returncode==0 or "p0_command_test_count_mismatch" not in error:
   raise RuntimeError("single_command_9_to_99_holdout_not_rejected:"+error[-500:])
  return {"status":"PASS","original_receipt":"ACCEPTED",
          "mutated_command_test_count":{"command_index":3,"original":9,"mutated":99,"result":"REJECTED"},
          "checker_entrypoint":"actual task-local CHECK.py","fixture":"NON_ADMITTING"}
def run():
 return {"status":"PASS","parser_framework_holdout":parser_holdout(),
         "receipt_entrypoint_holdout":receipt_holdout(),
         "ordinary_negative_suite_imported":False,"live_parent_mutated":False,
         "external_actions":0}
if __name__=="__main__":print(json.dumps(run(),ensure_ascii=True,indent=2))
