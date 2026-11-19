"""H71 bounded, auditable qualification runner (no creation, no payment).

All original keys, raw provider responses and environment artifacts remain
outside the repository. Only the frozen H71 task may invoke these operations.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
LEDGER = PACK / "ATTEMPT_LEDGER.jsonl"
SPEC = json.loads((PACK/"SPEC.json").read_text(encoding="utf-8"))
DEADLINE = datetime.datetime.fromisoformat(SPEC["original_deadline"])
H69 = PACK.parent/"H69_STRIPE_ANONYMOUS_SANDBOX_QUALIFICATION_V1"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def iso():
    return utcnow().isoformat()


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def rows():
    result=[json.loads(s) for s in LEDGER.read_text(encoding="utf-8").splitlines() if s.strip()] if LEDGER.exists() else []
    if [r["seq"] for r in result] != list(range(1,len(result)+1)):
        raise RuntimeError("ledger_sequence_invalid")
    return result


def append(kind,event,ident,**kwargs):
    history=rows()
    seen=[r for r in history if r["attempt_id"]==ident]
    if event=="BEGIN":
        if seen:
            raise RuntimeError("attempt_reused")
        if kind!="active_work" and sum(r["event"]=="BEGIN" and r["kind"]==kind for r in history) >= SPEC["budgets"][kind]:
            raise RuntimeError("attempt_budget_exceeded")
    elif event=="END":
        if len(seen)!=1 or seen[0]["event"]!="BEGIN" or seen[0]["kind"]!=kind:
            raise RuntimeError("invalid_attempt_end")
        if kwargs.get("status") not in {"SUCCEEDED","FAILED","INPUT_LIMIT","UNKNOWN"}:
            raise RuntimeError("invalid_attempt_status")
    else: raise RuntimeError("invalid_event")
    row={"seq":len(history)+1,"event":event,"attempt_id":ident,"kind":kind,"at":iso(),**kwargs}
    with LEDGER.open("ab") as fp:
        fp.write((json.dumps(row,ensure_ascii=True,sort_keys=True,separators=(",",":"))+"\n").encode())
        fp.flush();os.fsync(fp.fileno())


def precheck():
    if utcnow()>DEADLINE: raise RuntimeError("original_authorization_expired")
    if "task_id: "+PACK.name not in (ROOT/"CURRENT.md").read_text(encoding="utf-8"):
        raise RuntimeError("wrong_current_router")
    r=subprocess.run([sys.executable,str(PACK/"CHECK.py"),"integrity"],
                     cwd=ROOT,capture_output=True,timeout=80)
    if r.returncode: raise RuntimeError("frozen_integrity_failed")


def init():
    precheck()
    append("active_work","BEGIN","h71-active-001")
    append("implementation","BEGIN","h71-implementation-001")
    print("H71 executor envelope opened; external requests=0")


import contextlib
import re
import socket
import ssl
import time
import urllib.error
import urllib.request

H69_CONTACT = "h68-checkout-lab@example.invalid"
MAX_RESPONSE = 2*1024*1024
SOURCE_URLS = [
    ("sandbox_source","https://raw.githubusercontent.com/stripe/stripe-cli/v1.55.10/pkg/sandbox/sandbox.go"),
    ("cli_root_source","https://raw.githubusercontent.com/stripe/stripe-cli/v1.55.10/pkg/cmd/root.go"),
    ("keys_documentation","https://docs.stripe.com/keys"),
    ("cli_listen_documentation","https://docs.stripe.com/cli/listen"),
]
PRIVATE_SCHEMA="h71-long-qualification-private/v1"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def _private(name, existing=False):
    value=os.environ.get(name)
    if not value:raise RuntimeError("private_dir_missing")
    target=Path(value).resolve()
    if target.is_relative_to(ROOT) or target==ROOT or target.is_symlink():
        raise RuntimeError("private_location_invalid")
    if existing:
        if not target.is_dir():raise RuntimeError("original_private_unavailable")
    else:
        if target.exists():raise RuntimeError("task_private_already_exists")
        target.mkdir(parents=True,mode=0o700)
        os.chmod(target,0o700)
    return target


def _write_private(folder,rel,raw):
    target=(folder/rel)
    if not target.resolve().is_relative_to(folder):raise RuntimeError("private_escape")
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("xb") as fp:
        fp.write(raw);fp.flush();os.fsync(fp.fileno())
    return rel


def _load_private(folder,rel):
    target=(folder/rel).resolve()
    if not target.is_relative_to(folder) or not target.is_file():
        raise RuntimeError("private_reference_missing")
    return target.read_bytes()


def _load_h69():
    prior=_private("H69_PRIVATE_DIR",existing=True)
    prior_result=json.loads((H69/"RESULT.json").read_text(encoding="utf-8"))
    raw=_load_private(prior,"SNAPSHOT.json")
    if sha(raw)!=prior_result["private_snapshot_sha256"]:
        raise RuntimeError("h69_snapshot_changed")
    records=json.loads(raw)["http"]
    provision=next(v for v in records if v["url"]=="https://ai.stripe.com/keys/provision")
    body=_load_private(prior,provision["body_file"])
    if sha(body)!=provision["body_sha256"] or provision["status"]!=200:
        raise RuntimeError("h69_provision_integrity")
    result=json.loads(body)
    key=result.get("restricted_key") or result.get("secret_key")
    account=result.get("account_id") or result.get("merchant_token")
    actual=json.loads(_load_private(prior,"CREDENTIALS.json"))
    if not (key and account and key.startswith("rkcs_test_")
            and account.startswith("acct_")
            and actual=={"key":key,"account_id":account}
            and sha(account.encode())==prior_result["account_ref"]):
        raise RuntimeError("h69_key_account_binding_failed")
    return key,account,prior_result["private_snapshot_sha256"]


def _phases():
    return {name:{"status":"NOT_RUN","reason":"NOT_STARTED"} for name in SPEC["phases"]}


def _listener():
    return {"attempted":False,"ready":False,"test_mode":False,
            "config_isolated":False,"key_in_argv":False,"stopped":False,
            "receiver_stopped":False,"archive_file":None,"stdout_file":None,
            "stderr_file":None}


def _browser():
    return {"attempted":False,"isolated":False,"clicked":False,
            "observed":None,"closed":False,"proof_file":None}


def _phase(material,name,status,reason):
    material["phases"][name]={"status":status,"reason":reason}


def _source_quote(raw,terms):
    text=raw.decode("utf-8",errors="replace")
    for term in terms:
        position=text.lower().find(term.lower())
        if position>=0:
            return text[position:position+min(70,len(text)-position)].strip() or term
    # A minimal authentic literal excerpt still requires manual semantic review.
    return text[:60].strip()


def _sources():
    existing=[]
    for ident,url in SOURCE_URLS:
        if utcnow()>DEADLINE:break
        row_id="h71-source-"+ident
        append("source_http","BEGIN",row_id,url=url)
        start=iso();status=None;raw=b"";error=None
        try:
            request=urllib.request.Request(url,method="GET",headers={"User-Agent":"H71-public-source-review/1"})
            try:
                with urllib.request.build_opener(NoRedirect()).open(request,timeout=20) as response:
                    status=response.status
                    raw=response.read(MAX_RESPONSE+1)
            except urllib.error.HTTPError as exc:
                status=exc.code
                raw=exc.read(4096)
            except (urllib.error.URLError,TimeoutError,OSError) as exc:
                error=type(exc).__name__
            if status==200 and len(raw)>MAX_RESPONSE:
                error="BODY_SIZE_LIMIT"
            stop=iso()
            append("source_http","END",row_id,status="SUCCEEDED" if status==200 and not error else "INPUT_LIMIT",
                   bytes=len(raw),http_status=status,error=error)
        except BaseException:
            # Any unexpected exception must still close the append-only attempt.
            if not any(r["attempt_id"]==row_id and r["event"]=="END" for r in rows()):
                append("source_http","END",row_id,status="FAILED",bytes=len(raw),
                       http_status=status,error="UNEXPECTED")
            raise
        if status==200 and error is None:
            filepath=PACK/"sources"/(ident+".txt")
            filepath.parent.mkdir(parents=True,exist_ok=True)
            with filepath.open("xb") as f: f.write(raw)
            existing.append({"id":ident,"url":url,"file":"sources/"+ident+".txt",
                             "sha256":sha(raw),"bytes":len(raw),
                             "started_at":start,"finished_at":stop,"status":200})
    (PACK/"SOURCE_MANIFEST.json").write_text(
        json.dumps({"sources":existing},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return existing


def _matrix(sources):
    cache={s["id"]:(PACK/s["file"]).read_bytes() for s in sources}
    def refs(names,terms):
        found=[]
        for name in names:
            if name in cache:
                found.append({"source_id":name,"quote":_source_quote(cache[name],terms)})
        return found[:2]
    rows=[
      {"id":"account_read","operation":"GET /v1/account",
       "key_family":"rkcs_test_ anonymous restricted sandbox credential",
       "observed":"H69 original and both actor-specific /v1/account GET attempts returned HTTP 403.",
       "documented":"Official key documentation describes restricted keys, but UNKNOWN for this anonymous key's account endpoint.",
       "unknown":"Exact restricted key permission policy and whether this 403 is sandbox-specific.",
       "refs":refs(["keys_documentation","sandbox_source"],["restricted","GetSecretKey"])},
      {"id":"checkout_required_endpoints",
       "operation":"GET checkout.sessions/payment_intents/charges (limit=100) in frozen order",
       "key_family":"rkcs_test_ anonymous restricted sandbox credential",
       "observed":"NOT_MEASURED at source review; only actual bounded runtime GETs can establish observations.",
       "documented":"UNKNOWN for this anonymous key's entitlement; general key documentation does not grant it.",
       "unknown":"List GET allow/deny, object completeness and any Checkout creation permission.",
       "refs":refs(["keys_documentation","sandbox_source"],["restricted","GetAccountID"])},
      {"id":"test_listener",
       "operation":"Stripe CLI 1.55.10 test-mode listen to local 127.0.0.1",
       "key_family":"rkcs_test_ current H69 credential only",
       "observed":"NOT_MEASURED; must meet three list GET preconditions.",
       "documented":"Official CLI documentation describes a local listener; UNKNOWN for this sandbox key specifically.",
       "unknown":"Current key supports CLI handshake, test events and isolated config.",
       "refs":refs(["cli_listen_documentation","cli_root_source"],["listen","api-key"])},
      {"id":"same_environment_binding",
       "operation":"H69 original provision credential/account to H71 three GETs",
       "key_family":"rkcs_test_ original provision response, no native Account identity",
       "observed":"H69 confirmed original provision bytes and credential/account id; Account GET 403.",
       "documented":"Official CLI code extracts keys/account references; this is PROVISION_CREDENTIAL_CONTEXT_ONLY, not independent account assurance.",
       "unknown":"Whether this credential can read required sandbox resources or prove independent merchant identity.",
       "refs":refs(["sandbox_source"],["GetSecretKey","GetAccountID"])},
    ]
    (PACK/"PERMISSION_MATRIX.json").write_text(
        json.dumps({"rows":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return rows


def _get(private,material,key,url,i):
    if url!=SPEC["urls"][i]:raise RuntimeError("unapproved_runtime_target")
    if utcnow()>DEADLINE:raise RuntimeError("authorization_expired")
    ident="h71-live-get-"+str(i+1)
    append("live_get","BEGIN",ident,url=url)
    started=iso()
    status=None;raw=None;error=None
    try:
        req=urllib.request.Request(url,method="GET",
                headers={"Authorization":"Bearer "+key,"Stripe-Version":SPEC["api_version"],
                         "User-Agent":"H71-same-key-qualifier/1"})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as response:
                status=response.status
                raw=response.read(MAX_RESPONSE+1)
        except urllib.error.HTTPError as exc:
            status=exc.code;raw=exc.read(MAX_RESPONSE+1)
        except (urllib.error.URLError,socket.timeout,TimeoutError,OSError) as exc:
            reason=exc.reason if isinstance(exc,urllib.error.URLError) else exc
            error=("DNS" if isinstance(reason,socket.gaierror)
                   else "TLS" if isinstance(reason,ssl.SSLError)
                   else "TIMEOUT" if isinstance(reason,(socket.timeout,TimeoutError))
                   else "NETWORK")
        finished=iso()
        append("live_get","END",ident,http_status=status,
               status="SUCCEEDED" if status==200 and (raw is not None and len(raw)<=MAX_RESPONSE) else "INPUT_LIMIT")
    except BaseException:
        if not any(r["attempt_id"]==ident and r["event"]=="END" for r in rows()):
            append("live_get","END",ident,http_status=status,status="FAILED")
        raise
    if raw is not None and len(raw)>MAX_RESPONSE:
        raw=raw[:MAX_RESPONSE];error="BODY_TOO_LARGE"
    file=_write_private(private,"http/get_"+str(i+1)+".bin",raw) if raw is not None else None
    record={"method":"GET","url":url,"started_at":started,"finished_at":finished,
            "status":status,"error":error,"body_file":file,
            "body_sha256":sha(raw) if raw is not None else None,
            "key_sha256":sha(key.encode())}
    material["http"].append(record)
    if status!=200 or error is not None:
        return False,"READ_HTTP_"+str(status) if status is not None else "READ_"+(error or "NETWORK")
    try:
        raw_json=json.loads(raw)
        if raw_json.get("object")!="list" or raw_json.get("data")!=[] or raw_json.get("has_more") is not False:
            return False,"READ_UNEXPECTED_OBJECTS"
    except (ValueError,UnicodeDecodeError,AttributeError,TypeError):
        return False,"READ_INVALID_JSON"
    return True,"EMPTY_LIST_VERIFIED"


def _save(private,material,decision,stage,reason):
    snap=(json.dumps(material,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    _write_private(private,"SNAPSHOT.json",snap)
    result={"schema":"h71-long-qualification-result/v1","task_id":PACK.name,
            "run_id":material["run_id"],"decision":decision,"reason_code":reason,
            "stage":stage,"private_snapshot_sha256":sha(snap),
            "account_ref":material["account_ref"],
            "account_assurance":"PROVISION_CREDENTIAL_CONTEXT_ONLY",
            "checkout_write_permission":"NOT_MEASURED",
            "checkout_sessions":0,"payments":0}
    (PACK/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"decision":decision,"stage":stage,"reason_code":reason,
                      "live_get_count":len(material["http"])},sort_keys=True))


def _download(private,material):
    import urllib.parse
    import zipfile
    origin=SPEC["cli"]["url"]
    url=origin
    for i in range(3):
        if utcnow()>DEADLINE:return None,"AUTHORIZATION_EXPIRED"
        parsed=urllib.parse.urlsplit(url)
        host=parsed.hostname
        if not (parsed.scheme=="https" and parsed.username is None and parsed.password is None
                and ((i==0 and url==origin) or (i>0 and host in
                    {"release-assets.githubusercontent.com","objects.githubusercontent.com"}))):
            return None,"PINNED_DOWNLOAD_HOST_INVALID"
        ident="h71-download-"+str(i+1)
        append("download","BEGIN",ident,url=url)
        status=None;raw=b"";destination=None
        try:
            req=urllib.request.Request(url,method="GET",headers={"User-Agent":"H71-pinned-CLI/1"})
            try:
                with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as resp:
                    status=resp.status
                    raw=resp.read(64*1024*1024+1)
                    destination=resp.headers.get("Location")
            except urllib.error.HTTPError as exc:
                status=exc.code;destination=exc.headers.get("Location")
                raw=exc.read(4096)
            except (urllib.error.URLError,TimeoutError,OSError):
                status=None
        finally:
            append("download","END",ident,bytes=len(raw),
                   status="SUCCEEDED" if status==200 else "INPUT_LIMIT",
                   http_status=status)
        if status in (301,302,303,307,308):
            if not destination:return None,"PINNED_REDIRECT_MISSING"
            url=urllib.parse.urljoin(url,destination)
            continue
        if status!=200:return None,"PINNED_DOWNLOAD_HTTP_"+str(status)
        if len(raw)!=SPEC["cli"]["archive_bytes"] or sha(raw)!=SPEC["cli"]["archive_sha256"]:
            return None,"PINNED_DOWNLOAD_DIGEST_MISMATCH"
        _write_private(private,"stripe_1.55.10_windows_x86_64.zip",raw)
        return private/"stripe_1.55.10_windows_x86_64.zip",None
    return None,"PINNED_DOWNLOAD_REDIRECT_LIMIT"


def _local_receiver(private):
    import http.server
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path!="/stripe/webhook":self.send_error(404);return
            size=self.headers.get("Content-Length","0")
            if not size.isdecimal() or int(size)>MAX_RESPONSE:
                self.send_error(413);return
            self.rfile.read(int(size))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"H71 LOCAL NO FULFILLMENT")
        def log_message(self,*unused):pass
    srv=http.server.HTTPServer(("127.0.0.1",8768),Handler)
    try:
        print("H71_RECEIVER_READY",flush=True)
        srv.serve_forever(poll_interval=0.1)
    finally:srv.server_close()


def _native_windows_path(path):
    out=subprocess.run(["wslpath","-w",str(path)],capture_output=True,text=True,timeout=6)
    if out.returncode or not out.stdout.strip():raise RuntimeError("winpath_unavailable")
    return out.stdout.strip()


def _cli_environment(private,key):
    # Do not read normal Stripe CLI configuration or inherited provider selectors.
    winroot=_native_windows_path(private)
    isolated=private/"isolated-config"
    isolated.mkdir(mode=0o700,exist_ok=True)
    winisolated=_native_windows_path(isolated)
    child=dict(os.environ)
    for k in list(child):
        if k.upper().startswith("STRIPE_") or k.upper() in {
            "HOME","USERPROFILE","APPDATA","LOCALAPPDATA","XDG_CONFIG_HOME",
        }:
            del child[k]
    child.update({"STRIPE_API_KEY":key,"STRIPE_NO_AUTO_UPDATE":"1",
                  "STRIPE_CLI_TELEMETRY":"0",
                  "HOME":winisolated,"USERPROFILE":winisolated,
                  "APPDATA":winisolated,"LOCALAPPDATA":winisolated,
                  "XDG_CONFIG_HOME":winisolated})
    return child


def _cli_offline(private,archive,key,material):
    import zipfile
    try:
        with zipfile.ZipFile(archive) as z:
            members=[m for m in z.infolist() if Path(m.filename).name.lower()=="stripe.exe"]
            if len(members)!=1 or members[0].file_size>64*1024*1024:
                return None,None,"CLI_ARCHIVE_CONTENT_INVALID"
            _write_private(private,"stripe.exe",z.read(members[0]))
    except (OSError,KeyError,ValueError,zipfile.BadZipFile):
        return None,None,"CLI_ARCHIVE_EXTRACT_FAILED"
    exe=private/"stripe.exe"
    env=_cli_environment(private,key)
    for index,(arg,filename) in enumerate([(("--version",),"cli.version.log"),
                                           (("listen","--help"),"cli.help.log")],1):
        ident="h71-cli-offline-"+str(index)
        append("cli_offline","BEGIN",ident)
        data=b"";status=1
        try:
            proc=subprocess.run([str(exe),*arg],cwd=private,env=env,
                                stdin=subprocess.DEVNULL,capture_output=True,timeout=9)
            status=proc.returncode;data=proc.stdout+proc.stderr
        except (OSError,subprocess.TimeoutExpired):
            status=1
        finally:
            append("cli_offline","END",ident,
                   status="SUCCEEDED" if status==0 else "INPUT_LIMIT")
        _write_private(private,filename,data)
        if status:return None,None,"CLI_VERSION_OR_HELP_FAILED"
    version=_load_private(private,"cli.version.log")
    helptext=_load_private(private,"cli.help.log")
    if b"1.55.10" not in version:return None,None,"CLI_PINNED_VERSION_MISMATCH"
    if not all(flag in helptext for flag in (b"--events",b"--forward-to")):
        return None,None,"CLI_CONFIG_FLAGS_UNVERIFIED"
    return exe,env,None


def _listen(private,material,key,archive,exe,env):
    data=material["listener"]
    data["archive_file"]=archive.name
    data["test_mode"]=True
    data["config_isolated"]=True
    data["key_in_argv"]=False
    import signal
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as check:
        try:check.bind(("127.0.0.1",8768))
        except OSError:return "RECEIVER_PORT_IN_USE"
    receiver=None;cli=None;out=None;err=None
    receiver_started=False;cli_started=False
    start=time.monotonic()
    try:
        append("local_server","BEGIN","h71-local-server-001")
        receiver_started=True
        out=open(private/"receiver.stdout.log","wb")
        err=open(private/"receiver.stderr.log","wb")
        r_env=dict(os.environ)
        for k in list(r_env):
            if k.upper().startswith("STRIPE_"):r_env.pop(k)
        r_env["H71_PRIVATE_DIR"]=str(private)
        receiver=subprocess.Popen([sys.executable,str(PACK/"RUN.py"),"receiver"],
                   cwd=private,env=r_env,stdout=out,stderr=err,
                   stdin=subprocess.DEVNULL,start_new_session=True)
        data["receiver_pid"]=receiver.pid
        ready=False
        while time.monotonic()-start<5:
            if receiver.poll() is not None:break
            if (private/"receiver.stdout.log").exists() and b"H71_RECEIVER_READY" in (
                private/"receiver.stdout.log").read_bytes():
                ready=True;break
            time.sleep(0.15)
        if not ready:return "LOCAL_RECEIVER_START_FAILED"
        args=[str(exe),"listen","--events",",".join(SPEC["events"]),
              "--forward-to","http://127.0.0.1:8768/stripe/webhook",
              "--project-name","h71-isolated"]
        if any(a in SPEC["forbidden_flags"] for a in args):
            return "CLI_FORBIDDEN_FLAG"
        data["argv"]=["stripe.exe",*args[1:]]
        data["key_sha256"]=sha(key.encode())
        data["stdout_file"]="cli.stdout.log"
        data["stderr_file"]="cli.stderr.log"
        append("listener","BEGIN","h71-listener-001")
        cli_started=True
        data["attempted"]=True
        with open(private/"cli.stdout.log","wb") as stdout,open(private/"cli.stderr.log","wb") as stderr:
            cli=subprocess.Popen(args,cwd=private,env=env,stdout=stdout,stderr=stderr,
                                 stdin=subprocess.DEVNULL,start_new_session=True)
            data["listener_pid"]=cli.pid
            ready_since=None
            while time.monotonic()-start<44:
                if cli.poll() is not None:break
                logs=(private/"cli.stdout.log").read_bytes()+(private/"cli.stderr.log").read_bytes()
                if b"Ready!" in logs and re.search(rb"whsec_[A-Za-z0-9]+",logs):
                    data["ready"]=True
                    if ready_since is None:ready_since=time.monotonic()
                    if time.monotonic()-ready_since>=10:return None
                time.sleep(0.2)
        return "CLI_LISTENER_NOT_READY"
    finally:
        if cli is not None:
            if cli.poll() is None:cli.terminate()
            try:cli.wait(timeout=4)
            except subprocess.TimeoutExpired:cli.kill();cli.wait(timeout=2)
            data["stopped"]=cli.poll() is not None
            data["exit_code"]=cli.returncode
        if receiver is not None:
            if receiver.poll() is None:receiver.terminate()
            try:receiver.wait(timeout=4)
            except subprocess.TimeoutExpired:receiver.kill();receiver.wait(timeout=2)
            data["receiver_stopped"]=receiver.poll() is not None
        if out:out.close()
        if err:err.close()
        if cli_started:
            append("listener","END","h71-listener-001",
                status="SUCCEEDED" if data["ready"] and data["stopped"] else "INPUT_LIMIT",
                stopped=data["stopped"],owned_pid=data.get("listener_pid"))
        if receiver_started:
            append("local_server","END","h71-local-server-001",
                status="SUCCEEDED" if data["receiver_stopped"] else "INPUT_LIMIT",
                stopped=data["receiver_stopped"],
                owned_pid=data.get("receiver_pid"),
                started=receiver is not None)


def _browser_local(private,material):
    # The available workspace interface has no supported isolated-browser
    # session action; native Chrome/CDP fallback is prohibited by the contract.
    # Report a real capability limitation, not a self-authored click record.
    return "SUPPORTED_ISOLATED_BROWSER_TOOL_UNAVAILABLE"


def qualify():
    # No external operations until all frozen conditions and implementation close.
    check=subprocess.run([sys.executable,str(PACK/"CHECK.py"),"integrity"],cwd=ROOT,
                         capture_output=True,timeout=90)
    if check.returncode:raise RuntimeError("frozen_integrity_failed")
    if not any(r["attempt_id"]=="h71-implementation-001" and r["event"]=="END"
               and r.get("status")=="SUCCEEDED" for r in rows()):
        raise RuntimeError("implementation_not_closed")
    if any(r["kind"]=="live_get" for r in rows()) or (PACK/"RESULT.json").exists():
        raise RuntimeError("runtime_probe_already_performed")
    private=_private("H71_PRIVATE_DIR")
    material={"schema":PRIVATE_SCHEMA,"run_id":"h71-existing-anon-20261112-001",
              "h69_snapshot_sha256":None,"key_sha256":None,
              "account_ref":None,"phases":_phases(),"http":[],
              "listener":_listener(),"browser":_browser()}
    decision="INPUT_LIMIT";stage="prerequisites";reason="PREREQUISITE_UNKNOWN"
    try:
        key,account,h69_digest=_load_h69()
        material["h69_snapshot_sha256"]=h69_digest
        material["key_sha256"]=sha(key.encode())
        material["account_ref"]=sha(account.encode())
        _write_private(private,"CREDENTIALS.json",
                       json.dumps({"key":key,"account_id":account},sort_keys=True).encode())
        _phase(material,"prerequisites","PASS","ORIGINAL_H69_CREDENTIAL_VERIFIED")
        stage="source_review"
        archived=_sources()
        _matrix(archived)
        if not archived:
            reason="NO_OFFICIAL_SOURCE_BYTES"
            _phase(material,stage,"INPUT_LIMIT",reason)
            return
        _phase(material,stage,"PASS","OFFICIAL_SOURCE_BYTES_ARCHIVED")
        stage="readonly"
        for index,url in enumerate(SPEC["urls"]):
            valid,detail=_get(private,material,key,url,index)
            if not valid:
                reason=detail
                _phase(material,stage,"INPUT_LIMIT",reason)
                return
        _phase(material,stage,"PASS","THREE_EMPTY_COMPLETE_LISTS")
        stage="download"
        archive,problem=_download(private,material)
        if problem:
            reason=problem
            _phase(material,stage,"INPUT_LIMIT",reason)
            return
        exe,env,problem=_cli_offline(private,archive,key,material)
        if problem:
            reason=problem
            _phase(material,stage,"INPUT_LIMIT",reason)
            return
        material["listener"]["archive_file"]=archive.name
        _phase(material,stage,"PASS","PINNED_WINDOWS_CLI_VERIFIED")
        stage="listen"
        problem=_listen(private,material,key,archive,exe,env)
        if problem:
            reason=problem
            _phase(material,stage,"INPUT_LIMIT",reason)
            return
        _phase(material,stage,"PASS","ISOLATED_TEST_LISTENER_READY")
        stage="browser_local"
        problem=_browser_local(private,material)
        if problem:
            reason=problem
            _phase(material,stage,"INPUT_LIMIT",reason)
            return
        _phase(material,stage,"PASS","LOCAL_CLICK_OBSERVED")
        decision="READ_AND_LISTEN_READY"
        stage="complete"
        reason="QUALIFICATION_STAGES_COMPLETE"
    except (OSError,ValueError,RuntimeError,TypeError,KeyError,IndexError,
            subprocess.SubprocessError) as exc:
        # Private exception data contains no raw error/HTTP body.
        if material["phases"][stage]["status"]=="NOT_RUN":
            _phase(material,stage,"INPUT_LIMIT","LOCAL_"+type(exc).__name__.upper())
        reason="LOCAL_"+type(exc).__name__.upper()
        _write_private(private,"ERROR_KIND.json",
                       json.dumps({"stage":stage,"exception_type":type(exc).__name__}).encode())
    finally:
        _save(private,material,decision,stage,reason)


def command():
    args=sys.argv[1:]
    if args==["init"]:init()
    elif args==["implementation-done"]:
        append("implementation","END","h71-implementation-001",status="SUCCEEDED")
        print("H71 offline implementation closed")
    elif args==["offline-selftest"]:
        if len(SOURCE_URLS)>24 or len({u for _,u in SOURCE_URLS})!=len(SOURCE_URLS):
            raise RuntimeError("source_budget")
        if not all(u.startswith(("https://docs.stripe.com/","https://raw.githubusercontent.com/stripe/stripe-cli/v1.55.10/"))
                   for _,u in SOURCE_URLS):raise RuntimeError("source_allowlist")
        if len(SPEC["urls"])!=3 or not all(u.endswith("?limit=100") for u in SPEC["urls"]):
            raise RuntimeError("runtime_allowlist")
        print("H71 offline scope/allowlist selftest OK")
    elif args==["qualify"]:qualify()
    elif args==["close-work"]:
        history=rows()
        opens={r["attempt_id"]:r for r in history if r["event"]=="BEGIN"}
        ends={r["attempt_id"] for r in history if r["event"]=="END"}
        if set(opens)-ends!={"h71-active-001"}:raise RuntimeError("material_attempt_not_closed")
        result=json.loads((PACK/"RESULT.json").read_text(encoding="utf-8"))
        append("active_work","END","h71-active-001",
               status="SUCCEEDED" if result["decision"]=="READ_AND_LISTEN_READY" else "INPUT_LIMIT")
        print("H71 executor envelope closed")
    elif len(args) in (3,4) and args[0]=="l2":
        if args[1]=="BEGIN" and len(args)==3:
            append("l2","BEGIN",args[2])
        elif args[1]=="END" and len(args)==4:
            append("l2","END",args[2],status=args[3])
        else:raise RuntimeError("gate_argument_invalid")
        print("H71 local L2",args[1])
    else:raise SystemExit("H71 runner: init | implementation-done | offline-selftest | qualify | close-work | l2 BEGIN/END")


if __name__=="__main__":
    command()
