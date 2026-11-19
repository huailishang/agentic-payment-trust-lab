"""Bounded, checksummed range fetching of the pre-locked public SPIRE archive in WSL.
No package installation or binary execution in this tool; max 12 concurrent connections.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
LOCK = json.loads((ROOT / "ASSET_LOCK.json").read_text(encoding="utf-8"))["files"][0]
assert LOCK["filename"] == "spire-1.16.0-linux-amd64-musl.tar.gz"
CACHE = Path.home() / ".cache/h76-spire-source"
CACHE.mkdir(mode=0o700, parents=True, exist_ok=True)
PARTS = CACHE / "chunks"
PARTS.mkdir(mode=0o700, exist_ok=True)
SIZE = int(LOCK["size"])
CHUNK = 1024 * 1024
TOTAL = math.ceil(SIZE / CHUNK)
URL = LOCK["url"]
FILE = CACHE / LOCK["filename"]

def get(index):
    first = index * CHUNK
    last = min(SIZE, first + CHUNK) - 1
    n = last - first + 1
    dest = PARTS / f"{index:04d}.part"
    if dest.is_file() and dest.stat().st_size == n:
        return index, "CACHED"
    part = PARTS / f"{index:04d}.incoming"
    headers = PARTS / f"{index:04d}.headers"
    for attempt in range(2):
        cmd = ["curl", "--fail", "--silent", "--show-error", "--location",
               "--connect-timeout", "12", "--max-time", "85", "--retry", "0",
               "--range", f"{first}-{last}", "--dump-header", str(headers),
               "--output", str(part), URL]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=95)
            h = headers.read_text(errors="replace").lower() if headers.exists() else ""
            matched = re.search(r"content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)", h)
            correct_range = matched is not None and tuple(map(int,matched.groups())) == (first,last,SIZE)
            if p.returncode == 0 and part.exists() and part.stat().st_size == n and correct_range:
                part.replace(dest)
                return index, "DOWNLOADED"
            reason = f"exit={p.returncode}, size={part.stat().st_size if part.exists() else 0}, range_ok={correct_range}, stderr={p.stderr.decode(errors='replace')[-180:]}"
        except Exception as e:
            reason = type(e).__name__ + ": " + str(e)
    return index, "FAILED " + reason

def main():
    if FILE.exists() and FILE.stat().st_size == SIZE and sha256(FILE.read_bytes()).hexdigest() == LOCK["sha256"]:
        print("VERIFIED_EXISTING", FILE, flush=True)
        return
    print(f"Fetching fixed official SPIRE {LOCK['filename']} size={SIZE}, parts={TOTAL}, max_parallel=12",flush=True)
    failures=[]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures=[pool.submit(get,i) for i in range(TOTAL)]
        done=0
        for future in as_completed(futures):
            i,status=future.result()
            done+=1
            if status.startswith("FAILED"):
                failures.append((i,status))
            if done%8 == 0 or done==TOTAL:
                print(f"completed {done}/{TOTAL}, failed={len(failures)}",flush=True)
    if failures:
        print("INCOMPLETE", failures[:15],flush=True)
        raise SystemExit(2)
    with FILE.open("wb") as sink:
        for i in range(TOTAL):
            sink.write((PARTS / f"{i:04d}.part").read_bytes())
    digest=sha256(FILE.read_bytes()).hexdigest()
    print("assembled_bytes",FILE.stat().st_size, "sha256",digest, "expected",LOCK["sha256"],flush=True)
    if digest != LOCK["sha256"] or FILE.stat().st_size != SIZE:
        FILE.unlink(missing_ok=True)
        raise SystemExit("SHA_MISMATCH STOP; never execute")
    print("VERIFIED",FILE,flush=True)

if __name__ == "__main__":
    main()
