#!/usr/bin/env python3
"""Finalize the individually reviewed Shorts recovery set.

Document version: 1.0.2
Product version: 3.3.0
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_VERSION = "3.3.0"
TODAY = date.today().isoformat()
SOURCE_AUDIT = ROOT / "research/shorts-v3.3/source-audit.json"
FRAME_DIR = ROOT / "research/shorts-v3.3/.visual-frames"
VISUAL_REVIEW = ROOT / "research/shorts-v3.3/visual-review.json"

# Every other item in the 180-item queue passed the two-frame live-player review.
REJECTS: dict[str, str] = {
    "bkzA8NOjea4": "product_focused_soft_luggage_promotion",
    "F4Ps-zdiFmM": "product_hype_not_neutral_instruction",
    "RB6xDvoEPLY": "product_hype_not_neutral_instruction",
    "uTNx0egqMaU": "entertainment_challenge_not_instruction",
    "zpIVLoqWJpM": "commercial_call_to_shop",
    "ZEOQh34GpIc": "affiliate_product_overview",
    "0Lg9VTF-xjc": "product_specific_glove_overview",
    "H2nAVhI-swM": "model_product_news_not_suspension_instruction",
    "K0T6W4FZHeY": "visuals_do_not_show_claimed_lifting_instruction",
    "UWMgIk13MT8": "title_bait_without_useful_maintenance_procedure",
    "hk18FsDo0gk": "topic_too_vague_for_reliable_classification",
    "nHZzEdsByz0": "commercial_career_pitch_not_riding_instruction",
    "-BvZEljF0Y0": "affiliate_product_overview",
    "_emqc79E_dI": "product_specific_phone_mount_install",
    "32M-0vvje-g": "motorcycle_product_feature_not_ergonomics_instruction",
    "A-enaN_3gIM": "motorcycle_model_promotion_not_neutral_ergonomics",
    "IekY5hZaWRA": "visuals_and_claim_do_not_support_published_category",
    "eCwbo5iJkYQ": "affiliate_product_price_promotion",
    "wGP_yyis-d4": "false_keyword_match_deer_rut_is_not_terrain_ruts",
    "pKZPshN9AaI": "unclear_tire_grinding_content_not_slow_control",
    "Or4rjLDqLhc": "product_specific_luggage_with_promo_code",
    "C-c78aYjgaA": "affiliate_product_recovery_system_overview",
    "9dTri0b4KO4": "product_specific_gps_mount_with_promo_code",
    "LsZqLRKYFsc": "scenic_entertainment_not_camping_instruction",
    "epnx-1eSPbI": "tree_example_not_motorcycle_camping_instruction",
    "2w-0y0MZjQs": "mud_event_commentary_not_instruction",
    "bk3sYQMUMCo": "model_versus_mud_entertainment_not_instruction",
    "Rzuw2jRqPKM": "affiliate_intercom_insert_and_wrong_topic_classification",
}

RECLASSIFY: dict[str, str] = {
    "L1CnCC-2U0E": "road_strategy",
    "U3K9wlWxNo0": "riding_position",
    "PGVHO_Ek0Zw": "road_strategy",
    "R1cPEPdtLYc": "motorcycle_maintenance",
    "88_KylhSysU": "road_cornering",
    "Chu_AJtcyh0": "hills",
    "ISZaZtqTLWI": "road_strategy",
    "cmA1snLY93A": "road_strategy",
    "Di4hnvdMDfc": "riding_position",
    "MK_A6IorNQE": "water_crossings",
    "cQG9xm6u4Ho": "riding_position",
    "pCWR8FIfBf4": "road_braking",
    "1_a9ml4MhjE": "road_strategy",
    "5STGXzVHkLk": "tires_setup",
    "qXkDVTkiyEY": "riding_position",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def frame_hash(video_id: str, suffix: str) -> str:
    return hashlib.sha256((FRAME_DIR / f"{video_id}-{suffix}.png").read_bytes()).hexdigest()


def old_shorts() -> list[dict[str, Any]]:
    result = subprocess.run(
        ["git", "-c", "safe.directory=*", "show", "9883232:data/shorts.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


def topic_fields(category: str, templates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    topic = templates[category]
    return {
        "domain": topic["domain"],
        "subtopics": list(topic.get("subtopics") or []),
        "tags": list(topic.get("tags") or [category]),
        "risk_level": topic.get("risk_level") or "low",
    }


def build_visual_review(source: dict[str, Any]) -> dict[str, Any]:
    by_id = {item["youtube_video_id"]: item for item in source["items"]}
    queue = source["visual_review_queue_ids"]
    items = []
    for video_id in queue:
        item = by_id[video_id]
        rejected = REJECTS.get(video_id)
        final_category = RECLASSIFY.get(video_id, item.get("proposed_category"))
        items.append({
            "youtube_video_id": video_id,
            "live_title": item.get("live_title"),
            "decision": "remove" if rejected else "keep",
            "source_category": item.get("proposed_category"),
            "final_category": None if rejected else final_category,
            "reason": rejected or "title_description_captions_and_two_live_frames_agree",
            "review_method": "two_distinct_frames_from_live_youtube_shorts_player",
            "frame_sha256": [frame_hash(video_id, "a"), frame_hash(video_id, "b")],
        })
    decisions = Counter(item["decision"] for item in items)
    return {
        "document_title": "בדיקה חזותית פרטנית לשחזור ספריית הקצרים",
        "document_version": "1.0.0",
        "product_version": PRODUCT_VERSION,
        "reviewed_on": TODAY,
        "reviewed_count": len(items),
        "decision_counts": dict(decisions),
        "policy_he": "כל מועמד נבדק בשתי נקודות זמן בנגן החי. ספק, פרסום ממוקד או אי התאמה לתוכן גוררים הסרה.",
        "policy_en": "Each candidate was reviewed at two live-player time points. Doubt, product-focused promotion, or content mismatch means removal.",
        "items": items,
    }


def build_record(original: dict[str, Any], source: dict[str, Any], review: dict[str, Any], names: dict[str, dict[str, str]], templates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    category = review["final_category"]
    fields = topic_fields(category, templates)
    title = source.get("live_title") or original["title_original"]
    category_he = names[category]["he"]
    category_en = names[category]["en"]
    record = dict(original)
    record.update({
        "title_original": title,
        "title_he": f"קצר: {title}",
        "title_en": title,
        "channel_name": source.get("channel_name") or original.get("channel_name"),
        "duration_seconds": source.get("duration_seconds"),
        "subtitle_languages": [source["caption_language"]] if source.get("caption_language") in {"he", "en"} else [],
        "domain": fields["domain"],
        "primary_category": category,
        "secondary_categories": [],
        "subtopics": fields["subtopics"],
        "tags": fields["tags"],
        "risk_level": fields["risk_level"],
        "summary_he": f"קצר מאומת בנושא „{title}”, המסווג תחת {category_he} לאחר בדיקת מקור, כתוביות ונגן חי. פתחו את המקור להקשר המלא.",
        "summary_en": f"A verified Short about “{title}”, filed under {category_en} after source, caption and live-player review. Open the source for the complete context.",
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
        "why_watch_he": f"הכותרת, התיאור, הכתוביות והבדיקה החזותית תומכים בסיווג {category_he}.",
        "why_watch_en": f"The title, description, captions and visual review support the {category_en} classification.",
        "quality_score": max(4, int(original.get("quality_score") or 0)),
        "quality_reason_he": "המטא־דאטה נאסף מחדש והקצר עבר בדיקת מקור ובדיקה חזותית פרטנית בשתי נקודות זמן.",
        "quality_reason_en": "Metadata was refreshed and the Short passed source review plus individual visual review at two time points.",
        "contains_marketing": False,
        "verification": {
            "link_status": "active_public",
            "metadata_verified": True,
            "content_evidence_types": [
                "youtube_search_metadata",
                "youtube_player_description",
                *(["captions_available"] if source.get("caption_chars") else []),
                "visual_content_review",
            ],
            "classification_confidence": "high",
            "notes_he": f"נבדק מחדש ב־{TODAY}; נבדקו שתי תמונות מהנגן החי. לא נשמרו וידאו, אודיו, תיאור מלא או תמלול מלא.",
            "notes_en": f"Rechecked on {TODAY}; two live-player frames were reviewed. No video, audio, full description or full transcript was stored.",
        },
        "last_checked": TODAY,
        "media_format": "short",
    })
    return record


def assign_paths(paths: list[dict[str, Any]], videos: list[dict[str, Any]], shorts: list[dict[str, Any]]) -> dict[str, int]:
    long_by_id = {item["id"]: item for item in videos}
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in shorts:
        grouped[item["primary_category"]].append(item["id"])
    offsets: Counter[str] = Counter()
    steps_with_shorts = references = 0
    for path in paths:
        for step in path["steps"]:
            categories: list[str] = []
            for video_id in [*step.get("primary_video_ids", []), *step.get("alternative_video_ids", [])]:
                video = long_by_id.get(video_id)
                if video and video["primary_category"] not in categories:
                    categories.append(video["primary_category"])
            selected: list[str] = []
            for category in categories:
                candidates = grouped.get(category, [])
                if not candidates:
                    continue
                start = offsets[category] % len(candidates)
                for short_id in candidates[start:] + candidates[:start]:
                    if short_id not in selected:
                        selected.append(short_id)
                    if len(selected) == 3:
                        break
                offsets[category] += 1
                if len(selected) == 3:
                    break
            step["short_video_ids"] = selected
            steps_with_shorts += bool(selected)
            references += len(selected)
    return {"steps_with_shorts": steps_with_shorts, "short_references": references}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    source = load(SOURCE_AUDIT)
    visual = build_visual_review(source)
    write(VISUAL_REVIEW, visual)
    reviews = {item["youtube_video_id"]: item for item in visual["items"]}
    sources = {item["youtube_video_id"]: item for item in source["items"]}
    original_list = old_shorts()
    originals = {item["youtube_video_id"]: item for item in original_list}
    templates = {}
    for item in original_list:
        templates.setdefault(item["primary_category"], item)
    taxonomy = load(ROOT / "data/categories.json")
    names = {item["id"]: {"he": item["name_he"], "en": item["name_en"]} for item in taxonomy["categories"]}
    kept_ids = [video_id for video_id in source["visual_review_queue_ids"] if reviews[video_id]["decision"] == "keep"]
    shorts = [build_record(originals[video_id], sources[video_id], reviews[video_id], names, templates) for video_id in kept_ids]
    shorts.sort(key=lambda item: (item["primary_category"], item["channel_name"].casefold(), item["title_original"].casefold()))
    paths = load(ROOT / "data/learning-paths.json")
    path_stats = assign_paths(paths, load(ROOT / "data/videos.json"), shorts)
    write(ROOT / "data/shorts.json", shorts)
    write(ROOT / "data/learning-paths.json", paths)
    summary = {
        "document_title": "דוח שחזור והרחבת ספריית הקצרים",
        "document_version": "1.0.0",
        "product_version": PRODUCT_VERSION,
        "source_audited": source["completed_count"],
        "source_candidates": source["preliminary_decision_counts"]["candidate"],
        "visual_reviewed": visual["reviewed_count"],
        "published_shorts": len(shorts),
        "visual_rejected": visual["decision_counts"].get("remove", 0),
        "published_categories": dict(Counter(item["primary_category"] for item in shorts)),
        **path_stats,
    }
    write(ROOT / "reports/shorts-recovery-v3.3.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
