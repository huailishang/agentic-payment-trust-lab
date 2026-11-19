"""WSL alternative to H76: real SPIRE issuer/workload experiment, NOT Docker L2.
No changes to src/tests, host settings, system services, or Docker. Never export SVID keys.
"""
from __future__ import annotations
import base64
from datetime import datetime,timezone
import hashlib,json,os,pathlib,re,shutil,signal,socket,subprocess,sys,time,uuid

P=pathlib.Path(__file__).resolve().parent
REPO=P.parents[2]
LOCK=json.loads((P/"ASSET_LOCK.json").read_text(encoding="utf-8"))["files"][0]
CACHE=pathlib.Path.home()/".cache/h76-spire-source"
BINS=CACHE/"spire-1.16.0"/"bin"
S=BINS/"spire-server"; A=BINS/"spire-agent"
RUN_ID=uuid.uuid4().hex[:12]
BASE=pathlib.Path("/dev/shm")/("h76w"+RUN_ID)
OUT=P/"evidence"/"wsl_experiment"/RUN_ID
TARGET="spiffe://h76.test/agent/h76-agent/executor/h76-executor"
procs=[]
commands=[]
TOKEN=None
STATE={"schema":"h76-wsl-real-source/v1","run_id":RUN_ID,"mode":"WSL2_NATIVE_NOT_DOCKER_L2","started_utc":datetime.now(timezone.utc).isoformat(),"events":[],"status":"STARTED","private_key_export_count":0,"payment_calls":0}
def stamp():return datetime.now(timezone.utc).isoformat()
def log(event,**kwargs):
    STATE["events"].append({"at":stamp(),"event":event,**kwargs})
    print(event,json.dumps(kwargs,ensure_ascii=False),flush=True)
def save():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"RESULT.json").write_text(json.dumps(STATE,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def private_dir(p,mode=0o700):
    p.mkdir(parents=True,exist_ok=False)
    p.chmod(mode)
    return p
def call(name,argv,timeout=15,check=True,secret=False):
    t=time.time()
    res=subprocess.run([str(x) for x in argv],capture_output=True,timeout=timeout,check=False)
    if not secret:
        commands.append({"name":name,"argv":[str(x) for x in argv],"exit":res.returncode,"duration_s":round(time.time()-t,2)})
    if check and res.returncode!=0:
        raise RuntimeError(name+f" rc={res.returncode} stderr="+res.stderr.decode(errors="replace")[-350:])
    return res
def has_socket(p,timeout=28):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if p.exists() and p.is_socket():return True
        if any(proc.poll() is not None for proc in procs):
            raise RuntimeError("SPIRE process exited before socket: "+repr([(p.pid,p.poll()) for p in procs]))
        time.sleep(.3)
    return False
def root_from_bundle(s):
    match=re.findall(rb"-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----",s)
    if not match:raise RuntimeError("management bundle show did not return a PEM certificate")
    return b"\n".join(match)+b"\n"
def extract_token(data):
    t=data.decode("utf-8","replace")
    try:
        obj=json.loads(t)
        for k in ("value","token","Token"):
            if isinstance(obj,dict) and isinstance(obj.get(k),str) and len(obj[k])>10:return obj[k]
    except (json.JSONDecodeError,ValueError):
        pass
    m=re.search(r"(?:Token|token)\s*:\s*([^\s]+)",t)
    if m:return m.group(1)
    raise RuntimeError("SPIRE token CLI response format unknown; token not logged")
def agent_id_from_json(data):
    txt=data.decode("utf-8","replace")
    try:o=json.loads(txt)
    except json.JSONDecodeError: o=txt
    def strings(v):
        if isinstance(v,str):yield v
        elif isinstance(v,list):
            for x in v:yield from strings(x)
        elif isinstance(v,dict):
            for x in v.values():yield from strings(x)
    ids=[a for a in strings(o) if a.startswith("spiffe://h76.test/") and ("/spire/agent/" in a or "/agent/" in a)]
    if not ids:raise RuntimeError("Cannot derive actual Agent SPIFFE ID from server's agent list")
    return ids[0]
def run():
    global TOKEN
    if not (P/"OWNER_WSL_AUTHORIZATION_20261116.md").is_file():raise RuntimeError("WSL permission missing")
    archive=CACHE/LOCK["filename"]
    if not archive.is_file() or archive.stat().st_size!=LOCK["size"]:
        raise RuntimeError("locked archive missing")
    h=hashlib.sha256()
    with archive.open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):h.update(chunk)
    if h.hexdigest()!=LOCK["sha256"]:raise RuntimeError("SPIRE archive digest mismatch")
    log("LOCKED_SPIRE_ASSET_VERIFIED",version="1.16.0",sha256=h.hexdigest(),bytes=archive.stat().st_size)
    OUT.mkdir(parents=True,exist_ok=False)
    BASE.mkdir(mode=0o711)
    BASE.chmod(0o711)
    for name,mode in [("server-data",0o700),("server-api",0o700),("agent-data",0o700),("workload",0o755),("u1001",0o700),("u1002",0o700),("bin",0o755),("private",0o700)]:
        private_dir(BASE/name,mode)
    for uid,name in [(1001,"u1001"),(1002,"u1002")]:
        call("chown-"+name,["sudo","-n","chown",str(uid)+":"+str(uid),str(BASE/name)])
    # Verified binaries copied to tempfs, visible for UID processes but independent of home dir ACL.
    for src in (S,A):
        dst=BASE/"bin"/src.name
        shutil.copy2(src,dst)
        dst.chmod(0o755)
    port_sock=socket.socket()
    port_sock.bind(("127.0.0.1",0))
    port=port_sock.getsockname()[1];port_sock.close()
    STATE["port"]=port
    server_conf=f'''server {{
 bind_address = "127.0.0.1"
 bind_port = {port}
 socket_path = "{BASE}/server-api/api.sock"
 trust_domain = "h76.test"
 data_dir = "{BASE}/server-data"
 log_level = "INFO"
 ca_key_type = "ec-p256"
 default_x509_svid_ttl = "10m"
}}
plugins {{
 DataStore "sql" {{ plugin_data {{ database_type = "sqlite3" connection_string = "{BASE}/server-data/datastore.sqlite3" }} }}
 NodeAttestor "join_token" {{ plugin_data {{}} }}
 KeyManager "memory" {{ plugin_data {{}} }}
}}
'''
    agent_conf=f'''agent {{
 trust_domain = "h76.test"
 server_address = "127.0.0.1"
 server_port = {port}
 data_dir = "{BASE}/agent-data"
 socket_path = "{BASE}/workload/api.sock"
 trust_bundle_path = "{BASE}/private/root.pem"
 workload_x509_svid_key_type = "ec-p256"
 log_level = "INFO"
}}
plugins {{
 NodeAttestor "join_token" {{ plugin_data {{}} }}
 KeyManager "disk" {{ plugin_data {{ directory = "{BASE}/agent-data" }} }}
 WorkloadAttestor "unix" {{ plugin_data {{ discover_workload_path = false }} }}
}}
'''
    for name,content in [("server.conf",server_conf),("agent.conf",agent_conf)]:
        (BASE/name).write_text(content)
        (OUT/name).write_text(content)
    call("server-validate",[S,"validate","-config",BASE/"server.conf"])
    call("agent-validate",[A,"validate","-config",BASE/"agent.conf"])
    log("CONFIGS_VALID",localhost_port=port)
    server_log=(BASE/"private"/"server.raw.log").open("wb")
    server=subprocess.Popen([str(S),"run","-config",str(BASE/"server.conf")],stdout=server_log,stderr=subprocess.STDOUT,start_new_session=True)
    procs.append(server)
    if not has_socket(BASE/"server-api"/"api.sock",30):raise RuntimeError("server socket timeout")
    sock=BASE/"server-api"/"api.sock"
    # Management root is collected *before* Workload API / leaf issuance.
    root=root_from_bundle(call("management-root",[S,"bundle","show","-socketPath",sock,"-format","pem"],timeout=12).stdout)
    (BASE/"private"/"root.pem").write_bytes(root)
    (OUT/"root.pem").write_bytes(root)
    log("ROOT_CAPTURED_FROM_SPIRE_MANAGEMENT",root_pem_sha256=hashlib.sha256(root).hexdigest())
    token_response=call("generate_join_token",[S,"token","generate","-socketPath",sock,"-ttl","300","-output","json"],timeout=12,secret=True)
    TOKEN=extract_token(token_response.stdout)
    tokenfile=BASE/"private"/"join.token"
    tokenfile.write_text(TOKEN+"\n")
    tokenfile.chmod(0o600)
    log("JOIN_TOKEN_CREATED_PRIVATE",token_sha256=hashlib.sha256(TOKEN.encode()).hexdigest())
    agent_log=(BASE/"private"/"agent.raw.log").open("wb")
    agent=subprocess.Popen([str(A),"run","-config",str(BASE/"agent.conf"),"-joinTokenFile",str(tokenfile)],
        stdout=agent_log,stderr=subprocess.STDOUT,start_new_session=True)
    procs.append(agent)
    if not has_socket(BASE/"workload"/"api.sock",30):raise RuntimeError("agent workload socket timeout")
    (BASE/"workload"/"api.sock").chmod(0o766)
    log("WORKLOAD_SOCKET_READY",socket_mode=oct((BASE/"workload"/"api.sock").stat().st_mode & 0o777))
    # Need authoritative Agent registry state; no synthetic parentID.
    agent_list=None
    for _ in range(14):
        a=call("server-agent-list",[S,"agent","list","-socketPath",sock,"-output","json"],check=False)
        if a.returncode==0:
            try:agent_list=agent_id_from_json(a.stdout);break
            except RuntimeError: pass
        time.sleep(.5)
    parent_origin="server_management_agent_list"
    if not agent_list:
        # Use the real attested Agent's log only if the exact fresh join-token identity
        # is found in a successful NodeAttestation event. Do not fabricate any ID.
        raw=(BASE/"private"/"agent.raw.log").read_text(errors="replace")
        candidate="spiffe://h76.test/spire/agent/join_token/"+TOKEN
        if 'Node attestation was successful' in raw and 'spiffe_id="'+candidate+'"' in raw:
            agent_list=candidate
            parent_origin="actual_agent_success_log_verified_against_fresh_private_token"
        else:
            raise RuntimeError("Cannot establish actual Agent parent ID")
    parent=agent_list
    STATE["parent_source"]=parent_origin
    STATE["actual_parent_id_sha256"]=hashlib.sha256(parent.encode()).hexdigest()
    log("AGENT_REAL_PARENT_ID",parent_sha256=STATE["actual_parent_id_sha256"])
    reg=call("register_workload", [S,"entry","create","-socketPath",sock,"-output","json","-parentID",parent,"-spiffeID",TARGET,"-selector","unix:uid:1001","-x509SVIDTTL","600"],timeout=15,secret=True)
    STATE["entry_cli_success"]=reg.returncode==0
    log("REAL_UID1001_ENTRY_REGISTERED",entry_cli_success=True,selector="unix:uid:1001",spiffe_id=TARGET)
    # Match/unmatch users require the public socket, each private workdir owned by that UID.
    fetch=[str(BASE/"bin"/"spire-agent"),"api","fetch","x509","-socketPath",str(BASE/"workload"/"api.sock"),"-timeout","5s"]
    def uidrun(uid,dest):
        cmd=["sudo","-n","/usr/bin/setpriv","--reuid",str(uid),"--regid",str(uid),"--clear-groups",*fetch,"-write",str(BASE/dest)]
        return call(f"uid{uid}-fetch",cmd,timeout=17,check=False)
    def private_uid_file_exists(uid,path):
        # A UID checks its own mode-0700 directory. The orchestrator never stats private key material.
        return call("private-uid-file-check",["sudo","-n","/usr/bin/setpriv","--reuid",str(uid),"--regid",str(uid),"--clear-groups","/usr/bin/test","-f",path],check=False,secret=True).returncode==0
    time.sleep(2.5)  # registration propagation, no extra fetch attempts
    match=None
    for attempt in range(3):
        match=uidrun(1001,"u1001")
        if match.returncode==0 and private_uid_file_exists(1001,BASE/"u1001"/"svid.0.pem"):break
        time.sleep(2.0)
    assert match is not None
    (OUT/"matching.stdout.log").write_bytes(match.stdout)
    (OUT/"matching.stderr.log").write_bytes(match.stderr)
    has_leaf=private_uid_file_exists(1001,BASE/"u1001"/"svid.0.pem")
    has_key=private_uid_file_exists(1001,BASE/"u1001"/"svid.0.key")
    log("MATCHING_UID1001_FETCH",exit_code=match.returncode,certificate_present=has_leaf,private_key_present_for_owner=has_key)
    if match.returncode!=0 or not has_leaf or not has_key:
        raise RuntimeError("Matched UID1001 did not receive private key and SVID from actual API")
    (OUT/"leaf.pem").write_bytes(call("public-leaf",["sudo","-n","cat",BASE/"u1001"/"svid.0.pem"],secret=True).stdout)
    negative=uidrun(1002,"u1002")
    (OUT/"nonmatching.stdout.log").write_bytes(negative.stdout)
    (OUT/"nonmatching.stderr.log").write_bytes(negative.stderr)
    no_identity=not private_uid_file_exists(1002,BASE/"u1002"/"svid.0.pem")
    negative_stderr=negative.stderr.decode("utf-8","replace")
    STATE["unmatched_uid"]={"uid":1002,"exit_code":negative.returncode,"identity_count":0 if no_identity else 1,
        "reject_reason_code_permission_denied":"PermissionDenied" in negative_stderr or "PermissionDenied" in negative.stdout.decode(errors="replace"),
        "socket_connected":not any(e in negative_stderr.lower() for e in ("permission denied while dialing","connect: permission denied","no such file or directory","connection refused"))}
    log("UNMATCHED_UID1002_FETCH",**STATE["unmatched_uid"])
    issued=int(time.time())
    nonce=uuid.uuid4().hex
    payload=(f"agentic-payment-possession/v1\nnonce={nonce}\nagent=h76-agent\nprovider=h76-provider\nexecutor=h76-executor\nissued_at={issued}\n").encode()
    challenge=BASE/"workload"/"payload.bin"
    challenge.write_bytes(payload)
    challenge.chmod(0o644)
    STATE["nonce"]=nonce;STATE["issued_at_epoch"]=issued
    # Private key is loaded and used only within UID1001. Inline code reads private key and writes public signature.
    code=('import base64,pathlib,sys,os; from cryptography.hazmat.primitives import hashes,serialization; '
          'from cryptography.hazmat.primitives.asymmetric import ec; '
          'k=serialization.load_pem_private_key(pathlib.Path(sys.argv[1]).read_bytes(),password=None); '
          'sig=k.sign(pathlib.Path(sys.argv[2]).read_bytes(),ec.ECDSA(hashes.SHA256())); '
          'pathlib.Path(sys.argv[3]).write_bytes(base64.b64encode(sig)+b"\\n"); '
          'print("SIGNING_UID="+str(os.geteuid())+" PID="+str(os.getpid()))')
    sign=call("real-holder-sign",["sudo","-n","/usr/bin/setpriv","--reuid","1001","--regid","1001","--clear-groups",
        sys.executable,"-c",code,BASE/"u1001"/"svid.0.key",challenge,BASE/"u1001"/"signature.b64"],timeout=16,secret=True)
    (OUT/"payload.bin").write_bytes(payload)
    (OUT/"signature.b64").write_bytes(call("public-signature",["sudo","-n","cat",BASE/"u1001"/"signature.b64"],secret=True).stdout)
    STATE["holder_signing_stdout"]=sign.stdout.decode(errors="replace").strip()
    STATE["signing_uid"]=1001
    log("REAL_UID1001_HOLDER_SIGNED",nonce=nonce,signing_meta=STATE["holder_signing_stdout"])
    STATE["status"]="ISSUER_FETCH_SIGNATURE_CAPTURED"
    STATE["captured_utc"]=stamp()
def cleanup():
    # Dedicated sessions only; no wildcard process kills or system service changes.
    for proc in reversed(procs):
        if proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGTERM)
            except (ProcessLookupError,PermissionError):pass
    for proc in reversed(procs):
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except (ProcessLookupError,PermissionError):pass
    # root may own UID-created files; use strictly scoped sudo rm only after path ownership check.
    try:
        if BASE.exists():
            if BASE.parent==pathlib.Path("/dev/shm") and BASE.name.startswith("h76w") and len(BASE.name)==16:
                subprocess.run(["sudo","-n","rm","-rf","--",str(BASE)],timeout=20,check=True)
            else:log("CLEANUP_GUARD_REJECTED",path=str(BASE))
        STATE["tmpfs_removed"]=not BASE.exists()
    except Exception as e:
        STATE["tmpfs_removed"]=False
        STATE["cleanup_error"]=type(e).__name__+": "+str(e)
    STATE["spire_processes_terminated"]=all(proc.poll() is not None for proc in procs)
    STATE["finished_utc"]=stamp()
    (OUT/"COMMANDS.json").write_text(json.dumps(commands,indent=2)+"\n",encoding="utf-8")
    save()
def signal_handler(signum,frame):
    raise RuntimeError("Received signal "+str(signum))
if __name__=="__main__":
    signal.signal(signal.SIGTERM,signal_handler)
    try:
        run()
    except BaseException as e:
        STATE["status"]="FAILED"
        STATE["failure"]=type(e).__name__+": "+str(e)
        log("RUN_FAILED",reason=STATE["failure"])
        raise
    finally:
        # Redact join tokens and their derived agent IDs from raw logs before copying.
        if OUT.exists():
            for who in ("server","agent"):
                src=BASE/"private"/(who+".raw.log")
                if src.exists():
                    raw=src.read_text(errors="replace")
                    if TOKEN:raw=raw.replace(TOKEN,"[REDACTED_JOIN_TOKEN]")
                    raw=re.sub(r"join_token/[A-Za-z0-9_-]+","join_token/[REDACTED]",raw)
                    (OUT/(who+".redacted.log")).write_text(raw[-50000:],encoding="utf-8")
        cleanup()
