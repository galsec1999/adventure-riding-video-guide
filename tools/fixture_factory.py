"""Temporary scalability-fixture factory for tests and local acceptance only."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_video_fixture(
    source_videos: list[dict[str, Any]],
    target_count: int,
) -> list[dict[str, Any]]:
    if not source_videos:
        raise ValueError("source_videos must be non-empty")
    if not isinstance(target_count, int) or isinstance(target_count, bool) or target_count <= 0:
        raise ValueError("target_count must be a positive integer")
    if target_count < len(source_videos):
        raise ValueError("target_count cannot be smaller than the verified source dataset")

    fixture = copy.deepcopy(source_videos)
    used_ids = {video["youtube_video_id"] for video in fixture}
    sequence = 1
    while len(fixture) < target_count:
        source = source_videos[(len(fixture) - len(source_videos)) % len(source_videos)]
        while True:
            youtube_id = f"fx{sequence:09d}"
            sequence += 1
            if youtube_id not in used_ids:
                break
        used_ids.add(youtube_id)
        clone = copy.deepcopy(source)
        clone.update(
            {
                "id": f"yt-{youtube_id}",
                "youtube_video_id": youtube_id,
                "youtube_url": f"https://www.youtube.com/watch?v={youtube_id}",
                "thumbnail_url": f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
            }
        )
        fixture.append(clone)
    return fixture


def materialize_project_fixture(
    source_root: Path,
    target_root: Path,
    target_count: int,
) -> Path:
    """Copy validator inputs into a temporary root and expand videos there."""

    shutil.copytree(source_root / "data", target_root / "data")
    shutil.copytree(source_root / "schema", target_root / "schema")
    source_videos = load_json(source_root / "data" / "videos.json")
    videos = build_video_fixture(source_videos, target_count)
    videos_path = target_root / "data" / "videos.json"
    videos_path.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return videos_path
