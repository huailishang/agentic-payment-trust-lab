from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .interactive_lab import evaluate_interactive_scenario


_MAX_BODY_BYTES = 64 * 1024


def create_interactive_server(
    report_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    scenarios_dir: Path | None = None,
) -> ThreadingHTTPServer:
    report = report_path.resolve()
    if not report.exists():
        raise FileNotFoundError(f"interactive report does not exist: {report}")

    class Handler(BaseHTTPRequestHandler):
        server_version = "AgenticPaymentLab/0.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html", "/scenario_report.html"}:
                self._send_bytes(
                    HTTPStatus.OK,
                    report.read_bytes(),
                    "text/html; charset=utf-8",
                )
                return
            if parsed.path == "/health":
                self._send_json(
                    HTTPStatus.OK,
                    {"status": "ok", "simulation_only": True},
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
            parsed = urlparse(self.path)
            if parsed.path != "/api/evaluate":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return

            try:
                body = self._read_json_body()
                sample_id = str(body.get("sample_id", "")).strip()
                overrides = body.get("overrides", {})
                if not sample_id:
                    raise ValueError("sample_id is required")
                if not isinstance(overrides, dict):
                    raise ValueError("overrides must be an object")
                result = evaluate_interactive_scenario(
                    sample_id,
                    overrides,
                    scenarios_dir=scenarios_dir,
                )
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "invalid_request", "message": str(exc)},
                )
                return
            except Exception as exc:  # defensive boundary for local UI
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "evaluation_failed", "message": str(exc)},
                )
                return

            self._send_json(HTTPStatus.OK, result)

        def _read_json_body(self) -> dict[str, Any]:
            length_text = self.headers.get("Content-Length")
            if length_text is None:
                raise ValueError("Content-Length is required")
            try:
                length = int(length_text)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0 or length > _MAX_BODY_BYTES:
                raise ValueError("request body is too large")
            raw = self.rfile.read(length)
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def _send_json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status, payload, "application/json; charset=utf-8")

        def _send_bytes(self, status: HTTPStatus, payload: bytes, content_type: str) -> None:
            self.send_response(int(status))
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            # Keep the terminal focused on experiment output rather than every browser request.
            return

    return ThreadingHTTPServer((host, port), Handler)
