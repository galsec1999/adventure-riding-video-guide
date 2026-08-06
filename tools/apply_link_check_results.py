#!/usr/bin/env python3
"""Apply a complete, successful YouTube oEmbed audit to the catalogue."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--videos", type=Path, default=ROOT / "data" / "videos.json")
    args = parser.parse_args()

    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    videos_path = args.videos if args.videos.is_absolute() else ROOT / args.videos
    report = json.loads(report_path.read_text(encoding="utf-8"))
    videos = json.loads(videos_path.read_text(encoding="utf-8"))

    if report.get("mode") != "online_oembed" or report.get("network_performed") is not True:
        raise SystemExit("Refusing to apply a report that did not perform the online oEmbed audit")
    recorded_hash = report.get("source", {}).get("sha256")
    if recorded_hash != sha256(videos_path):
        raise SystemExit("Refusing to apply results: report source hash does not match data/videos.json")

    results = report.get("results", [])
    active = {item["id"] for item in results if item.get("online_status") == "active_public"}
    unresolved = [item for item in results if item.get("online_status") != "active_public"]
    catalogue_ids = {video["id"] for video in videos}
    if unresolved:
        raise SystemExit(f"Refusing to apply report with {len(unresolved)} non-active results")
    if active != catalogue_ids:
        raise SystemExit("Refusing to apply incomplete results: audited IDs do not equal catalogue IDs")

    checked_date = datetime.fromisoformat(report["generated_at"]).date().isoformat()
    changed = 0
    for video in videos:
        verification = video.setdefault("verification", {})
        if verification.get("link_status") != "active_public" or video.get("last_checked") != checked_date:
            changed += 1
        verification["link_status"] = "active_public"
        video["last_checked"] = checked_date

    videos_path.write_text(json.dumps(videos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Applied active_public to {len(videos)} records; {changed} records changed; checked {checked_date}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
