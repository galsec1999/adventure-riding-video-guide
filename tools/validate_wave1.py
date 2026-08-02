#!/usr/bin/env python3
"""Validate wave-1 content without changing project files."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    with (ROOT / relative).open(encoding="utf-8") as f:
        return json.load(f)


def fail(message):
    raise AssertionError(message)


def main():
    videos = load("data/videos.json")
    taxonomy = load("data/categories.json")
    paths = load("data/learning-paths.json")
    schema = load("schema/video.schema.json")

    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        print("ERROR: jsonschema is required for full schema validation.", file=sys.stderr)
        print("Install with: python -m pip install jsonschema", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for index, video in enumerate(videos):
        for error in validator.iter_errors(video):
            errors.append(f"videos[{index}] {'.'.join(map(str, error.path))}: {error.message}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    if len(videos) != 60:
        fail(f"expected exactly 60 videos, found {len(videos)}")
    video_ids = [v["youtube_video_id"] for v in videos]
    internal_ids = [v["id"] for v in videos]
    urls = [v["youtube_url"] for v in videos]
    if len(set(video_ids)) != 60 or len(set(internal_ids)) != 60 or len(set(urls)) != 60:
        fail("video IDs, internal IDs, and URLs must all be unique")

    collections = {
        "domain": {x["id"] for x in taxonomy["domains"]},
        "primary_category": {x["id"] for x in taxonomy["categories"]},
        "skill_level": {x["id"] for x in taxonomy["skill_levels"]},
        "risk_level": {x["id"] for x in taxonomy["risk_levels"]},
        "source_type": {x["id"] for x in taxonomy["source_types"]},
    }
    arrays = {
        "secondary_categories": collections["primary_category"],
        "tags": {x["id"] for x in taxonomy["controlled_tags"]},
        "motorcycle_types": {x["id"] for x in taxonomy["motorcycle_types"]},
        "motorcycle_weight_classes": {x["id"] for x in taxonomy["motorcycle_weight_classes"]},
        "terrain_types": {x["id"] for x in taxonomy["terrain_types"]},
        "road_conditions": {x["id"] for x in taxonomy["road_conditions"]},
        "subtitle_languages": {x["id"] for x in taxonomy["languages"]},
    }
    internal_set = set(internal_ids)
    hebrew = re.compile(r"[\u0590-\u05ff]")
    youtube_id = re.compile(r"^[A-Za-z0-9_-]{11}$")
    for video in videos:
        if not youtube_id.fullmatch(video["youtube_video_id"]):
            fail(f"invalid YouTube ID: {video['youtube_video_id']}")
        expected_url = f"https://www.youtube.com/watch?v={video['youtube_video_id']}"
        if video["youtube_url"] != expected_url:
            fail(f"URL/ID mismatch: {video['id']}")
        if not hebrew.search(video["summary_he"]):
            fail(f"summary is not Hebrew: {video['id']}")
        if len(video["learning_points_he"]) < 3:
            fail(f"too few learning points: {video['id']}")
        if video["verification"]["link_status"] != "active_public" or not video["verification"]["metadata_verified"]:
            fail(f"video not verified active/public: {video['id']}")
        if not video["verification"]["content_evidence_types"]:
            fail(f"no content evidence: {video['id']}")
        for field, allowed in collections.items():
            if video[field] not in allowed:
                fail(f"unknown {field} {video[field]} in {video['id']}")
        if video["language"] not in {x["id"] for x in taxonomy["languages"]}:
            fail(f"unknown language in {video['id']}")
        for field, allowed in arrays.items():
            unknown = set(video[field]) - allowed
            if unknown:
                fail(f"unknown {field} {sorted(unknown)} in {video['id']}")
        unknown_related = set(video["related_video_ids"]) - internal_set
        if unknown_related:
            fail(f"unknown related IDs in {video['id']}: {sorted(unknown_related)}")
        for chapter in video["chapters"]:
            if chapter["end_seconds"] < chapter["start_seconds"]:
                fail(f"invalid chapter range in {video['id']}")
            if video["duration_seconds"] is not None and chapter["end_seconds"] > video["duration_seconds"] + 2:
                fail(f"chapter exceeds duration in {video['id']}")

    referenced = []
    for path in paths:
        for step in path["steps"]:
            referenced.extend(step["primary_video_ids"])
            referenced.extend(step["alternative_video_ids"])
    unknown = set(referenced) - internal_set
    if unknown:
        fail(f"unknown learning-path IDs: {sorted(unknown)}")

    print("PASS: 60/60 records match schema")
    print("PASS: 60 unique YouTube IDs, URLs, and internal IDs")
    print("PASS: taxonomy, related-video, and learning-path references are valid")
    print("PASS: Hebrew summaries, learning points, evidence, and chapter ranges are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
