#!/usr/bin/env python3
"""Apply the 2026-08-05 legacy evidence review to the canonical data set.

Only records marked ``supports`` with ``high`` confidence survive. This keeps
partially supported local learning claims out of the published release.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REVIEW_DATE = "2026-08-05"
EXPECTED_REVIEWED = 78


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def filter_video_refs(value: Any, removed_ids: set[str]) -> tuple[Any, int]:
    """Recursively remove deleted IDs from travel-guide ``*_video_ids`` arrays."""
    changes = 0
    if isinstance(value, list):
        result = []
        for item in value:
            filtered, child_changes = filter_video_refs(item, removed_ids)
            result.append(filtered)
            changes += child_changes
        return result, changes
    if not isinstance(value, dict):
        return value, changes

    result: dict[str, Any] = {}
    for key, item in value.items():
        if key.endswith("video_ids") and isinstance(item, list):
            filtered = [video_id for video_id in item if video_id not in removed_ids]
            changes += len(item) - len(filtered)
            result[key] = filtered
        else:
            result[key], child_changes = filter_video_refs(item, removed_ids)
            changes += child_changes
    return result, changes


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    reports_dir = root / "reports" / "site-upgrade-v3"

    evidence_gap = load_json(reports_dir / "legacy-evidence-gap.json")
    evidence_results = evidence_gap.get("results", [])
    evidence_by_id = {item["local_id"]: item for item in evidence_results}

    reviews: list[dict[str, Any]] = []
    for batch in range(1, 4):
        reviews.extend(load_json(reports_dir / f"evidence-review-batch-{batch}.json"))

    reviewed_ids = [item["local_id"] for item in reviews]
    expected_ids = [item["local_id"] for item in evidence_results]
    if len(reviews) != EXPECTED_REVIEWED or reviewed_ids != expected_ids:
        raise SystemExit(
            "Evidence review coverage mismatch: expected the exact ordered 78-record evidence-gap set"
        )
    if len(set(reviewed_ids)) != EXPECTED_REVIEWED:
        raise SystemExit("Evidence review contains duplicate local IDs")

    retained_reviews = {
        item["local_id"]: item
        for item in reviews
        if item.get("decision") == "supports" and item.get("confidence") == "high"
    }
    removed_reviews = {
        item["local_id"]: item for item in reviews if item["local_id"] not in retained_reviews
    }
    removed_ids = set(removed_reviews)

    videos_path = root / "data" / "videos.json"
    videos = load_json(videos_path)
    original_by_id = {video["id"]: video for video in videos}
    missing_retained = set(retained_reviews) - set(original_by_id)
    if missing_retained:
        raise SystemExit(f"Retained reviewed IDs missing from data/videos.json: {sorted(missing_retained)}")

    updated_videos: list[dict[str, Any]] = []
    related_refs_removed = 0
    for video in videos:
        if video["id"] in removed_ids:
            continue

        related = video.get("related_video_ids", [])
        filtered_related = [video_id for video_id in related if video_id not in removed_ids]
        related_refs_removed += len(related) - len(filtered_related)
        video["related_video_ids"] = filtered_related

        review = retained_reviews.get(video["id"])
        if review:
            live_evidence = evidence_by_id[video["id"]]
            evidence_types = list(dict.fromkeys(review.get("evidence_types", [])))
            if not evidence_types or not live_evidence.get("description_present"):
                raise SystemExit(f"High-confidence retained record lacks live description evidence: {video['id']}")
            verification = video.setdefault("verification", {})
            verification["link_status"] = "active_public"
            verification["metadata_verified"] = True
            verification["content_evidence_types"] = evidence_types
            verification["classification_confidence"] = "high"
            verification["notes_he"] = (
                "ב־2026-08-05 נבדקו מחדש תיאור המקור"
                + (" ופרקי המקור" if "chapters" in evidence_types else "")
                + " באמצעות yt-dlp. הראיות תמכו בסיווג ובנקודות הלמידה ברמת ביטחון גבוהה. "
                "לא הורדו ולא נשמרו הסרטון או תמלול מלא."
            )
            verification["notes_en"] = (
                "On 2026-08-05 the source description"
                + (" and source chapters were" if "chapters" in evidence_types else " was")
                + " rechecked with yt-dlp. The evidence supported the classification and learning points "
                "with high confidence. No video or full transcript was downloaded or stored."
            )
            video["last_checked"] = REVIEW_DATE

        updated_videos.append(video)

    retained_ids = {video["id"] for video in updated_videos}

    paths_path = root / "data" / "learning-paths.json"
    learning_paths = load_json(paths_path)
    path_changes: list[dict[str, Any]] = []
    candidate_pool = sorted(
        updated_videos,
        key=lambda video: (
            bool(video.get("contains_marketing")),
            -int(video.get("quality_score") or 0),
            video["id"],
        ),
    )

    for path in learning_paths:
        for step in path.get("steps", []):
            before_primary = list(step.get("primary_video_ids", []))
            before_alternative = list(step.get("alternative_video_ids", []))
            before_all = before_primary + before_alternative
            desired_categories = {
                original_by_id[video_id].get("primary_category")
                for video_id in before_all
                if video_id in original_by_id
            }
            primary = [video_id for video_id in before_primary if video_id in retained_ids]
            alternative = [
                video_id
                for video_id in before_alternative
                if video_id in retained_ids and video_id not in primary
            ]
            selected = primary + alternative
            if not primary and alternative:
                primary.append(alternative.pop(0))
                selected = primary + alternative
            if not alternative and len(primary) > 1:
                alternative.append(primary.pop())
                selected = primary + alternative
            for candidate in candidate_pool:
                if primary and alternative and len(selected) >= 2:
                    break
                if candidate["id"] in selected:
                    continue
                if desired_categories and candidate.get("primary_category") not in desired_categories:
                    continue
                if not primary:
                    primary.append(candidate["id"])
                else:
                    alternative.append(candidate["id"])
                selected.append(candidate["id"])

            if len(selected) < 2 or not primary or not alternative:
                raise SystemExit(
                    f"Could not retain primary and alternative verified references for "
                    f"{path['id']} step {step['order']}"
                )
            step["primary_video_ids"] = primary
            step["alternative_video_ids"] = alternative
            if before_primary != primary or before_alternative != alternative:
                path_changes.append(
                    {
                        "path_id": path["id"],
                        "step_order": step["order"],
                        "before": before_all,
                        "after": primary + alternative,
                    }
                )

    travel_path = root / "data" / "travel-guides.json"
    travel_guides = load_json(travel_path)
    travel_guides, travel_refs_removed = filter_video_refs(travel_guides, removed_ids)

    write_json(videos_path, updated_videos)
    write_json(paths_path, learning_paths)
    write_json(travel_path, travel_guides)

    report = {
        "document_version": "1.0.0",
        "review_date": REVIEW_DATE,
        "policy": "retain only supports/high; remove supports/medium, insufficient and reject",
        "reviewed_count": len(reviews),
        "retained_high_confidence_count": len(retained_reviews),
        "removed_count": len(removed_ids),
        "video_count_before": len(videos),
        "video_count_after": len(updated_videos),
        "removed_by_review_decision": {
            decision: sum(1 for item in removed_reviews.values() if item.get("decision") == decision)
            for decision in ("supports", "insufficient", "reject")
        },
        "removed_ids": sorted(removed_ids),
        "retained_ids": sorted(retained_reviews),
        "related_references_removed": related_refs_removed,
        "learning_path_steps_changed": path_changes,
        "travel_guide_references_removed": travel_refs_removed,
    }
    write_json(reports_dir / "legacy-evidence-application.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
