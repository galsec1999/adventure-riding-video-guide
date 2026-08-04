#!/usr/bin/env python3
"""Audit candidate metadata and evidence without authoring production content.

The input reports may temporarily contain full YouTube descriptions outside the
repository. Outputs intentionally retain only hashes, lengths and review facts;
full descriptions and transcripts are never copied into the project.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
LATIN_RE = re.compile(r"[a-z]", re.IGNORECASE)
NON_INSTRUCTIONAL_RE = re.compile(
    r"(?:\bvlog\b|\breview\b|\bfirst ride\b|\btest ride\b|\bcrash\b|"
    r"\bcompilation\b|\bpodcast\b|\bnews\b|\bwalk ?around\b|\bpromo\b|"
    r"טיול|מסע|סקירה|חדשות|תאונה|כמעט ונפגע|רכיבה ראשונה|קורס.*מבט מבפנים|"
    r"מסלול טסט|טסט אופנוע|מבחן שליטה|רישיון|מירוץ|אליפות)",
    re.IGNORECASE,
)
MARKETING_RE = re.compile(
    r"(?:affiliate|sponsor|sponsored|discount code|use code|patreon|merch|"
    r"shop\b|store\b|buy now|book (?:a )?(?:course|class)|קוד קופון|חסות|"
    r"לרכישה|חנות|מבצע|הזמינו|קורס בתשלום)",
    re.IGNORECASE,
)
PROFESSIONAL_RE = re.compile(
    r"(?:school|academy|training|instructor|coach|safety|roadcraft|institute|"
    r"foundation|stay upright|champ ?school|motojitsu|motorcycle lessons|"
    r"riding smart|pro.?riding|מדרי(?:ך|כה)|הדרכ(?:ה|ת)|בית ספר|בטיחות בדרכים|"
    r"פרוריידינג|רלב[\"״]?ד|משה פרחי)",
    re.IGNORECASE,
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_language(item: dict[str, Any]) -> tuple[str | None, str]:
    declared = str(item.get("language") or "").casefold()
    title = str(item.get("title_original") or "")
    description = str(item.get("description") or "")
    visible = title + " " + description[:2000]
    he_count = len(HEBREW_RE.findall(visible))
    latin_count = len(LATIN_RE.findall(visible))
    if declared in {"he", "iw"}:
        return "he", f"declared_language={declared}"
    if he_count >= 24 and he_count >= latin_count * 0.18:
        return "he", f"hebrew_text_signal={he_count}"
    if declared and declared not in {"en", "und", "none"}:
        return None, f"unsupported_declared_language={declared}"
    if latin_count >= 24 or declared == "en":
        return "en", f"declared_or_text_english={declared or 'text'}"
    return None, "language_not_verifiable_as_he_or_en"


def choose_topic(matches: list[dict[str, Any]]) -> str:
    eligible = [item for item in matches if item.get("topic") != "required_seed"]
    source = eligible or matches
    if not source:
        return "unclassified"
    return str(min(source, key=lambda item: (int(item.get("rank", 999)), str(item.get("topic"))))["topic"])


def audit_candidate(
    item: dict[str, Any],
    plan_item: dict[str, Any],
    existing_ids: set[str],
) -> dict[str, Any]:
    video_id = str(item.get("youtube_video_id") or plan_item.get("youtube_video_id") or "")
    status = item.get("status")
    language, language_reason = normalize_language(item) if status == "pass" else (None, "source_unavailable")
    title = str(item.get("title_original") or plan_item.get("title_original") or "")
    description = str(item.get("description") or "")
    duration = item.get("duration_seconds")
    chapters = item.get("chapters") or []
    subtitles = sorted(set((item.get("subtitle_languages") or []) + (item.get("automatic_caption_languages") or [])))
    topic = choose_topic(plan_item.get("search_matches") or [])
    reasons: list[str] = []
    blockers: list[str] = []

    if status != "pass" or item.get("availability") != "public":
        blockers.append("source_not_active_public")
    if video_id in existing_ids:
        blockers.append("already_in_production")
    if language not in {"he", "en"}:
        blockers.append(language_reason)
    if not isinstance(duration, (int, float)):
        blockers.append("duration_missing")
    elif duration < 60:
        blockers.append("too_short_for_release_depth")
    elif duration > 5400:
        blockers.append("too_long_for_focused_guide_entry")
    if not description.strip():
        blockers.append("description_missing")
    if not chapters and not subtitles:
        blockers.append("no_chapters_or_captions_for_content_evidence")
    if NON_INSTRUCTIONAL_RE.search(title):
        blockers.append("title_indicates_non_instructional_or_promotional_content")

    description_hash = hashlib.sha256(description.encode("utf-8")).hexdigest()
    contains_marketing = bool(MARKETING_RE.search(description))
    source_professional_signal = bool(
        PROFESSIONAL_RE.search(str(item.get("channel_name") or "") + " " + description[:1200])
    )
    if chapters:
        reasons.append(f"youtube_chapters={len(chapters)}")
    if subtitles:
        reasons.append(f"caption_tracks={len(subtitles)}")
    if source_professional_signal:
        reasons.append("professional_source_signal")
    if contains_marketing:
        reasons.append("marketing_signal_present")

    evidence_score = 0
    evidence_score += 3 if subtitles else 0
    evidence_score += 2 if chapters else 0
    evidence_score += 2 if len(description) >= 400 else 1 if description else 0
    evidence_score += 2 if source_professional_signal else 0
    evidence_score += 1 if isinstance(duration, (int, float)) and 120 <= duration <= 1800 else 0
    evidence_score -= 2 if contains_marketing else 0

    decision = "rejected" if blockers else "eligible_for_content_review"
    decision_reason = "; ".join(blockers or reasons or ["metadata_and_evidence_available"])
    return {
        "youtube_video_id": video_id,
        "youtube_url": item.get("youtube_url") or plan_item.get("youtube_url"),
        "title_original": title,
        "channel_name": item.get("channel_name") or plan_item.get("channel_name"),
        "channel_id": item.get("channel_id") or plan_item.get("channel_id"),
        "published_date": item.get("published_date"),
        "duration_seconds": duration,
        "availability": item.get("availability"),
        "language": language,
        "language_evidence": language_reason,
        "topic": topic,
        "search_matches": plan_item.get("search_matches") or [],
        "description_checked": status == "pass",
        "description_characters": len(description),
        "description_sha256": description_hash,
        "youtube_chapters_checked": status == "pass",
        "chapter_count": len(chapters),
        "chapters": chapters,
        "captions_checked": status == "pass",
        "caption_languages": subtitles,
        "contains_marketing_signal": contains_marketing,
        "professional_source_signal": source_professional_signal,
        "evidence_score": evidence_score,
        "preliminary_decision": decision,
        "decision_reason": decision_reason,
        "source_error": item.get("error"),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "youtube_video_id",
        "youtube_url",
        "title_original",
        "channel_name",
        "language",
        "topic",
        "duration_seconds",
        "availability",
        "description_checked",
        "description_characters",
        "youtube_chapters_checked",
        "chapter_count",
        "captions_checked",
        "caption_languages",
        "contains_marketing_signal",
        "professional_source_signal",
        "evidence_score",
        "preliminary_decision",
        "decision_reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            copy = dict(row)
            copy["caption_languages"] = "|".join(row["caption_languages"])
            writer.writerow(copy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--batch-glob", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--hebrew-csv", type=Path, required=True)
    parser.add_argument("--existing", type=Path, default=ROOT / "data" / "videos.json")
    args = parser.parse_args()

    plan = load(args.plan)
    plan_items = {item["youtube_video_id"]: item for item in plan["selected"]}
    reports = [load(Path(path)) for path in sorted(glob.glob(args.batch_glob))]
    raw = [item for report in reports for item in report["results"]]
    existing_ids = {item["youtube_video_id"] for item in load(args.existing)}
    rows = [
        audit_candidate(item, plan_items.get(str(item.get("youtube_video_id")), {}), existing_ids)
        for item in raw
    ]
    # Failed extracts do not expose an ID. Re-associate them by URL from the plan.
    by_url = {item["youtube_url"]: item for item in plan["selected"]}
    for row, item in zip(rows, raw):
        if not row["youtube_video_id"] and item.get("youtube_url") in by_url:
            plan_item = by_url[item["youtube_url"]]
            replacement = audit_candidate(item, plan_item, existing_ids)
            row.clear()
            row.update(replacement)

    summary = {
        "checked": len(rows),
        "unique_ids": len({row["youtube_video_id"] for row in rows}),
        "active_public": sum(row["availability"] == "public" for row in rows),
        "eligible": sum(row["preliminary_decision"] == "eligible_for_content_review" for row in rows),
        "rejected": sum(row["preliminary_decision"] == "rejected" for row in rows),
        "languages": dict(Counter(str(row["language"]) for row in rows)),
        "hebrew_checked": sum(row["language"] == "he" for row in rows),
        "caption_available": sum(bool(row["caption_languages"]) for row in rows),
        "with_chapters": sum(row["chapter_count"] > 0 for row in rows),
        "professional_signal": sum(row["professional_source_signal"] for row in rows),
        "marketing_signal": sum(row["contains_marketing_signal"] for row in rows),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "audit_only": True,
            "full_descriptions_persisted_in_project": False,
            "preliminary_decision_requires_manual_content_review_before_approval": True,
        },
        "summary": summary,
        "candidates": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv, rows)
    write_csv(args.hebrew_csv, [row for row in rows if row["language"] == "he"])
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
