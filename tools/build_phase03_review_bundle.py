#!/usr/bin/env python3
"""Build and verify the allow-listed Phase 03 review bundle."""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "phase-03-review-bundle.zip"
MANIFEST_NAME = "PHASE_03_REVIEW_BUNDLE_MANIFEST.md"

REQUIRED_FILES = (
    "index.html",
    "package.json",
    "README.md",
    "MASTER_SPEC.md",
    "AGENTS.md",
    "QUALITY_GATES.md",
    "DECISIONS.md",
    "PROJECT_STATUS.md",
    "NEXT_ACTION.md",
    "HANDOFF_TO_CODEX.md",
    "REVIEW_PACKET.md",
    "prompts/01_WORK_FOUNDATION_AND_WAVE_1.md",
    "prompts/03_WORK_WAVE_2.md",
    "prompts/04_CODEX_INTEGRATE_AND_QA_V2.md",
    "prompts/PROMPT_03_WORK_EXECUTE_AND_PACKAGE_HE.md",
)

OPTIONAL_ROOT_FILES = (
    ".gitignore",
    "run-local.bat",
    "run-local.sh",
)

TREE_ROOTS = (
    "data",
    "schema",
    "research",
    "reports",
    "tools",
    "tests",
    "assets",
)

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "cache",
    "tmp",
    "temp",
}

EXCLUDED_NAMES = {
    ".env",
    ".ds_store",
    "thumbs.db",
    "credentials.json",
    "secrets.json",
}

EXCLUDED_NAME_MARKERS = (
    "api-key",
    "api_key",
    "apikey",
    "client-secret",
    "client_secret",
    "credential",
    "private-key",
    "private_key",
    "secret",
    "transcript",
)

EXCLUDED_SUFFIXES = {
    ".zip",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".pyc",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".mp4",
    ".webm",
    ".mkv",
    ".mov",
    ".avi",
    ".m4v",
    ".mp3",
    ".m4a",
    ".wav",
    ".ogg",
    ".opus",
    ".flac",
    ".srt",
    ".vtt",
    ".ass",
}

MANIFEST_ROW = re.compile(
    r"^\| `(?P<path>[^`]+)` \| (?P<size>\d+) \| `(?P<sha>[0-9a-f]{64})` \|$"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def relative(path: Path, root: Path = ROOT) -> str:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"Refusing path outside project root: {resolved}")
    return resolved.relative_to(resolved_root).as_posix()


def excluded_archive_name(name: str) -> bool:
    pure = PurePosixPath(name)
    lowered_parts = {part.lower() for part in pure.parts}
    lowered_name = pure.name.lower()
    if lowered_parts & EXCLUDED_PARTS:
        return True
    if lowered_name in EXCLUDED_NAMES or lowered_name.startswith(".env."):
        return True
    if any(marker in lowered_name for marker in EXCLUDED_NAME_MARKERS):
        return True
    return pure.suffix.lower() in EXCLUDED_SUFFIXES


def allowed(path: Path, root: Path = ROOT) -> bool:
    try:
        name = relative(path, root)
    except ValueError:
        return False
    return (
        path.is_file()
        and not path.is_symlink()
        and not excluded_archive_name(name)
    )


def collect_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    candidates: set[Path] = set()

    for name in REQUIRED_FILES:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"Required Phase 03 review file is missing: {name}")
        candidates.add(path)

    for name in OPTIONAL_ROOT_FILES:
        path = root / name
        if path.is_file():
            candidates.add(path)

    for name in TREE_ROOTS:
        tree = root / name
        if not tree.is_dir():
            raise FileNotFoundError(f"Required Phase 03 review directory is missing: {name}")
        candidates.update(path for path in tree.rglob("*") if allowed(path, root))

    files = sorted(
        (path for path in candidates if allowed(path, root)),
        key=lambda path: relative(path, root),
    )
    if not files:
        raise RuntimeError("Phase 03 review bundle would be empty")
    return files


def build_manifest(
    files: list[Path],
    root: Path = ROOT,
    generated_at: str | None = None,
) -> bytes:
    timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# PHASE 03 REVIEW BUNDLE MANIFEST",
        "",
        f"- Created (UTC): `{timestamp}`",
        f"- Payload files with SHA-256: **{len(files)}**",
        f"- Total archive files (including this manifest): **{len(files) + 1}**",
        "- The manifest is the sole archive member not hashed inside itself; all payload members are listed and verified below.",
        "- Excluded: Git metadata, dependency/cache/temp trees, ZIP files, common secret/key files, transcripts, captions, and downloaded video/audio media.",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for path in files:
        lines.append(
            f"| `{relative(path, root)}` | {path.stat().st_size} | `{file_sha256(path)}` |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_manifest(content: bytes) -> dict[str, tuple[int, str]]:
    text = content.decode("utf-8")
    entries: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        match = MANIFEST_ROW.match(line)
        if not match:
            continue
        name = match.group("path")
        if name in entries:
            raise RuntimeError(f"Manifest contains duplicate path: {name}")
        entries[name] = (int(match.group("size")), match.group("sha"))
    return entries


def validate_archive_name(name: str) -> None:
    if "\\" in name:
        raise RuntimeError(f"Archive path uses a backslash: {name}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"Unsafe archive path: {name}")
    if excluded_archive_name(name):
        raise RuntimeError(f"Excluded file was included in archive: {name}")


def verify_bundle(output: Path) -> dict[str, Any]:
    with zipfile.ZipFile(output) as archive:
        bad_entry = archive.testzip()
        if bad_entry:
            raise RuntimeError(f"Archive CRC check failed at {bad_entry}")

        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("Archive contains duplicate paths")
        for name in names:
            validate_archive_name(name)
        if MANIFEST_NAME not in names:
            raise RuntimeError(f"Archive is missing {MANIFEST_NAME}")

        manifest = parse_manifest(archive.read(MANIFEST_NAME))
        expected_names = set(manifest) | {MANIFEST_NAME}
        actual_names = set(names)
        if expected_names != actual_names:
            missing = sorted(expected_names - actual_names)
            extra = sorted(actual_names - expected_names)
            raise RuntimeError(f"Archive/manifest mismatch; missing={missing}; extra={extra}")

        for name, (expected_size, expected_hash) in manifest.items():
            content = archive.read(name)
            if len(content) != expected_size:
                raise RuntimeError(f"Archive size mismatch for {name}")
            if bytes_sha256(content) != expected_hash:
                raise RuntimeError(f"Archive SHA-256 mismatch for {name}")

    return {
        "status": "pass",
        "payload_files": len(manifest),
        "archive_files": len(names),
        "bytes": output.stat().st_size,
        "sha256": file_sha256(output),
    }


def build_bundle(
    output: Path = DEFAULT_OUTPUT,
    root: Path = ROOT,
) -> dict[str, Any]:
    root = root.resolve()
    output = output if output.is_absolute() else root / output
    output = output.resolve()
    if not output.is_relative_to(root):
        raise ValueError(f"Output must remain inside the project: {output}")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must be a .zip file")

    files = collect_files(root)
    manifest = build_manifest(files, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()

    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in files:
                archive.write(path, arcname=relative(path, root))
            archive.writestr(MANIFEST_NAME, manifest)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    return verify_bundle(output)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="ZIP path inside the project (default: reports/phase-03-review-bundle.zip)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    result = build_bundle(output)
    print("PASS: Phase 03 review bundle")
    print(f"Payload files: {result['payload_files']}")
    print(f"Archive files: {result['archive_files']}")
    print(f"Bytes: {result['bytes']}")
    print(f"SHA-256: {result['sha256']}")
    print(f"Output: {relative(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
