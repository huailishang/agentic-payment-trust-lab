"""H69 bounded qualification runner. Only the frozen task may invoke this."""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
LEDGER = PACK / "ATTEMPT_LEDGER.jsonl"


def _ledger_rows():
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()] if LEDGER.exists() else []


def _append(kind: str, event: str, attempt_id: str, **detail):
    rows = _ledger_rows()
    if [row["seq"] for row in rows] != list(range(1, len(rows)+1)):
        raise RuntimeError("ledger_invalid_sequence")
    matching = [row for row in rows if row["attempt_id"] == attempt_id]
    if event == "BEGIN" and matching or event == "END" and (len(matching) != 1 or matching[0]["event"] != "BEGIN"):
        raise RuntimeError("ledger_duplicate_or_missing_begin")
    row = {"seq":len(rows)+1, "event":event, "attempt_id":attempt_id,
           "kind":kind, "at":datetime.now(timezone.utc).isoformat(), **detail}
    with LEDGER.open("ab") as fp:
        fp.write((json.dumps(row, sort_keys=True, separators=(",",":"))+"\n").encode())
        fp.flush()
        os.fsync(fp.fileno())


def init():
    import subprocess
    result = subprocess.run([sys.executable, str(PACK/"CHECK.py"), "integrity"],
                            cwd=ROOT, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError("h69_integrity_not_ready")
    _append("active_work","BEGIN","h69-active-001")
    _append("implementation","BEGIN","h69-implementation-001")
    print("H69 bounded work opened; no external calls")


# Only standard-library HTTPS and a locally owned test receiver are used.
import hashlib
import http.server
import platform
import re
import shutil
import socket
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

MAX_BODY = 2 * 1024 * 1024
CONTACT = "h68-checkout-lab@example.invalid"
API_VERSION = "2026-10-28.endive"
TEST_EVENTS = "checkout.session.completed,checkout.session.expired,payment_intent.succeeded"


def _stamp():
    return datetime.now(timezone.utc).isoformat()


def _hash(blob):
    return hashlib.sha256(blob).hexdigest()


def _private():
    value = os.environ.get("H69_PRIVATE_DIR", "")
    if not value:
        raise RuntimeError("private_dir_required")
    private = Path(value).resolve()
    if private == ROOT or private.is_relative_to(ROOT) or private == PACK:
        raise RuntimeError("private_inside_repository")
    if private.is_symlink():
        raise RuntimeError("private_symlink_forbidden")
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(private, 0o700)
    if (private / "SNAPSHOT.json").exists() or (private / "CREDENTIALS.json").exists():
        raise RuntimeError("private_previous_material_already_exists")
    return private


def _write_private(private, rel, raw, overwrite=False):
    file = private / rel
    if not file.resolve().is_relative_to(private) or file.is_symlink():
        raise RuntimeError("private_path_escape")
    file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT
    if not overwrite:
        flags |= os.O_EXCL
    else:
        flags |= os.O_TRUNC
    fd = os.open(file, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return rel


def _json(raw):
    return json.loads(raw.decode("utf-8"))


def _snapshot(private, material, stage, decision, reason, account_ref):
    snapshot = (json.dumps(material, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
    _write_private(private, "SNAPSHOT.json", snapshot)
    result = {
        "schema":"h69-qualification-result/v1",
        "task_id":PACK.name, "run_id":material["run_id"],
        "decision":decision, "stage":stage, "reason_code":reason,
        "creation":material["creation"], "account_ref":account_ref,
        "private_snapshot_sha256":_hash(snapshot),
        "checkout_sessions":0, "payments":0, "browser_actions":0,
    }
    (PACK / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision":decision,"stage":stage,"creation":material["creation"],
                      "reason_code":reason}, sort_keys=True))


def _no_redirect(*args, **kwargs):
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _network_error(exc):
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "TIMEOUT"
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "TIMEOUT"
    if isinstance(reason, socket.gaierror):
        return "DNS"
    if isinstance(reason, ssl.SSLError):
        return "TLS"
    return "NETWORK"


def _http(private, material, *, kind, method, url, request_data=None, key=None):
    if kind not in {"challenge", "provision", "account_get"}:
        raise RuntimeError("unsupported_http_kind")
    targets = {
        "challenge":("POST","https://ai.stripe.com/keys/challenge"),
        "provision":("POST","https://ai.stripe.com/keys/provision"),
        "account_get":("GET","https://api.stripe.com/v1/account"),
    }
    if (method,url) != targets[kind]:
        raise RuntimeError("unexpected_network_target")
    if kind == "account_get" and (not key or not key.startswith("rkcs_test_")):
        raise RuntimeError("readback_non_test_key")
    ident = "h69-" + kind + "-001"
    rows = _ledger_rows()
    if any(row["kind"] == kind and row["event"] == "BEGIN" for row in rows):
        raise RuntimeError("no_repeated_external_attempt")
    if kind == "challenge":
        request_data = json.dumps({"email":CONTACT}, separators=(",",":")).encode()
    if method == "POST" and request_data is None:
        raise RuntimeError("missing_post_data")
    request_file = None
    if request_data is not None:
        request_file = _write_private(private, "http/"+kind+".request.json", request_data)
    _append(kind, "BEGIN", ident, target=url)
    started_at = _stamp()
    status, body, error = None, None, None
    try:
        headers = {"User-Agent":"H69-StripeAnonymousQualification/1",
                   "Stripe-Version":API_VERSION}
        if method == "POST":
            headers["Content-Type"] = "application/json"
        else:
            headers["Authorization"] = "Bearer " + key
        request = urllib.request.Request(url, data=request_data, method=method, headers=headers)
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request,timeout=30) as resp:
                status = int(resp.status)
                body = resp.read(MAX_BODY + 1)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            body = exc.read(MAX_BODY + 1)
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            error = _network_error(exc)
        if body is not None and len(body) > MAX_BODY:
            # Bound private bytes, record truncation explicitly, fail closed.
            body = body[:MAX_BODY]
            error = "BODY_TRUNCATED"
    finally:
        _append(kind, "END", ident, status="SUCCEEDED" if status == 200 and error is None
                else ("UNKNOWN" if kind == "provision" and status is None else "INPUT_LIMIT"),
                http_status=status, error=error)
    finished_at = _stamp()
    response_file = _write_private(private, "http/"+kind+".response.bin", body) if body is not None else None
    record = {
        "method":method,"url":url,"status":status,
        "error":error,"body_file":response_file,
        "body_sha256":_hash(body) if body is not None else None,
        "started_at":started_at,"finished_at":finished_at,
    }
    if request_file is not None:
        record["request_body_file"] = request_file
    material["http"].append(record)
    return status,body,error


def _solve(challenge):
    if not isinstance(challenge,dict):
        return None,"CHALLENGE_SCHEMA_INVALID"
    algo = challenge.get("algorithm","")
    target = challenge.get("challenge","")
    salt = challenge.get("salt","")
    signature = challenge.get("signature","")
    if not all(isinstance(x,str) for x in (algo,target,salt,signature)):
        return None,"CHALLENGE_SCHEMA_INVALID"
    if algo.lower().replace("-","") != "sha256":
        return None,"CHALLENGE_UNSUPPORTED_ALGORITHM"
    if not (len(target) == 64 and re.fullmatch(r"[0-9a-fA-F]{64}",target)
            and isinstance(salt,str) and salt and isinstance(signature,str) and signature):
        return None,"CHALLENGE_SCHEMA_INVALID"
    target = target.lower()
    salt_bytes = salt.encode("utf-8")
    deadline = time.monotonic()+30
    for number in range(100_000_000):
        if number & 0xfff == 0 and time.monotonic() >= deadline:
            return None,"CHALLENGE_SOLVE_TIMEOUT"
        if hashlib.sha256(salt_bytes+str(number).encode()).hexdigest() == target:
            return number,None
    return None,"CHALLENGE_MAX_ITERATIONS"


def _listener_default():
    return {
        "attempted":False,"ready":False,"test_mode":False,"stopped":False,
        "stdout_file":None,"stderr_file":None,"archive_sha256":None,
        "config_isolated":False,"key_in_argv":False,
        "receiver_stopped":False,"archive_file":None
    }


def _preflight(private, material):
    probes = {
        "run_id":material["run_id"], "eligible":False,
        "host_platform":platform.system(),"host_arch":platform.machine(),
        "native_windows":False, "native_windows_arch":None,
        "original_deadline":"2026-11-13T00:59:06+00:00",
        "authorized_scope":"anonymous_qualification_only",
    }
    try:
        native = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
        if platform.system() == "Windows":
            native = Path("powershell.exe")
        proc = subprocess.run([str(native),"-NoProfile","-NonInteractive","-Command",
            "[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()"],
            capture_output=True, timeout=12)
        arch = proc.stdout.decode("utf-8",errors="replace").strip()
        probes["native_windows"] = proc.returncode == 0
        probes["native_windows_arch"] = arch if len(arch) <= 20 else "UNKNOWN"
        ok_host = probes["native_windows"] and arch.upper() in {"X64","AMD64"}
    except (FileNotFoundError,OSError,subprocess.TimeoutExpired):
        ok_host = False
    # Isolated distribution is for Windows x64 only. Never substitute Linux binary.
    probes["eligible"] = bool(ok_host)
    _write_private(private, "PREFLIGHT.json",
                   (json.dumps(probes,sort_keys=True,indent=2)+"\n").encode())
    material["preflight_file"] = "PREFLIGHT.json"
    return ok_host


def _download(private, material):
    """Exact pinned release, max 3 HTTP hops/64 MiB, no general-purpose URL fetch."""
    spec = json.loads((PACK/"SPEC.json").read_text(encoding="utf-8"))
    archive_info = spec["cli"]
    original = archive_info["url"]
    current = original
    archive_name = "stripe_1.55.10_windows_x86_64.zip"
    data = None
    requests = 0
    for hop in range(3):
        parts = urllib.parse.urlsplit(current)
        if not (parts.scheme == "https" and
            ((hop == 0 and current == original) or
             (hop > 0 and parts.hostname in {
                "release-assets.githubusercontent.com",
                "objects.githubusercontent.com", "github.com"
             }))):
            return None,"DOWNLOAD_UNTRUSTED_REDIRECT"
        ident = "h69-download-%03d" % (hop+1)
        _append("download","BEGIN",ident,target_host=parts.hostname)
        requests += 1
        raw=None
        response_status=None
        destination=None
        error=None
        try:
            request=urllib.request.Request(current,method="GET",headers={
                "User-Agent":"H69-StripePinnedCLI/1"
            })
            try:
                with urllib.request.build_opener(_NoRedirect()).open(request,timeout=30) as resp:
                    response_status=int(resp.status)
                    if response_status == 200:
                        raw=resp.read(64*1024*1024 + 1)
                    else:
                        raw=resp.read(4096)
                    destination=resp.headers.get("Location")
            except urllib.error.HTTPError as exc:
                response_status=int(exc.code)
                destination=exc.headers.get("Location")
                raw=exc.read(4096)
            except (urllib.error.URLError,TimeoutError,socket.timeout,OSError) as exc:
                error=_network_error(exc)
        finally:
            _append("download","END",ident,
                    status="SUCCEEDED" if response_status == 200 else "INPUT_LIMIT",
                    bytes=len(raw) if raw else 0,http_status=response_status,error=error)
        if response_status in (301,302,303,307,308):
            if not destination:
                return None,"DOWNLOAD_REDIRECT_MISSING"
            current = urllib.parse.urljoin(current,destination)
            continue
        if response_status != 200 or raw is None:
            return None, "DOWNLOAD_HTTP_OR_NETWORK_LIMIT"
        if len(raw)>64*1024*1024:
            return None,"DOWNLOAD_TOO_LARGE"
        if len(raw)!=archive_info["archive_bytes"] or _hash(raw)!=archive_info["archive_sha256"]:
            return None,"DOWNLOAD_PINNED_DIGEST_MISMATCH"
        _write_private(private, archive_name, raw)
        return private/archive_name, None
    return None,"DOWNLOAD_REDIRECT_LIMIT"


def _receiver(private):
    """Child process: local-only receiver; never interprets incoming event as payment."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/stripe/webhook":
                self.send_error(404)
                return
            length = self.headers.get("Content-Length","0")
            if not length.isdigit() or int(length)>MAX_BODY:
                self.send_error(413)
                return
            raw = self.rfile.read(int(length))
            # No real webhook is expected; never print body, signature or headers.
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"accepted test callback without fulfillment")
        def log_message(self,*args):
            return
    server = http.server.HTTPServer(("127.0.0.1",8768),Handler)
    try:
        print("H69_LOCAL_RECEIVER_READY",flush=True)
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


def _listen(private, material, key, archive):
    """Exactly one isolated local receiver and Windows CLI process, both <=60s."""
    data=material["listener"]
    data["attempted"]=True
    data["archive_file"]=archive.name
    data["archive_sha256"]=_hash(archive.read_bytes())
    exe=private/"stripe.exe"
    try:
        with zipfile.ZipFile(archive) as zipped:
            names=[v for v in zipped.namelist() if Path(v).name.lower()=="stripe.exe"]
            if len(names)!=1:
                return "CLI_ARCHIVE_CONTENT_INVALID"
            info=zipped.getinfo(names[0])
            if info.file_size>64*1024*1024:
                return "CLI_EXECUTABLE_TOO_LARGE"
            _write_private(private,"stripe.exe",zipped.read(info))
    except (ValueError,zipfile.BadZipFile,KeyError,OSError):
        return "CLI_ARCHIVE_EXTRACTION_FAILED"
    native_path=str(exe)
    # WSL interoperates with native Windows executables on the mounted Windows volume.
    if not native_path.endswith(".exe"):
        return "CLI_NOT_WINDOWS_EXECUTABLE"
    private_windows=subprocess.run(["wslpath","-w",str(private)],capture_output=True,text=True,timeout=6)
    if private_windows.returncode:
        return "PRIVATE_WINDOWS_PATH_UNAVAILABLE"
    winroot=private_windows.stdout.strip()
    winexe=subprocess.run(["wslpath","-w",native_path],capture_output=True,text=True,timeout=6)
    if winexe.returncode:
        return "CLI_WINDOWS_PATH_UNAVAILABLE"
    executable=winexe.stdout.strip()
    runtime=private/"cli-runtime"
    runtime.mkdir(mode=0o700,exist_ok=True)
    winruntime=subprocess.run(["wslpath","-w",str(runtime)],capture_output=True,text=True,timeout=6)
    if winruntime.returncode:
        return "CLI_RUNTIME_PATH_UNAVAILABLE"
    child_env=dict(os.environ)
    for name in list(child_env):
        upper=name.upper()
        if upper.startswith("STRIPE_") or upper in {
            "HOME","USERPROFILE","APPDATA","LOCALAPPDATA","XDG_CONFIG_HOME"
        }:
            del child_env[name]
    child_env.update({
        "STRIPE_API_KEY":key,"STRIPE_NO_AUTO_UPDATE":"1",
        "STRIPE_CLI_TELEMETRY":"0",
        "HOME":winruntime.stdout.strip(),
        "USERPROFILE":winruntime.stdout.strip(),
        "APPDATA":winruntime.stdout.strip(),
        "LOCALAPPDATA":winruntime.stdout.strip(),
        "XDG_CONFIG_HOME":winruntime.stdout.strip(),
    })
    data["config_isolated"]=True
    data["test_mode"]=True
    args=[native_path,"listen","--events",TEST_EVENTS,
          "--forward-to","http://127.0.0.1:8768/stripe/webhook",
          "--project-name","h69-isolated"]
    data["key_in_argv"]=False
    # Verify the pinned CLI locally before any listener or callback service starts.
    for check_args, filename in (
        ([native_path, "--version"], "cli.version.log"),
        ([native_path, "listen", "--help"], "cli.help.log"),
    ):
        try:
            checked=subprocess.run(check_args, cwd=str(private), env=child_env,
                                   capture_output=True, timeout=8)
        except (OSError,subprocess.TimeoutExpired):
            return "CLI_OFFLINE_VERSION_OR_HELP_FAILED"
        _write_private(private, filename, checked.stdout+checked.stderr)
        if checked.returncode:
            return "CLI_OFFLINE_VERSION_OR_HELP_FAILED"
        if filename=="cli.version.log" and b"1.55.10" not in checked.stdout+checked.stderr:
            return "CLI_VERSION_MISMATCH"
    cli=None
    receiver=None
    try:
        # Ensure port availability without harming other services.
        precheck=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            precheck.bind(("127.0.0.1",8768))
        finally:
            precheck.close()
    except OSError:
        return "RECEIVER_PORT_UNAVAILABLE"
    _append("local_server","BEGIN","h69-receiver-001")
    recvout=open(private/"receiver.stdout.log","wb")
    recverr=open(private/"receiver.stderr.log","wb")
    try:
        env_recv=dict(os.environ)
        env_recv.pop("STRIPE_API_KEY",None)
        receiver=subprocess.Popen([sys.executable,str(PACK/"RUN.py"),"receiver"],
                                  cwd=str(private),env=env_recv,
                                  stdout=recvout,stderr=recverr,start_new_session=True)
        data["receiver_pid"]=receiver.pid
        wait_deadline=time.monotonic()+5
        while time.monotonic()<wait_deadline:
            if receiver.poll() is not None:
                return "RECEIVER_FAILED_TO_START"
            if (private/"receiver.stdout.log").exists() and b"H69_LOCAL_RECEIVER_READY" in (
                private/"receiver.stdout.log").read_bytes():
                break
            time.sleep(0.15)
        else:
            return "RECEIVER_NOT_READY"
        _append("listener","BEGIN","h69-listener-001")
        data["stdout_file"]="cli.stdout.log"
        data["stderr_file"]="cli.stderr.log"
        with open(private/"cli.stdout.log","wb") as cliout, open(private/"cli.stderr.log","wb") as clierr:
            cli=subprocess.Popen(args,cwd=str(private),env=child_env,stdout=cliout,stderr=clierr,
                                 start_new_session=True)
            data["listener_pid"]=cli.pid
            ready_since=None
            start=time.monotonic()
            while time.monotonic()-start < 40:
                if cli.poll() is not None:
                    break
                logs=(private/"cli.stdout.log").read_bytes()+(private/"cli.stderr.log").read_bytes()
                if b"Ready!" in logs and re.search(rb"whsec_[A-Za-z0-9]+",logs):
                    data["ready"]=True
                    if ready_since is None:
                        ready_since=time.monotonic()
                    if time.monotonic()-ready_since>=10:
                        break
                time.sleep(0.2)
            return None if data["ready"] else "CLI_LISTENER_NOT_READY"
    finally:
        listener_started = any(row["attempt_id"] == "h69-listener-001" and row["event"] == "BEGIN"
                               for row in _ledger_rows())
        if cli is not None:
            if cli.poll() is None:
                cli.terminate()
            try:cli.wait(timeout=4)
            except subprocess.TimeoutExpired:
                cli.kill();cli.wait(timeout=2)
            data["stopped"]=cli.poll() is not None
        if listener_started:
            _append("listener","END","h69-listener-001",
                    status="SUCCEEDED" if data["ready"] and data["stopped"] else "INPUT_LIMIT",
                    owned_pid=cli.pid if cli is not None else None,
                    stopped=data["stopped"])
        if receiver is not None:
            receiver.terminate() if receiver.poll() is None else None
            try:receiver.wait(timeout=5)
            except subprocess.TimeoutExpired:
                receiver.kill();receiver.wait(timeout=3)
            data["receiver_stopped"]=receiver.poll() is not None
        _append("local_server","END","h69-receiver-001",
                status="SUCCEEDED" if data["receiver_stopped"] else "INPUT_LIMIT",
                owned_pid=receiver.pid if receiver else None,
                stopped=data["receiver_stopped"])
        recvout.close()
        recverr.close()


def _qualify():
    import subprocess
    status=subprocess.run([sys.executable,str(PACK/"CHECK.py"),"integrity"],
        cwd=ROOT,capture_output=True,timeout=90)
    if status.returncode:
        raise RuntimeError("frozen_integrity_failed")
    rows=_ledger_rows()
    if not any(r["attempt_id"]=="h69-implementation-001" and
               r["event"]=="END" and r["status"]=="SUCCEEDED" for r in rows):
        raise RuntimeError("implementation_not_closed")
    if any(r["kind"] in {"challenge","provision","account_get"} and
           r["event"]=="BEGIN" for r in rows):
        raise RuntimeError("no_duplicate_live_qualification")
    if (PACK/"RESULT.json").exists():
        raise RuntimeError("result_already_present")
    private=_private()
    spec=json.loads((PACK/"SPEC.json").read_text(encoding="utf-8"))
    if datetime.now(timezone.utc)>=datetime.fromisoformat(spec["original_deadline"]):
        raise RuntimeError("original_authorization_expired")
    material={
        "schema":"h69-qualification-private/v1",
        "run_id":"h69-anon-20261112-001",
        "creation":"NOT_SENT",
        "http":[],
        "listener":_listener_default(),
    }
    decision="INPUT_LIMIT"
    stage="preflight"
    reason="LOCAL_PREFLIGHT_FAILED"
    account_ref=None
    try:
        if not _preflight(private,material):
            reason="NATIVE_WINDOWS_X64_REQUIRED"
            return
        stage="challenge"
        status, raw, error = _http(private,material,kind="challenge",method="POST",
                                  url="https://ai.stripe.com/keys/challenge")
        if error or status!=200:
            reason=("CHALLENGE_"+(error or "HTTP_"+str(status))).upper()
            return
        try:
            challenge=_json(raw)
        except (UnicodeDecodeError,ValueError):
            reason="CHALLENGE_INVALID_JSON"
            return
        number,reason=_solve(challenge)
        if reason:
            return
        req={
            "algorithm":challenge["algorithm"],
            "challenge":challenge["challenge"],
            "salt":challenge["salt"],
            "signature":challenge["signature"],
            "number":number,"email":CONTACT,
        }
        stage="provision"
        status,raw,error=_http(private,material,kind="provision",method="POST",
                               url="https://ai.stripe.com/keys/provision",
                               request_data=json.dumps(req,separators=(",",":")).encode())
        if status is None:
            material["creation"]="UNKNOWN"
            decision="UNKNOWN_PROVISION_RESULT"
            reason="PROVISION_"+(error or "NETWORK_UNKNOWN")
            return
        if error or status!=200:
            material["creation"]="FAILED"
            reason=("PROVISION_"+(error or "HTTP_"+str(status))).upper()
            return
        try:
            provider=_json(raw)
            key=provider.get("restricted_key") or provider.get("secret_key")
            account=provider.get("account_id") or provider.get("merchant_token")
            if not (isinstance(key,str) and key.startswith("rkcs_test_") and
                    isinstance(account,str) and account.startswith("acct_")):
                reason="PROVISION_UNEXPECTED_OBJECT"
                material["creation"]="FAILED"
                return
        except (ValueError,UnicodeDecodeError,AttributeError):
            reason="PROVISION_INVALID_JSON"
            material["creation"]="FAILED"
            return
        material["creation"]="CREATED"
        account_ref=_hash(account.encode())
        _write_private(private,"CREDENTIALS.json",
            (json.dumps({"key":key,"account_id":account},sort_keys=True)+"\n").encode())
        stage="account"
        status,raw,error=_http(private,material,kind="account_get",method="GET",
            url="https://api.stripe.com/v1/account",key=key)
        if error or status != 200:
            reason="ACCOUNT_"+(error or "HTTP_"+str(status))
            return
        try:
            verified=_json(raw).get("id")==account
        except (ValueError,UnicodeDecodeError,AttributeError):
            verified=False
        if not verified:
            reason="ACCOUNT_OWNERSHIP_MISMATCH"
            return
        stage="download"
        archive,reason=_download(private,material)
        if reason:
            return
        stage="listen"
        reason=_listen(private,material,key,archive)
        if reason:
            return
        decision="ELIGIBLE"
        stage="complete"
        reason="ANONYMOUS_TEST_LISTENER_READY"
    except (OSError,RuntimeError,ValueError,TypeError,KeyError,
            subprocess.SubprocessError) as exc:
        reason="QUALIFICATION_LOCAL_EXCEPTION"
        if material["http"] and material["http"][-1]["url"].endswith("provision"):
            record=material["http"][-1]
            if record["status"] is None:
                material["creation"]="UNKNOWN"
                decision="UNKNOWN_PROVISION_RESULT"
        # Full private exception category only; secret values are never printed.
        _write_private(private,"LOCAL_EXCEPTION.json",
                       (json.dumps({"kind":type(exc).__name__,"stage":stage})+"\n").encode())
    finally:
        _snapshot(private,material,stage,decision,reason,account_ref)


def close_implementation():
    _append("implementation","END","h69-implementation-001",status="SUCCEEDED")
    print("H69 offline implementation closed; live attempt remains unspent")


def close_work():
    rows=_ledger_rows()
    starts={r["attempt_id"] for r in rows if r["event"]=="BEGIN"}
    ends={r["attempt_id"] for r in rows if r["event"]=="END"}
    if starts-ends != {"h69-active-001"}:
        raise RuntimeError("unclosed_material_attempts")
    result=json.loads((PACK/"RESULT.json").read_text(encoding="utf-8"))
    _append("active_work","END","h69-active-001",status=
            "SUCCEEDED" if result["decision"]=="ELIGIBLE" else
            ("UNKNOWN" if result["decision"]=="UNKNOWN_PROVISION_RESULT" else "INPUT_LIMIT"))
    print("H69 executor work closed; result="+result["decision"])


def offline_selftest():
    # No network, browser, Stripe config or local listener.
    challenge = {"algorithm":"SHA-256",
                 "salt":"synthetic-H69-",
                 "challenge":hashlib.sha256(b"synthetic-H69-1234").hexdigest(),
                 "signature":"synthetic-signature"}
    assert _solve(challenge)==(1234,None)
    bad=dict(challenge,algorithm="SHA1")
    assert _solve(bad)[1]=="CHALLENGE_UNSUPPORTED_ALGORITHM"
    assert len(_ledger_rows())>=2
    assert json.loads((PACK/"SPEC.json").read_text(encoding="utf-8"))["synthetic_email"]==CONTACT
    print("H69 offline challenge, scope and ledger selftest OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["init"]:
        init()
    elif sys.argv[1:] == ["offline-selftest"]:
        offline_selftest()
    elif sys.argv[1:] == ["implementation-done"]:
        close_implementation()
    elif sys.argv[1:] == ["qualify"]:
        _qualify()
    elif sys.argv[1:] == ["close-work"]:
        close_work()
    elif len(sys.argv) in (4,5) and sys.argv[1] in {"l2","l3"} and sys.argv[2] in {"BEGIN","END"}:
        kind,event,identifier=sys.argv[1:4]
        if event=="BEGIN" and len(sys.argv)==4:
            _append(kind,"BEGIN",identifier)
            print("H69 local gate begun:",kind)
        elif event=="END" and len(sys.argv)==5 and sys.argv[4] in {"SUCCEEDED","FAILED","INPUT_LIMIT"}:
            _append(kind,"END",identifier,status=sys.argv[4])
            print("H69 local gate finished:",kind,sys.argv[4])
        else:
            raise SystemExit("invalid local gate action")
    elif sys.argv[1:] == ["receiver"]:
        _receiver(Path(os.environ["H69_PRIVATE_DIR"]))
    else:
        raise SystemExit("H69 runner: init | implementation-done | qualify | close-work | receiver")
