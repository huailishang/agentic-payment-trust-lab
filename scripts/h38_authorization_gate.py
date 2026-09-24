"""Fail-closed authorization gate for the H38 live sandbox probe.

This module intentionally uses only the Python standard library. The probe
must read the repository CURRENT.md directly; no CLI or environment override
is provided for the authorization source.
"""
from __future__ import annotations

import re
from pathlib import Path


EXPECTED = {
    "workflow": "evaluator-executor-workflow/v2.2",
    "task_id": "H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1",
    "state": "EXECUTING",
    "current_role": "Executor",
    "contract_path": "docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md",
}
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_FENCE_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)$")
_FENCE_LIKE = re.compile(r"^[ \t]+(`{3,}|~{3,})")
_UNQUOTED = re.compile(r"""^[^\s"'#{}\[\],]+$""")


class AuthorizationGateError(RuntimeError):
    """Raised when CURRENT.md cannot prove the exact H38 live authorization."""


def _decode_scalar(raw: str) -> str:
    """Decode the deliberately small scalar grammar accepted by CURRENT."""
    value = raw.strip()
    if not value:
        raise AuthorizationGateError("empty scalar")

    if value[0] in "'\"":
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise AuthorizationGateError("unpaired quoted scalar")
        inner = value[1:-1]
        if quote in inner or "\n" in inner or "\r" in inner:
            raise AuthorizationGateError("unsupported quoted scalar syntax")
        return inner

    if not _UNQUOTED.fullmatch(value):
        raise AuthorizationGateError("unsupported unquoted scalar syntax")
    return value


def _extract_active_yaml_blocks(markdown: str) -> list[list[str]]:
    """Extract top-level active triple-backtick yaml blocks conservatively."""
    blocks: list[list[str]] = []
    active_marker: str | None = None
    active_info: str | None = None
    active_lines: list[str] = []
    in_html_comment = False

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()

        if active_marker is not None:
            close_match = re.fullmatch(
                rf" {{0,3}}{re.escape(active_marker[0])}{{{len(active_marker)},}}[ \t]*",
                raw_line,
            )
            if close_match:
                if active_info == "yaml":
                    blocks.append(active_lines)
                active_marker = None
                active_info = None
                active_lines = []
                continue

            if active_info == "yaml":
                active_lines.append(raw_line)
            continue

        if in_html_comment:
            if "-->" not in raw_line:
                continue
            before, after = raw_line.split("-->", 1)
            if after.strip():
                raise AuthorizationGateError("content after html comment close")
            in_html_comment = False
            continue

        if stripped.startswith("<!--"):
            if not raw_line.lstrip().startswith("<!--"):
                raise AuthorizationGateError("inline html comment not allowed")
            if "-->" in raw_line:
                _, after = raw_line.split("-->", 1)
                if after.strip():
                    raise AuthorizationGateError("content after html comment close")
            else:
                in_html_comment = True
            continue

        if "<!--" in raw_line or "-->" in raw_line:
            raise AuthorizationGateError("malformed html comment")

        fence = _FENCE_OPEN.fullmatch(raw_line)
        if fence:
            marker = fence.group(2)
            info = fence.group(3).strip()
            if info.lower().startswith("yaml") and (marker != "```" or info != "yaml"):
                raise AuthorizationGateError("unsupported yaml fence")
            active_marker = marker
            active_info = info
            active_lines = []
            continue

        if _FENCE_LIKE.match(raw_line):
            raise AuthorizationGateError("unsupported indented markdown fence")

    if in_html_comment:
        raise AuthorizationGateError("unclosed html comment")
    if active_marker is not None:
        raise AuthorizationGateError("unclosed markdown fence")
    return blocks


def parse_current_workflow(markdown: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return decoded and raw top-level fields from the single active YAML fence."""
    blocks = _extract_active_yaml_blocks(markdown)
    if len(blocks) != 1:
        raise AuthorizationGateError("CURRENT must contain exactly one active yaml state block")

    decoded: dict[str, str] = {}
    raw_values: dict[str, str] = {}
    for line in blocks[0]:
        if not line.strip() or line.startswith("#"):
            continue
        if line[:1].isspace():
            raise AuthorizationGateError("nested or indented yaml is not allowed")
        if ":" not in line:
            raise AuthorizationGateError("malformed yaml scalar")

        key, raw = line.split(":", 1)
        key = key.strip()
        if not _KEY.fullmatch(key) or key in decoded:
            raise AuthorizationGateError("invalid or duplicate top-level field")

        raw = raw.strip()
        decoded[key] = _decode_scalar(raw)
        raw_values[key] = raw

    return decoded, raw_values


def require_h38_live_authorization(root: Path) -> None:
    """Read ROOT/CURRENT.md and require the exact frozen live authorization tuple."""
    current = root / "CURRENT.md"
    try:
        markdown = current.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuthorizationGateError("CURRENT unavailable") from exc

    fields, raw = parse_current_workflow(markdown)
    for key, expected in EXPECTED.items():
        if fields.get(key) != expected:
            raise AuthorizationGateError("authorization tuple mismatch")
    if raw.get("authorization_api_call") != "true":
        raise AuthorizationGateError("api authorization is not literal true")
