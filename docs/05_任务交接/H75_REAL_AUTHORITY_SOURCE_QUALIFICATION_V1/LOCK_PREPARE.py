"""Read public metadata/source only; never download/run release binaries or images."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence" / "continuation" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT.mkdir(parents=True, exist_ok=True)
observations = []


def get(url, *, headers=None, limit=16 * 1024 * 1024):
    req = urllib.request.Request(url, headers={"User-Agent": "H75-public-metadata-qualification", **(headers or {})})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read(limit + 1)
        observations.append({"url": url, "status": response.status, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "complete": len(body) <= limit})
        if len(body) > limit:
            raise RuntimeError("public_metadata_size_limit")
        return body


def jget(url, **kwargs):
    return json.loads(get(url, **kwargs))


def main():
    lock = {"observed_utc": datetime.now(timezone.utc).isoformat(), "scope": "PUBLIC_METADATA_ONLY_NOT_RUNTIME_VERIFICATION", "platform": "linux/amd64"}
    try:
        release = jget("https://api.github.com/repos/spiffe/spire/releases/tags/v1.16.0")
        (OUT / "spire_release.json").write_text(json.dumps(release, indent=2), encoding="utf-8")
        assets = [{k: a.get(k) for k in ("name", "size", "digest", "browser_download_url")} for a in release["assets"]]
        lock["spire"] = {"version": "1.16.0", "source_commit": "872c1d55b4d5ac7fc1bf05f0760f2ca740ab37aa", "assets": assets}
        token = jget("https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/python:pull")["token"]
        headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"}
        index_body = get("https://registry-1.docker.io/v2/library/python/manifests/3.12.13-slim-bookworm", headers=headers)
        index = json.loads(index_body)
        linux = [m for m in index["manifests"] if m["platform"].get("os") == "linux" and m["platform"].get("architecture") == "amd64" and not m["platform"].get("variant")]
        if len(linux) != 1:
            raise RuntimeError("ambiguous_linux_amd64_manifest")
        digest = linux[0]["digest"]
        manifest_body = get("https://registry-1.docker.io/v2/library/python/manifests/" + digest, headers=headers)
        if "sha256:" + hashlib.sha256(manifest_body).hexdigest() != digest:
            raise RuntimeError("manifest_digest_mismatch")
        manifest = json.loads(manifest_body)
        lock["python_image"] = {"tag": "python:3.12.13-slim-bookworm", "index_digest": "sha256:" + hashlib.sha256(index_body).hexdigest(), "linux_amd64_digest": digest, "compressed_layer_bytes": sum(x["size"] for x in manifest["layers"]), "layers": manifest["layers"], "config": manifest["config"]}
        for package, selector in (("cryptography", "cp311-abi3-manylinux_2_28_x86_64.whl"), ("cffi", "cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"), ("pycparser", "py3-none-any.whl")):
            data = jget("https://pypi.org/pypi/" + package + "/json")
            info = data["info"]
            selected = [x for x in data["urls"] if x["filename"].endswith(selector)]
            lock[package] = {"version": info["version"], "license_expression": info.get("license_expression"), "license": info.get("license"), "requires_dist": info.get("requires_dist"), "selector": selector, "wheels": [{"filename": x["filename"], "url": x["url"], "size": x["size"], "sha256": x["digests"]["sha256"]} for x in selected], "available_wheel_names": [x["filename"] for x in data["urls"] if "x86_64" in x["filename"]] if not selected else []}
        source_root = "https://raw.githubusercontent.com/spiffe/spire/872c1d55b4d5ac7fc1bf05f0760f2ca740ab37aa/"
        source_paths = ("LICENSE", "cmd/spire-agent/cli/api/fetch_x509.go", "cmd/spire-server/cli/bundle/show.go", "doc/plugin_server_nodeattestor_jointoken.md", "doc/plugin_agent_workloadattestor_unix.md", "conf/server/server.conf", "conf/agent/agent.conf")
        lock["fixed_sources"] = []
        for path in source_paths:
            body = get(source_root + path)
            dest = OUT / ("source_" + path.replace("/", "__"))
            dest.write_bytes(body)
            lock["fixed_sources"].append({"path": path, "url": source_root + path, "sha256": hashlib.sha256(body).hexdigest(), "evidence": str(dest.relative_to(HERE))})
        lock["status"] = "METADATA_CAPTURED_REQUIRES_REVIEW"
    except Exception as exc:
        lock["status"] = "INPUT_LIMIT"
        lock["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        lock["http_observations"] = observations
        lock["http_response_body_bytes"] = sum(x["bytes"] for x in observations)
        (OUT / "ASSET_METADATA.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": lock["status"], "requests_completed": len(observations), "response_body_bytes": lock["http_response_body_bytes"], "error": lock.get("error")}, indent=2))


if __name__ == "__main__":
    main()
