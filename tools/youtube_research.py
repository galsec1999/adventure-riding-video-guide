#!/usr/bin/env python3
"""Collect YouTube research metadata without downloading video or transcripts.

This helper is intentionally separate from production runtime code.  It uses
``yt-dlp`` only as a metadata extractor and writes compact evidence reports;
full descriptions are included only when ``--include-description`` is passed,
which is intended for a temporary path outside the project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
VIDEOS_PATH = ROOT / "data" / "videos.json"


def load_yt_dlp() -> Any:
    try:
        import yt_dlp  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is required for research metadata. Install it in an isolated "
            "environment and expose it through PYTHONPATH."
        ) from exc
    return yt_dlp


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def iso_upload_date(value: Any) -> str | None:
    text = str(value or "")
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return None


def language_codes(mapping: Any) -> list[str]:
    if not isinstance(mapping, dict):
        return []
    return sorted(str(key) for key in mapping if key)


def normalize_chapters(chapters: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for chapter in chapters or []:
        if not isinstance(chapter, dict):
            continue
        title = str(chapter.get("title") or "").strip()
        if not title or title.lower().startswith("<untitled chapter"):
            continue
        start = chapter.get("start_time")
        end = chapter.get("end_time")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            continue
        normalized.append(
            {
                "start_seconds": int(round(start)),
                "end_seconds": int(round(end)),
                "title": title,
            }
        )
    return normalized


def compact_metadata(info: dict[str, Any], *, include_description: bool) -> dict[str, Any]:
    description = str(info.get("description") or "")
    result: dict[str, Any] = {
        "youtube_video_id": info.get("id"),
        "youtube_url": info.get("webpage_url") or info.get("original_url"),
        "title_original": info.get("title"),
        "channel_name": info.get("channel") or info.get("uploader"),
        "channel_id": info.get("channel_id") or info.get("uploader_id"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "published_date": iso_upload_date(info.get("upload_date")),
        "duration_seconds": int(round(info["duration"])) if isinstance(info.get("duration"), (int, float)) else None,
        "availability": info.get("availability"),
        "language": info.get("language"),
        "subtitle_languages": language_codes(info.get("subtitles")),
        "automatic_caption_languages": language_codes(info.get("automatic_captions")),
        "chapters": normalize_chapters(info.get("chapters")),
        "description_present": bool(description.strip()),
        "description_characters": len(description),
        "description_sha256": hashlib.sha256(description.encode("utf-8")).hexdigest(),
        "extractor": info.get("extractor"),
    }
    if include_description:
        result["description"] = description
    return result


def metadata_options(*, flat: bool = False) -> dict[str, Any]:
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "cachedir": False,
        "extract_flat": "in_playlist" if flat else False,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }


def fetch_one(url: str, *, include_description: bool = False) -> dict[str, Any]:
    yt_dlp = load_yt_dlp()
    try:
        with yt_dlp.YoutubeDL(metadata_options()) as downloader:
            info = downloader.extract_info(url, download=False)
        if not isinstance(info, dict):
            raise RuntimeError("Extractor did not return a metadata object")
        return {"status": "pass", **compact_metadata(info, include_description=include_description)}
    except Exception as exc:  # yt-dlp exposes several extractor/network exception types.
        return {"status": "fail", "youtube_url": url, "error": str(exc)}


def fetch_many(
    urls: Iterable[str],
    *,
    workers: int,
    include_description: bool = False,
) -> list[dict[str, Any]]:
    ordered = list(dict.fromkeys(urls))
    completed: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetch_one, url, include_description=include_description): index
            for index, url in enumerate(ordered)
        }
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
    return [completed[index] for index in range(len(ordered))]


def audit_existing(output: Path, *, workers: int) -> int:
    videos = read_json(VIDEOS_PATH)
    fetched = fetch_many((item["youtube_url"] for item in videos), workers=workers)
    by_id = {item.get("youtube_video_id"): item for item in fetched}
    rows: list[dict[str, Any]] = []
    for local in videos:
        remote = by_id.get(local["youtube_video_id"], {})
        remote_chapters = remote.get("chapters") if remote.get("status") == "pass" else None
        checks = {
            "active_public": remote.get("availability") == "public",
            "title_matches": remote.get("title_original") == local.get("title_original"),
            "channel_matches": remote.get("channel_name") == local.get("channel_name"),
            "duration_matches": remote.get("duration_seconds") == local.get("duration_seconds"),
            "published_date_matches": remote.get("published_date") == local.get("published_date"),
            "chapters_match": remote_chapters == local.get("chapters"),
        }
        rows.append(
            {
                "id": local["id"],
                "youtube_video_id": local["youtube_video_id"],
                "status": remote.get("status", "fail"),
                "checks": checks,
                "local_chapter_count": len(local.get("chapters") or []),
                "remote_chapter_count": len(remote_chapters or []),
                "remote_chapters": remote_chapters or [],
                "description_present": remote.get("description_present", False),
                "description_characters": remote.get("description_characters", 0),
                "description_sha256": remote.get("description_sha256"),
                "subtitle_languages": remote.get("subtitle_languages", []),
                "automatic_caption_languages": remote.get("automatic_caption_languages", []),
                "error": remote.get("error"),
            }
        )
    failed = [row for row in rows if row["status"] != "pass"]
    mismatches = [
        {"id": row["id"], "failed_checks": [key for key, value in row["checks"].items() if not value]}
        for row in rows
        if row["status"] == "pass" and not all(row["checks"].values())
    ]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network_performed": True,
        "source": "YouTube metadata extracted with yt-dlp; no video or transcript downloaded",
        "videos_total": len(videos),
        "videos_fetched": len(videos) - len(failed),
        "videos_failed": len(failed),
        "records_with_local_chapters": sum(bool(item.get("chapters")) for item in videos),
        "local_chapters_total": sum(len(item.get("chapters") or []) for item in videos),
        "metadata_or_chapter_mismatches": mismatches,
        "results": rows,
    }
    write_json(output, report)
    print(f"Fetched: {report['videos_fetched']}/{report['videos_total']}")
    print(f"Failed: {report['videos_failed']}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Report: {output}")
    return 0 if not failed else 1


def read_urls(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        if isinstance(value, list):
            return [
                item if isinstance(item, str) else str(item.get("youtube_url") or item.get("url") or "")
                for item in value
                if isinstance(item, (str, dict))
            ]
        raise ValueError("JSON URL input must be an array")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def fetch_command(input_path: Path, output: Path, *, workers: int, include_description: bool) -> int:
    urls = [url for url in read_urls(input_path) if url]
    results = fetch_many(urls, workers=workers, include_description=include_description)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network_performed": True,
        "video_or_transcript_downloaded": False,
        "requested": len(urls),
        "passed": sum(item["status"] == "pass" for item in results),
        "failed": sum(item["status"] != "pass" for item in results),
        "results": results,
    }
    write_json(output, report)
    print(f"Fetched: {report['passed']}/{report['requested']}")
    print(f"Failed: {report['failed']}")
    print(f"Report: {output}")
    return 0 if report["failed"] == 0 else 1


def search_one(query_spec: dict[str, Any]) -> dict[str, Any]:
    """Run one metadata-only YouTube search and retain the query provenance."""

    query = str(query_spec.get("query") or "").strip()
    limit = int(query_spec.get("limit") or 12)
    if not query:
        return {"status": "fail", "query": query, "error": "Empty query", "entries": []}
    if not 1 <= limit <= 50:
        return {
            "status": "fail",
            "query": query,
            "error": f"Search limit must be 1-50; found {limit}",
            "entries": [],
        }
    yt_dlp = load_yt_dlp()
    options = metadata_options(flat=True)
    options.update({"playlistend": limit, "noplaylist": False})
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(f"ytsearch{limit}:{query}", download=False)
        raw_entries = info.get("entries") if isinstance(info, dict) else []
        entries: list[dict[str, Any]] = []
        for rank, item in enumerate(raw_entries or [], start=1):
            if not isinstance(item, dict) or not item.get("id"):
                continue
            video_id = str(item["id"])
            entries.append(
                {
                    "youtube_video_id": video_id,
                    "youtube_url": item.get("url")
                    if str(item.get("url") or "").startswith("http")
                    else f"https://www.youtube.com/watch?v={video_id}",
                    "title_original": item.get("title"),
                    "channel_name": item.get("channel") or item.get("uploader"),
                    "channel_id": item.get("channel_id") or item.get("uploader_id"),
                    "duration_seconds": item.get("duration"),
                    "rank": rank,
                }
            )
        return {
            "status": "pass",
            "query": query,
            "language_hint": query_spec.get("language_hint"),
            "topic": query_spec.get("topic"),
            "requested": limit,
            "returned": len(entries),
            "entries": entries,
        }
    except Exception as exc:
        return {
            "status": "fail",
            "query": query,
            "language_hint": query_spec.get("language_hint"),
            "topic": query_spec.get("topic"),
            "requested": limit,
            "returned": 0,
            "entries": [],
            "error": str(exc),
        }


def read_query_specs(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = read_json(path)
    if isinstance(payload, list):
        raw_queries = payload
        seed_ids: list[str] = []
    elif isinstance(payload, dict):
        raw_queries = payload.get("queries", [])
        seed_ids = [str(item).strip() for item in payload.get("seed_video_ids", []) if str(item).strip()]
    else:
        raise ValueError("Search input must be an array or object with a queries array")
    specs: list[dict[str, Any]] = []
    for item in raw_queries:
        if isinstance(item, str):
            specs.append({"query": item, "limit": 12})
        elif isinstance(item, dict):
            specs.append(dict(item))
        else:
            raise ValueError("Each search query must be a string or object")
    return specs, list(dict.fromkeys(seed_ids))


def discover_command(input_path: Path, output: Path, *, workers: int) -> int:
    specs, seed_ids = read_query_specs(input_path)
    completed: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(search_one, spec): index for index, spec in enumerate(specs)}
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
    searches = [completed[index] for index in range(len(specs))]

    unique: dict[str, dict[str, Any]] = {}
    for video_id in seed_ids:
        unique[video_id] = {
            "youtube_video_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "title_original": None,
            "channel_name": None,
            "channel_id": None,
            "duration_seconds": None,
            "search_matches": [
                {"query": "required_seed", "language_hint": "he", "topic": "required_seed", "rank": 0}
            ],
        }
    for search in searches:
        for entry in search["entries"]:
            video_id = entry["youtube_video_id"]
            candidate = unique.setdefault(
                video_id,
                {
                    key: entry.get(key)
                    for key in (
                        "youtube_video_id",
                        "youtube_url",
                        "title_original",
                        "channel_name",
                        "channel_id",
                        "duration_seconds",
                    )
                }
                | {"search_matches": []},
            )
            candidate["search_matches"].append(
                {
                    "query": search["query"],
                    "language_hint": search.get("language_hint"),
                    "topic": search.get("topic"),
                    "rank": entry["rank"],
                }
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network_performed": True,
        "video_or_transcript_downloaded": False,
        "queries_requested": len(specs),
        "queries_passed": sum(item["status"] == "pass" for item in searches),
        "queries_failed": sum(item["status"] != "pass" for item in searches),
        "raw_results": sum(item["returned"] for item in searches),
        "unique_candidates": len(unique),
        "seed_video_ids": seed_ids,
        "searches": searches,
        "candidates": list(unique.values()),
    }
    write_json(output, report)
    print(f"Queries: {report['queries_passed']}/{report['queries_requested']}")
    print(f"Unique candidates: {report['unique_candidates']}")
    print(f"Report: {output}")
    return 0 if report["queries_failed"] == 0 else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit-existing", help="Compare every production record with live YouTube metadata")
    audit.add_argument("--output", type=Path, required=True)
    audit.add_argument("--workers", type=int, default=4)

    fetch = subparsers.add_parser("fetch", help="Fetch metadata for URLs listed in a text or JSON file")
    fetch.add_argument("--input", type=Path, required=True)
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument("--workers", type=int, default=4)
    fetch.add_argument("--include-description", action="store_true")

    discover = subparsers.add_parser(
        "discover",
        help="Run metadata-only YouTube searches and deduplicate candidates",
    )
    discover.add_argument("--input", type=Path, required=True)
    discover.add_argument("--output", type=Path, required=True)
    discover.add_argument("--workers", type=int, default=2)
    return result


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args(argv)
    if not 1 <= args.workers <= 8:
        raise SystemExit("--workers must be between 1 and 8")
    try:
        if args.command == "audit-existing":
            return audit_existing(args.output, workers=args.workers)
        if args.command == "discover":
            return discover_command(args.input, args.output, workers=args.workers)
        return fetch_command(
            args.input,
            args.output,
            workers=args.workers,
            include_description=args.include_description,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
