"""H71R: pure offline bounded body capture. All responses come from an injected opener."""
from hashlib import sha256
from pathlib import Path
import time


def capture_attempt(
    opener, *, body_path, byte_limit, chunk_size=65536,
    clock=None, timeout_seconds=30,
) -> dict:
    """Capture one injected response, preserving evidence on partial failure.

    A limit is a maximum *read request* budget; hitting it without an observed
    EOF is not evidence that the body is complete. A failing read reserves its
    full requested size, rather than claiming no bytes reached the transport.
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
    deadline = now() + timeout_seconds
    target = Path(body_path)
    response = None
    handle = None
    status = None
    observed = 0
    charged = 0
    complete = False
    phase = "OPEN"
    error_type = None
    response_closed = False

    try:
        if now() >= deadline:
            phase = "TIMEOUT"
        else:
            response = opener()  # Exactly one call; never follow redirects.
            phase = "HEADERS"
            status = getattr(response, "status", None)
            headers = getattr(response, "headers", None)
            declared = None
            if headers is not None:
                if hasattr(headers, "get"):
                    declared = headers.get("Content-Length")
                    if declared is None:
                        declared = headers.get("content-length")
            if declared is not None:
                declared_text = str(declared).strip()
                if declared_text.isdigit() and int(declared_text) > byte_limit:
                    phase = "LIMIT"

            if phase != "LIMIT":
                phase = "BODY_WRITE"
                target.parent.mkdir(parents=True, exist_ok=True)
                handle = target.open("wb")
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
                        raise TypeError("non_bytes_response_body")
                    if len(block) > requested:
                        charged = min(byte_limit, charged + requested)
                        raise ValueError("oversized_read_return")
                    if not block:
                        complete = True
                        phase = "COMPLETE"
                        break
                    observed += len(block)
                    charged += len(block)
                    phase = "BODY_WRITE"
                    written = handle.write(block)
                    if written != len(block):
                        raise OSError("short_file_write")
                    handle.flush()
                    phase = "BODY_READ"
    except Exception as exc:
        # Only exception classes, never messages or response headers, are exposed.
        error_type = type(exc).__name__
    finally:
        if handle is not None:
            try:
                handle.close()
            except Exception as exc:
                if error_type is None:
                    error_type = type(exc).__name__
                    complete = False
                    phase = "BODY_WRITE"
        if response is not None:
            try:
                response.close()
                response_closed = True
            except Exception as exc:
                if error_type is None:
                    error_type = type(exc).__name__
                    complete = False
                    phase = "BODY_READ"

    archived = 0
    digest = sha256()
    if target.is_file():
        with target.open("rb") as stored:
            while True:
                chunk = stored.read(65536)
                if not chunk:
                    break
                archived += len(chunk)
                digest.update(chunk)
    if error_type is not None:
        complete = False
    return {
        "http_status": status,
        "failure_phase": phase,
        "body_complete": complete,
        "body_bytes_observed": observed,
        "body_bytes_total": observed if complete else None,
        "bytes_charged": charged,
        "body_sha256": digest.hexdigest(),
        "body_bytes_archived": archived,
        "error_type": error_type,
        "response_closed": response_closed,
    }
