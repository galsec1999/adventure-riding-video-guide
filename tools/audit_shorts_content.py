#!/usr/bin/env python3
"""Re-audit YouTube Shorts with source-backed semantic evidence.

Document version: 1.0.0

The tool fetches YouTube's public player metadata and, when available, caption
tracks. It never downloads video or audio and never persists descriptions or
full transcripts. The output contains hashes, counts, matched concepts and the
decision needed to reproduce a conservative content audit.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"


@dataclass(frozen=True)
class Topic:
    category: str
    domain: str
    patterns: tuple[str, ...]
    exclusions: tuple[str, ...] = ()


# Phrases are intentionally semantic rather than single-token keyword matches.
# A hit in title alone is discovery evidence only and can never approve a Short.
TOPICS = (
    Topic("intercoms_communications", "touring_travel", (
        r"\b(?:motorcycle|helmet|rider) intercom\b", r"\b(?:cardo|sena) (?:mesh|intercom|communication)\b",
        r"\bbluetooth (?:intercom|communication|headset)\b", r"\bmesh communication\b")),
    Topic("route_navigation", "touring_travel", (
        r"\b(?:motorcycle|adv|rally) navigation\b", r"\bnavigat(?:e|ing|ion) (?:a |the )?(?:route|trail|track|road)\b",
        r"\bgpx (?:file|track|route|import|export|navigation)\b", r"\b(?:gps|garmin) (?:navigation|unit|device|mount|setup)\b",
        r"\broad ?book (?:navigation|route|holder|setup|rally)\b", r"\broute plan(?:ning)?\b", r"\boffline maps?\b",
        r"\b(?:osmand|gaia gps|calimoto|rever|garmin z[ūu]mo|garmin tread)\b"),
        (r"\btractionator gps\b", r"\bgps (?:tire|tyre)\b", r"\bgpx tse\b", r"\bgpx moto\b")),
    Topic("protective_gear", "safety_recovery", (
        r"\bhelmet (?:fit|size|safety|rating|protection|choice|comparison)\b", r"\b(?:body )?armo(?:u)?r (?:fit|protection|rating|choice)\b",
        r"\b(?:motorcycle|riding) (?:boots?|jackets?|gloves?) (?:fit|protection|safety|choice|comparison)\b",
        r"\bairbag (?:vest|jacket|protection|system)\b", r"\bimpact protection\b", r"\babrasion resistance\b")),
    Topic("tires_setup", "mixed", (
        r"\b(?:motorcycle|adv|off[- ]?road) (?:tire|tyre)s?\b", r"\b(?:tire|tyre) pressure\b", r"\bair(?:ing)? down (?:the )?(?:tire|tyre)s?\b",
        r"\b(?:knobby|knobbie|mousse|tubeless) (?:tire|tyre|setup|pressure)\b", r"\btractionator (?:gps|rallz|desert|adventure)\b")),
    Topic("suspension_setup", "mixed", (
        r"\b(?:motorcycle|adv) suspension\b", r"\b(?:set|setting|adjust|measure)(?:ting)? (?:the )?sag\b",
        r"\b(?:fork|shock) (?:setup|setting|adjustment|damping)\b", r"\b(?:preload|rebound|compression damping) (?:setup|adjustment|setting)\b")),
    Topic("motorcycle_maintenance", "mixed", (
        r"\b(?:motorcycle|bike) maintenance\b", r"\bchain (?:care|clean|lubrication|slack|adjustment)\b",
        r"\b(?:oil|coolant|brake fluid|air filter|spark plug) (?:change|service|replacement|check)\b", r"\bpre[- ]?ride inspection\b")),
    Topic("roadside_repairs", "touring_travel", (
        r"\b(?:roadside|field|trail) repair\b", r"\b(?:repair|plug|patch)(?:ing)? (?:a )?(?:flat|puncture|tire|tyre)\b",
        r"\b(?:motorcycle|trail) tool ?kit\b", r"\bfix(?:ing)? (?:a )?(?:broken|flat|puncture)\b")),
    Topic("packing_luggage", "touring_travel", (
        r"\b(?:motorcycle|adv) (?:packing|luggage)\b", r"\b(?:soft|hard) (?:panniers?|luggage|bags?)\b",
        r"\bload(?:ing)? (?:your|the) (?:bike|motorcycle)\b", r"\bweight distribution (?:for|on) (?:a )?(?:bike|motorcycle)\b")),
    Topic("motorcycle_camping", "touring_travel", (
        r"\bmotorcycle camp(?:ing)?\b", r"\b(?:camping|tent|sleep system|camp kitchen) (?:on|for|with) (?:a )?(?:motorcycle|bike|adv)\b")),
    Topic("trip_preparation", "touring_travel", (
        r"\b(?:motorcycle|adv) trip prep(?:aration)?\b", r"\bbefore (?:a|the|your) (?:ride|trip)\b", r"\b(?:ride|trip) checklist\b")),
    Topic("group_riding", "touring_travel", (
        r"\bgroup (?:ride|riding) (?:safety|formation|rules|tips|communication)\b", r"\b(?:ride leader|sweep rider)\b")),
    Topic("fatigue_management", "safety_recovery", (
        r"\b(?:rider|motorcycle|riding) fatigue\b", r"\b(?:hydration|dehydration) (?:while|for|during) riding\b", r"\btake breaks? (?:while|when) riding\b")),
    Topic("lifting", "safety_recovery", (
        r"\b(?:pick|picking) up (?:a |the |your )?(?:fallen |dropped )?(?:motorcycle|bike)\b",
        r"\b(?:lift|lifting) (?:a |the |your )?(?:fallen |dropped )?(?:motorcycle|bike)\b")),
    Topic("recovery", "safety_recovery", (
        r"\b(?:motorcycle|bike|rider) recovery\b", r"\b(?:unstuck|recover|tow|winch)(?:ing)? (?:a |the |your )?(?:motorcycle|bike)\b",
        r"\b(?:failed|stuck on a) hill (?:recovery|restart)\b")),
    Topic("water_crossings", "offroad_adventure", (
        r"\b(?:motorcycle|adv|bike) water crossing\b", r"\b(?:cross|crossing)(?:ing)? (?:a |the )?(?:river|stream) (?:on|with) (?:a )?(?:motorcycle|bike)\b")),
    Topic("mud_wet", "offroad_adventure", (
        r"\b(?:ride|riding|traction|technique) (?:in |through )?(?:the )?mud\b", r"\bmuddy (?:trail|terrain|riding|conditions)\b", r"\bslippery dirt\b")),
    Topic("sand", "offroad_adventure", (
        r"\b(?:ride|riding|traction|technique) (?:in |through )?(?:deep |soft )?sand\b", r"\bsand riding\b", r"\bdeep sand technique\b")),
    Topic("ruts", "offroad_adventure", (
        r"\b(?:ride|riding|cross|escape|line) (?:in |through |out of )?(?:a |the )?ruts?\b", r"\brutted (?:trail|terrain|road)\b")),
    Topic("loose_rock", "offroad_adventure", (
        r"\b(?:ride|riding|line|traction) (?:on |through )?(?:loose |baby head )?rocks?\b", r"\brock garden (?:riding|technique|line)\b", r"\brocky trail technique\b")),
    Topic("obstacles", "offroad_adventure", (
        r"\b(?:cross|ride|clear|loft)(?:ing)? (?:a |the )?(?:log|ledge|obstacle|rock step)\b", r"\b(?:front )?wheel lift (?:technique|drill|over)\b", r"\bpivot turn (?:technique|drill)\b")),
    Topic("hills", "offroad_adventure", (
        r"\b(?:hill climb|climbing a hill|uphill) (?:technique|riding|restart|traction|tips)\b", r"\bsteep hill (?:climb|riding|technique|restart)\b")),
    Topic("descents", "offroad_adventure", (
        r"\b(?:downhill|descent|descending) (?:riding|technique|braking|body position|tips)\b", r"\b(?:ride|riding) down (?:a )?steep hill\b")),
    Topic("offroad_braking", "offroad_adventure", (
        r"\boff[- ]?road braking\b", r"\bbrak(?:e|ing) (?:on|in) (?:dirt|gravel|loose terrain)\b", r"\bfront brake (?:on|in) (?:dirt|off[- ]?road)\b")),
    Topic("gravel_dirt", "offroad_adventure", (
        r"\b(?:ride|riding|traction|technique) (?:on |in )?(?:gravel|dirt road|loose surface)\b", r"\bgravel riding\b")),
    Topic("offroad_turning", "offroad_adventure", (
        r"\boff[- ]?road (?:turn|turning|cornering)\b", r"\b(?:tight|skid|pivot) turn (?:on|in) (?:dirt|trail|off[- ]?road)\b",
        r"\bcounterbalance (?:on|for) (?:dirt|off[- ]?road)\b")),
    Topic("offroad_basics", "offroad_adventure", (
        r"\boff[- ]?road (?:riding|technique|skill|basics|training)\b", r"\badv(?:enture)? riding (?:technique|skill|basics|training|tips)\b", r"\btrail riding (?:technique|skill|basics|training)\b")),
    Topic("emergency_braking", "road", (
        r"\b(?:emergency|maximum|panic) braking\b", r"\bquick stop (?:drill|technique|motorcycle)\b", r"\bmotorcycle stopping distance\b")),
    Topic("road_braking", "road", (
        r"\b(?:motorcycle|road) braking (?:technique|control|tips)\b", r"\b(?:front|rear) brake (?:technique|control|use)\b", r"\btrail braking (?:technique|on the road|corner)\b")),
    Topic("road_cornering", "road", (
        r"\b(?:motorcycle|road) cornering\b", r"\b(?:corner|turn) (?:entry|exit|line|apex|technique)\b", r"\bcountersteer(?:ing)? (?:technique|motorcycle|corner)\b", r"\blean angle (?:corner|motorcycle|technique)\b")),
    Topic("u_turns_low_speed", "practice", (
        r"\b(?:motorcycle|bike|riding) u[- ]?turns?\b", r"\bfull[- ]?lock (?:u[- ]?turn|turn|circle)\b", r"\bfigure eight (?:drill|motorcycle|riding)\b", r"\btight circles? (?:drill|motorcycle|riding)\b")),
    Topic("balance_slow_control", "practice", (
        r"\b(?:motorcycle|riding) slow[- ]?speed (?:control|balance|skill|drill|technique)\b", r"\bwalking[- ]?pace (?:balance|control|riding)\b", r"\bbalance drill (?:on|for) (?:a )?(?:motorcycle|bike)\b")),
    Topic("controls_coordination", "practice", (
        r"\b(?:clutch|friction zone) (?:control|technique|drill|practice)\b", r"\bthrottle control (?:drill|technique|motorcycle|off[- ]?road)\b", r"\bclutch and throttle\b")),
    Topic("riding_position", "offroad_adventure", (
        r"\b(?:motorcycle|off[- ]?road|adv) (?:body|riding) position\b", r"\bstand(?:ing)? (?:up )?(?:on|while riding) (?:a )?(?:motorcycle|bike|off[- ]?road)\b",
        r"\bweight transfer (?:on|for) (?:a )?(?:motorcycle|bike|off[- ]?road)\b")),
    Topic("ergonomics", "mixed", (
        r"\b(?:motorcycle|adv) ergonomics\b", r"\b(?:handlebar|lever|foot ?peg) (?:position|setup|adjustment)\b", r"\bbar risers? (?:setup|fit|ergonomics)\b", r"\bseat height (?:fit|adjustment|ergonomics)\b")),
    Topic("electronic_aids", "mixed", (
        r"\btraction control (?:system|setting|mode|off|on|explained)\b", r"\b(?:motorcycle|cornering|off[- ]?road) abs\b", r"\briding modes? (?:explained|setting|setup)\b", r"\belectronic rider aids?\b")),
    Topic("road_strategy", "road", (
        r"\b(?:motorcycle|rider) hazard perception\b", r"\blane position (?:for|on) (?:a )?(?:motorcycle|rider)\b", r"\b(?:motorcycle|rider) (?:escape route|following distance|blind spot|intersection safety)\b", r"\btraffic strategy (?:for|on) (?:a )?(?:motorcycle|rider)\b")),
    Topic("drills", "practice", (
        r"\b(?:motorcycle|riding|off[- ]?road) (?:training|practice) drill\b", r"\briding exercise (?:for|on) (?:a )?(?:motorcycle|bike)\b", r"\bskills progression drill\b")),
    Topic("bike_selection", "touring_travel", (
        r"\bchoose (?:an? |the )?(?:adv|adventure|dual sport) motorcycle\b", r"\bbest beginner (?:adv|adventure|dual sport) bike\b",
        r"\b(?:heavy|light) (?:adv|adventure) bike (?:choice|comparison|pros|cons)\b", r"\bwhich (?:adv|adventure|dual sport) motorcycle\b")),
)

PROMO_RE = re.compile(
    r"\b(?:giveaway|sale|discount|coupon|promo code|use code|shop now|last chance|book now|"
    r"register now|link in bio|affiliate|sponsored by|buy now|pre[- ]?order|rental fleet|"
    r"in stock|free shipping|available now|shop our|order yours)\b", re.I,
)
ENTERTAINMENT_RE = re.compile(
    r"\b(?:b[- ]?roll|cinematic|raw ride|ride footage|sound check|exhaust sound|wheelie|"
    r"top speed|crash compilation|fails?|meme|satire|funny|epic|insane|wait for it|pov ride|"
    r"playing around|riding some fun|first time enjoying|minor accident major repair)\b", re.I,
)
EDUCATIONAL_RE = re.compile(
    r"\b(?:how|why|what|when|guide|tutorial|tip|technique|drill|practice|learn|explain|"
    r"avoid|mistake|setup|set up|adjust|compare|comparison|versus|\bvs\b|pros? and cons?|"
    r"difference|choose|correct|safe|safety|control|skill|lesson|training|review)\b", re.I,
)


def sha256_text(value: str) -> str | None:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


def normalize(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"#[\w-]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split()).strip()


def get_json(url: str, *, data: dict[str, Any] | None = None, timeout: int = 25) -> dict[str, Any]:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read(2_500_000).decode("utf-8", errors="replace"))


def youtube_config() -> tuple[str, str]:
    request = urllib.request.Request("https://www.youtube.com/", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        page = response.read(2_000_000).decode("utf-8", errors="replace")
    key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page)
    version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', page)
    if not key_match or not version_match:
        raise RuntimeError("YouTube public player configuration was not found")
    return key_match.group(1), version_match.group(1)


def watch_page_player(video_id: str) -> dict[str, Any]:
    """Read the public watch page player payload as a no-cookie fallback."""
    url = f"https://www.youtube.com/watch?v={urllib.parse.quote(video_id)}&hl=en&has_verified=1"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read(2_500_000).decode("utf-8", errors="replace")
    markers = ("var ytInitialPlayerResponse = ", '"ytInitialPlayerResponse":')
    decoder = json.JSONDecoder()
    for marker in markers:
        start = page.find(marker)
        if start < 0:
            continue
        payload_start = page.find("{", start + len(marker))
        if payload_start < 0:
            continue
        try:
            payload, _ = decoder.raw_decode(page[payload_start:])
            if isinstance(payload, dict) and payload.get("videoDetails"):
                return payload
        except json.JSONDecodeError:
            continue
    raise ValueError("ytInitialPlayerResponse not found on public watch page")


def caption_text(player: dict[str, Any]) -> tuple[str, str | None]:
    tracks = (
        player.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    if not tracks:
        return "", None
    preferred = next((track for track in tracks if str(track.get("languageCode", "")).startswith("en")), tracks[0])
    base_url = preferred.get("baseUrl")
    if not base_url:
        return "", preferred.get("languageCode")
    separator = "&" if "?" in base_url else "?"
    try:
        payload = get_json(f"{base_url}{separator}fmt=json3", timeout=20)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return "", preferred.get("languageCode")
    parts = []
    for event in payload.get("events", []):
        for segment in event.get("segs", []):
            text = segment.get("utf8")
            if text and text != "\n":
                parts.append(text)
    return normalize(" ".join(parts))[:20_000], preferred.get("languageCode")


def topic_scores(title: str, description: str, transcript: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    title_l = title.casefold()
    description_l = description.casefold()
    transcript_l = transcript.casefold()
    for topic in TOPICS:
        if any(re.search(pattern, " ".join((title_l, description_l, transcript_l)), re.I) for pattern in topic.exclusions):
            continue
        title_hits = sorted({match.group(0) for pattern in topic.patterns for match in re.finditer(pattern, title_l, re.I)})
        description_hits = sorted({match.group(0) for pattern in topic.patterns for match in re.finditer(pattern, description_l, re.I)})
        transcript_hits = sorted({match.group(0) for pattern in topic.patterns for match in re.finditer(pattern, transcript_l, re.I)})
        score = len(title_hits) + 3 * len(description_hits) + 4 * len(transcript_hits)
        if score:
            results.append({
                "category": topic.category,
                "domain": topic.domain,
                "score": score,
                "title_matches": title_hits,
                "description_matches": description_hits,
                "caption_matches": transcript_hits,
                "source_supported": bool(description_hits or transcript_hits),
            })
    return sorted(results, key=lambda item: (-item["score"], item["category"]))


def audit_one(record: dict[str, Any], api_key: str, client_version: str) -> dict[str, Any]:
    video_id = record["youtube_video_id"]
    result: dict[str, Any] = {
        "youtube_video_id": video_id,
        "published_category": record.get("primary_category"),
        "published_title": record.get("title_original"),
    }
    try:
        player = get_json(
            f"https://www.youtube.com/youtubei/v1/player?key={urllib.parse.quote(api_key)}&prettyPrint=false",
            data={
                "context": {"client": {"clientName": "WEB", "clientVersion": client_version, "hl": "en", "gl": "US"}},
                "videoId": video_id,
                "contentCheckOk": True,
                "racyCheckOk": True,
            },
        )
        playability = player.get("playabilityStatus", {})
        if playability.get("status") != "OK":
            player = watch_page_player(video_id)
            playability = player.get("playabilityStatus", {})
        status = playability.get("status")
        result["link_status"] = status
        if status != "OK":
            result.update(decision="remove", reason="not_public_or_unavailable", playability_reason=playability.get("reason"))
            return result
        details = player.get("videoDetails", {})
        title = normalize(str(details.get("title") or record.get("title_original") or ""))
        description = normalize(str(details.get("shortDescription") or ""))
        transcript, caption_language = caption_text(player)
        result.update({
            "live_title": title,
            "channel_name": details.get("author"),
            "duration_seconds": int(details.get("lengthSeconds") or 0) or None,
            "description_chars": len(description),
            "description_sha256": sha256_text(description),
            "caption_language": caption_language,
            "caption_chars": len(transcript),
            "caption_sha256": sha256_text(transcript),
        })
        combined = " ".join((title, description, transcript))
        if PROMO_RE.search(combined):
            result.update(decision="remove", reason="promotional_or_commercial_call_to_action")
            return result
        if ENTERTAINMENT_RE.search(title) or ENTERTAINMENT_RE.search(description[:500]):
            result.update(decision="remove", reason="entertainment_or_ride_footage")
            return result
        evidence_available = len(description) >= 40 or len(transcript) >= 80
        if not evidence_available:
            result.update(decision="remove", reason="insufficient_content_evidence")
            return result
        scores = topic_scores(title, description, transcript)
        result["topic_scores"] = scores[:3]
        # The same semantic concept must appear in the public title and in a
        # source-backed field. Generic channel boilerplate must not override a
        # specific title, and a title-only keyword can never approve a Short.
        supported = [item for item in scores if item["source_supported"] and item["title_matches"]]
        if not supported:
            result.update(decision="remove", reason="title_and_source_evidence_do_not_agree")
            return result
        winner = supported[0]
        runner_up = supported[1] if len(supported) > 1 else None
        if runner_up and winner["score"] - runner_up["score"] < 3:
            result.update(decision="remove", reason="ambiguous_topic", proposed_category=winner["category"])
            return result
        if not EDUCATIONAL_RE.search(combined) and len(winner["caption_matches"]) < 2:
            result.update(decision="remove", reason="no_educational_intent")
            return result
        confidence = "high" if transcript and winner["caption_matches"] and winner["score"] >= 5 else "medium"
        result.update(
            decision="keep",
            reason="source_evidence_supports_topic",
            proposed_category=winner["category"],
            proposed_domain=winner["domain"],
            classification_confidence=confidence,
            category_changed=winner["category"] != record.get("primary_category"),
        )
        return result
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result.update(decision="remove", reason="fetch_or_parse_failure", error=str(exc)[:400])
        return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "shorts.json")
    parser.add_argument("--output", type=Path, default=ROOT / "research" / "shorts-v3.2" / "content-audit.json")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    records = json.loads(args.input.read_text(encoding="utf-8"))
    if args.limit:
        records = records[: args.limit]
    previous: dict[str, dict[str, Any]] = {}
    if args.resume and args.output.exists():
        old = json.loads(args.output.read_text(encoding="utf-8"))
        previous = {item["youtube_video_id"]: item for item in old.get("items", [])}
    pending = [item for item in records if item["youtube_video_id"] not in previous]

    api_key, client_version = youtube_config()
    completed = dict(previous)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(audit_one, item, api_key, client_version): item for item in pending}
        for index, future in enumerate(as_completed(futures), start=1):
            item = future.result()
            completed[item["youtube_video_id"]] = item
            if index % 25 == 0 or index == len(pending):
                ordered = [completed[item["youtube_video_id"]] for item in records if item["youtube_video_id"] in completed]
                report = {
                    "document_version": "1.0.0",
                    "product_version": "3.2.0",
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "method": "YouTube public player metadata plus captions when available; title alone never approves a Short",
                    "video_or_audio_downloaded": False,
                    "full_descriptions_or_transcripts_stored": False,
                    "input_count": len(records),
                    "completed_count": len(ordered),
                    "decision_counts": dict(Counter(entry.get("decision") for entry in ordered)),
                    "reason_counts": dict(Counter(entry.get("reason") for entry in ordered)),
                    "category_change_count": sum(bool(entry.get("category_changed")) for entry in ordered),
                    "items": ordered,
                }
                write_json(args.output, report)
                elapsed = max(time.monotonic() - started, 0.001)
                print(f"Audited {len(ordered)}/{len(records)} ({index / elapsed:.2f}/s)", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
