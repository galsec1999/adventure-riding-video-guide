#!/usr/bin/env python3
"""Apply the strict Shorts trust audit to production data.

Document version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_VERSION = "3.2.0"
TODAY = date.today().isoformat()

CATEGORY_FIELDS = {
    "sand": {
        "domain": "offroad_adventure", "subtopics": ["sand_momentum"],
        "tags": ["sand", "momentum", "traction"], "content_type": "technique", "risk_level": "medium",
    },
    "lifting": {
        "domain": "safety_recovery", "subtopics": ["bike_lift"],
        "tags": ["lifting", "body_mechanics", "recovery"], "content_type": "technique", "risk_level": "medium",
    },
    "recovery": {
        "domain": "safety_recovery", "subtopics": ["sand_mud_recovery"],
        "tags": ["recovery", "traction", "safety"], "content_type": "technique", "risk_level": "medium",
    },
    "packing_luggage": {
        "domain": "touring_travel", "subtopics": ["packing_balance"],
        "tags": ["packing", "luggage", "weight_distribution"], "content_type": "explainer", "risk_level": "low",
    },
    "electronic_aids": {
        "domain": "mixed", "subtopics": ["traction_control"],
        "tags": ["electronic_aids", "traction_control", "abs"], "content_type": "explainer", "risk_level": "low",
    },
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def trusted_items(audit: dict[str, Any], visual: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    visual_by_id = {item["youtube_video_id"]: item for item in visual["items"]}
    kept: list[dict[str, Any]] = []
    removal_reasons: Counter[str] = Counter()
    revised_items: list[dict[str, Any]] = []
    for item in audit["items"]:
        revised = dict(item)
        if item.get("decision") != "keep":
            removal_reasons[item.get("reason", "previous_audit_rejection")] += 1
            revised_items.append(revised)
            continue
        scores = item.get("topic_scores") or []
        winner = scores[0] if scores else {}
        title_and_source_agree = bool(winner.get("title_matches")) and bool(winner.get("source_supported"))
        if not title_and_source_agree:
            revised.update(decision="remove", reason="title_and_source_evidence_do_not_agree")
            removal_reasons[revised["reason"]] += 1
            revised_items.append(revised)
            continue
        visual_item = visual_by_id.get(item["youtube_video_id"])
        if not visual_item or visual_item.get("decision") != "keep":
            revised.update(decision="remove", reason="visual_review_rejected_or_missing")
            removal_reasons[revised["reason"]] += 1
            revised_items.append(revised)
            continue
        if visual_item.get("category") != item.get("proposed_category"):
            revised.update(decision="remove", reason="visual_and_text_category_disagree")
            removal_reasons[revised["reason"]] += 1
            revised_items.append(revised)
            continue
        revised.update(
            decision="keep",
            reason="title_description_and_visual_review_agree",
            classification_confidence="high",
            visual_review="passed",
        )
        revised_items.append(revised)
        kept.append({"audit": revised, "visual": visual_item})

    updated_audit = {
        **{key: value for key, value in audit.items() if key != "items"},
        "document_version": "1.1.0",
        "product_version": PRODUCT_VERSION,
        "method": "Strict title plus source-description agreement followed by individual visual review; uncertainty means removal",
        "completed_count": len(revised_items),
        "decision_counts": {"keep": len(kept), "remove": len(revised_items) - len(kept)},
        "reason_counts": dict(removal_reasons),
        "visual_reviewed_finalists": len(visual_by_id),
        "visual_review_passed": len(kept),
        "items": revised_items,
    }
    return kept, updated_audit


def build_record(original: dict[str, Any], evidence: dict[str, Any], visual: dict[str, Any], names: dict[str, dict[str, str]]) -> dict[str, Any]:
    category = evidence["proposed_category"]
    fields = CATEGORY_FIELDS[category]
    category_he = names[category]["he"]
    category_en = names[category]["en"]
    record = dict(original)
    record.update({
        "title_original": evidence.get("live_title") or original["title_original"],
        "title_he": f"קצר: {evidence.get('live_title') or original['title_original']}",
        "title_en": evidence.get("live_title") or original["title_original"],
        "channel_name": evidence.get("channel_name") or original["channel_name"],
        "duration_seconds": evidence.get("duration_seconds"),
        "domain": fields["domain"],
        "primary_category": category,
        "secondary_categories": [],
        "subtopics": fields["subtopics"],
        "content_type": fields["content_type"],
        "tags": fields["tags"],
        "risk_level": fields["risk_level"],
        "summary_he": visual["summary_he"],
        "summary_en": visual["summary_en"],
        "learning_points_he": [
            f"לזהות את הנקודה המרכזית בנושא {category_he}",
            "לבחון את ההדגמה בהקשר המלא של היוצר",
            "לעבור למקור ארוך או להדרכה מוסמכת לפני תרגול בסיכון",
        ],
        "learning_points_en": [
            f"Identify the central point about {category_en}",
            "Review the demonstration in the creator's full context",
            "Use a full source or qualified instruction before higher-risk practice",
        ],
        "fit_for_he": "מתאים כרענון קצר לאחר לימוד מלא; אינו תחליף להדרכה או להערכת תנאי השטח.",
        "fit_for_en": "Suitable as a short refresher after full study; it does not replace instruction or terrain assessment.",
        "why_watch_he": f"הכותרת, תיאור המקור והבדיקה החזותית תומכים כולם בסיווג {category_he}.",
        "why_watch_en": f"The title, source description and visual review all support the {category_en} classification.",
        "quality_score": 4,
        "quality_reason_he": "הקישור והמטא־דאטה נבדקו מחדש; הכותרת ותיאור המקור הצביעו על אותו נושא והקצר נוגן ועבר בדיקה חזותית פרטנית.",
        "quality_reason_en": "The link and metadata were rechecked; title and source description pointed to the same topic and the Short passed individual visual review.",
        "contains_marketing": False,
        "verification": {
            "link_status": "active_public",
            "metadata_verified": True,
            "content_evidence_types": ["youtube_player_description", "visual_content_review"],
            "classification_confidence": "high",
            "notes_he": f"נבדק מחדש ב־{TODAY}; לא נשמרו וידאו, אודיו, תיאור מלא או תמלול מלא.",
            "notes_en": f"Rechecked on {TODAY}; no video, audio, full description or full transcript was stored.",
        },
        "last_checked": TODAY,
        "media_format": "short",
    })
    return record


def assign_paths(paths: list[dict[str, Any]], videos: list[dict[str, Any]], shorts: list[dict[str, Any]]) -> dict[str, int]:
    long_by_id = {item["id"]: item for item in videos}
    short_groups: dict[str, list[str]] = defaultdict(list)
    for item in shorts:
        short_groups[item["primary_category"]].append(item["id"])
    category_offsets: Counter[str] = Counter()
    steps_with_shorts = 0
    references = 0
    for path in paths:
        for step in path["steps"]:
            long_ids = [*step.get("primary_video_ids", []), *step.get("alternative_video_ids", [])]
            categories = []
            for video_id in long_ids:
                video = long_by_id.get(video_id)
                if video and video["primary_category"] not in categories:
                    categories.append(video["primary_category"])
            selected: list[str] = []
            for category in categories:
                candidates = short_groups.get(category, [])
                if not candidates:
                    continue
                start = category_offsets[category] % len(candidates)
                ordered = candidates[start:] + candidates[:start]
                for short_id in ordered:
                    if short_id not in selected:
                        selected.append(short_id)
                    if len(selected) == 3:
                        break
                category_offsets[category] += 1
                if len(selected) == 3:
                    break
            step["short_video_ids"] = selected
            if selected:
                steps_with_shorts += 1
                references += len(selected)
    return {"steps_with_shorts": steps_with_shorts, "short_references": references}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "research/shorts-v3.2/content-audit.json")
    parser.add_argument("--visual", type=Path, default=ROOT / "research/shorts-v3.2/visual-review.json")
    args = parser.parse_args()

    audit = load(args.audit)
    visual = load(args.visual)
    originals = {item["youtube_video_id"]: item for item in load(ROOT / "data/shorts.json")}
    taxonomy = load(ROOT / "data/categories.json")
    names = {item["id"]: {"he": item["name_he"], "en": item["name_en"]} for item in taxonomy["categories"]}
    kept, updated_audit = trusted_items(audit, visual)
    shorts = [build_record(originals[item["audit"]["youtube_video_id"]], item["audit"], item["visual"], names) for item in kept]
    shorts.sort(key=lambda item: (item["primary_category"], item["channel_name"].casefold(), item["title_original"].casefold()))
    paths = load(ROOT / "data/learning-paths.json")
    path_stats = assign_paths(paths, load(ROOT / "data/videos.json"), shorts)

    write(args.audit, updated_audit)
    write(ROOT / "data/shorts.json", shorts)
    write(ROOT / "data/learning-paths.json", paths)
    summary = {
        "document_version": "1.0.0",
        "product_version": PRODUCT_VERSION,
        "input_shorts": len(audit["items"]),
        "published_shorts": len(shorts),
        "removed_shorts": len(audit["items"]) - len(shorts),
        "published_categories": dict(Counter(item["primary_category"] for item in shorts)),
        **path_stats,
        "policy_he": "ספק שווה הסרה: קצר נשמר רק כאשר הכותרת, תיאור המקור והבדיקה החזותית מסכימים על אותו נושא.",
        "policy_en": "Uncertainty means removal: a Short is kept only when title, source description and visual review agree on the same topic.",
    }
    write(ROOT / "reports/shorts-content-audit-v3.2.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
