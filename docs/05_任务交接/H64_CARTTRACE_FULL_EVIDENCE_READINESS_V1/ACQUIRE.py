"""H64: allowlisted, budgeted, sequential public source acquisition only.

No generic URL input. Every GET is reserved in ATTEMPT_LEDGER before IO;
even rejected redirects, errors and partial bytes consume budget. This script
does not run CartTrace, model, merchant, wallet or payment code.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
SRC = json.loads((TASK / "SOURCE_INPUTS.json").read_text(encoding="utf-8"))
LEDGER = TASK / "ATTEMPT_LEDGER.json"
MiB = 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def write(obj):
    tmp = LEDGER.with_suffix(".pending")
    with tmp.open("w", encoding="utf-8", newline="\n") as fp:
        json.dump(obj, fp, ensure_ascii=False, indent=2)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    os.replace(tmp, LEDGER)


def load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    data = {"task_id": TASK.name, "started_at": now(),
            "active_minutes": 1, "formal_l2_attempts": 0,
            "measurement_versions": 0, "installation_calls": 0,
            "model_calls": 0, "payment_calls": 0, "product_calls": 0,
            "upstream_replay_calls": 0, "attempts": [], "materials": []}
    write(data)
    return data


class BoundedRedirect(HTTPRedirectHandler):
    def __init__(self, history):
        self.history = history

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in SRC["redirect_hosts"]:
            raise ValueError("redirect outside frozen public host allowlist")
        self.history.append(parsed.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def frozen_url(key, data):
    if key == "wheel":
        return SRC["decoder"]["url"], "acquired/decoder/" + SRC["decoder"]["filename"]
    for i, url in enumerate(SRC["parquet_urls"]):
        if key == f"parquet{i+1}":
            return url, "acquired/" + url.split(SRC["dataset_base"], 1)[1]
    if key.startswith("world-"):
        _, kind, world_id = key.split("-", 2)
        if kind not in {"envpacks", "manifests"}:
            raise ValueError("only envpacks/manifests")
        if not (TASK / "SELECTED.json").exists():
            raise ValueError("world GET requires frozen SELECTED")
        selected = json.loads((TASK / "SELECTED.json").read_text(encoding="utf-8"))
        if world_id not in {s["world_id"] for s in selected["samples"]}:
            raise ValueError("world was not selected")
        relative = f"worlds/{kind}/{world_id}.json"
        meta = json.loads((TASK / "references/HF_METADATA.json").read_text(encoding="utf-8"))
        if relative not in {r["rfilename"] for r in meta["siblings"]}:
            raise ValueError("world path absent in frozen metadata")
        return SRC["dataset_base"] + relative, "acquired/" + relative
    raise ValueError("unknown frozen source key")


def acquire(key):
    data = load()
    url, rel = frozen_url(key, data)
    if not url.startswith("https://"):
        raise ValueError("HTTPS required")
    if urlparse(url).hostname not in SRC["redirect_hosts"]:
        raise ValueError("invalid origin")
    path = TASK / rel
    if path.exists():
        raise FileExistsError("already obtained; no redundant GET")
    attempts = [a for a in data["attempts"] if a.get("kind") == "public_get"]
    if len(attempts) >= 20 or sum(a.get("bytes_received", 0) for a in attempts) >= 256*MiB:
        raise ValueError("frozen request/byte budget already exhausted")
    if sum(a.get("url") == url for a in attempts) >= 2:
        raise ValueError("per-source budget exhausted")
    ident = f"G-{len(attempts)+1:02d}"
    record = {"id": ident, "kind": "public_get", "started_at": now(),
              "finished_at": None, "status": "RESERVED", "url": url,
              "bytes_received": 0, "redirect_hosts": []}
    data["attempts"].append(record)
    write(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    received = 0
    hashobj = hashlib.sha256()
    history = []
    status = "FAILED"
    cause = "unknown"
    try:
        opener = build_opener(BoundedRedirect(history))
        request = Request(url, headers={"User-Agent": "AgenticPaymentTrustLab-H64/1.0", "Accept": "*/*"})
        with opener.open(request, timeout=30) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > 128*MiB:
                raise ValueError("declared file size exceeds 128MiB")
            with part.open("xb") as out:
                while True:
                    block = response.read(256*1024)
                    if not block:
                        break
                    received += len(block)
                    record["bytes_received"] = received
                    if received > 128*MiB:
                        raise ValueError("single file exceeds 128MiB")
                    all_so_far = sum(a.get("bytes_received", 0) for a in data["attempts"])
                    if all_so_far > 256*MiB:
                        raise ValueError("cumulative bytes exceed 256MiB")
                    out.write(block)
                    hashobj.update(block)
            digest = hashobj.hexdigest()
            if url in SRC["expected_sha256"] and digest != SRC["expected_sha256"][url]:
                raise ValueError("published checksum mismatch")
            os.replace(part, path)
            data["materials"].append({"file": rel, "url": url, "sha256": digest})
            status = "SUCCEEDED"
            cause = "sha256_verified" if url in SRC["expected_sha256"] else "published_world_sha_recorded"
    except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError, OSError) as err:
        cause = f"{type(err).__name__}: " + str(getattr(err, "code", type(err).__name__))
        # The redirected URL may contain signed query parameters; never log it.
        if isinstance(err, HTTPError):
            cause = f"HTTP {err.code}"
        if isinstance(err, ValueError):
            cause = str(err)[:140]
        status = "LIMIT" if "budget" in cause or "size" in cause or "checksum" in cause or "allowlist" in cause else "FAILED"
    finally:
        record["finished_at"] = now()
        record["status"] = status
        record["redirect_hosts"] = history
        record["bytes_received"] = received
        record["reason"] = cause
        write(data)
    print(json.dumps({"key": key, "id": ident, "status": status, "bytes": received,
                      "redirect_hosts": history, "reason": cause}, ensure_ascii=False))
    return status == "SUCCEEDED"


def install():
    import subprocess
    data = load()
    if data["installation_calls"] >= 1:
        raise ValueError("only one isolated install is allowed")
    material = next((m for m in data["materials"] if m["url"] == SRC["decoder"]["url"]), None)
    if not material:
        raise ValueError("wheel not acquired and checksum verified")
    wheel = TASK / material["file"]
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != SRC["decoder"]["sha256"]:
        raise ValueError("wheel digest drift")
    target = ROOT / SRC["decoder"]["target"]
    data["installation_calls"] += 1
    ident = f"I-{data['installation_calls']:02d}"
    record = {"id": ident, "kind": "install", "started_at": now(),
              "finished_at": None, "status": "RESERVED"}
    data["attempts"].append(record)
    write(data)
    target.mkdir(parents=True, exist_ok=True)
    command = ["python", "-m", "pip", "--isolated", "--disable-pip-version-check",
               "install", "--no-index", "--no-deps", "--no-compile", "--target",
               str(target), str(wheel)]
    output = subprocess.run(command, capture_output=True, text=True, errors="replace",
                            timeout=100, cwd=str(ROOT), check=False)
    evidence = TASK / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "INSTALL-01.stdout.log").write_text(output.stdout, encoding="utf-8")
    (evidence / "INSTALL-01.stderr.log").write_text(output.stderr, encoding="utf-8")
    record["finished_at"] = now()
    record["status"] = "SUCCEEDED" if output.returncode == 0 else "FAILED"
    record["exit_code"] = output.returncode
    write(data)
    print(json.dumps({"install_status": record["status"], "exit": output.returncode,
                      "target": SRC["decoder"]["target"]}))
    return output.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "init":
        data = load()
        print(json.dumps({"task_id": data["task_id"], "attempts": len(data["attempts"])}))
    elif sys.argv[1] == "fetch" and len(sys.argv) == 3:
        sys.exit(0 if acquire(sys.argv[2]) else 1)
    elif sys.argv[1] == "install" and len(sys.argv) == 2:
        sys.exit(0 if install() else 1)
    else:
        raise SystemExit("usage: ACQUIRE.py init | fetch <frozen-source-key> | install")
