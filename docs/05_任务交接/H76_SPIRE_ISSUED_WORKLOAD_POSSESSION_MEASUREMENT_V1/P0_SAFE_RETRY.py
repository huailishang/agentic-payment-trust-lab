"""H76 one newly owner-authorized safe retry of installed Docker Desktop only."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import time

P = Path(__file__).resolve().parent
OUT = P / "evidence" / "executor_p0" / "safe_retry_20261116"
DOCKER = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")
DESKTOP = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
POWERSHELL = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
PIPE = "npipe:////./pipe/dockerDesktopLinuxEngine"
W = Path(r"C:\Windows\System32\wsl.exe")
TASKLIST = Path(r"C:\Windows\System32\tasklist.exe")

def now():
    return datetime.now(timezone.utc).isoformat()

def run(name, cmd, timeout=20):
    start = now()
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
        d = dict(command=[str(x) for x in cmd], start_utc=start, end_utc=now(), exit_code=r.returncode,
                 stdout=r.stdout.decode("utf-8", "replace"), stderr=r.stderr.decode("utf-8", "replace"))
    except Exception as e:
        d = dict(command=[str(x) for x in cmd], start_utc=start, end_utc=now(), exit_code="EXCEPTION",
                 error=f"{type(e).__name__}: {e}", stdout="", stderr="")
    (OUT / (name + ".json")).write_text(json.dumps(d, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return d

def probe(name):
    d = run(name, [DOCKER, "--host", PIPE, "version"])
    return d["exit_code"] == 0 and "Server:" in d["stdout"]

def main():
    assert (P / "OWNER_SAFE_RETRY_20261116.md").is_file(), "new owner authorization missing"
    assert (P / "evidence" / "executor_p0" / "DESKTOP_START.json").is_file(), "prior start evidence missing"
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "SUMMARY.json").exists() and not (OUT / "START_ATTEMPT.json").exists(), "one safe retry already consumed"
    initial = probe("BEFORE")
    data = {"schema":"h76-safe-retry/v1","began_utc":now(),"new_owner_permission":"OWNER_SAFE_RETRY_20261116.md",
            "prior_start_attempts":1,"this_turn_start_attempts":0, "engine_initially_reachable":initial}
    if not initial:
        if not DESKTOP.exists() or not POWERSHELL.exists():
            data["result"]="INPUT_LIMIT_BINARIES_NOT_FOUND"
        else:
            ps = ("$ErrorActionPreference='Stop'; "
                  "$p = Start-Process -FilePath 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe' "
                  "-WorkingDirectory 'C:\\Program Files\\Docker\\Docker' -PassThru; "
                  "Write-Output ('STARTED_PID=' + $p.Id)")
            data["this_turn_start_attempts"]=1
            (OUT / "START_ATTEMPT.json").write_text(json.dumps({"began_utc":now(),"attempt":1, "launcher":"Windows PowerShell Start-Process, user context only", "status":"STARTED"}, indent=2)+"\n",encoding="utf-8")
            launch = run("START", [POWERSHELL,"-NoProfile","-NonInteractive","-Command",ps],timeout=30)
            data["launcher_exit_code"]=launch["exit_code"]
            data["launcher_stdout"]=launch["stdout"].strip()
            data["launcher_stderr"]=launch["stderr"].strip()
            time.sleep(8)
    first = probe("AFTER_8S")
    if not first and data["this_turn_start_attempts"]:
        time.sleep(8)
    final = probe("AFTER_16S")
    # Read-only Windows and WSL status checks. No terminate, config, or service changes.
    run("TASKLIST_DESKTOP", [TASKLIST,"/FI","IMAGENAME eq Docker Desktop.exe"])
    run("TASKLIST_BACKEND", [TASKLIST,"/FI","IMAGENAME eq com.docker.backend.exe"])
    ws = run("WSL_DISTROS", [W,"--list","--verbose"])
    # WSL emits UTF-16 LE via redirected Windows interop; do not infer distro status from decoded output.
    data.update(ended_utc=now(), engine_reachable=bool(first or final),
                result="ENGINE_AVAILABLE" if first or final else "INPUT_LIMIT_ENV_DOCKER_NOT_REACHABLE",
                read_only_wsl_exit_code=ws["exit_code"],
                asset_downloads=0, container_starts=0, test_keys_issued=0, payments=0)
    (OUT / "SUMMARY.json").write_text(json.dumps(data, indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False))
    raise SystemExit(0 if data["engine_reachable"] else 2)

if __name__=="__main__":
    main()
