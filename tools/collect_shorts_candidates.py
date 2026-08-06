#!/usr/bin/env python3
"""Enumerate YouTube Shorts candidates without downloading media or transcripts."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def enumerate_channel(seed: dict[str, Any]) -> dict[str, Any]:
    import yt_dlp  # type: ignore[import-not-found]

    channel_id = str(seed["channel_id"])
    url = f"https://www.youtube.com/channel/{channel_id}/shorts"
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "noplaylist": False,
        "cachedir": False,
    }
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)
        entries = []
        for rank, item in enumerate((info or {}).get("entries") or [], start=1):
            if not isinstance(item, dict) or not item.get("id"):
                continue
            video_id = str(item["id"])
            entries.append(
                {
                    "youtube_video_id": video_id,
                    "youtube_url": f"https://www.youtube.com/shorts/{video_id}",
                    "title_original": item.get("title"),
                    "channel_name": item.get("channel") or item.get("uploader") or seed["name"],
                    "channel_id": item.get("channel_id") or channel_id,
                    "duration_seconds": item.get("duration"),
                    "channel_rank": rank,
                    "focus_hints": seed.get("focus", []),
                }
            )
        return {"status": "pass", "seed": seed, "url": url, "entries": entries}
    except Exception as exc:
        return {"status": "fail", "seed": seed, "url": url, "entries": [], "error": str(exc)}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise SystemExit("--workers must be between 1 and 8")

    config = load_json(args.channels)
    seeds = config.get("channels", [])
    completed: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(enumerate_channel, seed): index for index, seed in enumerate(seeds)}
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
    channels = [completed[index] for index in range(len(seeds))]

    existing_ids = {item["youtube_video_id"] for item in load_json(ROOT / "data" / "videos.json")}
    unique: dict[str, dict[str, Any]] = {}
    duplicate_occurrences = 0
    for channel in channels:
        for entry in channel["entries"]:
            video_id = entry["youtube_video_id"]
            if video_id in unique:
                duplicate_occurrences += 1
                continue
            unique[video_id] = entry
    candidates = [entry for video_id, entry in unique.items() if video_id not in existing_ids]

    report = {
        "document_version": "1.0.0",
        "product_version": "3.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network_performed": True,
        "video_or_transcript_downloaded": False,
        "publication_status": "candidates_only",
        "channels_requested": len(seeds),
        "channels_passed": sum(item["status"] == "pass" for item in channels),
        "channels_failed": sum(item["status"] != "pass" for item in channels),
        "raw_entries": sum(len(item["entries"]) for item in channels),
        "unique_entries": len(unique),
        "duplicate_occurrences": duplicate_occurrences,
        "already_in_long_library": sum(video_id in existing_ids for video_id in unique),
        "candidate_count": len(candidates),
        "channels": [
            {
                "name": item["seed"]["name"],
                "channel_id": item["seed"]["channel_id"],
                "status": item["status"],
                "entry_count": len(item["entries"]),
                "error": item.get("error"),
            }
            for item in channels
        ],
        "candidates": candidates,
    }
    write_json(args.output, report)
    print(f"Channels: {report['channels_passed']}/{report['channels_requested']}")
    print(f"Raw Shorts: {report['raw_entries']}")
    print(f"Unique candidates: {report['candidate_count']}")
    print(f"Report: {args.output}")
    return 0 if report["channels_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
