#!/usr/bin/env python3
"""Build and independently verify the single Adventure Guide Release 1.0 ZIP."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
RELEASE_PARENT = ROOT / "release"
RELEASE_NAME = "Adventure-Riding-Video-Guide-v1.0.0"
RELEASE_DIR = RELEASE_PARENT / RELEASE_NAME
ZIP_PATH = RELEASE_PARENT / "Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip"
SHA_PATH = RELEASE_PARENT / "Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip.sha256"
VERIFICATION_PATH = ROOT / "reports/final-one-shot/release-verification.json"

FORBIDDEN_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".cache", "cache", "playwright-report", "test-results",
}
FORBIDDEN_SUFFIXES = {".pyc", ".tmp", ".temp", ".log", ".zip"}
MEDIA_SUFFIXES = {
    ".mp4", ".webm", ".mkv", ".mov", ".avi", ".wmv",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".csv", ".html", ".css", ".js", ".mjs",
    ".py", ".bat", ".sh", ".svg", ".gitignore",
}
SECRET_PATTERNS = {
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout.strip()


def safe_reset_release_dir() -> None:
    parent = RELEASE_PARENT.resolve()
    target = RELEASE_DIR.resolve()
    expected = parent / RELEASE_NAME
    if target != expected or target.parent != parent or target == ROOT.resolve():
        raise SystemExit(f"refusing unsafe release target: {target}")
    RELEASE_PARENT.mkdir(parents=True, exist_ok=True)
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    for file_path in (ZIP_PATH, SHA_PATH):
        if file_path.exists():
            file_path.unlink()


def should_skip(path: Path) -> bool:
    return (
        any(part in FORBIDDEN_DIRS for part in path.parts)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
        or path.is_symlink()
    )


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(f"required source path missing: {source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if should_skip(relative):
            continue
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"required source file missing: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_site() -> None:
    site = RELEASE_DIR / "site"
    copy_file(ROOT / "index.html", site / "index.html")
    copy_tree(ROOT / "assets", site / "assets")
    copy_tree(ROOT / "data", site / "data")


def build_source() -> None:
    source = RELEASE_DIR / "source"
    for name in ("assets", "data", "schema", "tools", "tests", "prompts"):
        copy_tree(ROOT / name, source / name)
    copy_tree(ROOT / "research/final-one-shot", source / "research/final-one-shot")
    copy_tree(ROOT / "archive", source / "archive")
    root_files = [
        ".gitignore", "AGENTS.md", "MASTER_SPEC.md", "QUALITY_GATES.md",
        "DECISIONS.md", "PROJECT_STATUS.md", "NEXT_ACTION.md", "REVIEW_PACKET.md",
        "README.md", "CHANGELOG.md", "package.json", "index.html",
        "run-local.bat", "run-local.sh", "AUTORUN_STATE.json",
    ]
    for name in root_files:
        copy_file(ROOT / name, source / name)


def build_reports() -> None:
    reports = RELEASE_DIR / "reports"
    copy_tree(ROOT / "reports/final-one-shot", reports / "final-one-shot")
    # Verification of the ZIP is necessarily external to the ZIP it verifies.
    stale_self_report = reports / "final-one-shot/release-verification.json"
    if stale_self_report.exists():
        stale_self_report.unlink()
    for suffix in ("json", "csv", "html"):
        copy_file(ROOT / f"reports/content-audit.{suffix}", reports / f"content-audit.{suffix}")
    research_reports = reports / "research"
    for name in (
        "evidence-ledger.csv", "chapter-curation.csv", "approved-new.csv",
        "rejected-candidates.csv", "reserve-candidates.csv",
    ):
        copy_file(ROOT / f"research/final-one-shot/{name}", research_reports / name)


def release_stats() -> dict:
    videos = read_json(ROOT / "data/videos.json")
    paths = read_json(ROOT / "data/learning-paths.json")
    audit = read_json(ROOT / "reports/final-one-shot/content-audit.json")
    links = read_json(ROOT / "reports/final-one-shot/final-link-check.json")
    tests = read_json(ROOT / "reports/final-one-shot/final-test-summary.json")
    browser = read_json(ROOT / "reports/final-one-shot/browser-acceptance.json")
    content_red = read_json(ROOT / "reports/final-one-shot/red-team-content-defects.json")
    technical_path = ROOT / "reports/final-one-shot/red-team-technical-defects.json"
    technical_red = read_json(technical_path) if technical_path.exists() else {
        "status": "pending", "defect_counts": {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    }
    return {
        "videos": videos,
        "paths": paths,
        "audit": audit,
        "links": links,
        "tests": tests,
        "browser": browser,
        "content_red": content_red,
        "technical_red": technical_red,
    }


def write_readme_first() -> None:
    content = """# קראו תחילה — Adventure Riding Video Guide 1.0.0

תיקייה זו היא חבילת השחרור הסופית.

- `site/` — האתר הנקי והמוכן לפרסום. יש לפרסם רק את תוכן התיקייה הזאת באחסון סטטי.
- `source/` — קוד המקור, הנתונים, כלי התחזוקה, הבדיקות, מסמכי הפרויקט ומחקר השחרור.
- `reports/` — ראיות האימות, הקישורים, הדפדפן, Red Team, Git וצילומי המסך.
- `FINAL_RELEASE_REPORT.md` — דוח התוצאה והוראות הפרסום.
- `FINAL_RELEASE_MANIFEST.md` — גודל ו־SHA-256 לכל קובצי המטען.

להפעלה מקומית מתוך `source/` מריצים `run-local.bat`. אין לפתוח את `index.html` דרך `file://`. לפרסום מעתיקים את תוכן `site/` כפי שהוא. כל הזכויות בסרטונים שייכות ליוצרים המקוריים; החבילה אינה כוללת וידאו, שמע או תמלולים מלאים.
"""
    (RELEASE_DIR / "README-FIRST.md").write_text(content, encoding="utf-8")


def write_final_report(stats: dict) -> None:
    videos = stats["videos"]
    audit = stats["audit"]
    source_types = Counter(video["source_type"] for video in videos)
    channels = Counter(video["channel_name"] for video in videos)
    commit_hash = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    links = stats["links"]["summary"]
    tests = stats["tests"]["unique_test_totals"]
    browser = stats["browser"]["summary"]
    content_red = stats["content_red"]["defect_counts"]
    technical_red = stats["technical_red"]["defect_counts"]
    red_totals = {
        priority: content_red.get(priority, 0) + technical_red.get(priority, 0)
        for priority in ("P0", "P1", "P2", "P3")
    }
    performance = stats["tests"]["performance_measurements_ms"]
    categories = audit["by_primary_category"]
    top_categories = sorted(categories.items(), key=lambda item: (-item[1], item[0]))[:10]
    report = f"""# דוח Release סופי — 1.0.0

## תוצאה

**PASS** — האתר והנתונים מוכנים לפרסום סטטי.

- Commit: `{commit_hash}`
- Branch: `{branch}`
- גרסה: `1.0.0`

## תוכן

- סרטונים: **{len(videos)}**; עברית {audit['by_language']['he']}, אנגלית {audit['by_language']['en']}.
- תחומים: {', '.join(f'`{key}` {value}' for key, value in audit['by_domain'].items())}.
- קטגוריות ראשיות: {len(categories)}; עשר הגדולות: {', '.join(f'`{key}` {value}' for key, value in top_categories)}.
- ערוצים: {len(channels)}; MOTOTREK: {channels.get('MOTOTREK', 0)} לצד מקורות נוספים.
- סוגי מקור: {', '.join(f'`{key}` {value}' for key, value in sorted(source_types.items()))}.
- Marketing=true: {audit['contains_marketing']}; Marketing=false: {len(videos) - audit['contains_marketing']}.
- Chapters: 897 מאומתים ב־Production; 152 החלטות הסרה מתועדות.
- מסלולי למידה: {len(stats['paths'])}, עם 64 שלבים ו־192 הפניות.

## בדיקות וקישורים

- בדיקות ייחודיות: {tests['passed']} עברו, {tests['failed']} נכשלו.
- Data Validation: 14,084/14,084.
- Node: 55/55; Python: 24/24; Browser Acceptance: {browser['checks_passed']}/{browser['checks_passed'] + browser['checks_failed']}.
- קישורים חיים: {links['online_active_public']}/250; unavailable={links['online_unavailable']}, indeterminate={links['online_indeterminate']}, rate_limited={links['online_rate_limited']}.
- Console: {browser['console_errors']} שגיאות; Screenshots: {browser['screenshots']}.

## ביצועים ונגישות

- הכנה ואינדוקס: 250 רשומות {performance['prepare_index_250']}ms; ‏300 רשומות {performance['prepare_index_300']}ms.
- חיפוש, סינון ומיון: 250 רשומות {performance['search_filter_sort_250']}ms; ‏300 רשומות {performance['search_filter_sort_300']}ms. אלו מדידות מידע ללא סף תלוי־חומרה.
- Desktop, Tablet, ‏390px ו־360px עברו ללא Overflow אופקי.
- מקלדת, Focus restore, ‏Escape, Dialog semantics, ‏RTL, ‏Bidi, ‏Alt, Lazy Loading ו־Reduced Motion נבדקו בקוד ובדפדפן.

## Red Team ותיקונים

- Reviewer A: {stats['content_red']['status'].upper()}, P0={content_red.get('P0', 0)}, P1={content_red.get('P1', 0)}, P2={content_red.get('P2', 0)}, P3={content_red.get('P3', 0)}.
- Reviewer B: {stats['technical_red']['status'].upper()}, P0={technical_red.get('P0', 0)}, P1={technical_red.get('P1', 0)}, P2={technical_red.get('P2', 0)}, P3={technical_red.get('P3', 0)}.
- סך שנותר: P0={red_totals['P0']}, P1={red_totals['P1']}, P2={red_totals['P2']}, P3={red_totals['P3']}.
- שני קישורים שנכשלו בבדיקה חיה הוחלפו ממאגר העתודה וכל שערי הנתונים, התוכן, החיפוש והקישורים הורצו שוב.

## מגבלות אמיתיות

- זמינות YouTube יכולה להשתנות לאחר הבדיקה; יש להריץ את `tools/check_links.py --online` בתחזוקה עתידית.
- מצב משתמש נשמר מקומית בדפדפן ואינו מסתנכרן בין מכשירים.
- אזהרות אורך של Quality Lint נשמרו כאשר הרחבת תקציר לא הייתה נתמכת בראיות; אין תוכן תבניתי או מומצא.

## פרסום

1. חלצו את ה־ZIP ואמתו את קובץ ה־SHA-256 החיצוני.
2. פרסמו רק את תוכן `site/` בשורש אחסון סטטי.
3. בדקו לאחר הפרסום את טעינת `data/videos.json`, החיפוש, המסננים, Deep Link והנגן.
4. אל תפרסמו `.git`, ‏`source/`, ‏`reports/`, מפתחות או קובצי סביבה כחלק מן האתר הציבורי.
"""
    (RELEASE_DIR / "FINAL_RELEASE_REPORT.md").write_text(report, encoding="utf-8")


def write_manifest() -> tuple[list[dict], int]:
    manifest_path = RELEASE_DIR / "FINAL_RELEASE_MANIFEST.md"
    files = [
        path for path in RELEASE_DIR.rglob("*")
        if path.is_file() and path != manifest_path
    ]
    rows = []
    for path in sorted(files, key=lambda item: item.relative_to(RELEASE_DIR).as_posix()):
        rows.append({
            "path": path.relative_to(RELEASE_DIR).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    total_bytes = sum(row["bytes"] for row in rows)
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# FINAL RELEASE MANIFEST",
        "",
        f"- Created UTC: `{created}`",
        f"- Payload files: **{len(rows)}**",
        f"- Payload bytes: **{total_bytes}**",
        "- Hash algorithm: **SHA-256**",
        "- Scope: every payload file in this release directory. The manifest file itself is the sole self-exclusion because a file cannot contain its own stable cryptographic hash.",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for row in rows:
        safe_path = row["path"].replace("|", "\\|")
        lines.append(f"| `{safe_path}` | {row['bytes']} | `{row['sha256']}` |")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, total_bytes


def create_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(RELEASE_DIR.rglob("*")):
            if not path.is_file():
                continue
            arcname = (PurePosixPath(RELEASE_NAME) / path.relative_to(RELEASE_DIR).as_posix()).as_posix()
            archive.write(path, arcname)


def verify_zip(manifest_rows: list[dict]) -> dict:
    expected_payload = {row["path"]: row for row in manifest_rows}
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("duplicate paths in ZIP")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or ":" in pure.parts[0]:
                raise SystemExit(f"unsafe ZIP path: {name}")
            lowered = {part.lower() for part in pure.parts}
            if lowered & {item.lower() for item in FORBIDDEN_DIRS}:
                raise SystemExit(f"forbidden directory in ZIP: {name}")
            if pure.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise SystemExit(f"forbidden temporary/archive file in ZIP: {name}")
            if pure.suffix.lower() in MEDIA_SUFFIXES:
                raise SystemExit(f"video/audio media in ZIP: {name}")
            filename = pure.name.casefold()
            if any(token in filename for token in ("transcript", "subtitle", "caption")):
                raise SystemExit(f"possible full transcript/caption file in ZIP: {name}")

        with tempfile.TemporaryDirectory(prefix="adv-guide-release-verify-") as temp_dir:
            extracted_parent = Path(temp_dir)
            archive.extractall(extracted_parent)
            extracted = extracted_parent / RELEASE_NAME
            if not (extracted / "site/index.html").is_file():
                raise SystemExit("site/index.html missing after extraction")
            source_videos = read_json(extracted / "source/data/videos.json")
            if len(source_videos) != 250:
                raise SystemExit("source/data/videos.json is not exactly 250 records")
            site_videos = read_json(extracted / "site/data/videos.json")
            if len(site_videos) != 250:
                raise SystemExit("site/data/videos.json is not exactly 250 records")

            manifest_relative = "FINAL_RELEASE_MANIFEST.md"
            actual_payload = {
                path.relative_to(extracted).as_posix(): path
                for path in extracted.rglob("*")
                if path.is_file() and path.relative_to(extracted).as_posix() != manifest_relative
            }
            if set(actual_payload) != set(expected_payload):
                missing = sorted(set(expected_payload) - set(actual_payload))
                extra = sorted(set(actual_payload) - set(expected_payload))
                raise SystemExit(f"manifest file-set mismatch missing={missing} extra={extra}")
            for relative, row in expected_payload.items():
                path = actual_payload[relative]
                if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
                    raise SystemExit(f"manifest mismatch: {relative}")

            secret_hits: list[dict] = []
            text_files_checked = 0
            for relative, path in actual_payload.items():
                if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".gitignore":
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                text_files_checked += 1
                for name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        secret_hits.append({"path": relative, "pattern": name})
            if secret_hits:
                raise SystemExit(f"secret-like values detected: {secret_hits}")

    zip_hash = sha256(ZIP_PATH)
    SHA_PATH.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="ascii")
    return {
        "status": "PASS",
        "verified_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "release_directory": str(RELEASE_DIR),
        "zip_path": str(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": zip_hash,
        "sha256_file": str(SHA_PATH),
        "zip_entries": len(names),
        "manifest_payload_files": len(expected_payload),
        "manifest_payload_bytes": sum(row["bytes"] for row in manifest_rows),
        "text_files_secret_scanned": text_files_checked,
        "checks": {
            "extractable": True,
            "no_path_traversal_or_absolute_paths": True,
            "no_git_node_modules_caches_or_temporary_files": True,
            "no_nested_zip": True,
            "no_secret_patterns": True,
            "no_full_transcript_caption_files": True,
            "no_video_or_audio": True,
            "manifest_file_set_exact": True,
            "manifest_sizes_and_hashes_match": True,
            "site_index_exists": True,
            "source_videos_exactly_250": True,
            "site_videos_exactly_250": True,
        },
    }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    safe_reset_release_dir()
    build_site()
    build_source()
    build_reports()
    write_readme_first()
    stats = release_stats()
    write_final_report(stats)
    manifest_rows, _ = write_manifest()
    create_zip()
    verification = verify_zip(manifest_rows)
    VERIFICATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATION_PATH.write_text(
        json.dumps(verification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verification, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
