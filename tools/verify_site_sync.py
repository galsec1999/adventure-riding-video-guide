#!/usr/bin/env python3
"""Verify that the published site mirrors the canonical root source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MIRRORED_DIRECTORIES = (Path("assets"), Path("data"), Path("downloads"))
MIRRORED_FILES = (
    Path("index.html"),
    Path("404.html"),
    Path("offline.html"),
    Path("manifest.webmanifest"),
    Path("service-worker.js"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mirrored_files(base: Path) -> set[Path]:
    files = {relative for relative in MIRRORED_FILES if (base / relative).is_file()}
    for directory in MIRRORED_DIRECTORIES:
        root = base / directory
        if not root.is_dir():
            continue
        files.update(
            path.relative_to(base)
            for path in root.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
    return files


def compare_site(root: Path = ROOT, site: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    site = (site or root / "site").resolve()
    source_files = mirrored_files(root)
    published_files = mirrored_files(site)
    missing = sorted(source_files - published_files, key=lambda item: item.as_posix())
    extra = sorted(published_files - source_files, key=lambda item: item.as_posix())
    mismatched: list[dict[str, str]] = []

    for relative in sorted(source_files & published_files, key=lambda item: item.as_posix()):
        source_hash = sha256_file(root / relative)
        published_hash = sha256_file(site / relative)
        if source_hash != published_hash:
            mismatched.append(
                {
                    "path": relative.as_posix(),
                    "source_sha256": source_hash,
                    "published_sha256": published_hash,
                }
            )

    issues = bool(missing or extra or mismatched or Path("index.html") not in source_files)
    return {
        "status": "fail" if issues else "pass",
        "root": str(root),
        "site": str(site),
        "source_file_count": len(source_files),
        "published_file_count": len(published_files),
        "missing": [path.as_posix() for path in missing],
        "extra": [path.as_posix() for path in extra],
        "mismatched": mismatched,
    }


def synchronize_site(root: Path = ROOT, site: Path | None = None) -> dict[str, list[str]]:
    """Make managed publication paths an exact copy of the canonical source."""

    root = root.resolve()
    site = (site or root / "site").resolve()
    expected_site = (root / "site").resolve()
    if root == site or site != expected_site or site.parent != root:
        raise ValueError(f"refusing unsafe publication target: {site}")
    copied: list[str] = []
    removed: list[str] = []
    source_files = mirrored_files(root)
    for relative in sorted(mirrored_files(site) - source_files, key=lambda item: item.as_posix()):
        (site / relative).unlink()
        removed.append(relative.as_posix())
    for relative in sorted(mirrored_files(root), key=lambda item: item.as_posix()):
        source = root / relative
        target = site / relative
        if target.is_file() and sha256_file(source) == sha256_file(target):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative.as_posix())
    return {"copied": copied, "removed": removed}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Canonical project root")
    parser.add_argument("--site", type=Path, help="Publication directory; defaults to <root>/site")
    parser.add_argument("--write", action="store_true", help="Synchronize managed publication paths before checking")
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable result")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    site = (args.site or root / "site").resolve()
    changes = synchronize_site(root, site) if args.write else {"copied": [], "removed": []}
    result = compare_site(root, site)
    result.update(changes)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status'].upper()}: verify_site_sync")
        print(f"Source files: {result['source_file_count']}")
        print(f"Published files: {result['published_file_count']}")
        print(f"Copied: {len(changes['copied'])}")
        print(f"Removed: {len(changes['removed'])}")
        for path in result["missing"]:
            print(f"MISSING: {path}", file=sys.stderr)
        for path in result["extra"]:
            print(f"EXTRA: {path}", file=sys.stderr)
        for item in result["mismatched"]:
            print(f"MISMATCH: {item['path']}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
