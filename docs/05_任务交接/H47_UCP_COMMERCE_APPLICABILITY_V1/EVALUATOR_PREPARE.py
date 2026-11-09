"""Read-only public-source acquisition for Evaluator design; never run upstream."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request
import sys
import zipfile

TASK = Path(__file__).resolve().parent
COMMIT = "99724a32da48bd0f4962c83e25f17c8345ce055e"
REPO = "Universal-Commerce-Protocol/samples"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Codex-public-source-audit"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(2_000_001)
    if not data or len(data) > 2_000_000:
        raise ValueError("empty or oversized public source")
    return data


def main():
    archive = zipfile.ZipFile(sys.argv[1]) if len(sys.argv) == 2 else None
    prefix = f"samples-{COMMIT}/"
    tree = ({"tree": [{"path": name[len(prefix):], "type": "blob"}
                       for name in archive.namelist() if name.startswith(prefix) and not name.endswith("/")]}
            if archive else json.loads(fetch(f"https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1")))
    paths = [row["path"] for row in tree["tree"] if row["type"] == "blob" and (
        row["path"] in {"LICENSE", "README.md"}
        or row["path"].startswith("rest/python/server/")
        or row["path"].startswith("rest/python/test_data/flower_shop/")
        or row["path"] in {"rest/python/client/flower_shop/README.md",
                            "rest/python/client/flower_shop/simple_happy_path_client.py",
                            "rest/python/client/flower_shop/signing.py",
                            "rest/python/client/flower_shop/pyproject.toml"})]
    jobs = [(path, f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{path}") for path in sorted(paths)]
    if archive:
        contents = [archive.read(prefix + path) for path, _ in jobs]
        archive.close()
    else:
        with ThreadPoolExecutor(max_workers=6) as pool:
            contents = list(pool.map(lambda pair: fetch(pair[1]), jobs))
    entries = []
    for (path, url), data in zip(jobs, contents):
        dest = TASK / "sources" / "ucp" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        entries.append({"path": dest.relative_to(TASK).as_posix(), "upstream_path": path,
                        "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    lock = {"schema": "h47-source-lock/v1", "repo": REPO, "commit": COMMIT,
            "license": "Apache-2.0", "retrieved_on": "2026-10-15", "files": entries}
    (TASK / "SOURCE_LOCK.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(entries), "bytes": sum(row["bytes"] for row in entries), "commit": COMMIT}))


if __name__ == "__main__":
    main()
