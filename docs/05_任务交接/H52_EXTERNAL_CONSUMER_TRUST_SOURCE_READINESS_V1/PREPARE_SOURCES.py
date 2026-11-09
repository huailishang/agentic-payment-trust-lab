"""Evaluator preparation only: freeze public references and inspect existing runtime."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
class Plain(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("p", "div", "li", "pre", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

def main():
    folder = TASK / "sources"
    folder.mkdir(exist_ok=True)
    draft = TASK / "DRAFT_BEFORE_FREEZE_20261030.md"
    if not draft.exists():
        shutil.copyfile(TASK / "CONTRACT.md", draft)
    sources = [
        ("ucp-ap2-extension-20260825", "https://ucp.dev/2026-08-25/specification/payment/extensions/ap2-mandates/", "Apache-2.0"),
        ("ucp-ap2-relation", "https://ucp.dev/documentation/ucp-and-ap2/", "Apache-2.0"),
        ("google-codelab", "https://codelabs.developers.google.com/next26/adk-agent-commerce", "CC-BY-4.0 text; Apache-2.0 code"),
    ]
    records = []
    for ident, url, license_name in sources:
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-payment-trust-lab-source-audit"})
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = response.read()
            resolved = response.url
        path = folder / (ident + ".html")
        path.write_bytes(raw)
        parser = Plain()
        parser.feed(raw.decode("utf-8"))
        plain = "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip()) + "\n"
        text_path = folder / (ident + ".txt")
        text_path.write_text(plain, encoding="utf-8")
        records.append({"id": ident, "url": url, "resolved_url": resolved, "license": license_name,
            "classification": "REFERENCE_ONLY", "html": path.relative_to(ROOT).as_posix(),
            "text": text_path.relative_to(ROOT).as_posix(),
            "html_sha256": hashlib.sha256(raw).hexdigest(),
            "text_sha256": hashlib.sha256(text_path.read_bytes()).hexdigest()})
    result = {"schema": "h52-public-source-snapshot/v1", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
              "boundary": "PUBLIC_DOCUMENT_DOWNLOAD_ONLY_NO_RUNTIME", "sources": records}
    (TASK / "SOURCE_MANIFEST.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"references_frozen": len(records), "network_boundary": result["boundary"]}))
if __name__ == "__main__":
    main()
