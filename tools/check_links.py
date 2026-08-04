#!/usr/bin/env python3
"""Check video-link consistency; network access is opt-in with --online."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
VIDEOS_PATH = ROOT / "data" / "videos.json"
DEFAULT_REPORT = ROOT / "reports" / "link-check.json"
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_videos(path: Path = VIDEOS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("data/videos.json must be an array of objects")
    return value


def local_results(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    id_counts: dict[Any, int] = {}
    youtube_counts: dict[Any, int] = {}
    url_counts: dict[Any, int] = {}
    for video in videos:
        for counts, key in ((id_counts, "id"), (youtube_counts, "youtube_video_id"), (url_counts, "youtube_url")):
            value = video.get(key)
            counts[value] = counts.get(value, 0) + 1
    results: list[dict[str, Any]] = []
    for video in videos:
        youtube_id = video.get("youtube_video_id")
        valid_id = isinstance(youtube_id, str) and YOUTUBE_ID_RE.fullmatch(youtube_id) is not None
        expected_url = f"https://www.youtube.com/watch?v={youtube_id}" if valid_id else None
        thumbnail = video.get("thumbnail_url")
        checks = {
            "youtube_id_format": valid_id,
            "internal_id_matches": valid_id and video.get("id") == f"yt-{youtube_id}",
            "youtube_url_matches": valid_id and video.get("youtube_url") == expected_url,
            "thumbnail_matches": valid_id and isinstance(thumbnail, str) and f"/vi/{youtube_id}/" in thumbnail,
            "internal_id_unique": id_counts.get(video.get("id")) == 1,
            "youtube_id_unique": youtube_counts.get(youtube_id) == 1,
            "youtube_url_unique": url_counts.get(video.get("youtube_url")) == 1,
        }
        results.append(
            {
                "id": video.get("id"),
                "youtube_video_id": youtube_id,
                "youtube_url": video.get("youtube_url"),
                "expected_url": expected_url,
                "local_checks": checks,
                "local_status": "pass" if all(checks.values()) else "fail",
                "online_status": "not_checked",
            }
        )
    return results


def check_oembed(
    result: dict[str, Any],
    timeout: float,
    retries: int = 2,
    backoff: float = 0.75,
    sleep: Any = time.sleep,
) -> dict[str, Any]:
    checked = dict(result)
    url = checked.get("expected_url")
    if checked["local_status"] != "pass" or not isinstance(url, str):
        checked["online_status"] = "not_checked_local_failure"
        return checked
    endpoint = f"https://www.youtube.com/oembed?url={quote(url, safe='')}&format=json"
    request = Request(
        endpoint,
        headers={
            "Accept": "application/json",
            "User-Agent": "AdventureRidingVideoGuide-LinkChecker/1.0",
        },
    )
    max_attempts = retries + 1
    for attempt in range(1, max_attempts + 1):
        checked["attempt_count"] = attempt
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                payload = json.loads(response.read().decode("utf-8"))
            provider_ok = payload.get("provider_name") == "YouTube"
            checked.update(
                {
                    "online_status": "active_public" if status == 200 and provider_ok else "indeterminate",
                    "http_status": status,
                    "oembed_provider": payload.get("provider_name"),
                    "oembed_title": payload.get("title"),
                    "oembed_author_name": payload.get("author_name"),
                }
            )
            break
        except HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if retryable and attempt < max_attempts:
                sleep(backoff * (2 ** (attempt - 1)))
                continue
            unavailable = exc.code in {400, 401, 403, 404, 410}
            checked.update(
                {
                    "online_status": (
                        "rate_limited" if exc.code == 429 else "unavailable" if unavailable else "indeterminate"
                    ),
                    "http_status": exc.code,
                    "error": f"HTTP {exc.code}: {exc.reason}",
                }
            )
            break
        except (URLError, TimeoutError, UnicodeError, json.JSONDecodeError, OSError) as exc:
            if attempt < max_attempts:
                sleep(backoff * (2 ** (attempt - 1)))
                continue
            checked.update({"online_status": "indeterminate", "error": str(exc)})
            break
    return checked


def build_report(
    videos: list[dict[str, Any]],
    *,
    online: bool = False,
    timeout: float = 10.0,
    workers: int = 4,
    retries: int = 2,
    backoff: float = 0.75,
    videos_path: Path = VIDEOS_PATH,
) -> dict[str, Any]:
    results = local_results(videos)
    if online:
        completed: dict[int, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(check_oembed, item, timeout, retries, backoff): index
                for index, item in enumerate(results)
            }
            for future in as_completed(futures):
                completed[futures[future]] = future.result()
        results = [completed[index] for index in range(len(results))]
    local_valid = sum(item["local_status"] == "pass" for item in results)
    online_counts = {
        status: sum(item["online_status"] == status for item in results)
        for status in (
            "active_public",
            "unavailable",
            "indeterminate",
            "rate_limited",
            "not_checked",
            "not_checked_local_failure",
        )
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "online_oembed" if online else "dry_run_local_only",
        "network_performed": online,
        "retry_policy": {"retries": retries, "backoff_seconds": backoff, "timeout_seconds": timeout},
        "notice": (
            "YouTube oEmbed was queried over HTTPS; active_public means oEmbed returned valid YouTube metadata."
            if online
            else "No network requests were made. This report validates only local ID and URL consistency."
        ),
        "source": {
            "file": str(videos_path.relative_to(ROOT)).replace("\\", "/") if videos_path.is_relative_to(ROOT) else str(videos_path),
            "sha256": file_sha256(videos_path),
        },
        "summary": {
            "total": len(results),
            "local_valid": local_valid,
            "local_invalid": len(results) - local_valid,
            **{f"online_{key}": value for key, value in online_counts.items()},
        },
        "results": results,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Opt in to HTTPS requests to the official YouTube oEmbed endpoint")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help=f"JSON report path (default: {DEFAULT_REPORT})")
    parser.add_argument("--no-report", action="store_true", help="Do not write a JSON report")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds for --online")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent oEmbed requests for --online (1-16)")
    parser.add_argument("--retries", type=int, default=2, help="Retries after transient failures (0-5)")
    parser.add_argument("--backoff", type=float, default=0.75, help="Initial exponential-backoff delay in seconds")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not 1 <= args.workers <= 16:
        parser.error("--workers must be between 1 and 16")
    if not 0 <= args.retries <= 5:
        parser.error("--retries must be between 0 and 5")
    if args.backoff < 0:
        parser.error("--backoff must be zero or greater")
    try:
        videos = load_videos()
        report = build_report(
            videos,
            online=args.online,
            timeout=args.timeout,
            workers=args.workers,
            retries=args.retries,
            backoff=args.backoff,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not args.no_report:
        write_report(args.report, report)
        print(f"Report: {args.report}")
    summary = report["summary"]
    print(f"Mode: {report['mode']}")
    print(f"Local checks: {summary['local_valid']} passed, {summary['local_invalid']} failed")
    if args.online:
        print(
            "Online checks: "
            f"{summary['online_active_public']} active, "
            f"{summary['online_unavailable']} unavailable, "
            f"{summary['online_indeterminate']} indeterminate, "
            f"{summary['online_rate_limited']} rate limited"
        )
    else:
        print("Online checks: not performed (use --online explicitly)")
    if summary["local_invalid"] or summary["online_unavailable"]:
        return 1
    if args.online and (summary["online_indeterminate"] or summary["online_rate_limited"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
