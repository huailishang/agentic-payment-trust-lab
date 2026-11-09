"""Evaluator-only, no-business harness test. Never imports payment/merchant code."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from RECOVERY_CASES import ROOT, TASK, direct_worker_runtime, read, save


def launch(prefix, *, paused):
    nonce = uuid.uuid4().hex
    input_path = Path(str(prefix) + ".input.json")
    value = {"operation": "harness_probe", "request": {}, "config": {},
             "harness_nonce": nonce}
    if paused:
        value.update(pause_at="probe", marker=str(prefix) + ".ready",
                     release=str(prefix) + ".release")
    save(input_path, value)
    binary, environment = direct_worker_runtime()
    proc = subprocess.Popen([binary, "-B", str(TASK / "WORKER.py"), str(input_path)],
                            cwd=ROOT, env=environment, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    return proc, nonce


def check_normal(prefix):
    proc, nonce = launch(prefix, paused=False)
    stdout, stderr = proc.communicate(timeout=15)
    assert proc.returncode == 0, (stdout, stderr)
    result = read(str(prefix) + ".output.json")
    assert result == {"result": {"status": "PROBED"}, "pid": proc.pid, "nonce": nonce}
    assert read(str(prefix) + ".monitor.json") == []
    assert proc.poll() is not None
    return {"pid_match": True, "nonce_verified": True, "actual_worker_exited": True}


def check_crash(prefix):
    proc, nonce = launch(prefix, paused=True)
    marker_path = Path(str(prefix) + ".ready")
    deadline = time.monotonic() + 10
    try:
        while not marker_path.exists():
            assert proc.poll() is None, "worker terminated before pause"
            if time.monotonic() > deadline:
                raise TimeoutError("no real worker marker")
            time.sleep(0.02)
        marker = read(marker_path)
        assert marker == {"stage": "probe", "pid": proc.pid, "nonce": nonce}, marker
        assert proc.poll() is None, "worker not alive at real PID pause"
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode != 0 and proc.poll() is not None, (stdout, stderr)
        assert read(str(prefix) + ".monitor.json") == []
        return {"pid_match": True, "nonce_verified": True, "actual_worker_exited": True,
                "termination_exit_code": proc.returncode}
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=10)


def check_bad_suffix(prefix):
    invalid = Path(str(prefix) + ".data.json")
    save(invalid, {"operation": "harness_probe", "harness_nonce": uuid.uuid4().hex})
    binary, environment = direct_worker_runtime()
    proc = subprocess.run([binary, "-B", str(TASK / "WORKER.py"), str(invalid)],
                          cwd=ROOT, env=environment, capture_output=True, text=True, timeout=15)
    assert proc.returncode != 0 and "frozen input must end" in proc.stderr
    assert not Path(str(prefix) + ".output.json").exists()
    assert not Path(str(prefix) + ".monitor.json").exists()
    return {"rejected": True}


def main():
    root = ROOT / ".task_envs/H62/runs"
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="h62_harness_only_", dir=root) as folder:
        temp = Path(folder)
        normal = check_normal(temp / "normal")
        crashed = check_crash(temp / "crash")
        bad_suffix = check_bad_suffix(temp / "invalid")
        # A different process starts only after the real first worker has exited.
        restarted = check_normal(temp / "restarted")
    print(json.dumps({"harness_only": True, "merchant_imported": False,
                      "recovery_calls": 0, "payment_calls": 0,
                      "normal": normal, "crash": crashed, "bad_suffix": bad_suffix,
                      "restart": restarted}, ensure_ascii=False))


if __name__ == "__main__":
    main()
