#!/usr/bin/env python3
"""Apply the reviewed Phase 03 Wave 2 records and learning-path additions once."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VIDEOS_PATH = ROOT / "data" / "videos.json"
PATHS_PATH = ROOT / "data" / "learning-paths.json"
METADATA_PATH = ROOT / "research" / "approved" / "wave-2-youtube-metadata.json"
APPROVED_IDS_PATH = ROOT / "research" / "approved" / "wave-2-approved-ids.txt"
RECORD_FILES = (
    ROOT / "research" / "approved" / "wave-2-offroad-records.json",
    ROOT / "research" / "approved" / "wave-2-road-records.json",
    ROOT / "research" / "approved" / "wave-2-technical-records.json",
)
DIFF_REPORT_PATH = ROOT / "reports" / "phase-03-id-diff.json"
EXPECTED_WAVE1_SHA256 = "b2c73f0dfd1c5d4acbc149ff5b93a8f22ee0f3efdc5b6b1ae67ea85a336e633e"


LEARNING_PATH_ADDITIONS: dict[str, dict[int, dict[str, list[str]]]] = {
    "beginner-offroad-adventure": {
        1: {"alternative_video_ids": ["yt-KC0Rv0aM7OI"]},
        2: {"alternative_video_ids": ["yt-sqhJXK1wKsM"]},
        4: {"alternative_video_ids": ["yt-_zQoFML9xPk"]},
        5: {"primary_video_ids": ["yt-187PCpqGp74"]},
        6: {"alternative_video_ids": ["yt-uscjPZXNyMc"]},
        7: {"primary_video_ids": ["yt-Dv8cfbJ09Uw"], "alternative_video_ids": ["yt-fPBC3-rB994"]},
        8: {"primary_video_ids": ["yt-AVbt7M2xHQ4"], "alternative_video_ids": ["yt-T-NlEZr1-ws"]},
        9: {"primary_video_ids": ["yt-OrPiMSJWZ5o"], "alternative_video_ids": ["yt-py2_NwJCzN0"]},
        10: {"primary_video_ids": ["yt-SXJZ_kYGLRY"], "alternative_video_ids": ["yt-ZGS_MoW7yps", "yt-qe-9xUK5V-c"]},
    },
    "beginner-road": {
        1: {"alternative_video_ids": ["yt-60isWQSlMg0"]},
        2: {"alternative_video_ids": ["yt-oOD9NnTevH0"]},
        3: {"alternative_video_ids": ["yt-aAybwTYH8YY"]},
        4: {"primary_video_ids": ["yt-HxJPOQ_4L18"]},
        5: {"primary_video_ids": ["yt-fl9mfnpJ1wo"], "alternative_video_ids": ["yt-VFZoZLMZGqQ"]},
        6: {"alternative_video_ids": ["yt-_ZH6lgTmpCs"]},
        7: {"primary_video_ids": ["yt-IS2mLzMgals"], "alternative_video_ids": ["yt-NN1twMtJrlA", "yt-d89y0c0SP94"]},
        8: {"primary_video_ids": ["yt-wdESPaOqd8I"], "alternative_video_ids": ["yt-wu01iLFdTE0", "yt-glxMLJ1A6rk"]},
        9: {"primary_video_ids": ["yt-U64nD-GHkik"], "alternative_video_ids": ["yt-SQhttXPPOsU"]},
        10: {"primary_video_ids": ["yt-PtRYyP96HHA"], "alternative_video_ids": ["yt-HGU8gAIq9ME"]},
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def normalize_subtitle_code(code: str) -> str | None:
    normalized = code.lower()
    if normalized in {"he", "iw"} or normalized.startswith(("he-", "iw-")):
        return "he"
    if normalized == "en" or normalized.startswith("en-"):
        return "en"
    if normalized == "ja" or normalized.startswith("ja-"):
        return "ja"
    return None


def validate_metadata(records: list[dict[str, Any]], metadata_report: dict[str, Any]) -> None:
    metadata_by_id = {
        item["youtube_video_id"]: item
        for item in metadata_report.get("results", [])
        if item.get("status") == "pass"
    }
    if len(metadata_by_id) != 70 or metadata_report.get("passed") != 70 or metadata_report.get("failed") != 0:
        raise RuntimeError("Approved metadata report is not a clean 70/70 result")
    for record in records:
        video_id = record["youtube_video_id"]
        metadata = metadata_by_id.get(video_id)
        if metadata is None:
            raise RuntimeError(f"No approved metadata for {video_id}")
        exact_fields = (
            "youtube_url",
            "title_original",
            "channel_name",
            "channel_url",
            "published_date",
            "duration_seconds",
            "chapters",
        )
        mismatches = [field for field in exact_fields if record.get(field) != metadata.get(field)]
        if mismatches:
            raise RuntimeError(f"Metadata mismatch for {video_id}: {mismatches}")
        available_subtitles = {
            normalized
            for code in (metadata.get("subtitle_languages") or []) + (metadata.get("automatic_caption_languages") or [])
            if (normalized := normalize_subtitle_code(code)) is not None
        }
        unknown_subtitles = set(record.get("subtitle_languages") or []) - available_subtitles
        if unknown_subtitles:
            raise RuntimeError(f"Unverified subtitle language for {video_id}: {sorted(unknown_subtitles)}")
        evidence = set(record.get("verification", {}).get("content_evidence_types") or [])
        if "description" not in evidence or "transcript" in evidence or "visual_review" in evidence:
            raise RuntimeError(f"Unsupported evidence declaration for {video_id}: {sorted(evidence)}")
        if bool(record.get("chapters")) != ("chapters" in evidence):
            raise RuntimeError(f"Chapter evidence mismatch for {video_id}")


def update_learning_paths(paths: list[dict[str, Any]], all_ids: set[str]) -> None:
    if {path.get("id") for path in paths} != set(LEARNING_PATH_ADDITIONS):
        raise RuntimeError("Expected the two established learning paths only")
    for path in paths:
        additions = LEARNING_PATH_ADDITIONS[path["id"]]
        for step in path["steps"]:
            step_additions = additions.get(step["order"], {})
            for field, new_ids in step_additions.items():
                existing = step[field]
                for video_id in new_ids:
                    if video_id not in existing:
                        existing.append(video_id)
            combined = step["primary_video_ids"] + step["alternative_video_ids"]
            if len(combined) != len(set(combined)):
                raise RuntimeError(f"Duplicate learning-path choice: {path['id']} step {step['order']}")
            missing = sorted(set(combined) - all_ids)
            if missing:
                raise RuntimeError(f"Missing learning-path IDs: {missing}")


def main() -> int:
    if sha256(VIDEOS_PATH) != EXPECTED_WAVE1_SHA256:
        raise SystemExit("Wave 1 input hash does not match the validated 60-record gate")

    before = load_json(VIDEOS_PATH)
    if len(before) != 60:
        raise SystemExit(f"Expected 60 Wave 1 records; found {len(before)}")

    batches = [load_json(path) for path in RECORD_FILES]
    batch_sizes = [len(batch) for batch in batches]
    if batch_sizes != [29, 30, 11]:
        raise SystemExit(f"Unexpected approved batch sizes: {batch_sizes}")
    additions = [record for batch in batches for record in batch]

    approved_ids = [line.strip() for line in APPROVED_IDS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    addition_youtube_ids = [record["youtube_video_id"] for record in additions]
    if len(approved_ids) != 70 or set(approved_ids) != set(addition_youtube_ids):
        raise SystemExit("Approved ID list and curated record set differ")
    if duplicates(addition_youtube_ids):
        raise SystemExit(f"Duplicate Wave 2 YouTube IDs: {duplicates(addition_youtube_ids)}")

    validate_metadata(additions, load_json(METADATA_PATH))

    after = before + additions
    internal_ids = [record["id"] for record in after]
    youtube_ids = [record["youtube_video_id"] for record in after]
    urls = [record["youtube_url"] for record in after]
    if len(after) != 130:
        raise SystemExit(f"Expected 130 records after append; found {len(after)}")
    duplicate_map = {
        "internal_ids": duplicates(internal_ids),
        "youtube_video_ids": duplicates(youtube_ids),
        "youtube_urls": duplicates(urls),
    }
    if any(duplicate_map.values()):
        raise SystemExit(f"Duplicate identifiers after append: {duplicate_map}")

    all_ids = set(internal_ids)
    learning_paths = load_json(PATHS_PATH)
    update_learning_paths(learning_paths, all_ids)

    before_ids = {record["id"] for record in before}
    after_ids = set(internal_ids)
    diff_report = {
        "status": "pass",
        "generated_at": "2026-08-03",
        "before_count": len(before),
        "after_count": len(after),
        "added_count": len(after_ids - before_ids),
        "removed_count": len(before_ids - after_ids),
        "added_ids": sorted(after_ids - before_ids),
        "removed_ids": sorted(before_ids - after_ids),
        "unique_internal_ids": len(after_ids),
        "unique_youtube_video_ids": len(set(youtube_ids)),
        "duplicate_values": duplicate_map,
        "approved_batch_sizes": {
            "offroad": batch_sizes[0],
            "road_safety": batch_sizes[1],
            "technical_gaps": batch_sizes[2],
        },
    }
    if diff_report["added_count"] != 70 or diff_report["removed_count"] != 0:
        raise SystemExit(f"Unexpected Phase 03 ID diff: {diff_report}")

    write_json(VIDEOS_PATH, after)
    write_json(PATHS_PATH, learning_paths)
    write_json(DIFF_REPORT_PATH, diff_report)
    print("Applied Wave 2: 60 -> 130; added=70; removed=0")
    print("Learning paths updated: 2")
    print(f"ID diff report: {DIFF_REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
