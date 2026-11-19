"""H72R actual bilingual native parser adversarial tests. No fsutil changes."""
from __future__ import annotations
import unittest
from pathlib import Path
import NATIVE

class ParserCases(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.eng=NATIVE.HIST.read_bytes()
  cls.ch=NATIVE.P0.read_bytes()
  cls.facts=NATIVE.parse(cls.eng)
 def fail(self,payload):
  with self.assertRaises(NATIVE.NativeError):NATIVE.parse(payload)
 def test_01_english_original_positive(self):
  self.assertEqual(NATIVE.parse(self.eng),self.facts)
 def test_02_chinese_original_positive(self):
  self.assertEqual(NATIVE.parse(self.ch),self.facts)
 def test_03_wrong_tag_rejected_semantically(self):
  raw=self.eng.replace(b"0xa000001d",b"0xa000001e",1)
  self.assertNotEqual(NATIVE.parse(raw)["tag"],self.facts["tag"])
 def test_04_wrong_declared_length_rejected(self):
  self.fail(self.eng.replace(b"0x14",b"0x15",1))
 def test_05_byte_payload_tamper_detected(self):
  raw=self.eng.replace(b"0000:  02",b"0000:  03",1)
  self.assertNotEqual(NATIVE.parse(raw)["data_sha256"],self.facts["data_sha256"])
 def test_06_truncated_final_row_rejected(self):
  self.fail(self.eng.replace(b"0010:  68 6f 6e 33",b"0010:  68 6f 6e",1))
 def test_07_noncontiguous_offset_rejected(self):
  self.fail(self.eng.replace(b"0010:  68",b"0020:  68",1))
 def test_08_duplicate_tag_header_rejected(self):
  line=self.eng.splitlines(keepends=True)[0]
  self.fail(line+self.eng)
 def test_09_extra_hex_data_rejected(self):
  self.fail(self.eng.replace(b"0010:  68 6f 6e 33",b"0010:  68 6f 6e 33 ff",1))
 def test_10_extra_hex_row_rejected(self):
  self.fail(self.eng+b"0020:  00\r\n")
 def test_11_missing_tag_header_rejected(self):
  self.fail(self.eng.replace(b"Reparse Tag Value",b"Unrelated Raw Label",1))
 def test_12_chinese_same_data_wrong_length_rejected(self):
  self.fail(self.ch.replace(b"0x14",b"0x16",1))
def run():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(ParserCases)
 import io
 stream=io.StringIO()
 result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 if not result.wasSuccessful() or result.testsRun!=12:
  raise NATIVE.NativeError("NATIVE_PARSER_NEGATIVE_TEST_FAILURE:"+stream.getvalue()[-500:])
 return {"status":"PASS","total_tests":12,"bilingual_positive_cases":2,
         "wrong_tag_detected":True,"wrong_length_detected":True,
         "changed_payload_detected":True,"malformed_truncated_duplicate_rejected":True}
if __name__=="__main__":
 print(run())
