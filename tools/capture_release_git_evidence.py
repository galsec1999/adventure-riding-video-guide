#!/usr/bin/env python3
"""Capture the exact Git evidence required by the Release 1.0 prompt."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/final-one-shot"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "git-status.txt": git("status", "--short", "--branch"),
        "git-log.txt": git("log", "-1", "--oneline"),
        "git-show-stat.txt": git("show", "--stat", "--oneline", "HEAD"),
        "git-diff-check.txt": git("diff", "--check"),
    }
    for name, content in evidence.items():
        (OUTPUT / name).write_text(content, encoding="utf-8")
    print(f"Captured {len(evidence)} Git evidence files in {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
