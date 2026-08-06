#!/usr/bin/env python3
"""Audit-only content-quality checks for the Adventure Riding Video Guide.

This module never edits project data. It reads the curated JSON files, records
source hashes before and after the audit, and produces machine-readable and HTML
reports. The checks deliberately favour visible review queues over silent
normalisation: a finding is either blocking or explicitly informational.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEOS = ROOT / "data" / "videos.json"
DEFAULT_PATHS = ROOT / "data" / "learning-paths.json"
DEFAULT_LEDGER = ROOT / "research" / "final-one-shot" / "evidence-ledger.csv"
DEFAULT_REPORT = ROOT / "reports" / "final-one-shot" / "content-quality-lint.json"
DEFAULT_HTML = ROOT / "reports" / "final-one-shot" / "content-quality-lint.html"

TEXT_FIELDS = (
    "summary_he",
    "why_watch_he",
    "fit_for_he",
    "quality_reason_he",
)
LIST_TEXT_FIELDS = (
    "learning_points_he",
    "exercises_he",
    "equipment_he",
    "safety_warnings_he",
    "common_mistakes_he",
)
NEAR_DUPLICATE_THRESHOLD = 0.88
SUMMARY_MIN_WORDS = 45
SUMMARY_MAX_WORDS = 100

GENERIC_CHAPTER_RE = re.compile(
    r"^(?:intro(?:duction)?|opening|welcome|news|update|outro|ending|"
    r"conclusion|wrap[ -]?up|subscribe|sponsor(?:ship)?|ad(?:vertisement)?|"
    r"promo(?:tion)?|giveaway|thanks?|credits?|סיום|פתיח|מבוא|חסות|פרסומת)$",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"(?:lorem ipsum|placeholder|todo|tbd|dummy|example\.com|youtube\.com/watch\?v=(?:x{6,}|0{6,}))",
    re.IGNORECASE,
)
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
TOKEN_RE = re.compile(r"[\w\u0590-\u05ff׳״'\-]+", re.UNICODE)

# These fragments identify the one-time Wave 1 template families. They are
# duplicated here solely for auditing; the migration script is quarantined and
# is never imported or executed by this linter.
LEGACY_WHY_FRAGMENTS = (
    "הסרטון מחבר בין",
    "הערך המרכזי כאן הוא ההסבר המעשי של",
    "כדאי לצפות כדי להבין",
    "זהו מקור ממוקד למי שרוצה לפרק את הנושא לשלושה רכיבים",
    "הצפייה מועילה במיוחד משום שהיא מציבה את",
    "במקום טיפ יחיד, הסרטון מציג רצף שמתחיל ב־",
    "התרומה הייחודית של הסרטון היא החיבור בין",
    "הסרטון עוזר לזהות בפועל",
)
LEGACY_FIT_FRAGMENTS = (
    "מתאים לרוכבים בתחילת הדרך על אופנועי",
    "קהל היעד הוא",
    "מיועד ל",
    "רלוונטי ל",
    "הסרטון מתאים ל",
    "ההתאמה הטובה ביותר היא ל",
)
LEGACY_QUALITY_FRAGMENTS = (
    "הציון ",
    " מאמתים כיסוי ממשי של ",
    "חוזקת הסרטון היא פירוק ברור של",
    "הסרטון מציע ערך לימודי קונקרטי סביב",
    "מוצדק משום שהמקור מדגים או מסביר",
    "הראיות (",
)
LEGACY_LIMITATION_FRAGMENTS = (
    "האימות נשען על תיאור המקור בלבד, ולכן רמת הביטחון נשארת בינונית.",
    "קיימים חסות, קידום או קישורים מסחריים, ולכן יש להפריד אותם מן ההדרכה.",
    "אין חלוקת פרקים מתועדת, ולכן אין לייחס לסרטון נקודות זמן פרטניות.",
    "הסרטון עוסק בנושא מוגדר ואינו מחליף הדרכה מעשית מלאה בתנאים משתנים.",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    record_id: str
    field: str
    message: str
    evidence: dict[str, Any] | None = None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_ledger(path: Path) -> Any:
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    return load_json(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(value: str) -> str:
    value = value.casefold().replace("־", "-")
    value = re.sub(r"\b\d+(?:[.:]\d+)?\b", "#", value)
    value = re.sub(r"[^\w\u0590-\u05ff]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def count_words(value: str) -> int:
    return len(TOKEN_RE.findall(value))


def contains_hebrew(value: str) -> bool:
    return bool(HEBREW_RE.search(value))


def text_values(video: dict[str, Any], field: str) -> list[str]:
    value = video.get(field)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def add(
    findings: list[Finding],
    severity: str,
    code: str,
    video: dict[str, Any] | None,
    field: str,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    findings.append(
        Finding(
            severity=severity,
            code=code,
            record_id=(video or {}).get("id", "dataset"),
            field=field,
            message=message,
            evidence=evidence,
        )
    )


def find_exact_duplicates(
    videos: list[dict[str, Any]], findings: list[Finding]
) -> None:
    # Shared standard equipment and safety phrasing is intentional. Duplicate
    # detection therefore targets authored explanatory fields, learning points,
    # exercises and mistakes rather than mandated safety boilerplate.
    duplicate_fields = (*TEXT_FIELDS, "learning_points_he", "exercises_he")
    for field in duplicate_fields:
        occurrences: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for video in videos:
            for value in text_values(video, field):
                normalized = normalize_text(value)
                if len(normalized) >= 24:
                    occurrences[normalized].append((video["id"], value))
        for entries in occurrences.values():
            ids = sorted({record_id for record_id, _ in entries})
            if len(ids) < 2:
                continue
            sample = entries[0][1]
            for record_id in ids:
                add(
                    findings,
                    "error",
                    "text.exact_duplicate",
                    {"id": record_id},
                    field,
                    f"Exact text is reused by {len(ids)} records",
                    {"record_ids": ids, "sample": sample[:220]},
                )


def find_near_duplicates(
    videos: list[dict[str, Any]], findings: list[Finding]
) -> None:
    for field in TEXT_FIELDS:
        entries: list[tuple[str, str, str]] = []
        for video in videos:
            value = video.get(field)
            if isinstance(value, str):
                normalized = normalize_text(value)
                if len(normalized) >= 60:
                    entries.append((video["id"], value, normalized))
        for index, (left_id, left_raw, left) in enumerate(entries):
            for right_id, right_raw, right in entries[index + 1 :]:
                length_ratio = min(len(left), len(right)) / max(len(left), len(right))
                if length_ratio < 0.72:
                    continue
                ratio = SequenceMatcher(None, left, right, autojunk=False).ratio()
                if ratio < NEAR_DUPLICATE_THRESHOLD:
                    continue
                evidence = {
                    "other_record_id": right_id,
                    "similarity": round(ratio, 4),
                    "left": left_raw[:220],
                    "right": right_raw[:220],
                }
                add(
                    findings,
                    "error",
                    "text.near_duplicate",
                    {"id": left_id},
                    field,
                    f"Near-duplicate text ({ratio:.1%}) with {right_id}",
                    evidence,
                )


def find_legacy_templates(video: dict[str, Any], findings: list[Finding]) -> None:
    why = video.get("why_watch_he", "")
    points = video.get("learning_points_he", [])
    if (
        isinstance(why, str)
        and any(fragment in why for fragment in LEGACY_WHY_FRAGMENTS)
        and len(points) >= 3
        and all(str(point) in why for point in points[:3])
    ):
        add(
            findings,
            "error",
            "legacy.wave1_why_watch_template",
            video,
            "why_watch_he",
            "Text matches a quarantined Wave 1 template family",
        )

    fit = video.get("fit_for_he", "")
    if isinstance(fit, str) and any(fragment in fit for fragment in LEGACY_FIT_FRAGMENTS):
        weight_markers = ("משקל הייחוס", "במשקל", "משקל ")
        if any(marker in fit for marker in weight_markers):
            add(
                findings,
                "error",
                "legacy.wave1_fit_for_template",
                video,
                "fit_for_he",
                "Text matches a quarantined Wave 1 template family",
            )

    quality = video.get("quality_reason_he", "")
    if isinstance(quality, str) and any(
        fragment in quality for fragment in LEGACY_QUALITY_FRAGMENTS
    ):
        point_hits = sum(str(point) in quality for point in points[:2])
        if point_hits >= 2 and any(
            fragment in quality for fragment in LEGACY_LIMITATION_FRAGMENTS
        ):
            add(
                findings,
                "error",
                "legacy.wave1_quality_reason_template",
                video,
                "quality_reason_he",
                "Text matches a quarantined Wave 1 template family",
            )


def audit_video(video: dict[str, Any], findings: list[Finding]) -> None:
    language = video.get("language")
    if language not in {"he", "en"}:
        add(
            findings,
            "error",
            "language.unsupported",
            video,
            "language",
            f"Release 1.0 permits only he/en; found {language!r}",
        )

    for field in TEXT_FIELDS:
        value = video.get(field)
        if not isinstance(value, str) or not value.strip():
            add(findings, "error", "text.missing", video, field, "Required text is empty")
            continue
        if PLACEHOLDER_RE.search(value):
            add(findings, "error", "text.placeholder", video, field, "Placeholder-like text detected")
        if not contains_hebrew(value):
            add(findings, "error", "text.not_hebrew", video, field, "Hebrew explanatory text is required")

    for field in LIST_TEXT_FIELDS:
        values = text_values(video, field)
        for value in values:
            if PLACEHOLDER_RE.search(value):
                add(findings, "error", "text.placeholder", video, field, "Placeholder-like text detected")

    summary = video.get("summary_he", "")
    if isinstance(summary, str):
        words = count_words(summary)
        if words < SUMMARY_MIN_WORDS or words > SUMMARY_MAX_WORDS:
            add(
                findings,
                "warning",
                "summary.word_count",
                video,
                "summary_he",
                f"Summary has {words} words; expected {SUMMARY_MIN_WORDS}-{SUMMARY_MAX_WORDS}",
                {"word_count": words},
            )

    verification = video.get("verification") or {}
    evidence_types = set(verification.get("content_evidence_types") or [])
    confidence = verification.get("classification_confidence")
    if evidence_types == {"description"}:
        add(
            findings,
            "error",
            "evidence.description_only",
            video,
            "verification.content_evidence_types",
            "Content classification relies on description alone",
        )
    if confidence == "low":
        add(
            findings,
            "error",
            "evidence.low_confidence",
            video,
            "verification.classification_confidence",
            "Low-confidence records are not releasable",
        )
    if video.get("risk_level") == "high":
        if confidence != "high" or not evidence_types.intersection({"transcript", "visual_review"}):
            add(
                findings,
                "error",
                "evidence.high_risk_insufficient",
                video,
                "verification",
                "High-risk guidance requires high confidence and transcript or visual review",
                {"confidence": confidence, "evidence_types": sorted(evidence_types)},
            )

    chapters = video.get("chapters") or []
    for chapter_index, chapter in enumerate(chapters):
        title = str(chapter.get("title", "")).strip()
        if GENERIC_CHAPTER_RE.fullmatch(title):
            add(
                findings,
                "error",
                "chapters.generic",
                video,
                f"chapters[{chapter_index}].title",
                f"Generic/non-instructional chapter must be removed: {title!r}",
                {"start_seconds": chapter.get("start_seconds")},
            )

    if not video.get("related_video_ids"):
        add(
            findings,
            "error",
            "related.empty",
            video,
            "related_video_ids",
            "At least one curated related video is required",
        )

    find_legacy_templates(video, findings)


def audit_dataset(videos: list[dict[str, Any]], ledger: Any | None) -> dict[str, Any]:
    findings: list[Finding] = []
    for video in videos:
        audit_video(video, findings)
    find_exact_duplicates(videos, findings)
    find_near_duplicates(videos, findings)

    ids = [video.get("id") for video in videos]
    youtube_ids = [video.get("youtube_video_id") for video in videos]
    if len(set(ids)) != len(ids):
        add(findings, "error", "ids.duplicate_internal", None, "id", "Duplicate internal IDs detected")
    if len(set(youtube_ids)) != len(youtube_ids):
        add(findings, "error", "ids.duplicate_youtube", None, "youtube_video_id", "Duplicate YouTube IDs detected")

    channels = Counter(str(video.get("channel_name", "")) for video in videos)
    channel_total = len(videos) or 1
    for channel, count in channels.items():
        if count > 20:
            add(
                findings,
                "error",
                "diversity.channel_cap",
                None,
                "channel_name",
                f"Channel {channel!r} has {count} records; maximum is 20",
                {"channel": channel, "count": count},
            )
    top_two = sum(count for _, count in channels.most_common(2))
    if top_two / channel_total > 0.15:
        add(
            findings,
            "error",
            "diversity.top_two_share",
            None,
            "channel_name",
            f"Top two channels represent {top_two / channel_total:.1%}; maximum is 15%",
            {"top_two_count": top_two, "total": len(videos)},
        )

    ledger_ids: set[str] = set()
    if isinstance(ledger, dict):
        entries = ledger.get("records", ledger.get("entries", []))
    else:
        entries = ledger if isinstance(ledger, list) else []
    if isinstance(entries, list):
        ledger_ids = {
            str(entry.get("id"))
            for entry in entries
            if isinstance(entry, dict) and entry.get("id")
        }
    missing_ledger = sorted(set(str(item) for item in ids) - ledger_ids)
    if ledger is not None and missing_ledger:
        add(
            findings,
            "error",
            "ledger.missing_records",
            None,
            "evidence-ledger",
            f"Evidence ledger is missing {len(missing_ledger)} records",
            {"record_ids": missing_ledger},
        )

    serialized = [asdict(item) for item in findings]
    counts = Counter(item.severity for item in findings)
    codes = Counter(item.code for item in findings)
    return {
        "document_version": "1.0.0",
        "status": "pass" if counts["error"] == 0 else "fail",
        "policy": {
            "summary_word_range": [SUMMARY_MIN_WORDS, SUMMARY_MAX_WORDS],
            "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
            "allowed_languages": ["he", "en"],
            "high_risk_evidence": "high confidence plus transcript or visual_review",
            "audit_only": True,
        },
        "stats": {
            "videos": len(videos),
            "unique_internal_ids": len(set(ids)),
            "unique_youtube_video_ids": len(set(youtube_ids)),
            "channels": len(channels),
            "top_two_channel_share": round(top_two / channel_total, 6),
            "errors": counts["error"],
            "warnings": counts["warning"],
            "findings": len(findings),
            "findings_by_code": dict(sorted(codes.items())),
        },
        "findings": serialized,
    }


def render_html(report: dict[str, Any]) -> str:
    status = report["status"]
    rows = []
    for finding in report["findings"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(finding['severity'])}</td>"
            f"<td>{html.escape(finding['code'])}</td>"
            f"<td><code>{html.escape(finding['record_id'])}</code></td>"
            f"<td><code>{html.escape(finding['field'])}</code></td>"
            f"<td>{html.escape(finding['message'])}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or '<tr><td colspan="5">No findings</td></tr>'
    stats = report["stats"]
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ביקורת איכות תוכן — {html.escape(status.upper())}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #18211d; background: #f7faf8; }}
    h1 {{ margin-bottom: .25rem; }}
    .status {{ display: inline-block; padding: .35rem .7rem; border-radius: 999px; background: {'#d9f5df' if status == 'pass' else '#ffe0dc'}; }}
    table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 1.5rem; }}
    th, td {{ border: 1px solid #ccd7d0; padding: .55rem; text-align: right; vertical-align: top; }}
    th {{ background: #e8f0eb; }}
    code {{ direction: ltr; unicode-bidi: isolate; }}
  </style>
</head>
<body>
  <h1>ביקורת איכות תוכן — גרסת מסמך 1.0.0</h1>
  <p class="status">{html.escape(status.upper())}</p>
  <p>{stats['videos']} סרטונים · {stats['errors']} שגיאות · {stats['warnings']} אזהרות</p>
  <table>
    <thead><tr><th>חומרה</th><th>קוד</th><th>רשומה</th><th>שדה</th><th>ממצא</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</body>
</html>
"""


def run_audit(
    videos_path: Path = DEFAULT_VIDEOS,
    ledger_path: Path | None = DEFAULT_LEDGER,
) -> dict[str, Any]:
    before = digest(videos_path)
    videos = load_json(videos_path)
    if not isinstance(videos, list):
        raise ValueError("videos.json must contain an array")
    ledger = load_ledger(ledger_path) if ledger_path and ledger_path.is_file() else None
    report = audit_dataset(videos, ledger)
    after = digest(videos_path)
    report.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": {
                "videos_path": str(videos_path),
                "videos_sha256_before": before,
                "videos_sha256_after": after,
                "unchanged": before == after,
                "ledger_path": str(ledger_path) if ledger_path else None,
                "ledger_present": bool(ledger_path and ledger_path.is_file()),
            },
        }
    )
    if before != after:
        raise RuntimeError("Audit-only invariant violated: videos.json changed during lint")
    return report


def write_reports(report: dict[str, Any], json_path: Path, html_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--videos", type=Path, default=DEFAULT_VIDEOS)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Write a baseline report but return success even when findings are blocking",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    report = run_audit(args.videos, args.ledger)
    write_reports(report, args.report, args.html)
    print(
        f"Content quality lint: {report['status'].upper()} | "
        f"videos={report['stats']['videos']} errors={report['stats']['errors']} "
        f"warnings={report['stats']['warnings']}"
    )
    return 0 if report["status"] == "pass" or args.no_fail else 1


if __name__ == "__main__":
    sys.exit(main())
