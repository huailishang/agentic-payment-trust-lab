"""Strict bilingual Windows fsutil reparsepoint parser for H72R.

Never follow a reparse point: lstat + fsutil reparsepoint query path; compare
native tag, the unique declared hex length and the full continuous hex payload.
Raw stdout/stderr are preserved separately with byte digests, not interpreted
as identity across OS locale. No filesystem or registry mutation.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,subprocess

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
PARENT=ROOT/"docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1"
HIST=ROOT/"docs/05_任务交接/H71R3_CONDA_AGENT_TEST_IMPORT_ISOLATION_V1/evidence/reassessment_20261114/HISTORICAL_REPARSE_QUERY.stdout.log"
P0=PARENT/"evidence/p0/SPECIAL_NODE_CURRENT.stdout.bin"
EVALUATOR=PARENT/"evidence/l3_review_20261115/NATIVE_CURRENT.stdout.bin"
class NativeError(ValueError):pass
def require(x,msg):
    if not x:raise NativeError(msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw:bytes)->dict:
    """Return facts only after rejecting ambiguous/malformed/partial data."""
    require(isinstance(raw,bytes) and 50<=len(raw)<=16384,"native_bytes_invalid")
    try:text=raw.decode("gbk",errors="strict")
    except UnicodeDecodeError as ex:raise NativeError("native_output_encoding") from ex
    lines=[line.rstrip() for line in text.splitlines()]
    tag_matches=[re.fullmatch(r"\s*(?:Reparse Tag Value|重分析标记值)\s*:\s*0x([a-fA-F0-9]{1,8})\s*",line) for line in lines]
    tag=[x.group(1) for x in tag_matches if x]
    length_matches=[re.fullmatch(r"\s*(?:Reparse Data Length|重新分析数据长度)\s*:\s*0x([a-fA-F0-9]{1,8})\s*",line) for line in lines]
    declared=[x.group(1) for x in length_matches if x]
    sections=[line for line in lines if re.fullmatch(r"\s*(?:Reparse Data|重分析数据)\s*:\s*",line)]
    require(len(tag)==len(declared)==len(sections)==1,"native_header_ambiguous_or_missing")
    expected=int(declared[0],16)
    require(0<expected<=16*1024,"native_length_invalid")
    row_lines=[line for line in lines if re.match(r"^[a-fA-F0-9]{4}:",line)]
    require(len(row_lines)==(expected+15)//16,"native_row_count")
    payload=bytearray()
    for rowindex,line in enumerate(row_lines):
        offset_text=line.split(":",1)[0]
        offset=int(offset_text,16)
        require(offset==len(payload)==rowindex*16,"native_noncontiguous_offset")
        body=line.split(":",1)[1]
        # Accept at most the declared bytes for that 16-byte offset.
        # The human ASCII gutter is advisory and cannot supply data bytes.
        n=min(16,expected-offset)
        # Split on whitespace, consuming exactly n hex-byte tokens from the left.
        fields=body.strip().split()
        require(len(fields)>=n,"native_short_row")
        for token in fields[:n]:
            require(re.fullmatch(r"[a-fA-F0-9]{2}",token) is not None,"native_invalid_hex_byte")
            payload.append(int(token,16))
        # Additional tokens must be ASCII gutter, never extra hex bytes.
        if len(fields)>n:
            trailer=fields[n:]
            require(not re.fullmatch(r"[a-fA-F0-9]{2}",trailer[0]),"native_extra_data_byte")
    require(len(payload)==expected,"native_payload_mismatched_length")
    return {"tag":int(tag[0],16),"length":expected,"row_count":len(row_lines),
            "data_sha256":sha(payload),"data_hex":payload.hex()}
def verify(*, save_first:bool=False)->dict:
    b=json.loads((P/"BASELINE.json").read_text(encoding="utf-8"))
    require(len(b["special_nodes"])==1,"special_nodes_scope")
    rel,node=next(iter(b["special_nodes"].items()))
    path=ROOT/rel
    # lstat checks the actual native node without traversing its target.
    tag=path.lstat().st_reparse_tag
    require(tag==node["reparse_tag"],"native_lstat_tag_changed")
    history=HIST.read_bytes()
    require(sha(history)==node["query_stdout_sha256"],"original_english_query_changed")
    samples={"historical_english":history,
             "p0_chinese":P0.read_bytes(),
             "evaluator_english":EVALUATOR.read_bytes()}
    old_b=json.loads((PARENT/"BASELINE.json").read_text(encoding="utf-8"))
    require(sha(samples["p0_chinese"])==old_b["special_nodes"][rel]["query_stdout_sha256"] or
            sha(samples["p0_chinese"])=="e4b996ac570e0163f076bcf06976c134b775de8cd9761f1cb507febbbf2e5f2e",
            "original_chinese_query_changed")
    first=parse(history)
    for name,raw in samples.items():
        require(parse(raw)==first,"native_historical_structure_changed:"+name)
    cmd=["fsutil","reparsepoint","query",str(path)]
    start=datetime.now(timezone.utc)
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=18)
    end=datetime.now(timezone.utc)
    require(r.returncode==0,"native_fsutil_query_exit_nonzero")
    current=parse(r.stdout)
    require(current==first and current["tag"]==tag,"native_live_structure_changed")
    if save_first:
        folder=P/"evidence/native_query_20261115"
        require(not folder.exists(),"native_measurement_already_saved")
        folder.mkdir(parents=True)
        (folder/"LIVE.stdout.bin").write_bytes(r.stdout)
        (folder/"LIVE.stderr.bin").write_bytes(r.stderr)
        receipt={"schema":"h72r-native-live-query/v1","task_id":P.name,
          "captured_start_utc":start.isoformat(),"captured_end_utc":end.isoformat(),
          "command_argv":cmd,"returncode":r.returncode,
          "stdout_sha256":sha(r.stdout),"stdout_bytes":len(r.stdout),
          "stderr_sha256":sha(r.stderr),"stderr_bytes":len(r.stderr),
          "historical_sha256":{k:sha(v) for k,v in samples.items()},
          "facts":{k:v for k,v in first.items() if k!="data_hex"},
          "real_node_lstat_tag":tag,
          "source':'":"native_windows_local","is_fixture":False}
        (folder/"RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        folder=P/"evidence/native_query_20261115"
        if (folder/"RECEIPT.json").is_file():
            receipt=json.loads((folder/"RECEIPT.json").read_text(encoding="utf-8"))
            require(receipt["facts"]=={k:v for k,v in first.items() if k!="data_hex"},
                    "native_original_measurement_drift")
            require(sha((folder/"LIVE.stdout.bin").read_bytes())==receipt["stdout_sha256"],
                    "native_saved_query_stdout_drift")
            require(sha((folder/"LIVE.stderr.bin").read_bytes())==receipt["stderr_sha256"],
                    "native_saved_query_stderr_drift")
    return {"status":"PASS","real_native_query":True,"lstat_tag":tag,
            "declared_bytes":current["length"],"payload_sha256":current["data_sha256"],
            "row_count":current["row_count"],
            "historical_raw_sha256":{k:sha(v) for k,v in samples.items()},
            "current_raw_sha256":sha(r.stdout),
            "raw_locale_mismatch_but_structure_identical":len({sha(x) for x in [history,samples["p0_chinese"],r.stdout]})>1,
            "no_reparse_traversal":True,"fixture_only":False}
if __name__=="__main__":
    print(json.dumps(verify(save_first=True),ensure_ascii=True,indent=2))
