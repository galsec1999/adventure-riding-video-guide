#!/usr/bin/env python3
"""HISTORICAL ONE-TIME MIGRATION. DO NOT USE TO AUTHOR OR AUDIT CONTENT.

Replace the single Wave 2 record that failed YouTube oEmbed verification. The
script is retained only as provenance for the completed replacement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OLD_YOUTUBE_ID = "5SlHGlyzF7w"
NEW_YOUTUBE_ID = "CI6h7XtyINY"
OLD_ID = f"yt-{OLD_YOUTUBE_ID}"
NEW_ID = f"yt-{NEW_YOUTUBE_ID}"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    videos_path = ROOT / "data" / "videos.json"
    paths_path = ROOT / "data" / "learning-paths.json"
    offroad_path = ROOT / "research" / "approved" / "wave-2-offroad-records.json"
    technical_path = ROOT / "research" / "approved" / "wave-2-technical-records.json"
    approved_path = ROOT / "research" / "approved" / "wave-2-approved-ids.txt"
    diff_path = ROOT / "reports" / "phase-03-id-diff.json"

    videos = load(videos_path)
    if len(videos) != 130:
        raise SystemExit(f"Expected the assembled 130-record dataset; found {len(videos)}")
    ids = [record["youtube_video_id"] for record in videos]
    if ids.count(OLD_YOUTUBE_ID) != 1 or NEW_YOUTUBE_ID in ids:
        raise SystemExit("Dataset is not in the expected pre-replacement state")

    offroad = load(offroad_path)
    technical = load(technical_path)
    if len(offroad) != 30 or len(technical) != 11:
        raise SystemExit("Approved record batches are not in the expected 30/11 state")
    replacement = next(
        (record for record in technical if record["youtube_video_id"] == NEW_YOUTUBE_ID),
        None,
    )
    if replacement is None:
        raise SystemExit("Verified replacement record is missing")
    reduced_offroad = [record for record in offroad if record["youtube_video_id"] != OLD_YOUTUBE_ID]
    if len(reduced_offroad) != 29:
        raise SystemExit("Expected to remove exactly one off-road record")

    replaced_videos = [
        replacement if record["youtube_video_id"] == OLD_YOUTUBE_ID else record
        for record in videos
    ]
    final_ids = [record["youtube_video_id"] for record in replaced_videos]
    if len(final_ids) != len(set(final_ids)) or len(final_ids) != 130:
        raise SystemExit("Replacement would break the 130 unique-ID invariant")

    learning_paths = load(paths_path)
    removed_references = 0
    for learning_path in learning_paths:
        for step in learning_path["steps"]:
            for field in ("primary_video_ids", "alternative_video_ids"):
                before = len(step[field])
                step[field] = [video_id for video_id in step[field] if video_id != OLD_ID]
                removed_references += before - len(step[field])
    if removed_references != 1:
        raise SystemExit(f"Expected one learning-path reference to remove; found {removed_references}")

    approved_ids = [
        line.strip()
        for line in approved_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(approved_ids) != 70 or approved_ids.count(OLD_YOUTUBE_ID) != 1 or NEW_YOUTUBE_ID in approved_ids:
        raise SystemExit("Approved ID list is not in the expected pre-replacement state")
    approved_ids = [NEW_YOUTUBE_ID if item == OLD_YOUTUBE_ID else item for item in approved_ids]

    before_ids = {record["id"] for record in replaced_videos[:60]}
    after_ids = {record["id"] for record in replaced_videos}
    diff_report = {
        "status": "pass",
        "generated_at": "2026-08-03",
        "before_count": 60,
        "after_count": 130,
        "added_count": len(after_ids - before_ids),
        "removed_count": len(before_ids - after_ids),
        "added_ids": sorted(after_ids - before_ids),
        "removed_ids": sorted(before_ids - after_ids),
        "unique_internal_ids": len(after_ids),
        "unique_youtube_video_ids": len(set(final_ids)),
        "duplicate_values": {
            "internal_ids": [],
            "youtube_video_ids": [],
            "youtube_urls": [],
        },
        "approved_batch_sizes": {
            "offroad": 29,
            "road_safety": 30,
            "technical_gaps": 11,
        },
        "online_gate_replacement": {
            "removed_id": OLD_ID,
            "reason": "YouTube oEmbed returned HTTP 401 although the watch page and metadata remained public",
            "replacement_id": NEW_ID,
            "replacement_oembed_status": 200,
        },
    }
    if diff_report["added_count"] != 70 or diff_report["removed_count"] != 0:
        raise SystemExit("Replacement changed the Wave 1 baseline diff")

    write(videos_path, replaced_videos)
    write(paths_path, learning_paths)
    write(offroad_path, reduced_offroad)
    approved_path.write_text("\n".join(approved_ids) + "\n", encoding="utf-8")
    write(diff_path, diff_report)
    print(f"Replaced {OLD_ID} with {NEW_ID}; dataset remains 130 records")
    print("Approved batches: offroad=29, road_safety=30, technical_gaps=11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
