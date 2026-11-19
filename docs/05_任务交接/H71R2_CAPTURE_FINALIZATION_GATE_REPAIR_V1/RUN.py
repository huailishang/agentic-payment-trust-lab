"""H71R2: offline, one-opener bounded capture with exclusive archive ownership.

This module never creates a network connection. The injected opener supplies
the complete response abstraction. Transport failures, output failures,
finalization failures, and cleanup failures all return structured evidence.
"""
from hashlib import sha256
from pathlib import Path
import time


def capture_attempt(
    opener, *, body_path, byte_limit, chunk_size=65536,
    clock=None, timeout_seconds=30,
) -> dict:
    """Capture one injected response without claiming unverified archive bytes.

    The output is created exclusively *before* opener is invoked. A failing
    read conservatively reserves its requested byte count. No read beyond the
    remaining budget is made to probe EOF.
    """
    if not callable(opener):
        raise TypeError("opener must be callable")
    if type(byte_limit) is not int or byte_limit < 0:
        raise ValueError("byte_limit must be a non-negative integer")
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if not isinstance(timeout_seconds, (int, float)) or timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")

    now = clock if clock is not None else time.monotonic
    target = Path(body_path)
    handle = None
    response = None
    owned = False
    status = None
    phase = "OUTPUT_PREPARE"
    errors = []
    observed = 0
    charged = 0
    eof_seen = False
    response_closed = False
    digest = None
    digest_state = "NOT_OWNED"
    archived = 0

    def record(where, exc):
        errors.append({"phase": where, "type": type(exc).__name__})

    # Prepare the *exact* destination atomically. Never use or hash any
    # pre-existing file, even when a subsequent opener would fail.
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = target.open("xb")
        owned = True
        digest_state = "UNAVAILABLE"
    except Exception as exc:
        record("OUTPUT_PREPARE", exc)

    if owned:
        try:
            deadline = now() + timeout_seconds
            if now() >= deadline:
                phase = "TIMEOUT"
            else:
                phase = "OPEN"
                response = opener()  # Once only; no redirect following.
                phase = "HEADERS"
                status = getattr(response, "status", None)
                headers = getattr(response, "headers", None)
                declared = None
                if headers is not None and hasattr(headers, "get"):
                    declared = headers.get("Content-Length")
                    if declared is None:
                        declared = headers.get("content-length")
                if declared is not None:
                    value = str(declared).strip()
                    if value.isdigit() and int(value) > byte_limit:
                        phase = "LIMIT"
                if phase != "LIMIT":
                    phase = "BODY_READ"
                    while True:
                        if now() >= deadline:
                            phase = "TIMEOUT"
                            break
                        remaining = byte_limit - charged
                        if remaining <= 0:
                            phase = "LIMIT"
                            break
                        requested = min(chunk_size, remaining)
                        try:
                            block = response.read(requested)
                        except Exception:
                            charged = min(byte_limit, charged + requested)
                            raise
                        if not isinstance(block, bytes):
                            raise TypeError("response_read_not_bytes")
                        if len(block) > requested:
                            charged = min(byte_limit, charged + requested)
                            raise ValueError("response_read_exceeds_request")
                        if not block:
                            eof_seen = True
                            phase = "COMPLETE"
                            break

                        observed += len(block)
                        charged += len(block)
                        phase = "BODY_WRITE"
                        offset = 0
                        while offset < len(block):
                            written = handle.write(block[offset:])
                            if type(written) is not int or written <= 0 or written > len(block) - offset:
                                raise OSError("invalid_write_count")
                            offset += written
                        handle.flush()
                        phase = "BODY_READ"
        except Exception as exc:
            record(phase, exc)
        finally:
            # Independent cleanup: never erase the original read/write error.
            if handle is not None:
                try:
                    handle.close()
                except Exception as exc:
                    record("ARCHIVE_CLOSE", exc)
                    if not errors[:-1] and phase == "COMPLETE":
                        phase = "ARCHIVE_CLOSE"
            if response is not None:
                try:
                    response.close()
                    response_closed = True
                except Exception as exc:
                    record("CLOSE", exc)
                    if len(errors) == 1:
                        phase = "CLOSE"

        # Verify the *owned* archive only. Both file metadata and digest
        # inspection are guarded independently; failure cannot erase status.
        stat_size = None
        try:
            stat_size = target.stat().st_size
        except Exception as exc:
            record("BODY_STAT", exc)
            if not (phase in ("BODY_READ", "BODY_WRITE", "OPEN", "HEADERS", "LIMIT", "TIMEOUT")):
                phase = "BODY_STAT"

        try:
            candidate = sha256()
            count = 0
            with target.open("rb") as saved:
                while True:
                    block = saved.read(65536)
                    if not block:
                        break
                    candidate.update(block)
                    count += len(block)
            archived = count
            if stat_size is not None and stat_size != count:
                record("BODY_HASH", ValueError("archive_size_disagreement"))
                if phase == "COMPLETE":
                    phase = "BODY_HASH"
            else:
                digest = candidate.hexdigest()
                digest_state = "KNOWN"
        except Exception as exc:
            record("BODY_HASH", exc)
            if phase == "COMPLETE":
                phase = "BODY_HASH"
            digest = None
            digest_state = "UNAVAILABLE"
            archived = stat_size

    complete = (
        owned and eof_seen and phase == "COMPLETE"
        and not errors and digest_state == "KNOWN"
        and archived == observed and response_closed
    )
    return {
        "http_status": status,
        "failure_phase": phase,
        "body_complete": complete,
        "body_bytes_observed": observed,
        "body_bytes_total": observed if complete else None,
        "bytes_charged": charged,
        "body_sha256": digest,
        "body_sha256_state": digest_state,
        "body_bytes_archived": archived,
        "body_artifact_owned": owned,
        "error_type": errors[0]["type"] if errors else None,
        "errors": errors,
        "response_closed": response_closed,
    }
