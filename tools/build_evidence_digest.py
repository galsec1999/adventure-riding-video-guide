#!/usr/bin/env python3
"""Build a temporary review digest from descriptions and subtitle samples.

The output contains source descriptions and must remain outside the repository.
It is an analyst aid only; it does not change production data and is deleted
after the evidence ledger has been completed.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAG_RE = re.compile(r"<[^>]+>")
TIME_RE = re.compile(r"^(\d{2}:)?\d{2}:\d{2}\.\d{3}\s+-->")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_vtt(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    for source in raw.splitlines():
        line = TAG_RE.sub("", source).strip().replace("&amp;", "&").replace("&nbsp;", " ")
        if (
            not line
            or line.startswith(("WEBVTT", "Kind:", "Language:"))
            or TIME_RE.match(line)
            or line.isdigit()
        ):
            continue
        if not lines or line != lines[-1]:
            lines.append(line)
    return " ".join(lines), hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sample_text(text: str) -> list[str]:
    if not text:
        return []
    samples: list[str] = []
    for fraction in (0.08, 0.35, 0.62, 0.86):
        start = max(0, int(len(text) * fraction) - 160)
        end = min(len(text), start + 520)
        sample = text[start:end]
        if start and " " in sample:
            sample = sample.split(" ", 1)[1]
        if end < len(text) and " " in sample:
            sample = sample.rsplit(" ", 1)[0]
        samples.append(sample)
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--candidate-glob", required=True)
    parser.add_argument("--subs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("Refusing to persist full descriptions inside the repository")

    selection = load(args.selection)
    audit = load(args.audit)
    compact = {item["youtube_video_id"]: item for item in audit["candidates"]}
    raw: dict[str, dict[str, Any]] = {}
    for name in sorted(glob.glob(args.candidate_glob)):
        for item in load(Path(name))["results"]:
            if item.get("youtube_video_id"):
                raw[item["youtube_video_id"]] = item

    records: list[dict[str, Any]] = []
    for video_id in selection["approved_ids"]:
        source = raw[video_id]
        subtitle_files = sorted(args.subs_dir.glob(f"{video_id}.*.vtt"))
        preferred = next((path for path in subtitle_files if ".en." in path.name), None)
        preferred = preferred or next((path for path in subtitle_files if ".he." in path.name or ".iw." in path.name), None)
        preferred = preferred or (subtitle_files[0] if subtitle_files else None)
        transcript, transcript_hash = clean_vtt(preferred) if preferred else ("", None)
        records.append(
            {
                "youtube_video_id": video_id,
                "youtube_url": source.get("youtube_url"),
                "title_original": source.get("title_original"),
                "channel_name": source.get("channel_name"),
                "language": compact[video_id]["language"],
                "topic": compact[video_id]["topic"],
                "published_date": source.get("published_date"),
                "duration_seconds": source.get("duration_seconds"),
                "description": source.get("description") or "",
                "chapters": source.get("chapters") or [],
                "subtitle_language": preferred.name.split(".")[-2] if preferred else None,
                "transcript_sha256": transcript_hash,
                "transcript_characters": len(transcript),
                "transcript_samples": sample_text(transcript),
                "contains_marketing_signal": compact[video_id]["contains_marketing_signal"],
                "professional_source_signal": compact[video_id]["professional_source_signal"],
            }
        )
    payload = {
        "warning": "TEMPORARY ANALYST FILE WITH SOURCE DESCRIPTIONS; DELETE BEFORE RELEASE",
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Digest records: {len(records)}")
    print(f"With transcript samples: {sum(bool(item['transcript_samples']) for item in records)}")
    print("Without transcript:", ", ".join(item["youtube_video_id"] for item in records if not item["transcript_samples"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
