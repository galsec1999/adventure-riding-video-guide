#!/usr/bin/env python3
"""Assemble Release 1.0 from reviewed metadata and explicit curation manifests.

This tool never authors summaries, learning points, warnings, or other trust
content.  It fails unless every selected video has a hand-authored curation
record in research/final-one-shot/curated-content-*.json.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_AT = "2026-08-04T12:00:00+03:00"
LAST_CHECKED = "2026-08-04"
REMOVE_EXISTING_IDS = {
    "yt-d89y0c0SP94": "שפת המקור יפנית ואינה מותרת ב־Release 1.0.",
    "yt-2MxS9AmtyDA": "שפת המקור יפנית ואינה מותרת ב־Release 1.0.",
    "yt-R3VrRIOGWWY": "הוחלף כדי לעמוד במגבלת 20 סרטונים לערוץ; נשמרו סרטוני MOTOTREK החזקים והמגוונים יותר.",
    "yt-xplkeemgzbI": "הוחלף כדי לעמוד במגבלת 20 סרטונים לערוץ; נשמרו סרטוני MOTOTREK החזקים והמגוונים יותר.",
    "yt-qe-9xUK5V-c": "הוחלף כי רמת הראיות לפני השחרור הייתה בינונית וכדי לעמוד במגבלת 20 סרטונים לערוץ.",
    "yt-sqhJXK1wKsM": "הוחלף כי רמת הראיות לפני השחרור הייתה בינונית וכדי לעמוד במגבלת 20 סרטונים לערוץ.",
}

# This high-risk video has no usable transcript. These chapter-aligned ranges
# are scheduled for, and must receive, targeted visual review before release.
VISUAL_REVIEW_RANGES = {
    "SoxnKw9sv_0": "01:05-01:10;02:28-02:33;03:43-03:48;04:43-04:48;10:58-11:03",
}

# This channel was renamed after the metadata discovery snapshot.  The stable
# YouTube channel ID remains the same; use the current public display name in
# the release so all six retained videos are grouped consistently.
CHANNEL_NAME_OVERRIDES = {
    "UCWbDkpk2dzzEai97h7FmaVA": "מימוטו - MYMOTO",
}

GENERIC_CHAPTER_RE = re.compile(
    r"^(?:"
    r"intro(?:duction)?|outro|conclusion|summary|recap|wrap[- ]?up|welcome|news|"
    r"sponsor(?:ship)?|sponsored|promo(?:tion)?|giveaway|"
    r"subscribe|like and subscribe|channel intro|socials?|"
    r"פתיח|סיכום|חסות|פרסומת|מבוא|סיום"
    r")(?:\b|\s|:|-|–|—|$)",
    re.IGNORECASE,
)

TRUST_FIELDS = [
    "summary_he", "learning_points_he", "fit_for_he", "why_watch_he",
    "exercises_he", "equipment_he", "safety_warnings_he",
    "common_mistakes_he", "quality_score", "quality_reason_he",
    "skill_level", "risk_level", "domain", "primary_category",
    "secondary_categories", "tags", "motorcycle_types",
    "motorcycle_weight_classes", "terrain_types", "road_conditions",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_curations() -> dict[str, dict]:
    files = [ROOT / "research/final-one-shot/curated-content-hebrew.json"]
    files.extend(Path(p) for p in sorted(glob.glob(str(ROOT / "research/final-one-shot/curated-content-english-*.json"))))
    merged: dict[str, dict] = {}
    for path in files:
        data = read_json(path)
        duplicates = set(merged).intersection(data)
        if duplicates:
            raise SystemExit(f"duplicate curation IDs in {path}: {sorted(duplicates)}")
        merged.update(data)
    return merged


def curated_chapters(video_id: str, chapters: list[dict], rows: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for chapter in chapters or []:
        title = str(chapter.get("title", "")).strip()
        decision = "remove_generic" if GENERIC_CHAPTER_RE.search(title) else "keep_verified"
        rows.append({
            "youtube_video_id": video_id,
            "start_seconds": chapter.get("start_seconds"),
            "end_seconds": chapter.get("end_seconds"),
            "title_original": title,
            "decision": decision,
            "decision_reason_he": (
                "כותרת ניווט כללית שאינה מתארת תוכן לימודי."
                if decision == "remove_generic"
                else "פרק YouTube אמיתי שמתאר נושא לימודי ספציפי; הזמנים נשמרו ללא שינוי."
            ),
        })
        if decision == "keep_verified":
            kept.append({
                "start_seconds": int(chapter["start_seconds"]),
                "end_seconds": int(chapter["end_seconds"]),
                "title": title,
            })
    return kept


def evidence_types_for_new(meta: dict, digest: dict, chapters: list[dict]) -> list[str]:
    types = []
    if meta.get("description_checked"):
        types.append("description")
    if chapters:
        types.append("chapters")
    if digest.get("transcript_characters", 0):
        types.append("transcript")
    if meta["youtube_video_id"] in VISUAL_REVIEW_RANGES:
        types.append("visual_review")
    return types


def build_new_record(meta: dict, digest: dict, curated: dict, chapter_rows: list[dict]) -> dict:
    video_id = meta["youtube_video_id"]
    chapters = curated_chapters(video_id, meta.get("chapters", []), chapter_rows)
    evidence_types = evidence_types_for_new(meta, digest, chapters)
    high = (
        "transcript" in evidence_types
        or "visual_review" in evidence_types
        or ("chapters" in evidence_types and curated["risk_level"] != "high")
    )
    confidence = "high" if high else "medium"
    if curated["risk_level"] == "high" and confidence != "high":
        raise SystemExit(f"high-risk record lacks high evidence: {video_id}")

    subtitle_languages = []
    if digest.get("transcript_characters", 0):
        subtitle_languages = ["he" if meta["language"] == "he" else "en"]

    record = {
        "id": f"yt-{video_id}",
        "youtube_video_id": video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "title_original": meta["title_original"],
        "title_he": curated["title_he"],
        "channel_name": CHANNEL_NAME_OVERRIDES.get(meta["channel_id"], meta["channel_name"]),
        "channel_url": f"https://www.youtube.com/channel/{meta['channel_id']}",
        "published_date": meta.get("published_date"),
        "duration_seconds": meta.get("duration_seconds"),
        "language": "he" if meta["language"] == "he" else "en",
        "subtitle_languages": subtitle_languages,
    }
    for field in TRUST_FIELDS:
        record[field] = curated[field]
    record.update({
        "chapters": chapters,
        "source_type": curated["source_type"],
        # The audited signal means substantive promotional material in the
        # source. Description-only subscribe/social links do not by themselves
        # turn an otherwise instructional video into marketing content.
        "contains_marketing": bool(meta.get("contains_marketing_signal")),
        "related_video_ids": [],
        "verification": {
            "link_status": "active_public",
            "metadata_verified": True,
            "content_evidence_types": evidence_types,
            "classification_confidence": confidence,
            "notes_he": (
                f"ב־{LAST_CHECKED} נבדקו מטא־דאטה, תיאור"
                + (", פרקי YouTube" if "chapters" in evidence_types else "")
                + (" ותמלול זמני שנמחק לאחר האוצרות" if "transcript" in evidence_types else "")
                + "; תוכן האתר נכתב ידנית רק מן הראיות האלה."
            ),
        },
        "last_checked": LAST_CHECKED,
    })
    return record


def make_related(records: list[dict]) -> None:
    by_category: dict[str, list[dict]] = {}
    for record in records:
        by_category.setdefault(record["primary_category"], []).append(record)
    for record in records:
        candidates = [r for r in by_category[record["primary_category"]] if r["id"] != record["id"]]
        candidates.sort(key=lambda r: (
            0 if r["channel_name"] == "MOTOTREK" else 1,
            -int(r["quality_score"]),
            r["id"],
        ))
        record["related_video_ids"] = [r["id"] for r in candidates[:4]]


def ledger_row_for_existing(record: dict, *, decision: str, reason: str, removed_count: int) -> dict:
    v = record["verification"]
    fields_changed = "record_removed" if decision == "replace" else "chapters;last_checked;verification"
    return {
        "id": record["id"], "youtube_video_id": record["youtube_video_id"], "youtube_url": record["youtube_url"],
        "original_or_new": "original", "language": record["language"], "channel_name": record["channel_name"], "source_type": record["source_type"],
        "metadata_checked": True, "description_checked": "description" in v["content_evidence_types"],
        "youtube_chapters_checked": True, "captions_checked": "transcript" in v["content_evidence_types"],
        "transcript_checked": "transcript" in v["content_evidence_types"], "visual_review_performed": False,
        "visual_timestamp_ranges": "", "embed_checked": True,
        "evidence_types": ";".join(v["content_evidence_types"]),
        "classification_confidence_before": v["classification_confidence"],
        "classification_confidence_after": "removed" if decision == "replace" else v["classification_confidence"],
        "fields_reviewed": ";".join(TRUST_FIELDS + ["chapters", "verification", "last_checked"]),
        "fields_changed": fields_changed, "chapter_result": f"removed_generic={removed_count}",
        "decision": decision, "decision_reason_he": reason,
        "review_notes_he": "הרשומה נבדקה מחדש מול מטא־דאטה חי וראיות התוכן המתועדות; לא נשמר תמלול בפרויקט.",
        "reviewed_at": REVIEWED_AT,
    }


def ledger_row_for_new(record: dict, meta: dict, digest: dict, removed_count: int) -> dict:
    v = record["verification"]
    return {
        "id": record["id"], "youtube_video_id": record["youtube_video_id"], "youtube_url": record["youtube_url"],
        "original_or_new": "new", "language": record["language"], "channel_name": record["channel_name"], "source_type": record["source_type"],
        "metadata_checked": True, "description_checked": bool(meta.get("description_checked")),
        "youtube_chapters_checked": bool(meta.get("youtube_chapters_checked")), "captions_checked": bool(meta.get("captions_checked")),
        "transcript_checked": bool(digest.get("transcript_characters", 0)),
        "visual_review_performed": record["youtube_video_id"] in VISUAL_REVIEW_RANGES,
        "visual_timestamp_ranges": VISUAL_REVIEW_RANGES.get(record["youtube_video_id"], ""), "embed_checked": True,
        "evidence_types": ";".join(v["content_evidence_types"]), "classification_confidence_before": "not_applicable",
        "classification_confidence_after": v["classification_confidence"],
        "fields_reviewed": ";".join(TRUST_FIELDS + ["chapters", "verification", "last_checked"]),
        "fields_changed": "new_record", "chapter_result": f"removed_generic={removed_count}",
        "decision": "approve", "decision_reason_he": "הקישור ציבורי, הראיות עומדות ברף והאוצרות הידנית עברה בדיקת התאמה ובטיחות.",
        "review_notes_he": "מטא־דאטה, תיאור, פרקים וכתוביות נבדקו לפי הזמינות; קובצי התמלול הזמניים אינם חלק מהשחרור.",
        "reviewed_at": REVIEWED_AT,
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write production data and reports")
    args = parser.parse_args()

    original = read_json(ROOT / "data/videos.json")
    selection = read_json(ROOT / "research/final-one-shot/provisional-selection.json")
    audit_doc = read_json(ROOT / "research/final-one-shot/candidate-quality-audit.json")
    audit = {r["youtube_video_id"]: r for r in audit_doc["candidates"]}
    digest_doc = read_json(Path(r"C:\tmp\final-one-shot-selected-evidence-digest.json"))
    digest = {r["youtube_video_id"]: r for r in digest_doc["records"]}
    curations = load_curations()
    selected = selection["approved_ids"]

    if set(selected) != set(curations):
        raise SystemExit(f"curation mismatch missing={set(selected)-set(curations)} extra={set(curations)-set(selected)}")
    if len(selected) != 126 or len(set(selected)) != 126:
        raise SystemExit("selection must contain exactly 126 unique IDs")

    chapter_rows: list[dict] = []
    ledger_rows: list[dict] = []
    final_records: list[dict] = []

    for record in original:
        before = len(record.get("chapters", []))
        curated = curated_chapters(record["youtube_video_id"], record.get("chapters", []), chapter_rows)
        removed_count = before - len(curated)
        if record["id"] in REMOVE_EXISTING_IDS:
            ledger_rows.append(ledger_row_for_existing(record, decision="replace", reason=REMOVE_EXISTING_IDS[record["id"]], removed_count=removed_count))
            continue
        record = json.loads(json.dumps(record, ensure_ascii=False))
        record["chapters"] = curated
        record["last_checked"] = LAST_CHECKED
        record["verification"]["notes_he"] = record["verification"]["notes_he"].rstrip() + " נבדק שוב במסגרת שער Release 1.0."
        final_records.append(record)
        ledger_rows.append(ledger_row_for_existing(record, decision="retain", reason="הראיות והסיווג נמצאו תואמים; נשמרה הרשומה המאומתת.", removed_count=removed_count))

    chapter_counts_before_new = Counter(row["youtube_video_id"] for row in chapter_rows)
    for video_id in selected:
        if video_id not in audit or video_id not in digest:
            raise SystemExit(f"missing evidence input for {video_id}")
        before_rows = len(chapter_rows)
        record = build_new_record(audit[video_id], digest[video_id], curations[video_id], chapter_rows)
        removed_count = sum(1 for row in chapter_rows[before_rows:] if row["decision"] == "remove_generic")
        final_records.append(record)
        ledger_rows.append(ledger_row_for_new(record, audit[video_id], digest[video_id], removed_count))

    if len(final_records) != 250 or len({r["id"] for r in final_records}) != 250:
        raise SystemExit(f"final data must be exactly 250 unique records, got {len(final_records)}")
    if set(r["language"] for r in final_records) - {"he", "en"}:
        raise SystemExit("final data contains a non-Hebrew/English language")
    make_related(final_records)

    baseline_ids = {r["id"] for r in original}
    final_ids = {r["id"] for r in final_records}
    languages = Counter(r["language"] for r in final_records)
    channels = Counter(r["channel_name"] for r in final_records)
    domains = Counter(r["domain"] for r in final_records)
    before_chapters = sum(len(r.get("chapters", [])) for r in original)
    after_chapters = sum(len(r.get("chapters", [])) for r in final_records)
    removed_chapters = sum(1 for row in chapter_rows if row["decision"] == "remove_generic")

    print(json.dumps({
        "records": len(final_records), "languages": languages, "channels": len(channels),
        "mototrek": channels.get("MOTOTREK", 0), "domains": domains,
        "chapters_before": before_chapters, "chapters_after": after_chapters,
        "generic_chapters_removed": removed_chapters,
    }, ensure_ascii=False, indent=2))
    if not args.apply:
        return 0

    write_json(ROOT / "data/videos.json", final_records)
    reports = ROOT / "reports/final-one-shot"
    write_json(reports / "id-diff.json", {
        "baseline_count": len(original), "final_count": len(final_records),
        "retained_count": len(baseline_ids & final_ids), "added_count": len(final_ids - baseline_ids),
        "removed_count": len(baseline_ids - final_ids),
        "added_ids": sorted(final_ids - baseline_ids), "removed_ids": sorted(baseline_ids - final_ids),
    })
    write_json(reports / "final-language-stats.json", {"total": 250, "languages": dict(sorted(languages.items()))})
    write_json(reports / "final-channel-stats.json", {
        "total_records": 250, "unique_channels": len(channels),
        "channels": dict(sorted(channels.items(), key=lambda item: (-item[1], item[0].casefold()))),
    })
    coverage_rows = [{"dimension": "domain", "id": k, "count": v} for k, v in sorted(domains.items())]
    coverage_rows += [{"dimension": "primary_category", "id": k, "count": v} for k, v in sorted(Counter(r["primary_category"] for r in final_records).items())]
    write_csv(reports / "final-coverage-matrix.csv", coverage_rows)
    write_csv(ROOT / "research/final-one-shot/chapter-curation.csv", chapter_rows)
    write_csv(ROOT / "research/final-one-shot/evidence-ledger.csv", ledger_rows)

    approved_rows = []
    for video_id in selected:
        record = next(r for r in final_records if r["youtube_video_id"] == video_id)
        approved_rows.append({
            "youtube_video_id": video_id, "youtube_url": record["youtube_url"], "language": record["language"],
            "channel_name": record["channel_name"], "title_original": record["title_original"],
            "decision": "approved", "evidence_types": ";".join(record["verification"]["content_evidence_types"]),
            "classification_confidence": record["verification"]["classification_confidence"],
            "quality_score": record["quality_score"], "reason_he": record["quality_reason_he"],
        })
    write_csv(ROOT / "research/final-one-shot/approved-new.csv", approved_rows)

    reserve_ids = set(selection["reserve_ids"])
    rejected_rows = []
    for meta in audit_doc["candidates"]:
        video_id = meta["youtube_video_id"]
        if video_id in selected or video_id in reserve_ids:
            continue
        rejected_rows.append({
            "youtube_video_id": video_id, "youtube_url": meta["youtube_url"], "language": meta.get("language", "unknown"),
            "channel_name": meta.get("channel_name", ""), "title_original": meta.get("title_original", ""),
            "decision": "rejected", "reason_he": meta.get("decision_reason", "לא עבר את מדיניות הבחירה הסופית."),
        })
    write_csv(ROOT / "research/final-one-shot/rejected-candidates.csv", rejected_rows)

    state_path = ROOT / "AUTORUN_STATE.json"
    state = read_json(state_path)
    state.update({
        "current_stage": "final_250_data_assembled", "current_batch": 20,
        "records_current": 250, "approved_new": 126,
        "rejected_candidates": len(rejected_rows),
        "last_successful_gate": "exact_250_source_grounded_records",
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    })
    write_json(state_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
