#!/usr/bin/env python3
"""Build a source-backed visual-review queue for the 3.3 Shorts recovery.

Document version: 1.0.0

The tool reads the preserved 3.2 audit, refreshes public YouTube metadata with
yt-dlp, and reads public caption tracks in memory when they are available. It
never downloads video or audio and does not persist descriptions or complete
transcripts. Its output is a candidate queue, not a publication decision:
every selected item still requires an individual visual review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import threading
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_shorts_content import (
    EDUCATIONAL_RE,
    ENTERTAINMENT_RE,
    PROMO_RE,
    TOPICS,
    normalize,
    sha256_text,
    topic_scores,
)


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
DOCUMENT_VERSION = "1.0.0"
PRODUCT_VERSION = "3.3.0"

HARD_SALES_RE = re.compile(
    r"\b(?:sale|discount|coupon|promo code|use code|shop now|last chance|book now|"
    r"register now|affiliate|sponsored by|buy now|pre[- ]?order|rental fleet|"
    r"in stock|free shipping|available now|shop our|order yours|view products?)\b",
    re.I,
)

FALSE_NAVIGATION_RE = re.compile(
    r"\b(?:tractionator gps|gps (?:tire|tyre)|gpx tse|gpx moto)\b",
    re.I,
)

# Recovery cues are intentionally broader than the 3.2 publication patterns.
# They only build a visual-review queue; they can never publish a record by
# themselves. Agreement with a public description or caption is still required.
RECOVERY_CUES: dict[str, tuple[str, ...]] = {
    "intercoms_communications": (r"\bintercoms?\b", r"\bcardo\b", r"\bsena\b", r"\bmesh communication\b", r"\bbluetooth headset\b"),
    "route_navigation": (r"\bnavigation\b", r"\bgpx\b", r"\bgps\b", r"\broad ?book\b", r"\bgarmin\b", r"\bosmand\b", r"\broute planning\b", r"\boffline maps?\b"),
    "protective_gear": (r"\bhelmets?\b", r"\bboots?\b", r"\bgloves?\b", r"\barmo(?:u)?r\b", r"\bairbag vest\b", r"\bprotective gear\b"),
    "tires_setup": (r"\btires?\b", r"\btyres?\b", r"\btire pressure\b", r"\bair[- ]?down\b", r"\btubeless\b", r"\bknobb(?:y|ie)\b", r"\bmousse\b"),
    "suspension_setup": (r"\bsuspension\b", r"\bforks?\b", r"\bshocks?\b", r"\bpreload\b", r"\brebound\b", r"\bcompression damping\b", r"\bsag\b"),
    "motorcycle_maintenance": (r"\bmaintenance\b", r"\boil change\b", r"\bchain (?:slack|clean|lube|care)\b", r"\bair filter\b", r"\bcoolant\b", r"\bbrake fluid\b"),
    "roadside_repairs": (r"\broadside repair\b", r"\btrail repair\b", r"\bflat tire\b", r"\bpuncture\b", r"\btool ?kit\b", r"\btire plug\b"),
    "packing_luggage": (r"\bpacking\b", r"\bluggage\b", r"\bpanniers?\b", r"\bsoft bags?\b", r"\bweight distribution\b"),
    "motorcycle_camping": (r"\bcamping\b", r"\bcampsite\b", r"\btents?\b", r"\bsleep system\b", r"\bcamp kitchen\b"),
    "trip_preparation": (r"\btrip prep", r"\btrip checklist\b", r"\bpre[- ]?ride checklist\b", r"\bbefore (?:the|your|a) trip\b"),
    "group_riding": (r"\bgroup rid", r"\bformation\b", r"\bride leader\b", r"\bsweep rider\b"),
    "fatigue_management": (r"\bfatigue\b", r"\bdehydration\b", r"\bhydration\b", r"\brider tired\b"),
    "lifting": (r"\bpick(?:ing)? up (?:a |the |your )?(?:bike|motorcycle)\b", r"\blift(?:ing)? (?:a |the |your )?(?:bike|motorcycle)\b", r"\bdropped bike\b"),
    "recovery": (r"\brecovery\b", r"\bunstuck\b", r"\btow(?:ing)?\b", r"\bwinch(?:ing)?\b", r"\bstuck bike\b"),
    "water_crossings": (r"\bwater crossing\b", r"\briver crossing\b", r"\bstream crossing\b"),
    "mud_wet": (r"\bmud(?:dy)?\b", r"\bwet terrain\b", r"\bslippery dirt\b"),
    "sand": (r"\bsand\b", r"\bsandy\b", r"\bdunes?\b"),
    "ruts": (r"\bruts?\b", r"\brutted\b"),
    "loose_rock": (r"\bloose rocks?\b", r"\brock garden\b", r"\brocky trail\b", r"\bbaby heads?\b"),
    "obstacles": (r"\bobstacles?\b", r"\blog crossing\b", r"\bwheel lift\b", r"\bledge\b", r"\brock step\b", r"\bpivot turn\b"),
    "hills": (r"\bhill climb\b", r"\buphill\b", r"\bclimb(?:ing)? (?:a |the )?hill\b", r"\bsteep hill\b"),
    "descents": (r"\bdownhill\b", r"\bdescents?\b", r"\bdescending\b", r"\bdown (?:a |the )?steep hill\b"),
    "offroad_braking": (r"\boff[- ]?road brak", r"\bbrak(?:e|ing) (?:on|in) (?:dirt|gravel)\b", r"\bfront brake (?:on|in) dirt\b"),
    "gravel_dirt": (r"\bgravel\b", r"\bdirt road\b", r"\bloose surface\b"),
    "offroad_turning": (r"\boff[- ]?road (?:turn|corner)", r"\bturn(?:ing)? (?:on|in) dirt\b", r"\bcounterbalance\b", r"\bskid turn\b"),
    "offroad_basics": (r"\boff[- ]?road\b", r"\badventure riding\b", r"\badv riding\b", r"\btrail riding\b"),
    "emergency_braking": (r"\bemergency braking\b", r"\bpanic braking\b", r"\bmaximum braking\b", r"\bquick stop\b", r"\bstopping distance\b"),
    "road_braking": (r"\bbraking\b", r"\bfront brake\b", r"\brear brake\b", r"\btrail braking\b", r"\bstop(?:ping)?\b"),
    "road_cornering": (r"\bcornering\b", r"\bcorners?\b", r"\bapex\b", r"\bcountersteer", r"\blean angle\b", r"\bturn entry\b"),
    "u_turns_low_speed": (r"\bu[- ]?turns?\b", r"\bfull[- ]?lock\b", r"\bfigure eights?\b", r"\btight circles?\b"),
    "balance_slow_control": (r"\bslow[- ]?speed\b", r"\bbalance\b", r"\bwalking pace\b", r"\bcoordination test\b"),
    "controls_coordination": (r"\bfriction zone\b", r"\bclutch control\b", r"\bthrottle control\b", r"\bclutch and throttle\b", r"\bcoordinate (?:the )?controls\b"),
    "riding_position": (r"\bbody position\b", r"\briding position\b", r"\bstanding position\b", r"\bweight transfer\b", r"\bweightless rider\b"),
    "ergonomics": (r"\bergonomics\b", r"\bhandlebars?\b", r"\blever position\b", r"\bfoot ?pegs?\b", r"\bbar risers?\b", r"\bseat height\b"),
    "electronic_aids": (r"\btraction control\b", r"\babs\b", r"\briding modes?\b", r"\brider aids?\b"),
    "road_strategy": (r"\bhazard\b", r"\blane position\b", r"\bescape route\b", r"\bfollowing distance\b", r"\bblind spots?\b", r"\bintersection\b"),
    "drills": (r"\bdrills?\b", r"\bexercise\b", r"\bpractice\b", r"\btraining\b"),
    "bike_selection": (r"\bchoose (?:a |an )?(?:bike|motorcycle)\b", r"\bbeginner (?:adv|adventure|dual sport)\b", r"\bwhich (?:adv|adventure|dual sport)\b", r"\bheavy (?:vs|versus) light\b"),
}

STOPWORDS = {
    "about", "after", "again", "against", "also", "because", "before", "being", "best",
    "bike", "can", "could", "does", "doing", "from", "have", "here", "into", "just",
    "more", "most", "motorcycle", "motorcycles", "much", "need", "only", "other", "our",
    "rider", "riders", "riding", "short", "should", "some", "than", "that", "their", "them",
    "then", "there", "these", "they", "this", "through", "tips", "using", "very", "video",
    "want", "what", "when", "where", "which", "while", "with", "would", "your", "youre",
}

_thread_state = threading.local()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def yt_dlp_class(module_dir: Path):
    module_text = str(module_dir.resolve())
    if module_text not in sys.path:
        sys.path.insert(0, module_text)
    from yt_dlp import YoutubeDL  # type: ignore

    return YoutubeDL


def ydl_instance(module_dir: Path):
    instance = getattr(_thread_state, "ydl", None)
    if instance is None:
        YoutubeDL = yt_dlp_class(module_dir)
        instance = YoutubeDL({
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "extract_flat": False,
            "socket_timeout": 30,
            "retries": 2,
            "extractor_retries": 2,
            "js_runtimes": {"node": {}},
        })
        _thread_state.ydl = instance
    return instance


def caption_track(info: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    pools = (info.get("subtitles") or {}, info.get("automatic_captions") or {})
    preferred_codes = ("en", "en-orig", "en-US", "en-GB")
    for pool in pools:
        for code in preferred_codes:
            tracks = pool.get(code) or []
            json_track = next((track for track in tracks if track.get("ext") == "json3"), None)
            if json_track and json_track.get("url"):
                return code, json_track
        for code, tracks in pool.items():
            if not str(code).startswith("en"):
                continue
            json_track = next((track for track in tracks if track.get("ext") == "json3"), None)
            if json_track and json_track.get("url"):
                return str(code), json_track
    return None, None


def read_caption(info: dict[str, Any]) -> tuple[str, str | None]:
    language, track = caption_track(info)
    if not track:
        return "", language
    request = urllib.request.Request(track["url"], headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.loads(response.read(2_500_000).decode("utf-8", errors="replace"))
    except Exception:
        return "", language
    parts = []
    for event in payload.get("events", []):
        for segment in event.get("segs", []):
            text = segment.get("utf8")
            if text and text != "\n":
                parts.append(str(text))
    return normalize(" ".join(parts))[:20_000], language


def meaningful_tokens(value: str) -> set[str]:
    tokens = {token for token in re.findall(r"[a-z][a-z0-9'-]{2,}", value.casefold())}
    return {token for token in tokens if token not in STOPWORDS}


def overlap_evidence(title: str, source: str) -> list[str]:
    return sorted(meaningful_tokens(title) & meaningful_tokens(source))


def matches(pattern: re.Pattern[str], value: str) -> list[str]:
    return sorted({match.group(0).casefold() for match in pattern.finditer(value)})


def topic_for_category(category: str | None):
    return next((topic for topic in TOPICS if topic.category == category), None)


def exclusion_hits(category: str | None, combined: str) -> list[str]:
    topic = topic_for_category(category)
    if not topic:
        return []
    return sorted({m.group(0).casefold() for pattern in topic.exclusions for m in re.finditer(pattern, combined, re.I)})


def recovery_topic_scores(title: str, description: str, caption: str, prior_category: str | None) -> list[dict[str, Any]]:
    combined = " ".join((title, description, caption))
    results: list[dict[str, Any]] = []
    for category, patterns in RECOVERY_CUES.items():
        exclusions = exclusion_hits(category, combined)
        if exclusions:
            continue
        title_hits = sorted({m.group(0).casefold() for pattern in patterns for m in re.finditer(pattern, title, re.I)})
        description_hits = sorted({m.group(0).casefold() for pattern in patterns for m in re.finditer(pattern, description, re.I)})
        caption_hits = sorted({m.group(0).casefold() for pattern in patterns for m in re.finditer(pattern, caption, re.I)})
        score = 5 * len(title_hits) + 2 * len(description_hits) + 3 * len(caption_hits)
        if category == prior_category and score:
            score += 1
        if score:
            topic = topic_for_category(category)
            results.append({
                "category": category,
                "domain": topic.domain if topic else None,
                "score": score,
                "title_matches": title_hits,
                "description_matches": description_hits,
                "caption_matches": caption_hits,
                "source_supported": bool(description_hits or caption_hits),
            })
    return sorted(results, key=lambda item: (-int(item["score"]), item["category"]))


def classify_source(record: dict[str, Any], info: dict[str, Any], caption: str, caption_language: str | None) -> dict[str, Any]:
    title = normalize(str(info.get("title") or record.get("published_title") or ""))
    description = normalize(str(info.get("description") or ""))
    combined = " ".join((title, description, caption))
    prior_category = record.get("published_category")
    strict_scores = topic_scores(title, description, caption)
    scores = recovery_topic_scores(title, description, caption, prior_category)
    # The old published category is only a one-point tie-breaker inside
    # recovery_topic_scores; it must never override stronger live evidence.
    winner = scores[0] if scores else None
    title_description_overlap = overlap_evidence(title, description)
    title_caption_overlap = overlap_evidence(title, caption)
    educational_hits = matches(EDUCATIONAL_RE, combined)
    description_marketing_hits = matches(PROMO_RE, description)
    title_sales_hits = matches(HARD_SALES_RE, title)
    caption_sales_hits = matches(HARD_SALES_RE, caption)
    prior_exclusions = exclusion_hits(prior_category, combined)
    false_navigation = bool(prior_category == "route_navigation" and FALSE_NAVIGATION_RE.search(combined))

    source_topic_supported = bool(
        winner
        and (
            winner.get("description_matches")
            or winner.get("caption_matches")
            or len(title_description_overlap) >= 2
            or len(title_caption_overlap) >= 2
        )
    )
    instructional_source = bool(
        educational_hits
        or (winner and len(winner.get("caption_matches") or []) >= 1)
        or len(title_caption_overlap) >= 3
    )
    entertainment = bool(ENTERTAINMENT_RE.search(title))
    commercial_focus = bool(title_sales_hits or (caption_sales_hits and not instructional_source))

    reason = "candidate_for_visual_review"
    preliminary = "candidate"
    if info.get("availability") not in (None, "public"):
        preliminary, reason = "remove", "not_public"
    elif int(info.get("duration") or 0) not in range(1, 181):
        preliminary, reason = "remove", "not_short_duration"
    elif false_navigation or prior_exclusions:
        preliminary, reason = "remove", "known_false_semantic_match"
    elif entertainment:
        preliminary, reason = "remove", "entertainment_or_ride_footage"
    elif commercial_focus:
        preliminary, reason = "remove", "commercial_content_focus"
    elif len(description) < 20 and len(caption) < 60:
        preliminary, reason = "remove", "insufficient_source_evidence"
    elif not winner:
        preliminary, reason = "remove", "no_taxonomy_topic"
    elif not source_topic_supported:
        preliminary, reason = "remove", "topic_not_supported_by_source"
    elif not instructional_source:
        preliminary, reason = "remove", "no_instructional_evidence"

    score = 0
    if preliminary == "candidate":
        score += 5
        score += 3 if caption else 0
        score += 2 if description else 0
        score += min(3, len(educational_hits))
        score += min(3, len(title_caption_overlap))
        score += min(2, len(title_description_overlap))
        score += 2 if winner and winner.get("title_matches") else 0
        score += 3 if winner and winner.get("caption_matches") else 0
        score -= 1 if description_marketing_hits else 0
        score -= 1 if winner and winner.get("category") != prior_category else 0

    return {
        "youtube_video_id": record["youtube_video_id"],
        "published_title": record.get("published_title"),
        "published_category": prior_category,
        "live_title": title,
        "channel_name": info.get("uploader") or info.get("channel") or record.get("channel_name"),
        "duration_seconds": int(info.get("duration") or 0) or None,
        "availability": info.get("availability") or "public",
        "description_chars": len(description),
        "description_sha256": sha256_text(description),
        "caption_language": caption_language,
        "caption_chars": len(caption),
        "caption_sha256": sha256_text(caption),
        "title_description_overlap": title_description_overlap[:12],
        "title_caption_overlap": title_caption_overlap[:12],
        "educational_markers": educational_hits[:12],
        "description_marketing_markers": description_marketing_hits[:12],
        "title_sales_markers": title_sales_hits[:12],
        "caption_sales_markers": caption_sales_hits[:12],
        "known_exclusions": prior_exclusions,
        "topic_scores": scores[:3],
        "strict_topic_scores": strict_scores[:3],
        "proposed_category": winner.get("category") if winner else None,
        "proposed_domain": winner.get("domain") if winner else None,
        "category_changed": bool(winner and winner.get("category") != prior_category),
        "candidate_score": score,
        "preliminary_decision": preliminary,
        "reason": reason,
        "visual_review_required": preliminary == "candidate",
        "source_evidence": [
            source for source, available in (
                ("youtube_title", bool(title)),
                ("youtube_description", bool(description)),
                ("youtube_captions", bool(caption)),
            ) if available
        ],
    }


def recover_one(record: dict[str, Any], module_dir: Path) -> dict[str, Any]:
    video_id = record["youtube_video_id"]
    try:
        info = ydl_instance(module_dir).extract_info(
            f"https://www.youtube.com/shorts/{video_id}",
            download=False,
        )
        if not isinstance(info, dict):
            raise ValueError("yt-dlp returned no metadata")
        caption, caption_language = read_caption(info)
        return classify_source(record, info, caption, caption_language)
    except Exception as exc:
        return {
            "youtube_video_id": video_id,
            "published_title": record.get("published_title"),
            "published_category": record.get("published_category"),
            "channel_name": record.get("channel_name"),
            "candidate_score": 0,
            "preliminary_decision": "remove",
            "reason": "fetch_or_parse_failure",
            "error": str(exc)[:500],
            "visual_review_required": False,
            "source_evidence": [],
        }


def balanced_queue(items: list[dict[str, Any]], per_category: int, limit: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item.get("preliminary_decision") != "candidate":
            continue
        groups[str(item.get("proposed_category") or item.get("published_category") or "unknown")].append(item)
    for group in groups.values():
        group.sort(key=lambda item: (-int(item.get("candidate_score") or 0), str(item.get("youtube_video_id"))))
    queue: list[dict[str, Any]] = []
    for category in sorted(groups):
        queue.extend(groups[category][:per_category])
    queue.sort(key=lambda item: (-int(item.get("candidate_score") or 0), str(item.get("proposed_category")), str(item.get("youtube_video_id"))))
    return queue[:limit] if limit else queue


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "research" / "shorts-v3.2" / "content-audit.json")
    parser.add_argument("--candidate-source", type=Path, default=ROOT / "research" / "shorts-v3.1" / "candidates.json")
    parser.add_argument("--yt-dlp-module-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "research" / "shorts-v3.3" / "source-audit.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--queue-limit", type=int, default=180)
    parser.add_argument("--per-category", type=int, default=8)
    parser.add_argument("--include-existing", action="store_true")
    parser.add_argument("--rebuild-existing", action="store_true")
    args = parser.parse_args()

    if args.rebuild_existing:
        report = load_json(args.output)
        results = report.get("items", [])
        for item in results:
            scores = item.get("topic_scores") or []
            if item.get("preliminary_decision") == "candidate" and scores:
                winner = scores[0]
                item["proposed_category"] = winner.get("category")
                item["proposed_domain"] = winner.get("domain")
                item["category_changed"] = winner.get("category") != item.get("published_category")
        queue = balanced_queue(results, max(1, args.per_category), max(0, args.queue_limit))
        queue_ids = {item["youtube_video_id"] for item in queue}
        for item in results:
            item["selected_for_visual_review"] = item["youtube_video_id"] in queue_ids
        report["generated_at"] = utc_now()
        report["candidate_categories"] = dict(Counter(
            item.get("proposed_category") for item in results if item.get("preliminary_decision") == "candidate"
        ))
        report["visual_review_queue_count"] = len(queue)
        report["visual_review_queue_ids"] = [item["youtube_video_id"] for item in queue]
        write_json(args.output, report)
        print(json.dumps({
            "candidate_categories": report["candidate_categories"],
            "visual_review_queue_count": report["visual_review_queue_count"],
        }, ensure_ascii=False, indent=2))
        return 0

    old_audit = load_json(args.audit)
    candidate_source = load_json(args.candidate_source)
    candidate_map = {item["youtube_video_id"]: item for item in candidate_source.get("candidates", [])}
    records = []
    for item in old_audit.get("items", []):
        if not args.include_existing and item.get("decision") == "keep":
            continue
        merged = dict(item)
        original = candidate_map.get(item["youtube_video_id"], {})
        merged.setdefault("channel_name", original.get("channel_name"))
        merged.setdefault("published_title", original.get("title_original"))
        records.append(merged)
    if args.limit:
        records = records[: args.limit]

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(recover_one, record, args.yt_dlp_module_dir): record for record in records}
        completed = 0
        for future in as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed % 25 == 0 or completed == len(records):
                print(f"Recovered {completed}/{len(records)}", flush=True)

    results.sort(key=lambda item: str(item.get("youtube_video_id")))
    queue = balanced_queue(results, max(1, args.per_category), max(0, args.queue_limit))
    queue_ids = {item["youtube_video_id"] for item in queue}
    for item in results:
        item["selected_for_visual_review"] = item["youtube_video_id"] in queue_ids

    report = {
        "document_version": DOCUMENT_VERSION,
        "product_version": PRODUCT_VERSION,
        "generated_at": utc_now(),
        "method": "yt-dlp public metadata and public captions in memory, followed by mandatory individual visual review",
        "video_or_audio_downloaded": False,
        "full_descriptions_or_transcripts_stored": False,
        "input_count": len(records),
        "completed_count": len(results),
        "preliminary_decision_counts": dict(Counter(item.get("preliminary_decision") for item in results)),
        "reason_counts": dict(Counter(item.get("reason") for item in results)),
        "candidate_categories": dict(Counter(item.get("proposed_category") for item in results if item.get("preliminary_decision") == "candidate")),
        "visual_review_queue_count": len(queue),
        "visual_review_queue_ids": [item["youtube_video_id"] for item in queue],
        "items": results,
    }
    write_json(args.output, report)
    print(json.dumps({key: report[key] for key in (
        "input_count", "completed_count", "preliminary_decision_counts", "reason_counts",
        "candidate_categories", "visual_review_queue_count",
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
