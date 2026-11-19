"""H77 native Ubuntu collector and narrowly scoped UID/cleanup helpers.

Only `issuer` starts SPIRE. That path independently checks the accepted router
and one-use Windows dispatch before making any mutation or starting a service.
All subprocesses use argv, never a shell; secrets stay inside owned tmpfs.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import time

TARGET = "spiffe://h76.test/agent/h76-agent/executor/h76-executor"
PLACEHOLDER = "[REDACTED_JOIN_TOKEN]"
HEX = re.compile(r"[0-9a-f]{32}\Z")


def need(value, message):
    if not value:
        raise ValueError(message)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append(path, data):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def redact(text, token=None):
    if token:
        text = text.replace(token, PLACEHOLDER)
    return re.sub(r"join_token/(?!\[)[A-Za-z0-9_-]+", "join_token/" + PLACEHOLDER, text)


def spiffe(value):
    if isinstance(value, str):
        need(value.startswith("spiffe://h76.test/") and not any(c.isspace() for c in value), "invalid SPIFFE ID")
        return value
    need(isinstance(value, dict), "expected structured SPIFFE ID")
    domain = value.get("trust_domain", value.get("trustDomain"))
    path = value.get("path")
    need(domain == "h76.test" and isinstance(path, str) and path.startswith("/") and ".." not in PurePosixPath(path).parts, "bad SPIFFE domain/path")
    return spiffe("spiffe://" + domain + path)


def field(obj, *keys):
    present = [obj[key] for key in keys if key in obj]
    need(len(present) == 1, "missing or ambiguous field: " + "/".join(keys))
    return present[0]


def parent_from_management(obj):
    need(isinstance(obj, dict) and isinstance(obj.get("agents"), list), "agent list schema")
    need(len(obj["agents"]) == 1, "expected exactly one attested agent")
    agent = obj["agents"][0]
    parent = spiffe(field(agent, "id", "spiffe_id", "spiffeId"))
    need(parent.startswith("spiffe://h76.test/spire/agent/join_token/") and len(parent.rsplit("/", 1)[1]) > 10, "not a join-token attested parent")
    attestor = agent.get("attestation_type", agent.get("attestationType"))
    if attestor is not None:
        need(attestor == "join_token", "wrong attestation type")
    return parent


def one_entry(obj):
    need(isinstance(obj, dict), "entry JSON must be object")
    if "entries" in obj:
        need(isinstance(obj["entries"], list) and len(obj["entries"]) == 1, "one registration entry required")
        return obj["entries"][0]
    if "entry" in obj:
        need(isinstance(obj["entry"], dict), "entry wrapper")
        return obj["entry"]
    need("id" in obj and ("spiffe_id" in obj or "spiffeId" in obj), "entry object schema")
    return obj


def entry_identity(obj):
    value = field(one_entry(obj), "id", "entry_id", "entryId")
    need(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9-]{8,80}", value), "entry ID")
    return value


def validate_entry(obj, parent, entry_id):
    entry = one_entry(obj)
    need(entry_identity(obj) == entry_id, "entry ID drift")
    need(spiffe(field(entry, "parent_id", "parentId")) == parent, "registration parent mismatch")
    need(spiffe(field(entry, "spiffe_id", "spiffeId")) == TARGET, "registration target mismatch")
    need(entry.get("selectors") == [{"type": "unix", "value": "uid:1001"}], "registration must have only UID1001")
    return entry


def extract_binaries(archive, destination, member_profile):
    names = ("spire-server", "spire-agent")
    need(isinstance(member_profile, dict) and member_profile.get("schema") == "h77r2-exact-members/v1"
         and member_profile.get("spire_version") == "1.16.0"
         and member_profile.get("no_floating_size_ceiling") is True
         and isinstance(member_profile.get("binaries"), dict)
         and set(member_profile["binaries"]) == set(names), "exact member profile required")
    need(archive.is_file() and not archive.is_symlink()
         and archive.stat().st_size == member_profile.get("archive_size")
         and sha(archive) == member_profile.get("archive_sha256"), "locked archive mismatch")
    expected = {}
    for name in names:
        item = member_profile["binaries"][name]
        need(isinstance(item, dict) and item.get("archive_member") == "spire-1.16.0/bin/" + name
             and type(item.get("size")) is int and item["size"] > 0
             and isinstance(item.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]),
             "invalid exact binary member profile")
        expected[name] = item
    need(member_profile.get("total_binary_bytes") == sum(x["size"] for x in expected.values()),
         "binary profile total mismatch")
    need(destination.is_dir() and not destination.is_symlink(), "unsafe extraction destination")
    result = {}
    with tarfile.open(archive, "r:gz") as stream:
        members = stream.getmembers()
        seen = set()
        for member in members:
            rel = PurePosixPath(member.name)
            need(not rel.is_absolute() and ".." not in rel.parts and "\\" not in member.name
                 and (member.isdir() or member.isfile()), "unsafe archive member")
            need(member.name not in seen, "duplicate archive member")
            seen.add(member.name)
        for name, item in expected.items():
            rel = item["archive_member"]
            candidates = [m for m in members if m.name == rel]
            need(len(candidates) == 1 and candidates[0].isfile()
                 and candidates[0].size == item["size"], "missing/nonregular/duplicate or wrong-size binary")
            destination_path = destination / name
            need(not destination_path.exists() and not destination_path.is_symlink(), "destination already exists")
            source = stream.extractfile(candidates[0])
            need(source is not None, "member unreadable")
            written = 0
            with source, destination_path.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    written += len(chunk)
                    need(written <= item["size"], "archive member overflow")
                    target.write(chunk)
            need(written == item["size"] and destination_path.stat().st_size == item["size"],
                 "short archive member")
            source_again = stream.extractfile(candidates[0])
            need(source_again is not None, "member reread unavailable")
            digest = hashlib.sha256()
            with source_again:
                for chunk in iter(lambda: source_again.read(1024 * 1024), b""):
                    digest.update(chunk)
            member_sha = digest.hexdigest()
            destination_path.chmod(0o755)
            executed_sha = sha(destination_path)
            need(member_sha == executed_sha == item["sha256"], "binary provenance mismatch")
            result[name] = {"archive_member": rel, "archive_member_sha256": member_sha,
                            "executed_sha256": executed_sha}
    return result


def proc_record(pid):
    base = Path("/proc") / str(pid)
    status = (base / "status").read_text()
    ids = next(line.split()[1:] for line in status.splitlines() if line.startswith("Uid:"))
    fields = (base / "stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "kernel_uid": int(ids[0]), "kernel_euid": int(ids[1]), "proc_status": status,
            "start_ticks": fields[19], "process_state": fields[0], "ppid": int(fields[1]),
            "cmdline": (base / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace"),
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def same_process(item):
    try:
        current = proc_record(item["pid"])
        return current["start_ticks"] == item["start_ticks"] and current["boot_id"] == item["boot_id"] and current["process_state"] != "Z"
    except (FileNotFoundError, ProcessLookupError):
        return False


def cleanup_guard(base, identity, run_id):
    need(HEX.fullmatch(run_id) and base == Path("/dev/shm") / ("h77w" + run_id), "cleanup path out of scope")
    return owned_directory_guard(base, identity)


def owned_directory_guard(base, identity):
    need(not base.is_symlink() and base.resolve() == base, "cleanup path symlink/realpath")
    info = base.lstat()
    need(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino, info.st_uid) == tuple(identity), "cleanup ownership/inode changed")
    return True


def private_files(out):
    count = 0
    for path in out.rglob("*"):
        need(not path.is_symlink(), "public output symlink")
        if path.is_file() and (path.suffix.lower() in (".key", ".p12", ".pfx") or b"PRIVATE KEY-----" in path.read_bytes()):
            count += 1
    return count


def cleanup_helper(args, inspect_only=False, stop_only=False):
    base = Path(args.base)
    need(HEX.fullmatch(args.run_id), "run ID")
    need(base == Path("/dev/shm") / ("h77w" + args.run_id), "cleanup base")
    owned = json.loads(args.owned)
    identity = [args.device, args.inode, args.owner]
    events = []
    if base.exists() or base.is_symlink():
        cleanup_guard(base, identity, args.run_id)
    for item in reversed(owned):
        need(isinstance(item["pid"], int) and item["pid"] > 1 and item["pid"] != os.getpid(), "unsafe cleanup PID")
        if not inspect_only:
            for signum, wait in ((signal.SIGTERM, 3), (signal.SIGKILL, 2)):
                if not same_process(item):
                    break
                os.kill(item["pid"], signum)
                events.append({"pid": item["pid"], "start_ticks": item["start_ticks"], "signal": int(signum)})
                until = time.monotonic() + wait
                while same_process(item) and time.monotonic() < until:
                    time.sleep(0.05)
    if not inspect_only and not stop_only and base.exists():
        cleanup_guard(base, identity, args.run_id)
        need(shutil.rmtree.avoids_symlink_attacks, "safe rmtree unavailable")
        shutil.rmtree(base)
        events.append({"path": str(base), "owner_inode_guard": identity, "removed": True})
    alive = [item for item in owned if same_process(item)]
    result = {"owned_processes_alive": alive, "private_tmpfs_exists": base.exists() or base.is_symlink(),
              "public_private_key_files": private_files(Path(args.out)), "events": events, "at_utc": stamp()}
    print(json.dumps(result), flush=True)
    return 0 if not alive and (stop_only or not result["private_tmpfs_exists"]) and result["public_private_key_files"] == 0 else 1


def uid_helper(args):
    base = Path(args.base)
    need(base == Path("/dev/shm") / ("h77w" + args.run_id) and HEX.fullmatch(args.run_id), "UID base")
    uid = 1002 if args.operation in ("nonmatching", "inspect_negative") else 1001
    need(os.getuid() == os.geteuid() == uid, "wrong real/effective UID")
    home = base / ("u" + str(uid))
    need(not home.is_symlink() and home.stat().st_uid == uid and stat.S_IMODE(home.stat().st_mode) == 0o700, "holder private directory")
    if args.operation in ("matching", "nonmatching", "signing"):
        info = proc_record(os.getpid())
        print("H77_KERNEL " + json.dumps(info), flush=True)
        need(sys.stdin.buffer.readline() == b"GO\n", "parent observation handshake missing")
    if args.operation in ("matching", "nonmatching"):
        command = [str(base / "bin/spire-agent"), "api", "fetch", "x509", "-socketPath", str(base / "workload/api.sock"), "-timeout", "5s", "-write", str(home)]
        os.execv(command[0], command)
    if args.operation in ("inspect", "inspect_negative"):
        certs = sorted(home.glob("svid.*.pem"))
        keys = sorted(home.glob("svid.*.key"))
        for key in keys:
            need(not key.is_symlink() and key.stat().st_uid == uid, "private key owner")
            key.chmod(0o600)
        result = {"count": len(certs), "key_count": len(keys), "directory_mode": format(stat.S_IMODE(home.stat().st_mode), "04o")}
        if len(certs) == len(keys) == 1:
            need(certs[0].name == "svid.0.pem" and keys[0].name == "svid.0.key", "unexpected credential filename")
            result.update(leaf_pem=certs[0].read_text(), private_key_owner_uid=keys[0].stat().st_uid,
                          private_key_mode=format(stat.S_IMODE(keys[0].stat().st_mode), "04o"))
        print(json.dumps(result), flush=True)
        return 0
    need(args.operation == "signing", "UID operation")
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    keypath = home / "svid.0.key"
    need(keypath.stat().st_uid == 1001 and stat.S_IMODE(keypath.stat().st_mode) == 0o600 and not keypath.is_symlink(), "signing private key boundary")
    key = serialization.load_pem_private_key(keypath.read_bytes(), password=None)
    need(isinstance(key, ec.EllipticCurvePrivateKey), "expected EC holder")
    signature = key.sign((base / "workload/payload.bin").read_bytes(), ec.ECDSA(hashes.SHA256()))
    print(json.dumps({"signature_b64": base64.b64encode(signature).decode(), "signing_uid": os.geteuid()}), flush=True)
    return 0


class Collector:
    def __init__(self, args):
        self.args, self.out = args, Path(args.out)
        self.task = Path(__file__).resolve().parent
        self.root = self.task.parents[2]
        self.base = Path("/dev/shm") / ("h77w" + args.run_id)
        self.identity = None
        self.owned, self.services, self.handles = [], [], []
        self.token = None
        self.sequence = 0
        # Reserve 100 seconds inside frozen CHECK's 1250-second wrapper for
        # guarded cleanup. This is a live-run watchdog, not a task time budget.
        self.deadline = time.monotonic() + 1100
        self.ledger = self.out / "LIVE_ATTEMPTS.jsonl"
        self.state = {"schema": "h77-wsl-real-source/v1", "run_id": args.run_id, "nonce": args.nonce,
                      "started_utc": stamp(), "status": "STARTED", "events": [], "payment_calls": 0,
                      "private_key_export_count": 0, "new_asset_downloads": 0, "model_api_calls": 0,
                      "active_minutes": "UNKNOWN", "network_wire_bytes": "UNKNOWN"}

    def event(self, kind, **values):
        value = {"kind": kind, "at_utc": stamp(), **values}
        append(self.ledger, value)
        self.state["events"].append(value)

    def authorize(self):
        need(sys.platform == "linux" and HEX.fullmatch(self.args.run_id) and HEX.fullmatch(self.args.nonce), "Ubuntu/run parameters")
        need(self.out == self.task / "evidence/evaluator_runs" / self.args.run_id and self.out.resolve() == self.out and not self.out.is_symlink(), "issuer output path")
        router = (self.root / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0]
        # Frozen flat YAML router; exact keys, not substring authority checks.
        fields = dict(line.split(":", 1) for line in router.splitlines() if ":" in line and not line.lstrip().startswith("#"))
        fields = {k.strip(): v.strip() for k, v in fields.items()}
        need((fields.get("task_id"), fields.get("state"), fields.get("current_role")) == (self.task.name, "READY_FOR_REVIEW", "Evaluator"), "Evaluator router required")
        for key in ("authorization_local_service", "authorization_existing_wsl", "authorization_ephemeral_test_credentials"):
            need(fields.get(key) == "true", "runtime authority missing")
        accepted = read(self.task / "evidence/ACCEPTED.json")
        for rel, expected in accepted["files"].items():
            path = (self.root / rel).resolve()
            need(path.is_relative_to(self.root) and sha(path) == expected, "accepted file drift")
        for name in ("RUN.py", "WORKLOAD.py", "TASK_TESTS.py"):
            need((self.task / name).relative_to(self.root).as_posix() in accepted["files"], "unaccepted script")
        marker = read(self.task / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json")
        dispatch = read(self.out / "DISPATCH.json")
        for value in (marker, dispatch):
            need(value["run_id"] == self.args.run_id and value["nonce"] == self.args.nonce, "attempt mismatch")
        need(marker["budget_consumed"] == 1, "attempt budget")
        with (self.out / "ISSUER_STARTED.json").open("x", encoding="utf-8") as stream:
            json.dump({"at_utc": stamp(), "run_id": self.args.run_id}, stream)

    def budget(self):
        need(time.monotonic() < self.deadline, "live watchdog expired")

    def public(self, raw):
        return redact(raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw, self.token)

    def record_command(self, name, command, started, rc, stdout, stderr, withheld=False):
        self.sequence += 1
        stem = f"raw/{self.sequence:03d}_{name}"
        (self.out / "raw").mkdir(exist_ok=True)
        stdout_path, stderr_path = stem + ".stdout.log", stem + ".stderr.log"
        (self.out / stdout_path).write_text("[WITHHELD: private join token generation response; not an unredacted original]\n" if withheld else self.public(stdout), encoding="utf-8")
        (self.out / stderr_path).write_text("[WITHHELD: private join token command stderr]\n" if withheld else self.public(stderr), encoding="utf-8")
        append(self.out / "COMMANDS.jsonl", {"name": name, "argv": [self.public(str(x)) for x in command], "exit_code": rc,
               "start_epoch": started, "end_epoch": time.time(), "duration_seconds": time.time() - started,
               "stdout": stdout_path, "stderr": stderr_path, "projection": "complete text with join token redaction; no truncation", "stdout_withheld": withheld})
        return {"stdout": stdout_path, "stderr": stderr_path}

    def call(self, name, command, timeout=30, check=True, withheld=False, cleanup=False):
        if not cleanup:
            self.budget()
            timeout = min(timeout, max(0.1, self.deadline - time.monotonic()))
        timeout = min(timeout, 180)
        command = [str(x) for x in command]
        started = time.time()
        try:
            result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            refs = self.record_command(name, command, started, "TIMEOUT", exc.stdout or b"", exc.stderr or b"", withheld)
            if cleanup:
                return subprocess.CompletedProcess(command, 124, exc.stdout or b"", exc.stderr or b""), refs
            raise RuntimeError("command watchdog: " + name) from None
        refs = self.record_command(name, command, started, result.returncode, result.stdout, result.stderr, withheld)
        if check:
            need(result.returncode == 0, "command failed: " + name)
        return result, refs

    def own(self, pid, name):
        item = proc_record(pid)
        item["name"] = name
        self.owned.append(item)
        save(self.out / "OWNED_PROCESSES.json", {"processes": self.owned})
        return item

    def service(self, name, command):
        self.budget()
        handle = (self.base / "private" / (name + ".raw.log")).open("xb")
        self.handles.append(handle)
        proc = subprocess.Popen([str(x) for x in command], stdout=handle, stderr=subprocess.STDOUT)
        self.services.append(proc)
        item = self.own(proc.pid, name)
        self.event("service_start", name=name, pid=proc.pid, start_ticks=item["start_ticks"], argv=[self.public(str(x)) for x in command])
        append(self.out / "COMMANDS.jsonl", {"name": name + "_start", "argv": [self.public(str(x)) for x in command], "pid": proc.pid, "start_ticks": item["start_ticks"], "at_utc": stamp(), "exit_code": "ASYNC_SEE_CLEANUP"})
        return proc

    def wait_socket(self, path):
        until = time.monotonic() + 35
        while time.monotonic() < until:
            self.budget()
            need(all(proc.poll() is None for proc in self.services), "issuer exited before readiness")
            if path.is_socket():
                return
            time.sleep(0.2)
        raise RuntimeError("socket readiness input limit")

    def uid(self, operation, uid, observe=True):
        self.budget()
        command = ["sudo", "-n", "/usr/bin/setpriv", "--reuid", str(uid), "--regid", str(uid), "--clear-groups",
                   "/usr/bin/python3", "-B", str(self.base / "bin/WORKLOAD.py"), "uid", "--run-id", self.args.run_id,
                   "--base", str(self.base), "--operation", operation]
        started = time.time()
        if not observe:
            result, refs = self.call("uid" + str(uid) + "_" + operation, command)
            return read_json_bytes(result.stdout), refs
        # A handshake holds the actual operation PID while its parent reads
        # /proc. fetch then execs SPIRE in that same PID; signing stays in it.
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.own(proc.pid, operation + "_launcher")
        import select
        first = b""
        proof = None
        try:
            ready, _, _ = select.select([proc.stdout], [], [], 15)
            need(bool(ready), "UID kernel handshake timeout")
            first = proc.stdout.readline(65536)
            need(first.startswith(b"H77_KERNEL "), "UID kernel handshake missing")
            reported = read_json_bytes(first[len(b"H77_KERNEL "):])
            observed = proc_record(reported["pid"])
            ancestor = observed
            for _ in range(6):
                if ancestor["pid"] == proc.pid:
                    break
                ancestor = proc_record(ancestor["ppid"])
            need(ancestor["pid"] == proc.pid, "operation is not our subprocess descendant")
            need(reported["proc_status"] == observed["proc_status"] or reported["start_ticks"] == observed["start_ticks"], "kernel process changed")
            need(reported["kernel_uid"] == observed["kernel_uid"] == uid and observed["kernel_euid"] == uid, "kernel UID mismatch")
            self.own(observed["pid"], operation + "_actual_operation")
            proof = {**observed, "child_proc_status": reported["proc_status"], "argv_public": command,
                     "same_workload_socket": True, "socket_path": str(self.base / "workload/api.sock"),
                     "observation_method": "parent /proc read during stdin handshake; fetch uses same-PID execv; signing in that PID"}
            if operation in ("matching", "nonmatching"):
                proof["exec_argv"] = [str(self.base / "bin/spire-agent"), "api", "fetch", "x509", "-socketPath", str(self.base / "workload/api.sock"), "-timeout", "5s", "-write", str(self.base / ("u" + str(uid))) ]
            proc.stdin.write(b"GO\n")
            proc.stdin.flush()
            stdout, stderr = proc.communicate(timeout=min(30, max(0.1, self.deadline - time.monotonic())))
        except BaseException:
            # Outer finally uses exact PID/start identity to reap descendant
            # processes even if this sudo launcher has to be terminated.
            if proc.poll() is None:
                proc.terminate()
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                stdout, stderr = b"", b"UID process retained for guarded finally cleanup"
            self.record_command(operation, command, started, "FAILED", first + stdout, stderr)
            raise
        refs = self.record_command(operation, command, started, proc.returncode, first + stdout, stderr)
        return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr), {**proof, "raw": refs}

    def collect(self):
        self.event("live_begin", live_run_budget_consumed=1)
        self.call("sudo_noninteractive", ["sudo", "-n", "/usr/bin/true"])
        need(Path("/usr/bin/setpriv").is_file(), "existing setpriv missing")
        from cryptography import __version__ as cryptography_version
        import cryptography
        dependency = Path(cryptography.__file__).resolve().parent
        modules = {str(path): sha(path) for path in sorted(dependency.rglob("*")) if path.is_file() and path.suffix in (".py", ".so")}
        need(bool(modules), "existing dependency files unavailable")
        os_release, _ = self.call("ubuntu_release", ["/usr/bin/cat", "/etc/os-release"])
        need('ID=ubuntu' in os_release.stdout.decode() or 'ID="ubuntu"' in os_release.stdout.decode(), "Ubuntu required")
        kernel, _ = self.call("kernel", ["/usr/bin/uname", "-a"])
        save(self.out / "ENVIRONMENT.json", {"distribution": "Ubuntu", "python_version": sys.version,
             "cryptography_version": cryptography_version, "cryptography_files_sha256": modules,
             "host_installs": 0, "package_installs": 0, "docker_used": False, "real_uid": os.getuid(),
             "effective_uid": os.geteuid(), "kernel_wsl_version": kernel.stdout.decode().strip(),
             "os_release": os_release.stdout.decode(), "measurement": "existing module files, os-release, uname; no image-lock equivalence"})
        old = self.task.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"
        lock = read(old / "ASSET_LOCK.json")["files"][0]
        archive = Path.home() / ".cache/h76-spire-source" / lock["filename"]
        need(archive.is_file() and not archive.is_symlink() and archive.stat().st_size == lock["size"] and sha(archive) == lock["sha256"], "locked existing archive input limit")
        self.event("locked_archive_verified", sha256=lock["sha256"], size=lock["size"], new_downloads=0)
        self.base.mkdir(mode=0o711, exist_ok=False)
        self.base.chmod(0o711)
        st = self.base.lstat()
        self.identity = [st.st_dev, st.st_ino, st.st_uid]
        save(self.out / "TMPFS_OWNER.json", {"path": str(self.base), "identity_device_inode_uid": self.identity})
        for name, mode in (("bin", 0o755), ("private", 0o700), ("server-data", 0o700), ("server-api", 0o700), ("agent-data", 0o700), ("workload", 0o755), ("u1001", 0o700), ("u1002", 0o700)):
            (self.base / name).mkdir(mode=mode)
            (self.base / name).chmod(mode)
        for uid in (1001, 1002):
            self.call("chown_u" + str(uid), ["sudo", "-n", "/usr/bin/chown", str(uid) + ":" + str(uid), self.base / ("u" + str(uid))])
        binaries = extract_binaries(archive, self.base / "bin", member_profile=read(self.task / "BINARY_MEMBER_LOCK.json"))
        shutil.copyfile(Path(__file__), self.base / "bin/WORKLOAD.py")
        (self.base / "bin/WORKLOAD.py").chmod(0o644)
        server, agent = self.base / "bin/spire-server", self.base / "bin/spire-agent"
        for name, binary in (("spire-server", server), ("spire-agent", agent)):
            version, refs = self.call(name + "_version", [binary, "--version"])
            need(re.search(rb"\b1\.16\.0\b", version.stdout + version.stderr), "SPIRE version mismatch")
            binaries[name].update(version="1.16.0", version_evidence=refs)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.state["port"] = port
        server_config = f'''server {{
 bind_address = "127.0.0.1"
 bind_port = {port}
 socket_path = "{self.base}/server-api/api.sock"
 trust_domain = "h76.test"
 data_dir = "{self.base}/server-data"
 log_level = "INFO"
 ca_key_type = "ec-p256"
 default_x509_svid_ttl = "10m"
}}
plugins {{
 DataStore "sql" {{ plugin_data {{ database_type = "sqlite3" connection_string = "{self.base}/server-data/datastore.sqlite3" }} }}
 NodeAttestor "join_token" {{ plugin_data {{}} }}
 KeyManager "memory" {{ plugin_data {{}} }}
}}
'''
        agent_config = f'''agent {{
 trust_domain = "h76.test"
 server_address = "127.0.0.1"
 server_port = {port}
 data_dir = "{self.base}/agent-data"
 socket_path = "{self.base}/workload/api.sock"
 trust_bundle_path = "{self.base}/private/root.pem"
 workload_x509_svid_key_type = "ec-p256"
 log_level = "INFO"
}}
plugins {{
 NodeAttestor "join_token" {{ plugin_data {{}} }}
 KeyManager "disk" {{ plugin_data {{ directory = "{self.base}/agent-data" }} }}
 WorkloadAttestor "unix" {{ plugin_data {{ discover_workload_path = false }} }}
}}
'''
        for name, content in (("server.conf", server_config), ("agent.conf", agent_config)):
            (self.base / name).write_text(content)
            (self.out / name).write_text(content, encoding="utf-8")
        self.call("server_validate", [server, "validate", "-config", self.base / "server.conf"])
        self.call("agent_validate", [agent, "validate", "-config", self.base / "agent.conf"])
        self.service("server", [server, "run", "-config", self.base / "server.conf"])
        management = self.base / "server-api/api.sock"
        self.wait_socket(management)
        root_command = [server, "bundle", "show", "-socketPath", management, "-format", "pem"]
        bundle, root_refs = self.call("management_root_before_agent", root_command)
        roots = re.findall(rb"-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----", bundle.stdout)
        need(len(roots) == 1, "one direct management root required")
        root = roots[0] + b"\n"
        (self.base / "private/root.pem").write_bytes(root)
        (self.out / "root.pem").write_bytes(root)
        root_event_epoch = time.time()
        self.event("management_root_captured_before_agent", root_pem_sha256=hashlib.sha256(root).hexdigest())
        token_result, _ = self.call("private_token_generate", [server, "token", "generate", "-socketPath", management, "-ttl", "300", "-output", "json"], withheld=True)
        token = read_json_bytes(token_result.stdout)
        self.token = field(token, "value", "token", "Token")
        need(isinstance(self.token, str) and re.fullmatch(r"[A-Za-z0-9_-]{12,256}", self.token), "private token format input limit")
        token_file = self.base / "private/join.token"
        with token_file.open("x") as stream:
            stream.write(self.token + "\n")
        token_file.chmod(0o600)
        self.service("agent", [agent, "run", "-config", self.base / "agent.conf", "-joinTokenFile", token_file])
        self.wait_socket(self.base / "workload/api.sock")
        (self.base / "workload/api.sock").chmod(0o766)
        parent = None
        for iteration in range(14):
            listed, _ = self.call("agent_list_" + str(iteration + 1), [server, "agent", "list", "-socketPath", management, "-output", "json"], check=False)
            if listed.returncode == 0:
                obj = read_json_bytes(listed.stdout)
                # Only an empty typed agents collection is retryable readiness.
                if obj == {} or (isinstance(obj, dict) and obj.get("agents") == []):
                    time.sleep(0.5)
                    continue
                parent = parent_from_management(obj)
                need(parent.rsplit("/", 1)[1] == self.token, "management parent not bound to this fresh join token")
                save(self.out / "agent-list.redacted.json", json.loads(self.public(json.dumps(obj))))
                break
            error = (listed.stdout + listed.stderr).decode(errors="replace").lower()
            need(any(value in error for value in ("unavailable", "connection refused", "deadline exceeded")), "nonretryable management failure")
            time.sleep(0.5)
        need(parent is not None, "management agent list input limit; no log fallback")
        created, _ = self.call("entry_create", [server, "entry", "create", "-socketPath", management, "-output", "json", "-parentID", parent, "-spiffeID", TARGET, "-selector", "unix:uid:1001", "-x509SVIDTTL", "600"])
        entry_id = entry_identity(read_json_bytes(created.stdout))
        shown, entry_refs = self.call("entry_show", [server, "entry", "show", "-socketPath", management, "-entryID", entry_id, "-output", "json"])
        entry_obj = read_json_bytes(shown.stdout)
        validate_entry(entry_obj, parent, entry_id)
        save(self.out / "entry.redacted.json", json.loads(self.public(json.dumps(entry_obj))))
        parent_hash = hashlib.sha256(parent.encode()).hexdigest()
        save(self.out / "SOURCE.json", {"archive_sha256": lock["sha256"], "archive_size": lock["size"],
             "source": "fresh_extraction_from_locked_archive", "asset_downloads": 0, "binaries": binaries,
             "root_source": "server_management_socket_before_agent_start", "root_pem_sha256": hashlib.sha256(root).hexdigest(),
             "root_command": [str(x) for x in root_command], "root_command_evidence": root_refs,
             "root_captured_epoch": root_event_epoch, "parent_source": "server_management_agent_list", "parent_id_sha256": parent_hash,
             "agent_list_raw_parent_id_sha256": parent_hash, "entry_raw_parent_id_sha256": hashlib.sha256(spiffe(field(one_entry(entry_obj), "parent_id", "parentId")).encode()).hexdigest(),
             "entry_id": entry_id, "selector": ["unix:uid:1001"], "target": TARGET, "entry_command_evidence": entry_refs,
             "redaction": "Full CLI JSON structure retained; join-token-derived parent secret replaced with fixed placeholder; parent_id_sha256 binds original."})
        processes = {}
        time.sleep(2.5)
        for attempt in range(1, 4):
            self.event("matching_fetch_start", attempt=attempt, max_attempts=3)
            matched, proof = self.uid("matching", 1001)
            info, info_refs = self.uid("inspect", 1001, observe=False)
            self.event("matching_fetch_end", attempt=attempt, exit_code=matched.returncode, identities=info["count"])
            (self.out / f"matching_attempt_{attempt}.stdout.log").write_text(self.public(matched.stdout), encoding="utf-8")
            (self.out / f"matching_attempt_{attempt}.stderr.log").write_text(self.public(matched.stderr), encoding="utf-8")
            if matched.returncode == 0:
                need(info["count"] == info["key_count"] == 1, "wrong matching credential count")
                break
            error = matched.stderr.decode(errors="replace")
            need(info["count"] == 0 and "PermissionDenied" in error and "no identity issued" in error, "nonretryable matching fetch failure")
            need(attempt < 3, "matching fetch budget exhausted")
            time.sleep(1)
        (self.out / "matching.stdout.log").write_text(self.public(matched.stdout), encoding="utf-8")
        (self.out / "matching.stderr.log").write_text(self.public(matched.stderr), encoding="utf-8")
        (self.out / "leaf.pem").write_text(info["leaf_pem"], encoding="utf-8")
        processes.update(matching=proof, matching_svid_count=info["count"], private_key_owner_uid=info["private_key_owner_uid"],
                         private_directory_mode=info["directory_mode"], private_key_mode=info["private_key_mode"], private_permissions_evidence=info_refs)
        self.event("nonmatching_fetch_start", attempt=1, max_attempts=1)
        denied, denied_proof = self.uid("nonmatching", 1002)
        # inspect helper intentionally runs in the holder directory, including UID1002.
        denied_info, _ = self.uid("inspect_negative", 1002, observe=False)
        self.event("nonmatching_fetch_end", exit_code=denied.returncode, identities=denied_info["count"])
        (self.out / "nonmatching.stdout.log").write_text(self.public(denied.stdout), encoding="utf-8")
        (self.out / "nonmatching.stderr.log").write_text(self.public(denied.stderr), encoding="utf-8")
        error = denied.stderr.decode(errors="replace")
        need(denied.returncode != 0 and denied_info["count"] == denied_info["key_count"] == 0 and "PermissionDenied" in error and "no identity issued" in error, "nonmatching identity/security failure")
        need(not any(t in error.lower() for t in ("connect: permission denied", "connection refused", "no such file")), "transport failure is not selector denial")
        processes.update(nonmatching=denied_proof, nonmatching_svid_count=0)
        issued = int(time.time())
        payload = (f"agentic-payment-possession/v1\nnonce={self.args.nonce}\nagent=h76-agent\nprovider=h76-provider\nexecutor=h76-executor\nissued_at={issued}\n").encode()
        (self.base / "workload/payload.bin").write_bytes(payload)
        (self.base / "workload/payload.bin").chmod(0o644)
        self.event("holder_signature_start", attempt=1, max_attempts=1)
        signed, sign_proof = self.uid("signing", 1001)
        need(signed.returncode == 0, "holder signature failed")
        signature = read_json_bytes(signed.stdout)
        need(signature["signing_uid"] == 1001, "holder signing UID")
        base64.b64decode(signature["signature_b64"], validate=True)
        (self.out / "payload.bin").write_bytes(payload)
        (self.out / "signature.b64").write_text(signature["signature_b64"] + "\n", encoding="utf-8")
        processes["signing"] = sign_proof
        save(self.out / "PROCESSES.json", processes)
        self.state.update(status="ISSUER_FETCH_SIGNATURE_CAPTURED", issued_at_epoch=issued, observed_at_epoch=int(time.time()),
                          signing_uid=1001, parent_source="server_management_agent_list", actual_parent_id_sha256=parent_hash,
                          entry_cli_success=True, unmatched_uid={"uid": 1002, "exit_code": denied.returncode, "identity_count": 0, "socket_connected": True})
        self.event("holder_signature_end", signing_uid=1001)

    def finish(self):
        # Defuse only our watchdog/signals so cleanup cannot be interrupted by
        # the live deadline. Other tasks/services are never enumerated/killed.
        signal.alarm(0)
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, signal.SIG_IGN)
        for handle in self.handles:
            handle.flush()
        cleanup = {"owned_processes_alive": self.owned, "private_tmpfs_exists": self.base.exists(), "public_private_key_files": private_files(self.out), "independent_check_exit_code": "NOT_RUN"}
        if self.identity is not None:
            common = ["--run-id", self.args.run_id, "--base", str(self.base), "--device", str(self.identity[0]),
                      "--inode", str(self.identity[1]), "--owner", str(self.identity[2]), "--owned", json.dumps(self.owned), "--out", str(self.out)]
            prefix = ["sudo", "-n", "/usr/bin/python3", "-B", str(Path(__file__).resolve())]
            stopped, stop_refs = self.call("stop_owned_before_final_log_copy", [*prefix, "stop-owned", *common], timeout=180, check=False, cleanup=True)
            for name in ("server", "agent"):
                path = self.base / "private" / (name + ".raw.log")
                if path.is_file():
                    (self.out / (name + ".redacted.log")).write_text(self.public(path.read_bytes()), encoding="utf-8")
            result, cleanup_refs = self.call("guarded_cleanup", [*prefix, "cleanup", *common], timeout=180, check=False, cleanup=True)
            for proc in self.services:
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            inspection, inspection_refs = self.call("independent_cleanup_inspection", [*prefix, "inspect-cleanup", *common], timeout=180, check=False, cleanup=True)
            if inspection.returncode == 0:
                cleanup = read_json_bytes(inspection.stdout)
            cleanup.update(independent_check_exit_code=inspection.returncode, independent_check_command=[*prefix, "inspect-cleanup", *common],
                           independent_check_raw=inspection_refs, cleanup_command_raw=cleanup_refs, cleanup_exit_code=result.returncode,
                           stop_owned_exit_code=stopped.returncode, stop_owned_raw=stop_refs,
                           owned_processes=[{k: item[k] for k in ("pid", "start_ticks", "boot_id", "name")} for item in self.owned],
                           tmpfs_owner_guard=self.identity)
        else:
            # A prerequisite failure may occur before creating any resources.
            cleanup.update(owned_processes_alive=[], private_tmpfs_exists=False, independent_check_exit_code="NOT_APPLICABLE_NO_RESOURCES", independent_check_command=[])
        save(self.out / "CLEANUP.json", cleanup)
        clean = cleanup["owned_processes_alive"] == [] and cleanup["private_tmpfs_exists"] is False and cleanup["public_private_key_files"] == 0
        if not clean:
            self.state.update(status="FAILED", failure="CLEANUP_NOT_PROVEN")
        self.state["finished_utc"] = stamp()
        self.event("live_end", status=self.state["status"], cleanup_proven=clean, actual_active_minutes="UNKNOWN", full_network_wire_bytes="UNKNOWN")
        save(self.out / "RESULT.json", self.state)
        # Deliberately exclude index itself. These two dispatcher files may
        # still be open; they contain no normal output from the collector.
        files = {path.relative_to(self.out).as_posix(): sha(path) for path in sorted(self.out.rglob("*"))
                 if path.is_file() and path.name != "PUBLIC_INDEX.json" and path.name not in ("dispatcher.stdout.log", "dispatcher.stderr.log")}
        save(self.out / "PUBLIC_INDEX.json", {"files": files, "excluded": {"PUBLIC_INDEX.json": "no self-hash", "dispatcher.stdout.log": "Windows dispatcher finalizes after collector exit", "dispatcher.stderr.log": "Windows dispatcher finalizes after collector exit"}, "redaction": "token generation withheld; other text complete with explicit token/parent redaction; no truncation"})
        return 0 if self.state["status"] == "ISSUER_FETCH_SIGNATURE_CAPTURED" and clean else 1


def read_json_bytes(value):
    return json.loads(value.decode("utf-8"))


def interrupt(signum, frame):
    raise RuntimeError("live watchdog/signal " + str(signum))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("issuer", "uid", "cleanup", "inspect-cleanup", "stop-owned"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--nonce")
    parser.add_argument("--out")
    parser.add_argument("--base")
    parser.add_argument("--operation", choices=("matching", "nonmatching", "inspect", "inspect_negative", "signing"))
    parser.add_argument("--owned")
    for name in ("device", "inode", "owner"):
        parser.add_argument("--" + name, type=int)
    args = parser.parse_args()
    if args.action == "uid":
        return uid_helper(args)
    if args.action in ("cleanup", "inspect-cleanup", "stop-owned"):
        return cleanup_helper(args, inspect_only=args.action == "inspect-cleanup", stop_only=args.action == "stop-owned")
    collector = Collector(args)
    # Check ownership/authority before timers, ledger or cleanup paths exist.
    collector.authorize()
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
        signal.signal(signum, interrupt)
    signal.alarm(1100)
    try:
        collector.collect()
    except BaseException as exc:
        collector.state.update(status="FAILED", failure_type=type(exc).__name__, failure=collector.public(str(exc)))
    finally:
        return collector.finish()


if __name__ == "__main__":
    raise SystemExit(main())
