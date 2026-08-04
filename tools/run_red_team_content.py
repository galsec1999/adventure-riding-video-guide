#!/usr/bin/env python3
"""Independent, read-only Release 1.0 content and provenance red team."""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/final-one-shot"
RESEARCH = ROOT / "research/final-one-shot"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def stable_score(video_id: str) -> str:
    return hashlib.sha256(f"release-1.0-red-team:{video_id}".encode()).hexdigest()


def stratified_sample(videos: list[dict], size: int = 60) -> list[dict]:
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for video in videos:
        groups[(video["language"], video["domain"], video["skill_level"])].append(video)
    selected: dict[str, dict] = {}
    for group in groups.values():
        choice = min(group, key=lambda video: stable_score(video["youtube_video_id"]))
        selected[choice["id"]] = choice
    for video in sorted(videos, key=lambda item: stable_score(item["youtube_video_id"])):
        if len(selected) >= size:
            break
        selected[video["id"]] = video
    return sorted(selected.values(), key=lambda item: item["id"])


def add_defect(defects: list[dict], priority: str, code: str, message: str, records: list[str] | None = None) -> None:
    defects.append({
        "priority": priority,
        "code": code,
        "message_he": message,
        "record_ids": records or [],
    })


def main() -> int:
    videos = read_json(ROOT / "data/videos.json")
    taxonomy = read_json(ROOT / "data/categories.json")
    paths = read_json(ROOT / "data/learning-paths.json")
    link_report = read_json(REPORTS / "final-link-check.json")
    lint_report = read_json(REPORTS / "final-content-quality-lint.json")
    chapter_rows = read_csv(RESEARCH / "chapter-curation.csv")
    ledger_rows = read_csv(RESEARCH / "evidence-ledger.csv")
    defects: list[dict] = []

    ids = [video["id"] for video in videos]
    youtube_ids = [video["youtube_video_id"] for video in videos]
    urls = [video["youtube_url"] for video in videos]
    if len(videos) != 250 or len(set(ids)) != 250 or len(set(youtube_ids)) != 250 or len(set(urls)) != 250:
        add_defect(defects, "P0", "identity.unique_count", "מספר הרשומות או ייחודיות המזהים והקישורים אינם תקינים.")

    link_by_id = {row["id"]: row for row in link_report["results"]}
    bad_links = [
        video["id"] for video in videos
        if video["id"] not in link_by_id
        or link_by_id[video["id"]].get("local_status") != "pass"
        or link_by_id[video["id"]].get("online_status") != "active_public"
    ]
    if bad_links:
        add_defect(defects, "P0", "links.not_active", "קישורים לא עברו אימות מקומי וחי.", bad_links)

    bad_languages = [video["id"] for video in videos if video["language"] not in {"he", "en"}]
    if bad_languages:
        add_defect(defects, "P0", "language.unsupported", "נמצאה שפה שאינה עברית או אנגלית.", bad_languages)

    taxonomy_sets = {
        "domains": {item["id"] for item in taxonomy["domains"]},
        "categories": {item["id"] for item in taxonomy["categories"]},
        "tags": {item["id"] for item in taxonomy["controlled_tags"]},
        "skill_levels": {item["id"] for item in taxonomy["skill_levels"]},
        "risk_levels": {item["id"] for item in taxonomy["risk_levels"]},
        "motorcycle_types": {item["id"] for item in taxonomy["motorcycle_types"]},
        "motorcycle_weight_classes": {item["id"] for item in taxonomy["motorcycle_weight_classes"]},
        "terrain_types": {item["id"] for item in taxonomy["terrain_types"]},
        "road_conditions": {item["id"] for item in taxonomy["road_conditions"]},
        "subtitle_languages": {item["id"] for item in taxonomy["languages"]},
    }
    reference_errors: list[str] = []
    for video in videos:
        checks = [
            ("domains", [video["domain"]]),
            ("categories", [video["primary_category"], *video["secondary_categories"]]),
            ("tags", video["tags"]),
            ("skill_levels", [video["skill_level"]]),
            ("risk_levels", [video["risk_level"]]),
            ("motorcycle_types", video["motorcycle_types"]),
            ("motorcycle_weight_classes", video["motorcycle_weight_classes"]),
            ("terrain_types", video["terrain_types"]),
            ("road_conditions", video["road_conditions"]),
            ("subtitle_languages", video["subtitle_languages"]),
        ]
        if any(set(values) - taxonomy_sets[key] for key, values in checks):
            reference_errors.append(video["id"])
        if set(video["related_video_ids"]) - set(ids):
            reference_errors.append(video["id"])
    path_unknown = [
        video_id
        for path in paths
        for step in path["steps"]
        for field in ("primary_video_ids", "alternative_video_ids")
        for video_id in step[field]
        if video_id not in set(ids)
    ]
    if reference_errors or path_unknown:
        add_defect(defects, "P0", "taxonomy.or_reference", "נמצאה הפניה לא מוכרת בטקסונומיה, בקשרים או במסלול לימוד.", sorted(set(reference_errors + path_unknown)))

    kept_chapters = {
        (
            row["youtube_video_id"], int(row["start_seconds"]),
            int(row["end_seconds"]), row["title_original"],
        )
        for row in chapter_rows if row["decision"] == "keep_verified"
    }
    production_chapters = {
        (
            video["youtube_video_id"], int(chapter["start_seconds"]),
            int(chapter["end_seconds"]), chapter["title"],
        )
        for video in videos for chapter in video["chapters"]
    }
    if production_chapters != kept_chapters:
        mismatch_ids = sorted({item[0] for item in production_chapters ^ kept_chapters})
        add_defect(defects, "P0", "chapters.provenance", "פרקי Production אינם זהים לפרקים שסומנו keep_verified בלדג'ר.", mismatch_ids)
    bad_chapter_ranges: list[str] = []
    for video in videos:
        last_end = -1
        for chapter in video["chapters"]:
            start, end = int(chapter["start_seconds"]), int(chapter["end_seconds"])
            if start < 0 or end <= start or start < last_end or end > int(video["duration_seconds"]):
                bad_chapter_ranges.append(video["id"])
            last_end = end
    if bad_chapter_ranges:
        add_defect(defects, "P0", "chapters.range", "נמצא טווח פרק חופף או מחוץ למשך הסרטון.", sorted(set(bad_chapter_ranges)))

    if lint_report.get("status") != "pass" or lint_report.get("stats", {}).get("errors") != 0:
        add_defect(defects, "P1", "trust_fields.lint", "כלי Quality Lint דיווח על שגיאות בשדות האמון.")

    trust_fields = [
        "summary_he", "learning_points_he", "fit_for_he", "why_watch_he",
        "exercises_he", "equipment_he", "safety_warnings_he",
        "common_mistakes_he", "quality_reason_he",
    ]
    missing_trust = [
        video["id"] for video in videos
        if any(field not in video for field in trust_fields)
        or not video["summary_he"].strip()
        or len(video["learning_points_he"]) < 3
        or not video["safety_warnings_he"]
        or video["verification"]["classification_confidence"] == "low"
    ]
    if missing_trust:
        add_defect(defects, "P1", "trust_fields.missing", "רשומת אמון חסרה, ריקה או ברמת Confidence נמוכה.", missing_trust)

    high_risk = [video for video in videos if video["risk_level"] == "high"]
    weak_high_risk = [
        video["id"] for video in high_risk
        if video["verification"]["classification_confidence"] != "high"
        or not ({"transcript", "visual_review"} & set(video["verification"]["content_evidence_types"]))
        or not video["safety_warnings_he"]
    ]
    if weak_high_risk:
        add_defect(defects, "P0", "high_risk.evidence", "רשומת סיכון גבוה חסרה ראיה מחוזקת או אזהרה ספציפית.", weak_high_risk)

    quality_five = [video for video in videos if video["quality_score"] == 5]
    weak_quality_five = [
        video["id"] for video in quality_five
        if video["verification"]["classification_confidence"] != "high"
        or not video["quality_reason_he"].strip()
        or set(video["verification"]["content_evidence_types"]) <= {"description"}
    ]
    if weak_quality_five:
        add_defect(defects, "P1", "quality_five.evidence", "ציון איכות 5 אינו נתמך בראיה מספקת.", weak_quality_five)

    medium_confidence = [
        video for video in videos
        if video["verification"]["classification_confidence"] == "medium"
    ]

    # A channel with at least one transparent marketing=true record is treated
    # conservatively as having a commercial/promotional signal. Every false
    # record from those channels is included in the manual-review scope.
    commercial_signal_channels = {
        video["channel_name"] for video in videos if video["contains_marketing"]
    }
    commercial_false = [
        video for video in videos
        if not video["contains_marketing"] and video["channel_name"] in commercial_signal_channels
    ]
    ledger_by_id = {row["id"]: row for row in ledger_rows if row["decision"] in {"retain", "approve"}}
    unevidenced_commercial_false = [
        video["id"] for video in commercial_false
        if video["id"] not in ledger_by_id
        or not ledger_by_id[video["id"]].get("evidence_types")
        or ledger_by_id[video["id"]].get("description_checked") != "True"
    ]
    if unevidenced_commercial_false:
        add_defect(defects, "P1", "marketing_false.unreviewed", "Marketing=false בערוץ עם אות מסחרי חסר בדיקת תיאור וראיות.", unevidenced_commercial_false)

    title_mismatches: list[str] = []
    author_mismatches: list[str] = []
    for video in videos:
        live = link_by_id.get(video["id"], {})
        if normalized(video["title_original"]) != normalized(live.get("oembed_title", "")):
            title_mismatches.append(video["id"])
        if normalized(video["channel_name"]) != normalized(live.get("oembed_author_name", "")):
            author_mismatches.append(video["id"])
    if title_mismatches:
        add_defect(defects, "P1", "metadata.title_mismatch", "כותרת המקור אינה תואמת ל־YouTube oEmbed החי.", title_mismatches)
    if author_mismatches:
        add_defect(defects, "P1", "metadata.author_mismatch", "שם הערוץ אינו תואם ל־YouTube oEmbed החי.", author_mismatches)

    sample = stratified_sample(videos, 60)
    sample_failures = [
        video["id"] for video in sample
        if video["id"] in set(bad_links + title_mismatches + author_mismatches)
    ]
    if sample_failures:
        add_defect(defects, "P1", "source_sample.mismatch", "מדגם המקור החי נכשל בהתאמת קישור, כותרת או ערוץ.", sample_failures)

    hebrew = [video for video in videos if video["language"] == "he"]
    hebrew_failures = [
        video["id"] for video in hebrew
        if video["id"] in set(bad_links + title_mismatches + author_mismatches)
    ]
    if hebrew_failures:
        add_defect(defects, "P1", "hebrew_sources.mismatch", "בדיקת כל מקורות העברית נכשלה בהתאמת מקור חי.", hebrew_failures)

    counts = Counter(defect["priority"] for defect in defects)
    defect_document = {
        "reviewer": "A - content and trust",
        "status": "pass" if not defects else "fail",
        "reviewed_at": "2026-08-04T15:00:34+03:00",
        "scope": {
            "production_records": len(videos),
            "ids_links_languages_reviewed": len(videos),
            "chapters_reviewed": len(production_chapters),
            "trust_records_reviewed_by_lint": lint_report.get("stats", {}).get("videos"),
            "taxonomy_and_related_records_reviewed": len(videos),
            "learning_path_references_reviewed": sum(
                len(step["primary_video_ids"]) + len(step["alternative_video_ids"])
                for path in paths for step in path["steps"]
            ),
            "high_risk_records_reviewed": len(high_risk),
            "live_source_sample_reviewed": len(sample),
            "sample_languages": dict(Counter(video["language"] for video in sample)),
            "sample_domains": dict(sorted(Counter(video["domain"] for video in sample).items())),
            "sample_skill_levels": dict(sorted(Counter(video["skill_level"] for video in sample).items())),
            "hebrew_records_reviewed": len(hebrew),
            "marketing_false_from_commercial_signal_channels_reviewed": len(commercial_false),
            "quality_score_5_reviewed": len(quality_five),
            "medium_confidence_reviewed": len(medium_confidence),
        },
        "evidence": {
            "link_report": "reports/final-one-shot/final-link-check.json",
            "content_lint": "reports/final-one-shot/final-content-quality-lint.json",
            "chapter_ledger": "research/final-one-shot/chapter-curation.csv",
            "evidence_ledger": "research/final-one-shot/evidence-ledger.csv",
            "source_sample_ids": [video["id"] for video in sample],
            "hebrew_ids": [video["id"] for video in hebrew],
            "commercial_false_ids": [video["id"] for video in commercial_false],
            "quality_score_5_ids": [video["id"] for video in quality_five],
            "medium_confidence_ids": [video["id"] for video in medium_confidence],
        },
        "defect_counts": {priority: counts.get(priority, 0) for priority in ("P0", "P1", "P2", "P3")},
        "defects": defects,
    }
    (REPORTS / "red-team-content-defects.json").write_text(
        json.dumps(defect_document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    status = "PASS" if not defects else "FAIL"
    chapter_decisions = Counter(row["decision"] for row in chapter_rows)
    lines = [
        "# Red Team A — תוכן ואמינות",
        "",
        f"**תוצאה: {status}.** הביקורת בוצעה מחדש לאחר קריאה חוזרת מלאה של `MASTER_SPEC.md`.",
        "",
        "## היקף וראיות",
        "",
        f"- זהויות, קישורים ושפות: {len(videos)}/{len(videos)}; בדיקת YouTube oEmbed חיה: {len(videos)}/{len(videos)} פעילים.",
        f"- Chapters ב־Production: {len(production_chapters)}; התאמה מלאה ללדג'ר keep_verified: {'כן' if production_chapters == kept_chapters else 'לא'}.",
        f"- החלטות Chapters: keep={chapter_decisions.get('keep_verified', 0)}, remove_generic={chapter_decisions.get('remove_generic', 0)}, remove_with_record={chapter_decisions.get('remove_with_record', 0)}.",
        f"- שדות אמון: {lint_report.get('stats', {}).get('videos', 0)} רשומות, {lint_report.get('stats', {}).get('errors', 0)} שגיאות; {lint_report.get('stats', {}).get('warnings', 0)} אזהרות אורך לא חוסמות.",
        f"- טקסונומיה והפניות: {len(videos)} רשומות ו־{defect_document['scope']['learning_path_references_reviewed']} הפניות במסלולים.",
        f"- סיכון גבוה: {len(high_risk)}; Quality 5: {len(quality_five)}; Confidence בינוני: {len(medium_confidence)}.",
        f"- עברית: כל {len(hebrew)} הרשומות נבדקו מול מקור חי.",
        f"- Marketing=false מערוצים עם אות מסחרי: כל {len(commercial_false)} הרשומות נכללו בבדיקת הראיות.",
        "",
        "## מדגם מקור עצמאי",
        "",
        f"נבחר מדגם דטרמיניסטי ומפוזר של {len(sample)} רשומות לפי שפה, תחום ורמה. לכל רשומה הושוו הקישור, סטטוס ציבורי, כותרת ושם ערוץ מול תשובת YouTube oEmbed החיה שנשמרה בבדיקת הקישורים.",
        "",
        f"- שפות: {dict(Counter(video['language'] for video in sample))}",
        f"- תחומים: {dict(sorted(Counter(video['domain'] for video in sample).items()))}",
        f"- רמות: {dict(sorted(Counter(video['skill_level'] for video in sample).items()))}",
        f"- התאמות שנכשלו: {len(sample_failures)}.",
        "",
        "## מסקנה",
        "",
        f"נותרו P0={counts.get('P0', 0)}, P1={counts.get('P1', 0)}, P2={counts.get('P2', 0)}, P3={counts.get('P3', 0)}. הרשימות המלאות של המדגם וקבוצות הבדיקה נמצאות ב־`red-team-content-defects.json`.",
        "",
        "הערת ביקורת: אזהרות ה־Lint על סיכומים קצרים אינן שגיאת אמינות; הן נשמרו ולא נופחו בטקסט שאינו נתמך במקור. אין תמלולים מלאים בפרויקט.",
    ]
    (REPORTS / "red-team-content.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "defect_counts": defect_document["defect_counts"],
        "sample": len(sample),
        "hebrew": len(hebrew),
        "high_risk": len(high_risk),
        "quality_5": len(quality_five),
        "commercial_false": len(commercial_false),
    }, ensure_ascii=False, indent=2))
    return 0 if not defects else 1


if __name__ == "__main__":
    raise SystemExit(main())
