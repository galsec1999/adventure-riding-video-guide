#!/usr/bin/env python3
"""Apply the two evidence-backed Release 1.0 link replacements.

All editorial content lives in the reviewed manifest.  This tool performs only
deterministic JSON/CSV bookkeeping and refuses to leave dangling references.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research/final-one-shot"
REPORTS = ROOT / "reports/final-one-shot"
MANIFEST_PATH = RESEARCH / "release-link-replacements.json"
REVIEWED_AT = "2026-08-04T15:00:34+03:00"

TRUST_FIELDS = [
    "summary_he", "learning_points_he", "fit_for_he", "why_watch_he",
    "exercises_he", "equipment_he", "safety_warnings_he",
    "common_mistakes_he", "quality_score", "quality_reason_he",
    "skill_level", "risk_level", "domain", "primary_category",
    "secondary_categories", "tags", "motorcycle_types",
    "motorcycle_weight_classes", "terrain_types", "road_conditions",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def replace_records(videos: list[dict], manifest: dict) -> list[dict]:
    replacements = {
        item["replaces_youtube_video_id"]: item["record"]
        for item in manifest["replacements"]
    }
    new_ids = {record["youtube_video_id"] for record in replacements.values()}
    current_ids = {record["youtube_video_id"] for record in videos}
    if current_ids & new_ids and current_ids & set(replacements):
        raise SystemExit("mixed pre/post replacement state in data/videos.json")

    if not (current_ids & set(replacements)):
        if not new_ids.issubset(current_ids):
            raise SystemExit("neither complete pre-state nor complete post-state found")
        records_by_new_id = {
            record["youtube_video_id"]: record for record in replacements.values()
        }
        result = [
            records_by_new_id.get(record["youtube_video_id"], record)
            for record in videos
        ]
    else:
        missing = set(replacements) - current_ids
        if missing:
            raise SystemExit(f"missing records scheduled for replacement: {sorted(missing)}")
        result = [replacements.get(record["youtube_video_id"], record) for record in videos]

    if len(result) != 250 or len({record["id"] for record in result}) != 250:
        raise SystemExit("replacement must preserve exactly 250 unique records")
    return result


def rebuild_related(videos: list[dict]) -> None:
    by_category: dict[str, list[dict]] = {}
    for record in videos:
        by_category.setdefault(record["primary_category"], []).append(record)
    for record in videos:
        candidates = [
            candidate for candidate in by_category[record["primary_category"]]
            if candidate["id"] != record["id"]
        ]
        candidates.sort(key=lambda candidate: (
            0 if candidate["channel_name"] == "MOTOTREK" else 1,
            -int(candidate["quality_score"]),
            candidate["id"],
        ))
        record["related_video_ids"] = [candidate["id"] for candidate in candidates[:4]]


def update_paths(old_ids: set[str]) -> list[dict]:
    path_file = ROOT / "data/learning-paths.json"
    paths = read_json(path_file)
    desired = {
        ("beginner-adventure-foundations", 6): (
            ["yt-fPBC3-rB994", "yt-Dv8cfbJ09Uw"],
            ["yt-iLqs-fA7RRk"],
        ),
        ("advanced-offroad-terrain", 7): (
            ["yt-eiRMikxU3Z4", "yt-fPBC3-rB994"],
            ["yt-mCIxtcnmeYQ"],
        ),
        ("passenger-group-safety", 1): (
            ["yt-qt262cjyWAc", "yt-U64nD-GHkik"],
            ["yt-6yE85BVYNKY"],
        ),
    }
    seen: set[tuple[str, int]] = set()
    for path in paths:
        for step in path["steps"]:
            key = (path["id"], int(step["order"]))
            if key in desired:
                primary, alternative = desired[key]
                step["primary_video_ids"] = primary
                step["alternative_video_ids"] = alternative
                seen.add(key)
    if seen != set(desired):
        raise SystemExit(f"learning-path targets missing: {sorted(set(desired) - seen)}")
    referenced = {
        video_id
        for path in paths
        for step in path["steps"]
        for key in ("primary_video_ids", "alternative_video_ids")
        for video_id in step[key]
    }
    if referenced & {f"yt-{video_id}" for video_id in old_ids}:
        raise SystemExit("removed video still referenced by a learning path")
    write_json(path_file, paths)
    return paths


def update_approved(manifest: dict) -> int:
    path = RESEARCH / "approved-new.csv"
    fields, rows = read_csv(path)
    replacements = {
        item["replaces_youtube_video_id"]: item["record"]
        for item in manifest["replacements"]
    }
    new_ids = {record["youtube_video_id"] for record in replacements.values()}
    result: list[dict] = []
    inserted: set[str] = set()
    for row in rows:
        video_id = row["youtube_video_id"]
        if video_id in new_ids:
            if video_id not in inserted:
                result.append(row)
                inserted.add(video_id)
            continue
        if video_id not in replacements:
            result.append(row)
            continue
        record = replacements[video_id]
        result.append({
            "youtube_video_id": record["youtube_video_id"],
            "youtube_url": record["youtube_url"],
            "language": record["language"],
            "channel_name": record["channel_name"],
            "title_original": record["title_original"],
            "decision": "approved",
            "evidence_types": ";".join(record["verification"]["content_evidence_types"]),
            "classification_confidence": record["verification"]["classification_confidence"],
            "quality_score": record["quality_score"],
            "reason_he": record["quality_reason_he"],
        })
        inserted.add(record["youtube_video_id"])
    for record in replacements.values():
        if record["youtube_video_id"] not in inserted:
            result.append({
                "youtube_video_id": record["youtube_video_id"],
                "youtube_url": record["youtube_url"],
                "language": record["language"],
                "channel_name": record["channel_name"],
                "title_original": record["title_original"],
                "decision": "approved",
                "evidence_types": ";".join(record["verification"]["content_evidence_types"]),
                "classification_confidence": record["verification"]["classification_confidence"],
                "quality_score": record["quality_score"],
                "reason_he": record["quality_reason_he"],
            })
    if len(result) != 127 or len({row["youtube_video_id"] for row in result}) != 127:
        raise SystemExit(f"approved-new.csv must contain 127 unique rows, got {len(result)}")
    write_csv(path, fields, result)
    return len(result)


def update_reserve(manifest: dict) -> int:
    path = RESEARCH / "reserve-candidates.csv"
    fields, rows = read_csv(path)
    promoted = {
        item["record"]["youtube_video_id"] for item in manifest["replacements"]
    }
    result = [row for row in rows if row["youtube_video_id"] not in promoted]
    if len(result) != 38 or len({row["youtube_video_id"] for row in result}) != 38:
        raise SystemExit(f"reserve-candidates.csv must contain 38 unique rows, got {len(result)}")
    write_csv(path, fields, result)
    return len(result)


def update_rejected(manifest: dict) -> int:
    path = RESEARCH / "rejected-candidates.csv"
    fields, rows = read_csv(path)
    removed = {item["youtube_video_id"]: item for item in manifest["removed"]}
    rows = [row for row in rows if row["youtube_video_id"] not in removed]
    for item in manifest["removed"]:
        rows.append({
            "youtube_video_id": item["youtube_video_id"],
            "youtube_url": item["youtube_url"],
            "language": "en",
            "channel_name": (
                "Cross Training Enduro"
                if item["youtube_video_id"] == "6hgkx7ZScqY"
                else "Cafe Racer New York City"
            ),
            "title_original": item["title_original"],
            "decision": "rejected",
            "reason_he": item["reason_he"],
        })
    if len(rows) != 339 or len({row["youtube_video_id"] for row in rows}) != 339:
        raise SystemExit(f"rejected-candidates.csv must contain 339 unique rows, got {len(rows)}")
    write_csv(path, fields, rows)
    return len(rows)


def update_chapter_ledger(manifest: dict) -> dict[str, int]:
    path = RESEARCH / "chapter-curation.csv"
    fields, rows = read_csv(path)
    removed = {item["youtube_video_id"]: item for item in manifest["removed"]}
    new_ids = {item["record"]["youtube_video_id"] for item in manifest["replacements"]}
    result: list[dict] = []
    for row in rows:
        video_id = row["youtube_video_id"]
        if video_id in new_ids:
            continue
        if video_id in removed:
            row["decision"] = "remove_with_record"
            row["decision_reason_he"] = removed[video_id]["reason_he"]
        result.append(row)
    for item in manifest["replacements"]:
        record = item["record"]
        for chapter in record["chapters"]:
            result.append({
                "youtube_video_id": record["youtube_video_id"],
                "start_seconds": chapter["start_seconds"],
                "end_seconds": chapter["end_seconds"],
                "title_original": chapter["title"],
                "decision": "keep_verified",
                "decision_reason_he": "פרק YouTube אמיתי שמתאר נושא לימודי ספציפי; הזמנים נשמרו ללא שינוי.",
            })
        if record["youtube_video_id"] == "nBhWbHKCkks":
            result.append({
                "youtube_video_id": "nBhWbHKCkks",
                "start_seconds": 707,
                "end_seconds": 743,
                "title_original": "Bloopers",
                "decision": "remove_generic",
                "decision_reason_he": "קטע פספוסים שאינו תחנת לימוד ולכן הוסר מן הניווט.",
            })
    write_csv(path, fields, result)
    counts = Counter(row["decision"] for row in result)
    expected = {"keep_verified": 897, "remove_generic": 143, "remove_with_record": 9}
    if dict(counts) != expected:
        raise SystemExit(f"unexpected chapter decisions: {dict(counts)} != {expected}")
    return dict(counts)


def update_evidence_ledger(manifest: dict) -> int:
    path = RESEARCH / "evidence-ledger.csv"
    fields, rows = read_csv(path)
    removed = {item["youtube_video_id"]: item for item in manifest["removed"]}
    new_ids = {item["record"]["youtube_video_id"] for item in manifest["replacements"]}
    result: list[dict] = []
    seen_removed: set[str] = set()
    for row in rows:
        video_id = row["youtube_video_id"]
        if video_id in new_ids:
            continue
        if video_id in removed:
            row["classification_confidence_after"] = "removed"
            row["fields_changed"] = "record_removed"
            row["chapter_result"] = "removed_with_record=5" if video_id == "6hgkx7ZScqY" else "removed_with_record=0"
            row["decision"] = "replace_unavailable"
            row["decision_reason_he"] = removed[video_id]["reason_he"]
            row["review_notes_he"] = "בדיקת Release חיה גברה על האימות המוקדם; הרשומה נשמרת בלדג'ר ההיסטורי בלבד."
            row["reviewed_at"] = REVIEWED_AT
            seen_removed.add(video_id)
        result.append(row)
    if seen_removed != set(removed):
        raise SystemExit(f"removed records missing from evidence ledger: {sorted(set(removed)-seen_removed)}")

    for item in manifest["replacements"]:
        record = item["record"]
        evidence = record["verification"]["content_evidence_types"]
        result.append({
            "id": record["id"],
            "youtube_video_id": record["youtube_video_id"],
            "youtube_url": record["youtube_url"],
            "original_or_new": "new",
            "language": record["language"],
            "channel_name": record["channel_name"],
            "source_type": record["source_type"],
            "metadata_checked": True,
            "description_checked": True,
            "youtube_chapters_checked": True,
            "captions_checked": True,
            "transcript_checked": True,
            "visual_review_performed": False,
            "visual_timestamp_ranges": "",
            "embed_checked": True,
            "evidence_types": ";".join(evidence),
            "classification_confidence_before": "not_applicable",
            "classification_confidence_after": "high",
            "fields_reviewed": ";".join(TRUST_FIELDS + ["chapters", "verification", "last_checked"]),
            "fields_changed": "new_record",
            "chapter_result": "removed_generic=1" if record["youtube_video_id"] == "nBhWbHKCkks" else "removed_generic=0",
            "decision": "approve",
            "decision_reason_he": "קישור ציבורי פעיל, ראיות מקור מפורטות ואוצרות ידנית עומדים ברף Release 1.0.",
            "review_notes_he": "מטא־דאטה, תיאור, פרקים וכתוביות ידניות נבדקו; קובצי הכתוביות הזמניים אינם חלק מן הפרויקט או השחרור.",
            "reviewed_at": REVIEWED_AT,
        })
    if len({row["youtube_video_id"] for row in result}) != len(result):
        raise SystemExit("duplicate IDs in evidence ledger")
    write_csv(path, fields, result)
    return len(result)


def update_reports(videos: list[dict], manifest: dict, chapter_counts: dict[str, int], paths: list[dict]) -> None:
    baseline = read_json(REPORTS / "baseline/videos-before.json")
    baseline_ids = {record["id"] for record in baseline}
    final_ids = {record["id"] for record in videos}
    languages = Counter(record["language"] for record in videos)
    channels = Counter(record["channel_name"] for record in videos)
    domains = Counter(record["domain"] for record in videos)
    categories = Counter(record["primary_category"] for record in videos)

    write_json(REPORTS / "id-diff.json", {
        "baseline_count": len(baseline),
        "final_count": len(videos),
        "retained_count": len(baseline_ids & final_ids),
        "added_count": len(final_ids - baseline_ids),
        "removed_count": len(baseline_ids - final_ids),
        "added_ids": sorted(final_ids - baseline_ids),
        "removed_ids": sorted(baseline_ids - final_ids),
    })
    write_json(REPORTS / "final-language-stats.json", {
        "total": len(videos), "languages": dict(sorted(languages.items()))
    })
    write_json(REPORTS / "final-channel-stats.json", {
        "total_records": len(videos),
        "unique_channels": len(channels),
        "channels": dict(sorted(channels.items(), key=lambda item: (-item[1], item[0].casefold()))),
    })
    coverage_fields = ["dimension", "id", "count"]
    coverage_rows = [
        {"dimension": "domain", "id": key, "count": count}
        for key, count in sorted(domains.items())
    ] + [
        {"dimension": "primary_category", "id": key, "count": count}
        for key, count in sorted(categories.items())
    ]
    write_csv(REPORTS / "final-coverage-matrix.csv", coverage_fields, coverage_rows)

    write_json(REPORTS / "release-link-replacements.json", {
        "status": "applied_pending_final_link_recheck",
        "checked_at": manifest["generated_at"],
        "removed": manifest["removed"],
        "promoted_ids": [item["record"]["youtube_video_id"] for item in manifest["replacements"]],
        "final_records": len(videos),
        "languages": dict(sorted(languages.items())),
        "unique_channels": len(channels),
        "mototrek_records": channels.get("MOTOTREK", 0),
        "learning_paths": len(paths),
        "chapters_before": sum(len(record.get("chapters", [])) for record in baseline),
        "chapters_after": sum(len(record.get("chapters", [])) for record in videos),
        "chapter_decisions": chapter_counts,
        "candidate_counts": manifest["final_candidate_counts"],
    })


def main() -> int:
    manifest = read_json(MANIFEST_PATH)
    removed_ids = {item["youtube_video_id"] for item in manifest["removed"]}
    videos = replace_records(read_json(ROOT / "data/videos.json"), manifest)
    rebuild_related(videos)
    paths = update_paths(removed_ids)
    write_json(ROOT / "data/videos.json", videos)

    approved = update_approved(manifest)
    reserve = update_reserve(manifest)
    rejected = update_rejected(manifest)
    chapter_counts = update_chapter_ledger(manifest)
    ledger_rows = update_evidence_ledger(manifest)
    update_reports(videos, manifest, chapter_counts, paths)

    state_path = ROOT / "AUTORUN_STATE.json"
    state = read_json(state_path)
    state.update({
        "current_stage": "release_link_replacements_applied",
        "records_current": 250,
        "approved_new": approved,
        "rejected_candidates": rejected,
        "reserve_candidates": reserve,
        "last_successful_gate": "exact_250_records_after_live_link_replacements",
        "last_updated": manifest["generated_at"],
    })
    write_json(state_path, state)

    ids = {record["id"] for record in videos}
    dangling = sorted({
        related
        for record in videos
        for related in record["related_video_ids"]
        if related not in ids
    })
    text = json.dumps(videos, ensure_ascii=False)
    if dangling or any(video_id in text for video_id in removed_ids):
        raise SystemExit(f"postcondition failed: dangling={dangling}")
    if Counter(record["language"] for record in videos) != {"en": 219, "he": 31}:
        raise SystemExit("language totals changed unexpectedly")
    if Counter(record["channel_name"] for record in videos).get("MOTOTREK") != 20:
        raise SystemExit("MOTOTREK presence changed unexpectedly")
    print(json.dumps({
        "status": "applied",
        "videos": len(videos),
        "approved": approved,
        "rejected": rejected,
        "reserve": reserve,
        "evidence_ledger_rows": ledger_rows,
        "chapters": sum(len(record.get("chapters", [])) for record in videos),
        "chapter_decisions": chapter_counts,
        "learning_paths": len(paths),
        "mototrek": 20,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
