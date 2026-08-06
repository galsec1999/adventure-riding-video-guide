#!/usr/bin/env python3
"""Verify YouTube Shorts metadata and build the public v3.1 Shorts library.

The script never downloads video or audio. Caption text may be read in memory as
classification evidence; full captions are not written to disk.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()

PROMO_RE = re.compile(
    r"\b(giveaway|sale|discount|coupon|use code|promo code|shop now|last chance|book now|"
    r"register now|link in bio|merch|sponsored|affiliate|buy now|pre[- ]?order)\b",
    re.I,
)
NON_EDUCATIONAL_RE = re.compile(
    r"\b(b[- ]?roll|cinematic|raw ride|ride footage|sound check|exhaust sound|wheelie|"
    r"top speed|crash compilation|fails|meme|drum solo|unboxing|launch event)\b",
    re.I,
)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
HASHTAG_RE = re.compile(r"#[\w-]+", re.UNICODE)
TAG_RE = re.compile(r"<[^>]+>")

# Ordered: specific topics must win before broad topics.
TOPICS: list[dict[str, Any]] = [
    {"category":"intercoms_communications","domain":"touring_travel","sub":"bluetooth_vs_mesh","tags":["intercom","bluetooth","mesh","communication"],"words":r"intercom|cardo|sena|bluetooth|mesh communication|helmet audio"},
    {"category":"route_navigation","domain":"touring_travel","sub":"navigation_apps","tags":["navigation","gpx","offline_maps"],"words":r"navigation|gps|gpx|garmin|osmand|gaia|offline map|route planning|phone mount"},
    {"category":"protective_gear","domain":"safety_recovery","sub":"protective_gear_selection","tags":["protective_gear","safety","fit"],"words":r"helmet|protective gear|body armor|armour|airbag|riding boot|riding jacket|glove|abrasion|impact protection"},
    {"category":"tires_setup","domain":"mixed","sub":"tire_pressure","tags":["tires","tire_pressure","traction"],"words":r"tyre|tire|air down|pressure|knobb|mousse"},
    {"category":"suspension_setup","domain":"mixed","sub":"sag_preload","tags":["suspension","sag","preload"],"words":r"suspension|sag|preload|damping|fork setup|shock setup"},
    {"category":"motorcycle_maintenance","domain":"mixed","sub":"chain_care","tags":["maintenance","chain","inspection"],"words":r"chain|oil change|maintenance|service|lubric|coolant|battery|brake fluid|air filter|spark plug"},
    {"category":"roadside_repairs","domain":"touring_travel","sub":"field_repair","tags":["tire_repair","tools","breakdowns"],"words":r"repair|puncture|flat tire|flat tyre|tool kit|roadside|broken bike|field fix|tow a motorcycle"},
    {"category":"packing_luggage","domain":"touring_travel","sub":"packing_balance","tags":["packing","luggage","weight_distribution"],"words":r"pannier|luggage|packing|soft bags|hard bags|load your bike"},
    {"category":"motorcycle_camping","domain":"touring_travel","sub":"packing_balance","tags":["camping","packing","adventure"],"words":r"motorcycle camp|camping|tent|sleep system|camp kitchen"},
    {"category":"trip_preparation","domain":"touring_travel","sub":"pre_ride_tclocs","tags":["pre_ride","checklist","planning"],"words":r"pre[- ]?ride|before you ride|trip prep|ride checklist|inspection|hydration"},
    {"category":"group_riding","domain":"touring_travel","sub":"group_formation","tags":["group_riding","communication","safety"],"words":r"group ride|group riding|formation|ride leader|sweep rider"},
    {"category":"fatigue_management","domain":"safety_recovery","sub":"fatigue_breaks","tags":["fatigue","breaks","hydration"],"words":r"fatigue|tired|hydration|dehydration|take a break|long distance"},
    {"category":"lifting","domain":"safety_recovery","sub":"bike_lift","tags":["lifting","body_mechanics","recovery"],"words":r"pick up.*motorcycle|lift.*motorcycle|motorcycle lift|fallen bike|dropped bike"},
    {"category":"recovery","domain":"safety_recovery","sub":"sand_mud_recovery","tags":["recovery","traction","safety"],"words":r"stuck|recovery|unstuck|tow|winch|failed hill"},
    {"category":"water_crossings","domain":"offroad_adventure","sub":"water_assessment","tags":["water_crossing","line_selection","momentum"],"words":r"water crossing|cross.*river|river crossing|deep water"},
    {"category":"mud_wet","domain":"offroad_adventure","sub":"mud_traction","tags":["mud","wet_trail","traction"],"words":r"\bmud|muddy|wet trail|slippery dirt"},
    {"category":"sand","domain":"offroad_adventure","sub":"sand_momentum","tags":["sand","momentum","traction"],"words":r"\bsand\b|deep sand|soft sand|sand riding"},
    {"category":"ruts","domain":"offroad_adventure","sub":"rut_line","tags":["ruts","line_selection","balance"],"words":r"\brut|rutted"},
    {"category":"loose_rock","domain":"offroad_adventure","sub":"loose_rock_line","tags":["loose_rock","line_selection","momentum"],"words":r"loose rock|rock garden|river rock|rocky trail|baby heads"},
    {"category":"obstacles","domain":"offroad_adventure","sub":"logs_ledges","tags":["obstacles","logs","momentum"],"words":r"\blog\b|ledge|obstacle|rock step|pivot turn|wheel lift|loft"},
    {"category":"hills","domain":"offroad_adventure","sub":"hill_approach","tags":["hill_climb","momentum","gear_selection"],"words":r"hill climb|uphill|hill restart|steep hill|climbing"},
    {"category":"descents","domain":"offroad_adventure","sub":"steep_descent","tags":["downhill","braking","body_position"],"words":r"downhill|descent|descending|down a hill"},
    {"category":"offroad_braking","domain":"offroad_adventure","sub":"offroad_foundations","tags":["offroad_braking","front_brake","traction"],"words":r"off[- ]?road brak|brak.*dirt|rear wheel skid|front brake.*dirt"},
    {"category":"gravel_dirt","domain":"offroad_adventure","sub":"gravel_stability","tags":["gravel","dirt","line_selection"],"words":r"gravel|dirt road|loose surface|fire road"},
    {"category":"offroad_turning","domain":"offroad_adventure","sub":"offroad_tight_turn","tags":["offroad_turning","counterbalance","vision"],"words":r"off[- ]?road turn|tight turn.*dirt|pivot turn|skid turn|turn.*adventure bike"},
    {"category":"offroad_basics","domain":"offroad_adventure","sub":"offroad_foundations","tags":["offroad_basics","standing","adventure"],"words":r"off[- ]?road|adv riding|adventure riding|trail riding|dirt bike skill"},
    {"category":"emergency_braking","domain":"road","sub":"maximum_braking","tags":["emergency_braking","front_brake","safety"],"words":r"emergency brak|maximum brak|panic brak|quick stop|stopping distance"},
    {"category":"road_braking","domain":"road","sub":"brake_coordination","tags":["braking","front_brake","smooth_control"],"words":r"braking|front brake|rear brake|brake lever"},
    {"category":"road_cornering","domain":"road","sub":"vision_line","tags":["cornering","vision","line_selection"],"words":r"corner|countersteer|lean angle|apex|trail braking|turn entry|corner exit"},
    {"category":"u_turns_low_speed","domain":"practice","sub":"u_turn","tags":["u_turn","slow_speed","balance"],"words":r"u[- ]?turn|figure eight|full lock|tight circle"},
    {"category":"balance_slow_control","domain":"practice","sub":"walking_pace_balance","tags":["slow_control","balance","clutch"],"words":r"slow speed|slow control|balance drill|walking pace|gymkhana"},
    {"category":"controls_coordination","domain":"practice","sub":"friction_zone","tags":["clutch","throttle","smooth_control"],"words":r"clutch|friction zone|throttle control|shift gear|shifting|control coordination"},
    {"category":"riding_position","domain":"offroad_adventure","sub":"neutral_body_position","tags":["body_position","standing","weight_transfer"],"words":r"body position|riding position|stand up|standing|weight transfer|relaxed grip|bend.*arm"},
    {"category":"ergonomics","domain":"mixed","sub":"control_setup","tags":["ergonomics","controls_setup","fit"],"words":r"ergonomic|bar riser|handlebar|lever position|control setup|seat height|foot peg"},
    {"category":"electronic_aids","domain":"mixed","sub":"traction_control","tags":["electronic_aids","traction_control","abs"],"words":r"traction control|\babs\b|riding mode|electronic aid"},
    {"category":"road_strategy","domain":"road","sub":"hazard_perception","tags":["hazard_perception","lane_position","safety"],"words":r"hazard|road strategy|lane position|traffic|intersection|escape route|following distance|blind spot|motorcycle safety"},
    {"category":"drills","domain":"practice","sub":"beginner_foundations","tags":["practice_drill","training","skills_progression"],"words":r"drill|practice|training tip|riding exercise|coordination test"},
    {"category":"bike_selection","domain":"touring_travel","sub":"beginner_foundations","tags":["bike_selection","weight","adventure"],"words":r"choose.*motorcycle|best beginner bike|bike selection|heavy bike|light bike|which motorcycle"},
]
for topic in TOPICS:
    topic["regex"] = re.compile(topic.pop("words"), re.I)

CATEGORY_HE = {
    "intercoms_communications":"דיבוריות ותקשורת", "route_navigation":"ניווט ומסלולים",
    "protective_gear":"ציוד מיגון", "tires_setup":"צמיגים ולחצים", "suspension_setup":"כיוון מתלים",
    "motorcycle_maintenance":"תחזוקת אופנוע", "roadside_repairs":"תיקוני דרך", "packing_luggage":"אריזה ומטען",
    "motorcycle_camping":"קמפינג באופנוע", "trip_preparation":"הכנה לטיול", "group_riding":"רכיבה בקבוצה",
    "fatigue_management":"עייפות וניהול מאמץ", "lifting":"הרמת אופנוע", "recovery":"חילוץ והתאוששות",
    "water_crossings":"חציות מים", "mud_wet":"בוץ ושטח רטוב", "sand":"רכיבה בחול", "ruts":"חריצים",
    "loose_rock":"אבנים משוחררות", "obstacles":"מכשולים", "hills":"עליות", "descents":"ירידות",
    "offroad_braking":"בלימה בשטח", "gravel_dirt":"חצץ ועפר", "offroad_turning":"פניות בשטח",
    "offroad_basics":"יסודות רכיבת שטח", "emergency_braking":"בלימת חירום", "road_braking":"בלימה בכביש",
    "road_cornering":"פניות בכביש", "u_turns_low_speed":"פניות פרסה ושליטה איטית",
    "balance_slow_control":"איזון ושליטה איטית", "controls_coordination":"תיאום מצמד, גז ובלמים",
    "riding_position":"תנוחת רכיבה", "ergonomics":"ארגונומיה וכיוון פקדים", "electronic_aids":"עזרי רכיבה אלקטרוניים",
    "road_strategy":"אסטרטגיית כביש", "drills":"תרגילי אימון", "bike_selection":"בחירת אופנוע",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_evidence(value: str) -> str:
    value = URL_RE.sub(" ", value or "")
    value = HASHTAG_RE.sub(" ", value)
    return " ".join(value.split()).strip()


def caption_text(info: dict[str, Any]) -> str:
    tracks = info.get("subtitles") or {}
    if not tracks:
        tracks = info.get("automatic_captions") or {}
    choices = tracks.get("en") or tracks.get("en-US") or tracks.get("en-GB") or []
    choice = next((x for x in choices if x.get("ext") in {"json3", "srv3", "vtt"} and x.get("url")), None)
    if not choice:
        return ""
    try:
        request = urllib.request.Request(choice["url"], headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read(350_000).decode("utf-8", errors="replace")
        if choice.get("ext") == "json3":
            payload = json.loads(raw)
            text = " ".join(seg.get("utf8", "") for event in payload.get("events", []) for seg in event.get("segs", []))
        else:
            text = TAG_RE.sub(" ", raw)
            text = re.sub(r"(?m)^(WEBVTT|NOTE.*|\d+|\d\d:\d\d.*)$", " ", text)
        return " ".join(html.unescape(text).split())[:5000]
    except Exception:
        return ""


def classify(text: str) -> dict[str, Any] | None:
    matches = [(len(topic["regex"].findall(text)), index, topic) for index, topic in enumerate(TOPICS)]
    score, _, topic = max(matches, key=lambda item: (item[0], -item[1]))
    return topic if score else None


def fetch_one(candidate: dict[str, Any]) -> dict[str, Any]:
    import yt_dlp  # type: ignore[import-not-found]

    opts = {"quiet":True, "no_warnings":True, "skip_download":True, "cachedir":False, "socket_timeout":20, "retries":2}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(candidate["youtube_url"], download=False)
        if not info:
            return {"status":"reject", "reason":"metadata_missing", "candidate":candidate}
        duration = info.get("duration")
        if not isinstance(duration, (int, float)) or not 1 <= duration <= 180:
            return {"status":"reject", "reason":"not_short_duration", "candidate":candidate}
        title = str(info.get("title") or candidate.get("title_original") or "").strip()
        description = clean_evidence(str(info.get("description") or ""))
        captions = ""
        evidence_types: list[str] = []
        if len(description) >= 35 and description.casefold() != title.casefold():
            evidence_types.append("description")
        else:
            captions = clean_evidence(caption_text(info))
            if len(captions) >= 60:
                evidence_types.append("captions")
        evidence = " ".join([title, description, captions])
        if not evidence_types:
            return {"status":"reject", "reason":"insufficient_content_evidence", "candidate":candidate}
        if PROMO_RE.search(title) or PROMO_RE.search(description[:700]):
            return {"status":"reject", "reason":"promotional", "candidate":candidate}
        if NON_EDUCATIONAL_RE.search(title):
            return {"status":"reject", "reason":"non_educational_format", "candidate":candidate}
        topic = classify(evidence)
        if not topic:
            return {"status":"reject", "reason":"outside_taxonomy", "candidate":candidate}
        upload_date = str(info.get("upload_date") or "")
        published = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}" if len(upload_date) == 8 else None
        subtitles = sorted({key.split("-")[0] for key in (info.get("subtitles") or {}) if key})
        channel = str(info.get("channel") or info.get("uploader") or candidate["channel_name"])
        category_en = topic["category"].replace("_", " ")
        category_he = CATEGORY_HE[topic["category"]]
        content_type = "drill" if topic["category"] == "drills" else "maintenance_howto" if topic["category"] in {"motorcycle_maintenance","roadside_repairs"} else "explainer" if topic["category"] in {"protective_gear","route_navigation","intercoms_communications","electronic_aids","tires_setup","suspension_setup","bike_selection"} else "technique"
        risk = "medium" if topic["domain"] in {"offroad_adventure","road"} else "low"
        terrain = []
        for token, terrain_id in [("sand","sand"),("gravel","gravel"),("mud","mud"),("rock","loose_rock"),("water crossing","water_crossing"),("hill","hill"),("parking lot","parking_lot")]:
            if token in evidence.casefold() and terrain_id not in terrain:
                terrain.append(terrain_id)
        road = []
        for token, road_id in [("traffic","traffic"),("rain","wet_pavement"),("wet road","wet_pavement"),("corner","rural_twisty"),("parking lot","parking_lot")]:
            if token in evidence.casefold() and road_id not in road:
                road.append(road_id)
        marketing = bool(re.search(r"\b(sponsor|affiliate|product|brand partner)\b", description, re.I))
        quality = 4 if "captions" in evidence_types else 3
        video_id = candidate["youtube_video_id"]
        record = {
            "id": f"yts-{video_id}", "youtube_video_id": video_id,
            "youtube_url": f"https://www.youtube.com/shorts/{video_id}",
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "title_original": title, "title_he": f"קצר: {title}", "title_en": title,
            "channel_name": channel,
            "channel_url": str(info.get("channel_url") or f"https://www.youtube.com/channel/{candidate['channel_id']}"),
            "published_date": published, "duration_seconds": int(duration), "language": "en",
            "subtitle_languages": subtitles, "domain": topic["domain"], "primary_category": topic["category"],
            "secondary_categories": [], "subtopics": [topic["sub"]], "content_type": content_type,
            "tags": topic["tags"], "skill_level": "beginner" if risk == "low" else "advanced_beginner",
            "risk_level": risk, "motorcycle_types": ["general_motorcycle"], "motorcycle_weight_classes": ["general"],
            "terrain_types": terrain, "road_conditions": road,
            "summary_he": f"קטע קצר ומאומת מערוץ {channel} בנושא {category_he}. הרשומה מסכמת רק את הסיווג שנתמך בתיאור או בכתוביות; לצפייה בהדגמה ובהקשר המלא יש לפתוח את המקור.",
            "summary_en": f"A verified short clip from {channel} about {category_en}. This record states only the classification supported by the description or captions; open the source for the complete demonstration and context.",
            "learning_points_he": [f"לזהות את הרעיון המרכזי בנושא {category_he}", "לשים לב להדגמה הקצרה ולהקשר שהיוצר מציג", "להחליט אם נדרש סרטון ארוך או מדריך מוסמך לפני תרגול"],
            "learning_points_en": [f"Identify the central idea about {category_en}", "Notice the short demonstration and the context provided by the creator", "Decide whether a full lesson or qualified instruction is needed before practice"],
            "fit_for_he": "מתאים כרענון מהיר לפני לימוד מעמיק; אינו תחליף להדרכה מעשית או להסבר מלא.",
            "fit_for_en": "Best used as a quick refresher before deeper study; it does not replace practical instruction or a full explanation.",
            "why_watch_he": f"הקטע מאפשר לקלוט במהירות נקודה אחת בנושא {category_he} ולהחליט אם להמשיך למקור מעמיק יותר.",
            "why_watch_en": f"The clip offers one quick point about {category_en} and helps decide whether to continue to a deeper source.",
            "exercises_he": [], "exercises_en": [],
            "equipment_he": ["ציוד מיגון מתאים", "סביבה חוקית ובטוחה אם בוחרים לתרגל"],
            "equipment_en": ["Appropriate protective riding gear", "A safe and legal environment if you choose to practise"],
            "safety_warnings_he": ["קצר אינו מציג תמיד את כל הסיכונים, התנאים והחריגים; אין לתרגל על סמך הקטע לבדו."],
            "safety_warnings_en": ["A Short may omit risks, conditions and exceptions; do not practise from this clip alone."],
            "common_mistakes_he": ["להסיק כלל מלא מהדגמה קצרה", "לנסות טכניקה לפני בדיקת התאמה לרוכב, לאופנוע ולסביבה"],
            "common_mistakes_en": ["Treating a brief demonstration as a complete rule", "Trying a technique before checking fit for rider, motorcycle and environment"],
            "chapters": [], "quality_score": quality,
            "quality_reason_he": f"הקישור והמטא־דאטה נבדקו; הסיווג נתמך ב{('כתוביות' if 'captions' in evidence_types else 'תיאור המקור')}. קוצר הפורמט מגביל את עומק האימות.",
            "quality_reason_en": f"The link and metadata were checked; classification is supported by {'captions' if 'captions' in evidence_types else 'the source description'}. The short format limits verification depth.",
            "source_type": "professional_instructor", "contains_marketing": marketing, "related_video_ids": [],
            "verification": {"link_status":"active_public", "metadata_verified":True, "content_evidence_types":evidence_types,
                "classification_confidence":"medium",
                "notes_he":f"נבדק ב־{TODAY}. לא נשמרו וידאו, אודיו או תמלול מלא; נעשה שימוש בראיית תוכן מוגבלת לצורך הסיווג.",
                "notes_en":f"Checked on {TODAY}. No video, audio or full transcript is stored; limited content evidence was used for classification."},
            "last_checked": TODAY, "media_format":"short",
        }
        return {"status":"accept", "record":record, "candidate":candidate}
    except Exception as exc:
        return {"status":"reject", "reason":"fetch_error", "error":str(exc)[:500], "candidate":candidate}


def round_robin_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for item in candidates:
        title = str(item.get("title_original") or "")
        if PROMO_RE.search(title) or NON_EDUCATIONAL_RE.search(title):
            continue
        topic_hits = sum(bool(topic["regex"].search(title)) for topic in TOPICS)
        if topic_hits:
            item = dict(item)
            item["_discovery_score"] = topic_hits
            groups[item["channel_name"]].append(item)
    ordered: list[dict[str, Any]] = []
    channel_order = sorted(groups, key=lambda key: len(groups[key]), reverse=True)
    while any(groups.values()):
        for channel in channel_order:
            if groups[channel]:
                ordered.append(groups[channel].popleft())
    return ordered


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=120)
    args = parser.parse_args()
    source = load_json(args.candidates)
    queue = round_robin_candidates(source["candidates"])
    accepted: list[dict[str, Any]] = load_json(args.output) if args.output.exists() else []
    previous_report = load_json(args.report) if args.report.exists() else {}
    rejected: list[dict[str, Any]] = list(previous_report.get("rejections") or [])
    completed_ids = {item["youtube_video_id"] for item in accepted}
    completed_ids.update(item["youtube_video_id"] for item in rejected)
    queue = [item for item in queue if item["youtube_video_id"] not in completed_ids]
    examined = 0
    for start in range(0, len(queue), args.batch_size):
        batch = queue[start:start + args.batch_size]
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(fetch_one, item) for item in batch]
            for future in as_completed(futures):
                result = future.result()
                examined += 1
                if result["status"] == "accept":
                    accepted.append(result["record"])
                else:
                    rejected.append({
                        "youtube_video_id": result["candidate"]["youtube_video_id"],
                        "channel_name": result["candidate"]["channel_name"],
                        "title_original": result["candidate"].get("title_original"),
                        "reason": result["reason"], "error": result.get("error"),
                    })
        print(f"Examined {examined}; accepted {len(accepted)}; rejected {len(rejected)}", flush=True)
        accepted.sort(key=lambda item: (-item["quality_score"], item["channel_name"].casefold(), item["title_original"].casefold()))
        write_json(args.output, accepted[:args.target])
        write_json(args.report, {
            "document_version":"1.0.0", "product_version":"3.1.0", "status":"in_progress",
            "generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "publication_target":args.target, "candidates_available":len(source["candidates"]),
            "accepted_before_cap":len(accepted), "published_count":min(len(accepted), args.target),
            "rejected_count":len(rejected), "rejection_reasons":dict(Counter(item["reason"] for item in rejected)),
            "video_or_audio_downloaded":False, "full_transcript_stored":False, "rejections":rejected,
        })
        if len(accepted) >= args.target:
            break
    accepted.sort(key=lambda item: (-item["quality_score"], item["channel_name"].casefold(), item["title_original"].casefold()))
    published = accepted[:args.target]
    write_json(args.output, published)
    report = {
        "document_version":"1.0.0", "product_version":"3.1.0",
        "generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "publication_target":args.target, "candidates_available":len(source["candidates"]),
        "candidates_prioritized":len(queue), "candidates_examined":examined,
        "accepted_before_cap":len(accepted), "published_count":len(published),
        "rejected_count":len(rejected), "rejection_reasons":dict(Counter(item["reason"] for item in rejected)),
        "published_channels":dict(Counter(item["channel_name"] for item in published)),
        "published_categories":dict(Counter(item["primary_category"] for item in published)),
        "video_or_audio_downloaded":False, "full_transcript_stored":False,
        "rejections":rejected,
    }
    write_json(args.report, report)
    print(f"Published: {len(published)} -> {args.output}")
    return 0 if len(published) >= args.target else 2


if __name__ == "__main__":
    raise SystemExit(main())
