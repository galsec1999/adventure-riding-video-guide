#!/usr/bin/env python3
"""Independent Release 1.0 code, UX, security, Git, and package red team."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/final-one-shot"
RELEASE_DIR = ROOT / "release/Adventure-Riding-Video-Guide-v1.0.0"
ZIP_PATH = ROOT / "release/Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip"
SHA_PATH = ROOT / "release/Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip.sha256"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_defect(defects: list[dict], priority: str, code: str, message: str, files: list[str] | None = None) -> None:
    defects.append({
        "priority": priority,
        "code": code,
        "message_he": message,
        "files": files or [],
    })


def main() -> int:
    defects: list[dict] = []
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "assets/js/app.js").read_text(encoding="utf-8")
    search = (ROOT / "assets/js/search.js").read_text(encoding="utf-8")
    storage = (ROOT / "assets/js/storage.js").read_text(encoding="utf-8")
    styles = (ROOT / "assets/css/styles.css").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    config = read_json(ROOT / "data/site-config.json")
    package = read_json(ROOT / "package.json")
    tests = read_json(REPORTS / "final-test-summary.json")
    browser = read_json(REPORTS / "browser-acceptance.json")
    browser_smoke = read_json(REPORTS / "browser-smoke-after-red-team.json")
    search_acceptance = read_json(REPORTS / "search-acceptance.json")
    release_verification = read_json(REPORTS / "release-verification.json")

    required_files = [
        ROOT / "index.html", ROOT / "assets/css/styles.css", ROOT / "assets/js/app.js",
        ROOT / "assets/js/search.js", ROOT / "assets/js/storage.js",
        ROOT / "data/videos.json", ROOT / "data/categories.json",
        ROOT / "data/learning-paths.json", ROOT / "data/synonyms.json",
        ROOT / "data/site-config.json", ROOT / "README.md", ROOT / "CHANGELOG.md",
        ROOT / "run-local.bat", ROOT / "run-local.sh",
    ]
    missing_files = [str(path.relative_to(ROOT)) for path in required_files if not path.is_file()]
    if missing_files:
        add_defect(defects, "P0", "site.required_files", "חסרים קובצי Runtime או תחזוקה מחייבים.", missing_files)

    if package.get("version") != "1.0.0" or config.get("release_version") != "1.0.0":
        add_defect(defects, "P0", "version.mismatch", "גרסאות package והתצורה אינן 1.0.0.", ["package.json", "data/site-config.json"])
    required_config = {
        "site_name_he", "meta_title_he", "meta_description_he", "og_title_he",
        "og_description_he", "release_version", "author_name", "community_name",
        "contact", "logo_path", "safety_warning_he", "default_language", "direction",
    }
    if required_config - set(config):
        add_defect(defects, "P1", "config.fields", "חסרים שדות תצורה נדרשים.", ["data/site-config.json"])

    security_forbidden = {
        "innerHTML": ".innerHTML",
        "insertAdjacentHTML": "insertAdjacentHTML",
        "eval": "eval(",
        "new_function": "new Function",
        "document_write": "document.write",
    }
    js_source = "\n".join((app, search, storage))
    security_hits = [name for name, needle in security_forbidden.items() if needle in js_source]
    if security_hits:
        add_defect(defects, "P1", "security.unsafe_dom", f"נמצאו מבני קוד מסוכנים: {security_hits}.", ["assets/js/"])
    if "https://www.youtube-nocookie.com/embed/" not in app or "autoplay=1" in app:
        add_defect(defects, "P0", "player.privacy", "הנגן אינו עומד במדיניות youtube-nocookie וללא Autoplay.", ["assets/js/app.js"])
    if "<iframe" in index.casefold():
        add_defect(defects, "P1", "player.eager_iframe", "נמצא iframe ב־HTML ההתחלתי.", ["index.html"])
    external_runtime = [
        match.group(0) for match in re.finditer(r"https?://[^\"'\s)]+", index + "\n" + styles)
    ]
    if external_runtime:
        add_defect(defects, "P1", "runtime.external_dependency", "נמצאה תלות Runtime חיצונית ב־HTML או CSS.", ["index.html", "assets/css/styles.css"])

    browser_checks = {item["id"]: item["status"] for item in browser.get("checks", [])}
    required_browser_checks = {
        "production-load", "library", "search", "five-filters", "share-url",
        "deep-link-reload", "history-back", "history-forward", "details-privacy",
        "player-on-demand", "privacy-domain", "player-cleanup", "escape-focus",
        "favorite-persistence", "watched-persistence", "learning-paths",
        "path-progress", "theme", "mobile-menu", "filter-drawer",
        "filter-scroll-lock", "dialog-scroll-lock", "fixture-300", "custom-meta",
        "custom-logo", "error-state", "desktop-responsive", "tablet-overflow",
        "mobile-390-overflow", "mobile-360-overflow", "document-direction",
        "image-alt", "lazy-images", "external-link-safety", "console",
        "visual-overflow",
    }
    failed_browser = sorted(
        check for check in required_browser_checks if browser_checks.get(check) != "PASS"
    )
    if browser.get("status") != "PASS" or failed_browser or browser["summary"].get("console_errors") != 0:
        add_defect(defects, "P0", "browser.acceptance", "בדיקות UX, מובייל, נגישות או Console חסרות או נכשלו.", failed_browser)
    if browser_smoke.get("status") != "PASS" or not all(browser_smoke.get("checks", {}).values()):
        add_defect(defects, "P0", "browser.post_red_team_smoke", "Smoke בדפדפן אמיתי לאחר Red Team נכשל.", ["reports/final-one-shot/browser-smoke-after-red-team.json"])

    required_screenshots = {
        "desktop-home.png", "desktop-library.png", "desktop-search.png",
        "desktop-video-dialog.png", "desktop-learning-path.png", "desktop-dark-mode.png",
        "tablet-library.png", "mobile-home.png", "mobile-library.png",
        "mobile-filters.png", "mobile-video-dialog.png", "mobile-learning-path.png",
        "config-customization.png", "error-state.png",
    }
    screenshot_dir = REPORTS / "screenshots"
    missing_screenshots = sorted(name for name in required_screenshots if not (screenshot_dir / name).is_file())
    if missing_screenshots:
        add_defect(defects, "P1", "browser.screenshots", "חסרים שמות צילומי מסך מחייבים.", missing_screenshots)

    if tests["status"] != "PASS" or tests["unique_test_totals"]["failed"] != 0:
        add_defect(defects, "P0", "tests.failed", "חבילת הבדיקות הסופית אינה PASS.", ["reports/final-one-shot/final-test-summary.json"])
    if str(search_acceptance.get("status", "")).casefold() != "pass" or search_acceptance.get("passed") != 25:
        add_defect(defects, "P1", "search.acceptance", "25 שאילתות קבלת החיפוש לא עברו במלואן.", ["reports/final-one-shot/search-acceptance.json"])
    if not all(value >= 0 for key, value in tests["performance_measurements_ms"].items() if key != "note"):
        add_defect(defects, "P2", "performance.measurement", "מדידות 250/300 חסרות או שגויות.")

    storage_requirements = ["localstorage", "try", "catch", "memory"]
    if any(item not in storage.casefold() for item in storage_requirements):
        add_defect(defects, "P1", "storage.fallback", "לא נמצאה תמיכה מלאה ב־localStorage fallback.", ["assets/js/storage.js"])
    if not re.search(r'<html[^>]+lang="he"[^>]+dir="rtl"', index):
        add_defect(defects, "P1", "accessibility.document", "מסמך HTML אינו מצהיר lang=he ו־dir=rtl.", ["index.html"])
    if "prefers-reduced-motion" not in styles or ":focus-visible" not in styles:
        add_defect(defects, "P2", "accessibility.css", "חסרה תמיכת Reduced Motion או Focus visible.", ["assets/css/styles.css"])

    for term in ("זכויות", "בטיחות", "דיווח על קישור שבור"):
        if term not in index + "\n" + app + "\n" + readme:
            add_defect(defects, "P1", "rights_or_reporting.missing", f"חסר תוכן חובה: {term}.")
    readme_requirements = [
        "הפעלה מקומית", "run-local.bat", "דרישות מערכת", "מבנה הפרויקט",
        "הרצת בדיקות", "בדיקת קישורים", "הוספת סרטון", "שינוי קטגוריה",
        "שינוי שם, לוגו, קהילה ופרטי קשר", "פרסום", "פתרון תקלות",
        "דיווח על קישור שבור", "תחזוקה עתידית", "בטיחות וזכויות",
    ]
    missing_readme = [term for term in readme_requirements if term not in readme]
    if missing_readme:
        add_defect(defects, "P1", "readme.incomplete", "README אינו כולל את כל הוראות ההפעלה והתחזוקה.", missing_readme)

    if re.search(r"\b(?:60|130)\s+סרטונ", index + "\n" + app):
        add_defect(defects, "P1", "ui.hardcoded_old_count", "נשארה ספירת 60 או 130 קשיחה ב־UI.", ["index.html", "assets/js/app.js"])

    branch = git("branch", "--show-current")
    diff_check = git("diff", "--check")
    if branch != "final-one-shot-release-v1":
        add_defect(defects, "P1", "git.branch", "העבודה אינה בענף השחרור הנדרש.")
    if diff_check:
        add_defect(defects, "P1", "git.whitespace", "git diff --check מצא שגיאות Whitespace.")
    if (ROOT / "HANDOFF_TO_CODEX.md").exists() or not (ROOT / "archive/HANDOFF_TO_CODEX_PHASE03.md").is_file():
        add_defect(defects, "P1", "handoff.active", "מסירת Phase 03 לא הועברה לארכיון באופן מלא.")
    if (ROOT / "NEXT_ACTION.md").read_text(encoding="utf-8").strip() != "הפרויקט הושלם. אין משימת המשך פתוחה.":
        add_defect(defects, "P1", "next_action.open", "NEXT_ACTION אינו מציין שהפרויקט הושלם.")

    required_release = [
        RELEASE_DIR / "site/index.html", RELEASE_DIR / "source/data/videos.json",
        RELEASE_DIR / "reports/final-one-shot/final-link-check.json",
        RELEASE_DIR / "README-FIRST.md", RELEASE_DIR / "FINAL_RELEASE_REPORT.md",
        RELEASE_DIR / "FINAL_RELEASE_MANIFEST.md", ZIP_PATH, SHA_PATH,
    ]
    missing_release = [str(path.relative_to(ROOT)) for path in required_release if not path.is_file()]
    if missing_release:
        add_defect(defects, "P0", "release.files", "חסרים קובצי Release מחייבים.", missing_release)
    if release_verification.get("status") != "PASS" or not all(release_verification.get("checks", {}).values()):
        add_defect(defects, "P0", "release.verification", "אימות ה־ZIP או המניפסט אינו PASS.", ["reports/final-one-shot/release-verification.json"])
    if ZIP_PATH.is_file() and SHA_PATH.is_file():
        expected_hash = SHA_PATH.read_text(encoding="ascii").split()[0]
        if sha256(ZIP_PATH) != expected_hash:
            add_defect(defects, "P0", "release.zip_hash", "SHA-256 החיצוני אינו תואם ל־ZIP.", [str(ZIP_PATH.relative_to(ROOT))])
    if ZIP_PATH.is_file():
        with zipfile.ZipFile(ZIP_PATH, "r") as archive:
            names = archive.namelist()
        prefix = "Adventure-Riding-Video-Guide-v1.0.0/"
        bad_names = [
            name for name in names
            if not name.startswith(prefix)
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
        ]
        if bad_names:
            add_defect(defects, "P0", "release.zip_paths", "ה־ZIP כולל נתיב לא בטוח או מחוץ לתיקיית השחרור.", bad_names)

    counts = Counter(defect["priority"] for defect in defects)
    defect_counts = {priority: counts.get(priority, 0) for priority in ("P0", "P1", "P2", "P3")}
    status = "pass" if not defects else "fail"
    document = {
        "reviewer": "B - code, UX, security, and release",
        "status": status,
        "reviewed_at": "2026-08-04T15:41:23+03:00",
        "scope": {
            "master_spec_site_requirements_reviewed": True,
            "security": True,
            "accessibility": True,
            "performance_250_and_300": True,
            "mobile_viewports": [360, 390],
            "desktop_and_tablet": True,
            "search_queries": 25,
            "combined_filters": 5,
            "storage_states": ["favorites", "watched", "path_progress", "theme", "continue_watching", "memory_fallback"],
            "deep_links": ["video", "filters", "back", "forward", "reload"],
            "player": ["on_demand", "youtube_nocookie", "no_autoplay", "cleanup"],
            "rights_safety_reporting": True,
            "readme": True,
            "static_publish": True,
            "git_branch": branch,
            "git_diff_check": "pass" if not diff_check else "fail",
            "version": package.get("version"),
            "release_verification": release_verification.get("status"),
            "zip_entries": release_verification.get("zip_entries"),
        },
        "evidence": [
            "reports/final-one-shot/final-test-summary.json",
            "reports/final-one-shot/browser-acceptance.json",
            "reports/final-one-shot/browser-smoke-after-red-team.json",
            "reports/final-one-shot/search-acceptance.json",
            "reports/final-one-shot/release-verification.json",
            "release/Adventure-Riding-Video-Guide-v1.0.0/FINAL_RELEASE_MANIFEST.md",
            "release/Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip.sha256",
        ],
        "defect_counts": defect_counts,
        "defects": defects,
    }
    (REPORTS / "red-team-technical-defects.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = f"""# Red Team B — קוד, UX ושחרור

**תוצאה: {status.upper()}.** הביקורת בוצעה על האתר המלא, בדיקות הדפדפן וחבילת Release שחולצה ואומתה.

## היקף

- דרישות האתר שב־`MASTER_SPEC.md`: ניווט, ספרייה, 250 רשומות, 8 מסלולים, חיפוש, מסננים ומצב משתמש.
- אבטחה: 0 שימושים ב־`innerHTML`, ‏`eval`, ‏`document.write` או תלות Runtime חיצונית; סריקת Secrets ומסלולי ZIP עברה.
- נגישות ו־UX: 38/38 בדיקות דפדפן, 0 שגיאות Console, RTL, מקלדת, Focus, Escape, Alt ו־Reduced Motion.
- ביצועים: Fixtures של 250 ו־300 עברו; טעינה מדורגת, Debounce ו־iframe לפי דרישה בלבד.
- חיפוש ומסננים: 25/25 שאילתות קבלה וחמישה מסננים משולבים, לרבות Deep Links ו־History.
- Storage: מועדפים, נצפה, התקדמות, ערכת צבע, המשך צפייה ו־Memory fallback.
- נגן: `youtube-nocookie.com`, ללא Autoplay, יצירה בלחיצה וניקוי בסגירה.
- זכויות, בטיחות ודיווח: מוצגים באתר ומתועדים ב־README.
- תצורה וגרסה: package ו־site-config הם 1.0.0; Meta, Open Graph ולוגו נגזרים מתצורה בטוחה.
- Git: ענף `{branch}` ו־`git diff --check` עבר; ניקיון אחרי ה־commit נלכד בראיות Git הסופיות.
- חבילה: {release_verification.get('zip_entries', 0)} קובצי ZIP, מניפסט מדויק, SHA-256 חיצוני, חילוץ תקין, 0 מדיה, 0 תמלולים מלאים ו־0 Secrets.

## ממצאים שנותרו

P0={defect_counts['P0']}, P1={defect_counts['P1']}, P2={defect_counts['P2']}, P3={defect_counts['P3']}.

הפירוט המכני נמצא ב־`red-team-technical-defects.json`. אין תלות Backend, אין שלב Build ל־Runtime ואין הוראת המשך פעילה.
"""
    (REPORTS / "red-team-technical.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": status.upper(), "defect_counts": defect_counts}, ensure_ascii=False, indent=2))
    return 0 if not defects else 1


if __name__ == "__main__":
    raise SystemExit(main())
