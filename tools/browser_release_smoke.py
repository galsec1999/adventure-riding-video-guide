#!/usr/bin/env python3
"""Run a post-red-team smoke in a real local Chromium-family browser."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/final-one-shot/browser-smoke-after-red-team.json"


def browser_candidates() -> list[Path]:
    program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    program_files_x86 = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
    local_app_data = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"))
    return [
        program_files / "Google/Chrome/Application/chrome.exe",
        program_files_x86 / "Google/Chrome/Application/chrome.exe",
        local_app_data / "Google/Chrome/Application/chrome.exe",
        program_files / "Microsoft/Edge/Application/msedge.exe",
        program_files_x86 / "Microsoft/Edge/Application/msedge.exe",
    ]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_for_server(url: str) -> None:
    last_error: Exception | None = None
    for _ in range(50):
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception as exc:  # local startup race only
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"local server did not become ready: {last_error}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    browser = next((path for path in browser_candidates() if path.is_file()), None)
    if browser is None:
        raise SystemExit("Chrome or Edge executable was not found")

    port = free_port()
    url = f"http://127.0.0.1:{port}/"
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server = subprocess.Popen(
        [sys.executable, "tools/serve_local.py", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )
    try:
        wait_for_server(url)
        with tempfile.TemporaryDirectory(prefix="adv-guide-browser-smoke-") as profile:
            result = subprocess.run(
                [
                    str(browser), "--headless=new", "--disable-gpu",
                    "--disable-extensions", "--disable-background-networking",
                    "--no-first-run", "--no-default-browser-check",
                    f"--user-data-dir={profile}", "--virtual-time-budget=5000",
                    "--dump-dom", url,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
                creationflags=creation_flags,
            )
        dom = result.stdout
        error_tag = re.search(r'<section[^>]*id="app-error"[^>]*>', dom)
        checks = {
            "browser_exit_zero": result.returncode == 0,
            "hebrew_rtl_document": '<html lang="he" dir="rtl"' in dom,
            "configured_title": "מדריך הווידאו לרכיבת אדוונצ'ר" in dom,
            "production_count_rendered": '>250<' in dom,
            "video_cards_rendered": dom.count('class="video-card') >= 6,
            "eight_paths_rendered": '>8<' in dom and 'id="path-switcher"' in dom,
            "no_eager_iframe": "<iframe" not in dom.casefold(),
            "error_panel_hidden": bool(error_tag and "hidden" in error_tag.group(0)),
        }
        report = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checked_at": "2026-08-04T15:50:00+03:00",
            "browser_executable": str(browser),
            "url": url,
            "real_browser": True,
            "headless": True,
            "dom_bytes": len(dom.encode("utf-8")),
            "checks": checks,
            "stderr_tail": result.stderr[-1000:],
        }
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "checks": checks}, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
