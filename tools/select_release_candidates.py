#!/usr/bin/env python3
"""Select an evidence-balanced shortlist; never authors production fields."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOPIC_DOMAIN = {
    **{topic: "offroad_adventure" for topic in (
        "offroad_position", "offroad_basics", "gravel", "sand", "mud",
        "hill_climb", "descent", "ruts", "obstacles", "water_crossing", "hills",
    )},
    **{topic: "road" for topic in (
        "cornering", "countersteering", "trail_braking", "rain", "road_hills",
        "road_position", "overtaking", "urban_hazards", "night", "swerving",
        "emergency_braking",
    )},
    **{topic: "practice" for topic in ("slow_control", "u_turn", "advanced_training", "basics")},
    **{topic: "safety_recovery" for topic in (
        "fatigue", "group_riding", "protective_gear", "lifting", "recovery",
        "passenger", "safety_body",
    )},
    **{topic: "mixed" for topic in (
        "maintenance", "tires", "suspension", "ergonomics", "pre_ride",
        "navigation", "luggage", "puncture", "channel_seed", "required_seed",
    )},
}

SHALLOW_OR_NONINSTRUCTIONAL_RE = re.compile(
    r"(?:\bmovie\b|\bPOV\b|\bconcept\b|\bofficial launch\b|\bspecs?\b|"
    r"\bcommon problems\b|\bfirst year\b|\bI took\b|\bwhat size .* bike\b|"
    r"\bready to take .* class\b|\bfears?\b|\betiquette\b|\bwalk.?around\b|"
    r"טיול|מסע|סקירה|חדשות|מבט מבפנים|אליפות|מירוץ|רכיבה ראשונה)",
    re.IGNORECASE,
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rank(row: dict[str, Any]) -> tuple[Any, ...]:
    score = int(row["evidence_score"])
    score += 4 if row["professional_source_signal"] else 0
    score += 1 if row["chapter_count"] else 0
    score -= 2 if row["contains_marketing_signal"] else 0
    return (-score, -int(row["evidence_score"]), str(row["channel_name"]), row["youtube_video_id"])


def eligible_english(row: dict[str, Any], policy: dict[str, Any]) -> bool:
    return (
        row["preliminary_decision"] == "eligible_for_content_review"
        and row["language"] == "en"
        and row["youtube_video_id"] not in set(policy["hard_excluded_ids"])
        and row["channel_name"] not in set(policy["excluded_new_channels"])
        and row["topic"] in TOPIC_DOMAIN
        and not SHALLOW_OR_NONINSTRUCTIONAL_RE.search(row["title_original"])
    )


def select(
    candidates: list[dict[str, Any]], policy: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {row["youtube_video_id"]: row for row in candidates}
    approved: list[dict[str, Any]] = []
    for video_id in policy["approved_hebrew_ids"]:
        row = by_id.get(video_id)
        if not row or row["preliminary_decision"] != "eligible_for_content_review" or row["language"] != "he":
            raise ValueError(f"Hebrew approval is not eligible: {video_id}")
        approved.append(row)

    pool = sorted((row for row in candidates if eligible_english(row, policy)), key=rank)
    domain_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    channel_counts: Counter[str] = Counter(row["channel_name"] for row in approved)
    max_channel = int(policy["maximum_new_per_channel"])
    max_topic = int(policy["default_maximum_per_topic"])
    quotas = {key: int(value) for key, value in policy["english_domain_quotas"].items()}

    for row in pool:
        domain = TOPIC_DOMAIN[row["topic"]]
        if domain_counts[domain] >= quotas[domain]:
            continue
        if topic_counts[row["topic"]] >= max_topic:
            continue
        if channel_counts[row["channel_name"]] >= max_channel:
            continue
        approved.append(row)
        domain_counts[domain] += 1
        topic_counts[row["topic"]] += 1
        channel_counts[row["channel_name"]] += 1

    # Fill a domain only after topic breadth has been exhausted.
    for row in pool:
        domain = TOPIC_DOMAIN[row["topic"]]
        if row in approved or domain_counts[domain] >= quotas[domain]:
            continue
        if channel_counts[row["channel_name"]] >= max_channel:
            continue
        approved.append(row)
        domain_counts[domain] += 1
        topic_counts[row["topic"]] += 1
        channel_counts[row["channel_name"]] += 1

    expected = len(policy["approved_hebrew_ids"]) + sum(quotas.values())
    if len(approved) != expected:
        raise ValueError(f"Shortlist target is {expected}; selected {len(approved)}")

    approved_ids = {row["youtube_video_id"] for row in approved}
    remaining = [
        row for row in sorted(candidates, key=rank)
        if row["preliminary_decision"] == "eligible_for_content_review"
        and row["youtube_video_id"] not in approved_ids
        and row["language"] in {"he", "en"}
        and not SHALLOW_OR_NONINSTRUCTIONAL_RE.search(row["title_original"])
    ]
    reserve: list[dict[str, Any]] = []
    reserve_channels: Counter[str] = Counter()
    for row in remaining:
        if len(reserve) >= int(policy["reserve_count"]):
            break
        if reserve_channels[row["channel_name"]] >= 2:
            continue
        reserve.append(row)
        reserve_channels[row["channel_name"]] += 1
    if len(reserve) != int(policy["reserve_count"]):
        raise ValueError("Insufficient reserve candidates")
    return approved, reserve


def csv_rows(path: Path, rows: list[dict[str, Any]], decision: str) -> None:
    fields = [
        "youtube_video_id", "youtube_url", "title_original", "channel_name", "language",
        "topic", "duration_seconds", "evidence_score", "chapter_count", "caption_languages",
        "professional_source_signal", "contains_marketing_signal", "decision", "decision_reason_he",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{key: row.get(key) for key in fields if key not in {"decision", "decision_reason_he"}},
                "caption_languages": "|".join(row["caption_languages"]),
                "decision": decision,
                "decision_reason_he": (
                    "עבר סינון זמינות, שפה וראיות; ממתין לאימות תוכן סופי ותמלול לפני כתיבת הרשומה."
                    if decision == "provisional_approved"
                    else "חלופת איכות פעילה עם ראיות זמינות; תיכנס רק אם מועמד מאושר ייכשל בשער הסופי."
                ),
            })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approved-csv", type=Path, required=True)
    parser.add_argument("--reserve-csv", type=Path, required=True)
    args = parser.parse_args()
    audit = load(args.audit)
    policy = load(args.policy)
    approved, reserve = select(audit["candidates"], policy)
    approved_ids = {row["youtube_video_id"] for row in approved}
    reserve_ids = {row["youtube_video_id"] for row in reserve}
    rejected = [
        row for row in audit["candidates"]
        if row["youtube_video_id"] not in approved_ids | reserve_ids
    ]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "provisional_pending_content_review",
        "approved_count": len(approved),
        "reserve_count": len(reserve),
        "rejected_count": len(rejected),
        "approved_languages": dict(Counter(row["language"] for row in approved)),
        "approved_domains": dict(Counter(TOPIC_DOMAIN.get(row["topic"], "manual") for row in approved)),
        "approved_channels": len({row["channel_name"] for row in approved}),
        "approved_professional_signal": sum(row["professional_source_signal"] for row in approved),
        "approved_marketing_signal": sum(row["contains_marketing_signal"] for row in approved),
        "approved_ids": [row["youtube_video_id"] for row in approved],
        "reserve_ids": [row["youtube_video_id"] for row in reserve],
        "rejected_ids": [row["youtube_video_id"] for row in rejected],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_rows(args.approved_csv, approved, "provisional_approved")
    csv_rows(args.reserve_csv, reserve, "reserve")
    print(json.dumps({key: value for key, value in payload.items() if not key.endswith("_ids")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
