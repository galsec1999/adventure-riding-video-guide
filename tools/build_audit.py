#!/usr/bin/env python3
"""Build source-derived JSON, CSV and HTML content-audit reports."""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable

try:
    from validate_data import ROOT, run_validation
except ModuleNotFoundError:  # Supports `python -m tools.build_audit`.
    from tools.validate_data import ROOT, run_validation


DEFAULT_OUTPUT_DIR = ROOT / "reports"
SOURCE_PATHS = (
    ROOT / "data" / "videos.json",
    ROOT / "data" / "categories.json",
    ROOT / "data" / "learning-paths.json",
    ROOT / "data" / "synonyms.json",
    ROOT / "data" / "site-config.json",
    ROOT / "schema" / "video.schema.json",
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def counts(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def duplicates(values: Iterable[Any], field: str) -> list[dict[str, Any]]:
    return [
        {"field": field, "value": value, "count": count}
        for value, count in sorted(Counter(values).items(), key=lambda pair: str(pair[0]))
        if count > 1
    ]


def current_link_check(
    videos_hash: str,
    output_dir: Path,
    link_report: Path | None = None,
) -> dict[str, Any]:
    path = link_report if link_report is not None else output_dir / "link-check.json"
    if not path.exists():
        return {"available": False, "reason": f"{path.as_posix()} does not exist"}
    try:
        report = read_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"available": False, "reason": f"Cannot read link-check report: {exc}"}
    recorded_hash = report.get("source", {}).get("sha256") if isinstance(report, dict) else None
    if recorded_hash != videos_hash:
        return {"available": False, "stale": True, "reason": "Link-check source hash does not match current videos.json"}
    return {
        "available": True,
        "stale": False,
        "generated_at": report.get("generated_at"),
        "mode": report.get("mode"),
        "network_performed": report.get("network_performed"),
        "summary": report.get("summary"),
    }


def build_audit(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    link_report: Path | None = None,
) -> dict[str, Any]:
    videos = read_json(ROOT / "data" / "videos.json")
    paths = read_json(ROOT / "data" / "learning-paths.json")
    schema = read_json(ROOT / "schema" / "video.schema.json")
    validation = run_validation()
    internal_ids = [item["id"] for item in videos]
    youtube_ids = [item["youtube_video_id"] for item in videos]
    urls = [item["youtube_url"] for item in videos]
    duplicate_rows = (
        duplicates(internal_ids, "id")
        + duplicates(youtube_ids, "youtube_video_id")
        + duplicates(urls, "youtube_url")
    )
    broken_or_unverified = [
        item["id"]
        for item in videos
        if item["verification"]["link_status"] != "active_public"
        or item["verification"]["metadata_verified"] is not True
    ]
    required_fields = set(schema["required"])
    missing_required = [
        {"id": item.get("id"), "fields": sorted(required_fields - set(item))}
        for item in videos
        if required_fields - set(item)
    ]
    category_counts = counts(item["primary_category"] for item in videos)
    evidence_counts = counts(
        evidence
        for item in videos
        for evidence in item["verification"]["content_evidence_types"]
    )
    all_path_refs = [
        video_id
        for learning_path in paths
        for step in learning_path["steps"]
        for field_name in ("primary_video_ids", "alternative_video_ids")
        for video_id in step[field_name]
    ]
    source_hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): digest(path)
        for path in SOURCE_PATHS
    }
    videos_hash = source_hashes["data/videos.json"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "tools/build_audit.py",
        "source_files_sha256": source_hashes,
        "validation": validation,
        "total_videos": len(videos),
        "unique_youtube_video_ids": len(set(youtube_ids)),
        "unique_internal_ids": len(set(internal_ids)),
        "unique_youtube_urls": len(set(urls)),
        "duplicates": duplicate_rows,
        "missing_required_fields": missing_required,
        "broken_or_unverified_links": broken_or_unverified,
        "broken_or_unverified_links_recorded": broken_or_unverified,
        "broken_or_unverified_links_basis": "recorded verification.link_status and metadata_verified fields; not a live network claim",
        "link_check": current_link_check(videos_hash, output_dir, link_report),
        "by_language": counts(item["language"] for item in videos),
        "by_domain": counts(item["domain"] for item in videos),
        "by_skill_level": counts(item["skill_level"] for item in videos),
        "by_primary_category": category_counts,
        "by_evidence_type": evidence_counts,
        "classification_confidence": counts(item["verification"]["classification_confidence"] for item in videos),
        "contains_marketing": sum(item["contains_marketing"] for item in videos),
        "quality_scores": counts(item["quality_score"] for item in videos),
        "thin_categories": [key for key, value in category_counts.items() if value == 1],
        "coverage": {
            "with_published_date": sum(item["published_date"] is not None for item in videos),
            "with_duration": sum(item["duration_seconds"] is not None for item in videos),
            "with_subtitles": sum(bool(item["subtitle_languages"]) for item in videos),
            "with_chapters": sum(bool(item["chapters"]) for item in videos),
            "with_related_videos": sum(bool(item["related_video_ids"]) for item in videos),
        },
        "learning_paths": {
            "count": len(paths),
            "steps": sum(len(item["steps"]) for item in paths),
            "primary_video_references": sum(len(step["primary_video_ids"]) for item in paths for step in item["steps"]),
            "alternative_video_references": sum(len(step["alternative_video_ids"]) for item in paths for step in item["steps"]),
            "unknown_video_ids": sorted(set(all_path_refs) - set(internal_ids)),
        },
    }


def csv_rows(report: dict[str, Any]) -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = [
        ("summary", "total_videos", report["total_videos"]),
        ("summary", "unique_youtube_video_ids", report["unique_youtube_video_ids"]),
        ("summary", "unique_internal_ids", report["unique_internal_ids"]),
        ("summary", "unique_youtube_urls", report["unique_youtube_urls"]),
        ("summary", "duplicates", len(report["duplicates"])),
        ("summary", "missing_required_fields", len(report["missing_required_fields"])),
        ("summary", "broken_or_unverified_links_recorded", len(report["broken_or_unverified_links_recorded"])),
        ("summary", "contains_marketing", report["contains_marketing"]),
        ("validation", "checks_passed", report["validation"]["checks_passed"]),
        ("validation", "checks_failed", report["validation"]["checks_failed"]),
        ("learning_paths", "count", report["learning_paths"]["count"]),
        ("learning_paths", "steps", report["learning_paths"]["steps"]),
        ("learning_paths", "primary_video_references", report["learning_paths"]["primary_video_references"]),
        ("learning_paths", "alternative_video_references", report["learning_paths"]["alternative_video_references"]),
    ]
    for section in (
        "by_language",
        "by_domain",
        "by_skill_level",
        "by_primary_category",
        "by_evidence_type",
        "classification_confidence",
        "quality_scores",
        "coverage",
    ):
        rows.extend((section, key, value) for key, value in report[section].items())
    return rows


def table(title: str, values: dict[str, Any]) -> str:
    body = "".join(
        f"<tr><th scope=\"row\">{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in values.items()
    )
    return f"<section><h2>{html.escape(title)}</h2><table><tbody>{body}</tbody></table></section>"


def render_html(report: dict[str, Any]) -> str:
    status = report["validation"]["status"]
    summary = {
        "סרטונים": report["total_videos"],
        "מזהי YouTube ייחודיים": report["unique_youtube_video_ids"],
        "כפילויות": len(report["duplicates"]),
        "רשומות עם שדות חסרים": len(report["missing_required_fields"]),
        "קישורים לא מאומתים לפי הנתון השמור": len(report["broken_or_unverified_links_recorded"]),
        "בדיקות שעברו": report["validation"]["checks_passed"],
        "בדיקות שנכשלו": report["validation"]["checks_failed"],
    }
    link = report["link_check"]
    link_note = (
        f"מצב דוח קישורים: {html.escape(str(link.get('mode')))}; בוצעה רשת: {html.escape(str(link.get('network_performed')))}"
        if link.get("available")
        else f"דוח קישורים עדכני אינו זמין: {html.escape(str(link.get('reason')))}"
    )
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>דוח ביקורת תוכן</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ max-width: 1100px; margin: auto; padding: 2rem; line-height: 1.5; }}
    header, section {{ margin-block: 1.5rem; }}
    .status {{ font-weight: 700; color: {'#16723b' if status == 'pass' else '#b42318'}; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #8886; padding: .5rem; text-align: right; }}
    th {{ width: 70%; }}
    code {{ direction: ltr; unicode-bidi: embed; }}
  </style>
</head>
<body>
  <header>
    <h1>דוח ביקורת תוכן</h1>
    <p>נוצר אוטומטית ב־<code>{html.escape(report['generated_at'])}</code>.</p>
    <p class="status">מצב אימות: {html.escape(status)}</p>
    <p>{link_note}</p>
  </header>
  {table('סיכום', summary)}
  {table('שפות', report['by_language'])}
  {table('תחומים', report['by_domain'])}
  {table('רמות', report['by_skill_level'])}
  {table('קטגוריות ראשיות', report['by_primary_category'])}
  {table('סוגי ראיות', report['by_evidence_type'])}
  {table('כיסוי מטא־דאטה', report['coverage'])}
</body>
</html>
"""


def write_reports(output_dir: Path, report: dict[str, Any]) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "content-audit.json"
    csv_path = output_dir / "content-audit.csv"
    html_path = output_dir / "content-audit.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("section", "key", "count"))
        writer.writerows(csv_rows(report))
    html_path.write_text(render_html(report), encoding="utf-8")
    return json_path, csv_path, html_path


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help=f"Report directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument(
        "--link-report",
        type=Path,
        help="Link-check JSON to embed (default: <output-dir>/link-check.json)",
    )
    args = parser.parse_args(argv)
    link_report = args.link_report
    if link_report is not None and not link_report.is_absolute():
        link_report = ROOT / link_report
    report = build_audit(args.output_dir, link_report=link_report)
    paths = write_reports(args.output_dir, report)
    print(f"Audit status: {report['validation']['status']}")
    print(f"Validation checks: {report['validation']['checks_passed']} passed, {report['validation']['checks_failed']} failed")
    for path in paths:
        print(f"Wrote: {path}")
    return 0 if report["validation"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
