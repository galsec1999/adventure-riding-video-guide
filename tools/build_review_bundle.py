#!/usr/bin/env python3
"""Build the allow-listed phase-02 review bundle and its SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "phase-02-review-bundle.zip"
MANIFEST = ROOT / "REVIEW_BUNDLE_MANIFEST.md"

ROOT_FILES = (
    ".gitignore",
    "AGENTS.md",
    "index.html",
    "package.json",
    "run-local.bat",
    "run-local.sh",
    "README.md",
    "MASTER_SPEC.md",
    "QUALITY_GATES.md",
    "HANDOFF_TO_CODEX.md",
    "PROJECT_STATUS.md",
    "DECISIONS.md",
    "NEXT_ACTION.md",
    "REVIEW_PACKET.md",
    "prompts/02_CODEX_BUILD_SITE_V1.md",
)

TREE_ROOTS = (
    "assets",
    "data",
    "schema",
    "tests",
    "tools",
    "reports/screenshots",
)

REPORT_FILES = (
    "reports/content-audit.json",
    "reports/content-audit.csv",
    "reports/content-audit.html",
    "reports/data-validation.json",
    "reports/link-check.json",
    "reports/browser-acceptance.json",
    "reports/test-summary.json",
)

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".cache",
    "cache",
    "tmp",
    "temp",
}

EXCLUDED_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
    "phase-02-review-bundle.zip",
}

EXCLUDED_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".pyc",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"Refusing path outside project root: {resolved}")
    return resolved.relative_to(ROOT).as_posix()


def allowed(path: Path) -> bool:
    rel = Path(relative(path))
    lowered_parts = {part.lower() for part in rel.parts}
    if lowered_parts & EXCLUDED_PARTS:
        return False
    if path.name.lower() in EXCLUDED_NAMES:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file() and not path.is_symlink()


def collect_files() -> list[Path]:
    candidates: set[Path] = set()
    for rel in (*ROOT_FILES, *REPORT_FILES):
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"Required review file is missing: {rel}")
        candidates.add(path)
    for rel in TREE_ROOTS:
        tree = ROOT / rel
        if not tree.is_dir():
            raise FileNotFoundError(f"Required review directory is missing: {rel}")
        candidates.update(path for path in tree.rglob("*") if allowed(path))
    files = sorted((path for path in candidates if allowed(path)), key=relative)
    if not files:
        raise RuntimeError("Review bundle would be empty")
    return files


def write_manifest(files: list[Path]) -> None:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# REVIEW BUNDLE MANIFEST",
        "",
        f"- Generated: `{generated_at}`",
        f"- Listed project files: **{len(files) + 1}**",
        "- Archive path: `reports/phase-02-review-bundle.zip`",
        "- The archive is allow-listed; `.git/`, `node_modules/`, caches, temporary files and common secret/key files are excluded.",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for path in files:
        lines.append(f"| `{relative(path)}` | {path.stat().st_size} | `{sha256(path)}` |")
    lines.append("| `REVIEW_BUNDLE_MANIFEST.md` | generated | self |")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_bundle(output: Path) -> tuple[int, int, str]:
    files = collect_files()
    write_manifest(files)
    archive_files = sorted([*files, MANIFEST], key=relative)

    output = output.resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError(f"Output must remain inside the project: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()

    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in archive_files:
                archive.write(path, arcname=relative(path))
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    with zipfile.ZipFile(output) as archive:
        bad_entry = archive.testzip()
        if bad_entry:
            raise RuntimeError(f"Archive CRC check failed at {bad_entry}")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("Archive contains duplicate paths")
        if "REVIEW_BUNDLE_MANIFEST.md" not in names:
            raise RuntimeError("Archive is missing REVIEW_BUNDLE_MANIFEST.md")
    return len(archive_files), output.stat().st_size, sha256(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="ZIP path inside the project (default: reports/phase-02-review-bundle.zip)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    count, size, digest = build_bundle(output)
    print("PASS: phase-02 review bundle")
    print(f"Files: {count}")
    print(f"Bytes: {size}")
    print(f"SHA-256: {digest}")
    print(f"Output: {relative(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
