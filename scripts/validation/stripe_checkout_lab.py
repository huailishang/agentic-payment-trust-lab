"""H68 isolated capability probe. Never navigates a paid session or makes network calls.

Uses the existing Windows Chrome binary and its native DevTools pipe with a
new profile outside the repository. No Selenium, Playwright or browser install.
A failed probe is an INPUT_LIMIT, never a provider payment outcome.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import subprocess
import threading

CHROME = Path("/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")
CMD = Path("/mnt/c/Windows/System32/cmd.exe")


def probe_browser(timeout: float = 12.0) -> dict[str, object]:
    if not CHROME.is_file() or not CMD.is_file():
        return {"capability": "INPUT_LIMIT", "reason": "existing_chrome_or_windows_shell_missing"}
    try:
        completed = subprocess.run(
            [str(CMD), "/c", "echo", "%TEMP%"], capture_output=True,
            text=True, timeout=5, check=True,
        )
        windows_temp = completed.stdout.strip()
        if not windows_temp or ":" not in windows_temp or "\n" in windows_temp:
            return {"capability": "INPUT_LIMIT", "reason": "private_browser_profile_location_missing"}
        profile = windows_temp.rstrip("\\") + "\\h68-chrome-" + secrets.token_hex(8)
        process = subprocess.Popen([
            str(CHROME), "--headless=new", "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--disable-background-networking",
            "--remote-debugging-pipe", "--user-data-dir=" + profile, "about:blank",
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
           stderr=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"capability": "INPUT_LIMIT", "reason": "chrome_launch_unavailable"}

    output = {"capability": "INPUT_LIMIT", "reason": "devtools_pipe_unavailable"}
    try:
        def _exchange():
            try:
                assert process.stdin and process.stdout
                process.stdin.write(b'{"id":1,"method":"Browser.getVersion"}\0')
                process.stdin.flush()
                wire = bytearray()
                while len(wire) < 8192:
                    piece = process.stdout.read(1)
                    if not piece or piece == b"\0":
                        break
                    wire.extend(piece)
                response = json.loads(bytes(wire))
                if response.get("id") == 1 and response.get("result", {}).get("protocolVersion"):
                    output.update({"capability": "CHROME_CDP_PIPE_OK",
                                   "reason": "native_browser_control_available"})
            except (OSError, ValueError, AssertionError):
                pass
        t = threading.Thread(target=_exchange, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            output["reason"] = "devtools_pipe_timeout"
        return output
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                output["reason"] = "task_chrome_process_could_not_be_stopped"


def probe_browser_port(timeout: float = 12.0) -> dict[str, object]:
    """Second native interface probe, loopback-only and isolated, no page/payment."""
    import socket
    import time
    from urllib.request import urlopen
    if not CHROME.is_file() or not CMD.is_file():
        return {"capability":"INPUT_LIMIT", "reason":"native_chrome_missing"}
    try:
        temp = subprocess.run(
            [str(CMD), "/c", "echo", "%TEMP%"], capture_output=True, text=True,
            timeout=5, check=True,
        ).stdout.strip()
        if not temp or ":" not in temp or "\n" in temp:
            return {"capability":"INPUT_LIMIT", "reason":"private_profile_unavailable"}
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        profile = temp.rstrip("\\") + "\\h68-chrome-" + secrets.token_hex(8)
        process = subprocess.Popen([
            str(CHROME), "--headless=new", "--no-first-run",
            "--disable-background-networking", "--disable-extensions",
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=" + str(port), "--user-data-dir=" + profile,
            "about:blank",
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
           stderr=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"capability":"INPUT_LIMIT", "reason":"native_browser_start_failure"}
    result = {"capability":"INPUT_LIMIT", "reason":"devtools_loopback_unreachable"}
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urlopen("http://127.0.0.1:" + str(port) + "/json/version", timeout=1) as response:
                    doc = json.load(response)
                if isinstance(doc, dict) and doc.get("Protocol-Version") and doc.get("webSocketDebuggerUrl"):
                    result = {"capability":"CHROME_CDP_PORT_OK",
                              "reason":"native_browser_control_available"}
                    break
            except (OSError, ValueError):
                pass
            time.sleep(0.3)
        return result
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                result["reason"] = "task_chrome_process_stop_unknown"


if __name__ == "__main__":
    print(json.dumps(probe_browser(), sort_keys=True))
