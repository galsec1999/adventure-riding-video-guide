#!/usr/bin/env python3
"""Add source-verified Chris Birch Adventure training content.

Document version: 1.0.0
Product version: 3.4.0
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKED = "2026-08-06"
OFFICIAL_CHANNEL = "UCTK4SLXIIvcFNeUYpv9Prvg"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def chapter(start: int, end: int, title: str) -> dict[str, Any]:
    return {"start_seconds": start, "end_seconds": end, "title": title}


def record(spec: dict[str, Any], *, short: bool = False) -> dict[str, Any]:
    vid = spec["youtube_video_id"]
    evidence = list(spec.get("evidence", ["description"]))
    high_risk = spec.get("risk_level", "medium") == "high"
    media_id = f"yts-{vid}" if short else f"yt-{vid}"
    youtube_url = f"https://www.youtube.com/shorts/{vid}" if short else f"https://www.youtube.com/watch?v={vid}"
    item = {
        "id": media_id,
        "youtube_video_id": vid,
        "youtube_url": youtube_url,
        "thumbnail_url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        "title_original": spec["title_original"],
        "title_he": spec["title_he"],
        "title_en": spec["title_original"],
        "channel_name": spec["channel_name"],
        "channel_url": f"https://www.youtube.com/channel/{spec['channel_id']}",
        "published_date": spec["published_date"],
        "duration_seconds": spec["duration_seconds"],
        "language": "en",
        "subtitle_languages": spec.get("subtitle_languages", []),
        "domain": spec.get("domain", "offroad_adventure"),
        "primary_category": spec["primary_category"],
        "secondary_categories": spec.get("secondary_categories", []),
        "subtopics": spec["subtopics"],
        "content_type": spec.get("content_type", "technique"),
        "tags": spec["tags"],
        "skill_level": spec.get("skill_level", "intermediate"),
        "risk_level": spec.get("risk_level", "medium"),
        "motorcycle_types": ["adventure"],
        "motorcycle_weight_classes": spec.get("motorcycle_weight_classes", ["medium", "heavy"]),
        "terrain_types": spec.get("terrain_types", ["dirt"]),
        "road_conditions": spec.get("road_conditions", []),
        "summary_he": spec["summary_he"],
        "summary_en": spec["summary_en"],
        "learning_points_he": spec["learning_points_he"],
        "learning_points_en": spec["learning_points_en"],
        "fit_for_he": spec.get("fit_for_he", "לרוכבי אדוונצ'ר שרוצים ללמוד את הנושא לפני תרגול מדורג בשטח סגור ומתאים."),
        "fit_for_en": spec.get("fit_for_en", "For Adventure riders who want to study the topic before progressive practice in a suitable controlled area."),
        "why_watch_he": spec["why_watch_he"],
        "why_watch_en": spec["why_watch_en"],
        "exercises_he": spec.get("exercises_he", []),
        "exercises_en": spec.get("exercises_en", []),
        "equipment_he": spec.get("equipment_he", ["מיגון רכיבה מלא", "מגן מנוע מתאים"]),
        "equipment_en": spec.get("equipment_en", ["Full protective riding gear", "Appropriate engine protection"]),
        "safety_warnings_he": spec.get("safety_warnings_he", [
            "יש לתרגל בהדרגה ובשטח סגור; הסרטון אינו תחליף למדריך שמכיר את הרוכב, האופנוע והתנאים."
        ]),
        "safety_warnings_en": spec.get("safety_warnings_en", [
            "Practise progressively in a controlled area; the video does not replace an instructor who knows the rider, motorcycle and conditions."
        ]),
        "common_mistakes_he": spec.get("common_mistakes_he", ["ניסיון להעתיק את הקצב של המאמן לפני ביסוס היסודות"]),
        "common_mistakes_en": spec.get("common_mistakes_en", ["Copying the instructor's pace before the fundamentals are stable"]),
        "chapters": spec.get("chapters", []),
        "quality_score": spec.get("quality_score", 4),
        "quality_reason_he": spec["quality_reason_he"],
        "quality_reason_en": spec["quality_reason_en"],
        "source_type": "professional_instructor",
        "contains_marketing": spec.get("contains_marketing", False),
        "related_video_ids": spec.get("related_video_ids", []),
        "verification": {
            "link_status": "active_public",
            "metadata_verified": True,
            "content_evidence_types": evidence,
            "classification_confidence": spec.get("confidence", "high"),
            "notes_he": spec.get("verification_he", f"נבדקו מטא־דאטה וראיות התוכן ב־{CHECKED}; לא נשמרו וידאו, אודיו או תמלול מלא."),
            "notes_en": spec.get("verification_en", f"Metadata and content evidence were reviewed on {CHECKED}; no video, audio or full transcript was stored."),
        },
        "last_checked": CHECKED,
    }
    if high_risk:
        item["safety_warnings_he"] = spec.get("safety_warnings_he", ["טכניקה בסיכון גבוה: אין לתרגל מן הסרטון בלבד; נדרשים מדריך מוסמך, מיגון מלא ושטח סגור."])
        item["safety_warnings_en"] = spec.get("safety_warnings_en", ["High-risk technique: do not practise from the video alone; use qualified instruction, full gear and a closed area."])
    if short:
        item["media_format"] = "short"
    return item


FULL_SPECS: list[dict[str, Any]] = [
    {
        "youtube_video_id": "BySQmyz62EI", "title_original": "6 Tips on Riding Adventure Bike Off-road by Chris Birch",
        "title_he": "שישה טיפים לרכיבת אדוונצ'ר בשטח עם כריס בירץ'", "channel_name": "Bin Chin", "channel_id": "UCNTsZ7-zogUAvXtX_7hLiXw",
        "published_date": "2018-01-26", "duration_seconds": 428, "primary_category": "offroad_basics",
        "secondary_categories": ["ergonomics", "riding_position"], "subtopics": ["control_setup", "neutral_body_position", "standing_position"],
        "content_type": "explainer", "tags": ["controls_setup", "body_position", "standing", "countersteering", "adventure"],
        "summary_he": "שישה דגשים מקליניקת כריס בירץ' על אופנועי V-Twin גדולים: זווית הכידון והמנופים, תנוחת ישיבה, מרפקים ופקודות היגוי בשטח.",
        "summary_en": "Six clinic-derived pointers for large V-twin Adventure motorcycles, covering handlebar and lever angle, seated position, elbow position and steering input off road.",
        "learning_points_he": ["לכוון את זווית הכידון לפי תנועת הגוף ולא לפי מראה בלבד", "לשמור מנופים נגישים בלי לפגוע בתנוחת שורש כף היד", "למקם גוף ומרפקים כך שנשאר טווח תנועה לשליטה באופנוע כבד", "להבחין בין הטיית גוף לבין פקודת היגוי מכוונת"],
        "learning_points_en": ["Set handlebar angle around rider movement rather than appearance alone", "Keep levers reachable without compromising wrist position", "Use body and elbow position that preserves movement on a heavy motorcycle", "Distinguish body lean from deliberate steering input"],
        "why_watch_he": "הנושאים אומתו בתיאור ובכותרות הפרקים המוצגות בנגן החי, על גבי אופנועי אדוונצ'ר גדולים.",
        "why_watch_en": "The topics were confirmed from the description and live-player topic labels on large Adventure motorcycles.",
        "quality_score": 5, "quality_reason_he": "תיאור מפורש ובדיקה חזותית בשש נקודות זמן מאמתים הדרכה ולא סרטון ראווה.",
        "quality_reason_en": "An explicit description and six live-player time checks confirm instruction rather than a showcase clip.",
        "evidence": ["description", "visual_content_review"], "related_video_ids": ["yt-X_Dwq8hmuJ0", "yt-oZiD8uxH0hQ"]
    },
    {
        "youtube_video_id": "waIHKJpQiB4", "title_original": "ADVENTURE BETTER | CHRIS' TOP 5 OFF-ROAD EXERCISES",
        "title_he": "חמשת תרגילי השטח המובילים של כריס בירץ'", "channel_name": "Bike World", "channel_id": "UCHc-Qw3YyvSAKMfhotUmY3w",
        "published_date": "2026-01-31", "duration_seconds": 1594, "domain": "practice", "primary_category": "drills",
        "secondary_categories": ["offroad_basics", "balance_slow_control"], "subtopics": ["walking_pace_balance", "friction_zone", "course_selection"],
        "content_type": "drill", "tags": ["practice_drill", "training", "balance", "smooth_control", "adventure"],
        "summary_he": "שיעור ארוך שמרכז חמישה תרגילי שטח של כריס בירץ' לשיפור שליטה באופנוע אדוונצ'ר באמצעות חזרות מדורגות.",
        "summary_en": "A long-form lesson presenting five Chris Birch off-road exercises for improving Adventure-motorcycle control through structured repetition.",
        "learning_points_he": ["לבודד מיומנות אחת בכל תרגיל", "להתחיל לאט ולהגדיל קושי רק לאחר חזרות עקביות", "להשתמש בתרגול מכוון במקום להסתמך רק על רכיבת שביל", "לעצור כאשר הדיוק מתפרק מעייפות"],
        "learning_points_en": ["Isolate one skill in each exercise", "Start slowly and increase difficulty only after consistent repetitions", "Use deliberate drills rather than relying only on trail mileage", "Stop when fatigue causes precision to break down"],
        "why_watch_he": "הסרטון מוגדר במפורש כשיעור תרגילים לאופנועי אדוונצ'ר ולא כסרטון אירוע או מוצר.",
        "why_watch_en": "The source explicitly presents an Adventure-motorcycle exercise lesson rather than an event or product video.",
        "quality_reason_he": "כותרת, תיאור ומטא־דאטה עקביים לגבי חמישה תרגילי שטח של המאמן.",
        "quality_reason_en": "Title, description and metadata consistently identify five off-road exercises from the instructor.",
        "evidence": ["description", "youtube_search_metadata"], "related_video_ids": ["yt-oZiD8uxH0hQ", "yt-mrLyIWGyUWo"]
    },
    {
        "youtube_video_id": "mrLyIWGyUWo", "title_original": "Chris Birch Adventure Clinic",
        "title_he": "קטעי הדרכה מקליניקת האדוונצ'ר של כריס בירץ'", "channel_name": "adventurist.tv", "channel_id": "UCvJXmBBsPNzy2efzCsuITgg",
        "published_date": "2018-03-10", "duration_seconds": 412, "domain": "practice", "primary_category": "training_courses",
        "secondary_categories": ["offroad_basics", "drills"], "subtopics": ["course_selection", "beginner_foundations", "offroad_foundations"],
        "content_type": "course_overview", "tags": ["training_courses", "professional_training", "practice", "offroad_basics", "adventure"],
        "summary_he": "קטעים מאימון מגרש בבוקר של קליניקת אדוונצ'ר, עם הסברים של כריס בירץ', הדגמות ומשוב מיידי לרוכבים על אופנועים גדולים.",
        "summary_en": "Morning paddock-training excerpts from an Adventure clinic, with Chris Birch explanations, demonstrations and immediate rider feedback on large motorcycles.",
        "learning_points_he": ["לצפות בהדגמה לפני ביצוע", "לקבל תיקון מיידי ולא לחזור על אותה טעות", "להפריד תרגול מגרש מרכיבת שביל", "לבנות מיומנות בשלבים בהתאם למשוב"],
        "learning_points_en": ["Observe the demonstration before attempting the drill", "Use immediate feedback instead of repeating the same error", "Separate paddock drills from trail riding", "Build the skill in stages based on feedback"],
        "why_watch_he": "תיאור היוצר מבהיר שהסרטון מציג את חלק האימון ולא את רכיבת השבילים שבאה אחריו.",
        "why_watch_en": "The creator states that this video shows the training portion, separate from the later trail ride.",
        "quality_reason_he": "התיאור מזהה קליניקת אדוונצ'ר, הסברים, משוב ואימון מגרש; ההקשר אינו אנדורו.",
        "quality_reason_en": "The description identifies an Adventure clinic with explanations, feedback and paddock training, not an Enduro session.",
        "evidence": ["description"], "related_video_ids": ["yt-waIHKJpQiB4", "yt-oZiD8uxH0hQ"]
    },
    {
        "youtube_video_id": "M5yAd24z5y0", "title_original": "Chris Birch Hill Climb Tips - KTM1190 Adventure R",
        "title_he": "טיפים לעלייה עם KTM 1190 Adventure R", "channel_name": "Motorcycle Adventure Dirtbike TV", "channel_id": "UCHCgMd5ICEW6pHpfR69UrwA",
        "published_date": "2015-10-27", "duration_seconds": 179, "primary_category": "hills", "secondary_categories": ["riding_position"],
        "subtopics": ["hill_approach", "hill_momentum", "weight_transfer"], "tags": ["hill_climb", "body_position", "traction", "adventure"],
        "summary_he": "כריס בירץ' מסביר דגשים לעלייה בשטח על KTM 1190 Adventure R, עם קשר בין תנוחת גוף, דחף ואחיזה.",
        "summary_en": "Chris Birch explains off-road hill-climb pointers on a KTM 1190 Adventure R, connecting body position, drive and traction.",
        "learning_points_he": ["להכין קו ועלייה לפני פתיחת הגז", "למקם גוף כדי לאזן אחיזה קדמית ואחורית", "לשמור דחף רציף בלי שינויי גז חדים"],
        "learning_points_en": ["Choose the line and approach before adding throttle", "Position the body to balance front and rear traction", "Maintain drive without abrupt throttle changes"],
        "why_watch_he": "הכותרת והתיאור מציינים במפורש טיפים לעלייה על אופנוע אדוונצ'ר גדול.", "why_watch_en": "The title and description explicitly identify hill-climb tips on a large Adventure motorcycle.",
        "quality_reason_he": "מטא־דאטה ותיאור פעילים תומכים בנושא ובסוג האופנוע; אין קישור מוצר או קריאת מכירה.", "quality_reason_en": "Active metadata and description support the topic and motorcycle type, with no product link or sales call.",
        "evidence": ["description"], "related_video_ids": ["yt-di8dBE6jkjM", "yt-OXsQaL28fgo"]
    },
    {
        "youtube_video_id": "axhRmbeUy28", "title_original": "Handlebar Lifting Technique by Chris Birch",
        "title_he": "הרמת אופנוע אדוונצ'ר מן הכידון עם כריס בירץ'", "channel_name": "Bin Chin", "channel_id": "UCNTsZ7-zogUAvXtX_7hLiXw",
        "published_date": "2018-05-26", "duration_seconds": 113, "domain": "safety_recovery", "primary_category": "lifting", "secondary_categories": ["recovery"],
        "subtopics": ["bike_lift", "bike_lift_hill", "weight_transfer"], "tags": ["lifting", "body_mechanics", "recovery", "adventure"],
        "summary_he": "הדגמת הרמת אופנוע אדוונצ'ר כבד מן הכידון: הערכת המצב, שימוש ברגליים ובאגן, גב ישר והפעלת שרירי הליבה.",
        "summary_en": "A heavy-Adventure-bike handlebar lift demonstration: assess the situation, use legs and hips, straighten the back and engage the core.",
        "learning_points_he": ["להעריך שיפוע, צד נפילה ונקודות אחיזה לפני שמרימים", "להפיק כוח מהרגליים ומהאגן", "ליישר גב ולהפעיל ליבה במקום למשוך בגב", "להתקדם בזהירות ולא למהר אחרי שהאופנוע מתרומם"],
        "learning_points_en": ["Assess slope, fall side and grip points before lifting", "Generate force with legs and hips", "Straighten the back and engage the core instead of pulling with the back", "Move carefully rather than rushing once the motorcycle rises"],
        "why_watch_he": "ארבעת השלבים מוצגים על המסך ונבדקו חזותית על KTM אדוונצ'ר גדול.", "why_watch_en": "Four on-screen steps were visually confirmed on a large KTM Adventure motorcycle.",
        "equipment_he": ["מיגון רכיבה", "כפפות אחיזה", "אדם נוסף כשאפשר"], "equipment_en": ["Protective riding gear", "Grip gloves", "A helper when available"],
        "safety_warnings_he": ["יש לכבות מנוע, לייצב את הקרקע ולהפסיק אם יש כאב גב או שאין אחיזה בטוחה."],
        "safety_warnings_en": ["Switch off the engine, stabilize the ground and stop if there is back pain or no secure grip."],
        "quality_score": 5, "quality_reason_he": "תיאור ובדיקה חזותית רציפה אימתו אופנוע אדוונצ'ר, ארבעה שלבים והדגמה מלאה.",
        "quality_reason_en": "Description and continuous visual review confirmed an Adventure motorcycle, four steps and a complete demonstration.",
        "evidence": ["description", "visual_content_review"], "related_video_ids": ["yt-zMuVNBk9Ogw", "yt-di8dBE6jkjM"]
    },
    {
        "youtube_video_id": "w_mg182B1OA", "title_original": "How I fix a flat without a center stand. Chris Birch KTM 790 AdventureR",
        "title_he": "תיקון תקר ב־KTM 790 Adventure R ללא רגלית אמצע", "channel_name": "Chris Birch - Off Road Coach", "channel_id": OFFICIAL_CHANNEL,
        "published_date": "2020-04-16", "duration_seconds": 473, "domain": "touring_travel", "primary_category": "roadside_repairs", "secondary_categories": ["tires_setup"],
        "subtopics": ["tire_repair_tube", "field_repair"], "content_type": "maintenance_howto", "tags": ["tire_repair", "tools", "maintenance", "adventure"],
        "summary_he": "הליך שטח של כריס בירץ' לטיפול בתקר ב־KTM 790 Adventure R כאשר אין רגלית אמצע, כולל יצירת תמיכה בטוחה להסרת גלגל.",
        "summary_en": "Chris Birch's field procedure for a flat on a KTM 790 Adventure R without a center stand, including stable support for wheel removal.",
        "learning_points_he": ["לתכנן נקודת תמיכה לפני שחרור הציר", "לייצב את האופנוע כך שלא ייפול כשהגלגל בחוץ", "לסדר כלים וחלקים לפי סדר ההרכבה", "לבדוק גלגל ובלמים לפני חזרה לרכיבה"],
        "learning_points_en": ["Plan the support point before loosening the axle", "Stabilize the motorcycle so it cannot fall with the wheel removed", "Lay out tools and parts in reassembly order", "Check wheel and brakes before returning to the ride"],
        "why_watch_he": "זהו מדריך רשמי וממוקד לבעיה אמיתית באופנוע אדוונצ'ר, לא סקירת מוצר.", "why_watch_en": "This is an official, problem-focused Adventure-bike procedure rather than a product review.",
        "equipment_he": ["כלי ציר מתאימים לדגם", "ערכת תיקון תקר", "משאבה", "אמצעי תמיכה יציב"], "equipment_en": ["Model-correct axle tools", "Puncture repair kit", "Pump", "Stable support"],
        "quality_score": 5, "quality_reason_he": "ערוץ המאמן הרשמי, תיאור מפורש ואופנוע מזוהה תומכים בהליך התחזוקה.",
        "quality_reason_en": "The instructor's official channel, explicit description and identified motorcycle support the maintenance procedure.",
        "evidence": ["description"], "contains_marketing": True, "related_video_ids": ["yt-rCJmU0mIn_U"]
    },
    {
        "youtube_video_id": "di8dBE6jkjM", "title_original": "How to Hill Recovery Motorcycle Chris Birch",
        "title_he": "חילוץ אופנוע שנתקע בעלייה תלולה", "channel_name": "Motorcycle Adventure Dirtbike TV", "channel_id": "UCHCgMd5ICEW6pHpfR69UrwA",
        "published_date": "2014-03-21", "duration_seconds": 196, "domain": "safety_recovery", "primary_category": "recovery", "secondary_categories": ["hills"],
        "subtopics": ["bike_lift_hill", "hill_approach", "sand_mud_recovery"], "tags": ["failed_hill", "recovery", "hill", "adventure"],
        "summary_he": "כריס בירץ' מדגים כיצד לחלץ בבטחה אופנוע שנתקע על עלייה תלולה; המקור מציין שהטכניקה חלה גם על אופנועי אדוונצ'ר.",
        "summary_en": "Chris Birch demonstrates safe recovery of a motorcycle stalled on a steep hill; the source explicitly applies the technique to Adventure bikes.",
        "learning_points_he": ["לעצור ולייצב לפני שהאופנוע צובר תנועה לאחור", "להקטין את זווית האופנוע אל השיפוע בצעדים נשלטים", "להפנות ולהוריד את האופנוע רק לאחר יצירת עמדה יציבה"],
        "learning_points_en": ["Stop and stabilize before the motorcycle gains backward momentum", "Reduce the bike's angle to the slope in controlled steps", "Turn and descend only after establishing a stable position"],
        "why_watch_he": "התיאור מגדיר במפורש חילוץ בטוח בעלייה והתאמה לאופנועי אדוונצ'ר.", "why_watch_en": "The description explicitly identifies safe hill recovery and applicability to Adventure motorcycles.",
        "risk_level": "high", "quality_reason_he": "נושא, שימוש בטוח והתאמה לאדוונצ'ר מאומתים בתיאור המקור.",
        "quality_reason_en": "Topic, safe-use intent and Adventure applicability are verified in the source description.",
        "evidence": ["description"], "related_video_ids": ["yt-M5yAd24z5y0", "yt-OXsQaL28fgo", "yt-zMuVNBk9Ogw"]
    },
    {
        "youtube_video_id": "rCJmU0mIn_U", "title_original": "Say No To Spend Tyre Changing - Chris Birch",
        "title_he": "החלפת צמיג אדוונצ'ר בשטח בכלים פשוטים", "channel_name": "Chris Birch - Off Road Coach", "channel_id": OFFICIAL_CHANNEL,
        "published_date": "2023-08-25", "duration_seconds": 799, "domain": "mixed", "primary_category": "motorcycle_maintenance", "secondary_categories": ["tires_setup", "roadside_repairs"],
        "subtopics": ["tire_repair_tube", "field_repair", "tire_choice"], "content_type": "maintenance_howto", "tags": ["maintenance", "tires", "tools", "adventure"],
        "summary_he": "מדריך רשמי להחלפת צמיג באופנוע אדוונצ'ר בכלים פשוטים ובעלות נמוכה, כדי לאפשר החלפה לפי סוג הרכיבה.",
        "summary_en": "An official guide to changing an Adventure-bike tyre with simple, low-cost tools so tyres can be swapped to match the ride.",
        "learning_points_he": ["להכין סביבת עבודה נקייה ויציבה", "לעבוד בהדרגה סביב שפת הצמיג ולא בכוח בנקודה אחת", "להגן על החישוק והפנימית בזמן העבודה", "לבצע בדיקת לחץ, כיוון גלגל ובלמים לאחר ההרכבה"],
        "learning_points_en": ["Prepare a clean and stable work area", "Work progressively around the bead rather than forcing one point", "Protect the rim and tube during the procedure", "Check pressure, wheel alignment and brakes after reassembly"],
        "why_watch_he": "המטרה הראשית היא הליך תחזוקה לאופנוע אדוונצ'ר ולא מכירת כלי או צמיג.", "why_watch_en": "The primary purpose is an Adventure-bike maintenance procedure, not selling a tool or tyre.",
        "equipment_he": ["כפות צמיג", "מגן חישוק", "משאבה", "כלי שסתום", "כפפות עבודה"], "equipment_en": ["Tyre irons", "Rim protection", "Pump", "Valve tool", "Work gloves"],
        "quality_score": 5, "quality_reason_he": "הערוץ הרשמי והתיאור המפורט מאמתים הליך החלפת צמיג מלא לאופנוע אדוונצ'ר.",
        "quality_reason_en": "The official channel and detailed description verify a complete Adventure-bike tyre-change procedure.",
        "evidence": ["description"], "contains_marketing": True, "related_video_ids": ["yt-w_mg182B1OA"]
    },
    {
        "youtube_video_id": "6oh95eTdsNs", "title_original": "Say No to Slow : How to Wheelie an Adventure Bike",
        "title_he": "כיצד להרים גלגל קדמי באופנוע אדוונצ'ר", "channel_name": "Chris Birch - Off Road Coach", "channel_id": OFFICIAL_CHANNEL,
        "published_date": "2019-02-24", "duration_seconds": 600, "domain": "offroad_adventure", "primary_category": "obstacles", "secondary_categories": ["controls_coordination", "riding_position"],
        "subtopics": ["logs_ledges", "weight_transfer", "throttle_precision", "friction_zone"], "content_type": "technique", "tags": ["clutch", "body_position", "controls", "practice_drill", "adventure"],
        "summary_he": "פרק הדרכה חינמי ומפורט שבו כריס בירץ' מפרק הרמת גלגל באופנוע אדוונצ'ר לארבעה חלקים: כיוון אופנוע, עבודת גוף, שליטת מנוע וחיבור הכול.",
        "summary_en": "A free detailed episode in which Chris Birch breaks an Adventure-bike wheelie into four parts: bike setup, body work, motor control and putting it together.",
        "learning_points_he": ["להתחיל מכיוון אופנוע ופקדים שמתאים לתרגיל", "לייצר תנועה בעבודת גוף לפני בקשת כוח", "לתאם מצמד וגז בצורה מדודה", "לחבר את השלבים רק לאחר שכל אחד נשלט בנפרד"],
        "learning_points_en": ["Start with bike and control setup appropriate to the drill", "Create movement with body work before requesting power", "Coordinate clutch and throttle progressively", "Combine the steps only after each is controlled separately"],
        "why_watch_he": "תיאור המקור מפרט את ארבעת שלבי ההדרכה ומזהה במפורש אופנוע אדוונצ'ר.", "why_watch_en": "The source description lists all four instructional stages and explicitly identifies an Adventure bike.",
        "risk_level": "high", "quality_score": 5, "quality_reason_he": "מקור רשמי, ארבעה שלבים מפורשים ומשך של עשר דקות מספקים הדרכה מלאה יחסית.",
        "quality_reason_en": "An official source, four explicit stages and a ten-minute duration provide comparatively complete instruction.",
        "evidence": ["description"], "contains_marketing": True, "related_video_ids": ["yt-waIHKJpQiB4", "yt-mrLyIWGyUWo"]
    },
    {
        "youtube_video_id": "X_Dwq8hmuJ0", "title_original": "Chris Birch Off Road Riding Tips KTM 790 R",
        "title_he": "תנוחה, פניות ובלימה בשטח עם KTM 790 R", "channel_name": "David Mancilla", "channel_id": "UCRwFYUuj3kVynycDuCxcb4Q",
        "published_date": "2022-04-20", "duration_seconds": 618, "primary_category": "riding_position", "secondary_categories": ["offroad_turning", "offroad_braking", "electronic_aids"],
        "subtopics": ["standing_position", "weight_transfer", "offroad_cornering", "brake_coordination", "abs_strategy"], "content_type": "technique", "tags": ["body_position", "cornering", "rear_brake", "electronic_aids", "abs", "adventure"],
        "summary_he": "שיעור צפוף של כריס בירץ' על תנוחת עמידה, העברת גוף בהאצה ובלימה, משקל מחוץ לפנייה, תחושת בלם אחורי ועזרי רכיבה ב־KTM 790 R.",
        "summary_en": "A dense Chris Birch lesson on standing position, body movement under acceleration and braking, outside weighting, rear-brake feel and KTM 790 R rider aids.",
        "learning_points_he": ["לכופף אגן כדי לאפשר טווח תנועה ולא לעמוד זקוף ונוקשה", "להעביר ראש קדימה בהאצה ואגן אחורה בבלימה בלי למשוך בכידון", "להעביר אגן, ראש ומרפקים מחוץ לפנייה כדי להישאר מעל נקודות המגע", "להשתמש בבלם אחורי ליציבות ובקדמי להאטה", "לתרגל תחושת בלם אחורי במדרון קל ומבוקר"],
        "learning_points_en": ["Hinge at the hips to preserve movement instead of standing tall and rigid", "Move the head forward under acceleration and hips back under braking without pulling on the bars", "Move hips, head and elbows outside the turn to stay over the contact patches", "Use the rear brake for stability and the front brake for deceleration", "Develop rear-brake feel on an easy controlled slope"],
        "why_watch_he": "פרקים ותמלול אוטומטי מלא אומתו; המאמן מדבר במפורש על אופנוע 200 ק״ג ועל מעבר מכביש לשטח.",
        "why_watch_en": "Chapters and a full automatic transcript were verified; the instructor explicitly discusses a 200 kg bike and the road-to-off-road transition.",
        "chapters": [chapter(0, 38, "Standing position"), chapter(38, 232, "Accelerating and braking body movement"), chapter(232, 370, "Off-road cornering"), chapter(370, 405, "Standing-position recap"), chapter(405, 603, "Rear-brake control and feel"), chapter(603, 618, "Rider aids")],
        "exercises_he": ["במדרון רחב וקל, מנוע כבוי והילוך סרק, תרגל לחץ בלם אחורי מדורג רק בהשגחה"],
        "exercises_en": ["On a wide gentle slope, engine off and in neutral, practise progressive rear-brake pressure only with supervision"],
        "quality_score": 5, "quality_reason_he": "נבדקו תיאור, שישה פרקים ותמלול שמכסה תנוחה, פניות, בלמים ועזרי רכיבה.",
        "quality_reason_en": "Description, six chapters and transcript evidence cover position, cornering, braking and rider aids.",
        "evidence": ["description", "chapters", "transcript"], "related_video_ids": ["yt-BySQmyz62EI", "yt-h5YrGuIGgVI"]
    },
    {
        "youtube_video_id": "OXsQaL28fgo", "title_original": "Hill Recovery, Cornering & Off-Camber: 3 Essential Skills I Learned from Chris Birch",
        "title_he": "שלוש מיומנויות מכריס בירץ': חילוץ בעלייה, פניות ושיפוע צד", "channel_name": "Feathers Offroad", "channel_id": "UCB3_GM4eGdC3nYgdzQf9nbw",
        "published_date": "2023-07-03", "duration_seconds": 534, "primary_category": "hills", "secondary_categories": ["offroad_turning", "recovery", "riding_position"],
        "subtopics": ["bike_lift_hill", "offroad_cornering", "weight_transfer"], "content_type": "case_study", "tags": ["recovery", "offroad_turning", "counterbalance", "hill", "adventure"],
        "summary_he": "רוכב KTM 890 Adventure מתרגל שלוש מיומנויות שלמד מכריס בירץ': חילוץ בעלייה, פנייה בישיבה ובעמידה, ותנוחת גוף בשיפוע צד.",
        "summary_en": "A KTM 890 Adventure rider practises three skills learned from Chris Birch: hill recovery, seated and standing cornering, and off-camber body position.",
        "learning_points_he": ["להשתמש במצמד כבלם בעת נסיגה מבוקרת בעלייה", "להטות מעט את האופנוע לכיוון העלייה כדי לנהל שיווי משקל", "להעביר משקל החוצה בפנייה בעמידה", "לאזן שיפוע צד באמצעות תנוחת גוף נגדית ומדודה"],
        "learning_points_en": ["Use the clutch as a brake during controlled backing on a hill", "Tip the motorcycle slightly uphill to manage balance", "Move body weight outside during standing turns", "Counter an off-camber slope with deliberate body position"],
        "why_watch_he": "התיאור המפורט והפרקים מפרידים בין שלוש המיומנויות ומזהים KTM 890 Adventure.", "why_watch_en": "The detailed description and chapters separate all three skills and identify a KTM 890 Adventure.",
        "chapters": [chapter(0, 127, "Introduction and bike setup"), chapter(127, 198, "Seated and standing cornering"), chapter(198, 425, "Hill recovery"), chapter(425, 500, "Off-camber position"), chapter(500, 534, "Wheelie practice")],
        "quality_reason_he": "תיאור מפורט וחמישה פרקים מאמתים את התוכן; קישורי שותפים בציוד סומנו כשיווק.",
        "quality_reason_en": "A detailed description and five chapters verify the content; affiliate gear links are marked as marketing.",
        "evidence": ["description", "chapters"], "contains_marketing": True, "related_video_ids": ["yt-di8dBE6jkjM", "yt-M5yAd24z5y0"]
    },
    {
        "youtube_video_id": "P3ckIVpbi9E", "title_original": "Chris Birch Clinic - Backing in a corner",
        "title_he": "כניסה לפנייה בהחלקת גלגל אחורי — קליניקת כריס בירץ'", "channel_name": "Adam de Paiva", "channel_id": "UCsDvHIvSSUbu0LACPcpwwDQ",
        "published_date": "2019-12-14", "duration_seconds": 171, "domain": "offroad_adventure", "primary_category": "offroad_braking", "secondary_categories": ["offroad_turning", "controls_coordination"],
        "subtopics": ["offroad_cornering", "brake_coordination", "entry_speed"], "content_type": "technique", "tags": ["offroad_braking", "rear_brake", "cornering", "controls", "adventure"],
        "summary_he": "כריס בירץ' מסביר בקליניקת אדוונצ'ר כיצד ליזום החלקה קטנה של האחורי בכניסה לפנייה בעזרת בלם אחורי, מהירות מספקת ושליטת מצמד.",
        "summary_en": "At an Adventure clinic, Chris Birch explains how to initiate a small rear slide into a corner using rear brake, sufficient entry speed and clutch control.",
        "learning_points_he": ["להשתמש בבלם אחורי כדי להתחיל החלקה קטנה ולא החלקה ראוותנית", "לאפשר למצמד המחליק לעבוד ולגעת במצמד רק אם מופיעה קפיצה", "להבין שמהירות כניסה נמוכה מדי אינה מאפשרת להקל את האחורי", "לוותר על התרגיל אם רמת הביטחון אינה מספקת"],
        "learning_points_en": ["Use the rear brake to initiate a small slide rather than a dramatic one", "Let the slipper clutch work and ease the clutch only if hopping appears", "Recognize that too little entry speed will not unload the rear", "Opt out when confidence or conditions are insufficient"],
        "why_watch_he": "הכתוביות האוטומטיות נבדקו מול הנגן ומכילות הסבר ישיר של המאמן, לא רק הדגמה.", "why_watch_en": "Automatic captions were checked against the player and contain direct instructor explanation, not only a demonstration.",
        "risk_level": "high", "quality_score": 5, "quality_reason_he": "תמלול זמני ובדיקה חזותית מאמתים את רצף הבלם, המצמד, המהירות ואפשרות הוויתור.",
        "quality_reason_en": "Temporary transcript and visual review verify the brake, clutch, speed and opt-out guidance.",
        "evidence": ["transcript", "visual_content_review"], "related_video_ids": ["yt-X_Dwq8hmuJ0"]
    },
    {
        "youtube_video_id": "y5-Kro247Qs", "title_original": "Chris Birch - Riding technique - Körteknik",
        "title_he": "טכניקת רכיבה בסיסית על KTM 1290 Super Adventure R", "channel_name": "fastbikesse", "channel_id": "UC5hLFJCVU-QBDPhKGMt-hHQ",
        "published_date": "2017-03-16", "duration_seconds": 378, "primary_category": "offroad_basics", "secondary_categories": ["riding_position"],
        "subtopics": ["offroad_foundations", "neutral_body_position", "weight_transfer"], "content_type": "explainer", "tags": ["offroad_basics", "body_position", "adventure", "traction"],
        "summary_he": "כריס בירץ' משתף עקרונות רכיבה בסיסיים במהלך מבחן KTM 1290 Super Adventure R בשטח המדברי של פראקס.",
        "summary_en": "Chris Birch shares fundamental riding pointers while testing a KTM 1290 Super Adventure R in the desert terrain of Paracas.",
        "learning_points_he": ["להתאים תנוחת גוף למסה ולעוצמה של אופנוע גדול", "לשמור ידיים רפויות ולא להילחם בכידון", "להעביר משקל לפני שינויי תאוצה וכיוון"],
        "learning_points_en": ["Adapt body position to the mass and power of a large motorcycle", "Keep the hands relaxed rather than fighting the bars", "Move body weight before changes in acceleration and direction"],
        "why_watch_he": "התיאור מזהה במפורש טיפים בסיסיים, דגם אדוונצ'ר גדול והקשר שטח.", "why_watch_en": "The description explicitly identifies basic tips, a large Adventure model and an off-road setting.",
        "quality_reason_he": "מקור מגזיני עם דגם, מיקום ומטרת הדרכה מפורשים; אין קישור רכישה בתיאור.",
        "quality_reason_en": "A magazine source with explicit model, location and teaching purpose, and no purchase link in the description.",
        "evidence": ["description"], "related_video_ids": ["yt-BySQmyz62EI", "yt-X_Dwq8hmuJ0"]
    },
    {
        "youtube_video_id": "BKgVjALEDVk", "title_original": "What We Think We Know About Riding—And What Chris Birch Actually Teaches",
        "title_he": "מה כריס בירץ' באמת מלמד על רכיבת אדוונצ'ר", "channel_name": "Adventure Rider Radio", "channel_id": "UC84bun_j5ouVRbqcUR3gE9g",
        "published_date": "2025-04-22", "duration_seconds": 6114, "domain": "offroad_adventure", "primary_category": "offroad_basics", "secondary_categories": ["riding_position", "electronic_aids", "suspension_setup"],
        "subtopics": ["standing_position", "course_selection", "damping_basics", "traction_control"], "content_type": "explainer", "tags": ["training", "suspension", "electronic_aids", "body_position", "adventure"],
        "summary_he": "שיחת עומק עם כריס בירץ' על מתי לשבת או לעמוד בשטח, התפתחות ההדרכה, השפעת מתלים מודרניים ועזרי רכיבה על תהליך הלמידה.",
        "summary_en": "An in-depth conversation with Chris Birch about when to sit or stand off road, the evolution of training, and how modern suspension and rider aids affect learning.",
        "learning_points_he": ["לא להפוך עמידה בשטח לכלל מוחלט", "לבחור ישיבה או עמידה לפי שליטה, אנרגיה ותנאי הדרך", "להבין שמתלים טובים יכולים להסתיר טעויות יסוד", "להשתמש באלקטרוניקה ככלי למידה ולא כתחליף לטכניקה"],
        "learning_points_en": ["Do not treat standing off road as an absolute rule", "Choose sitting or standing based on control, energy and terrain", "Recognize that capable suspension can hide fundamental mistakes", "Use electronics as a learning aid rather than a substitute for technique"],
        "why_watch_he": "הראיון עוסק ישירות ברכיבת אדוונצ'ר ובהוראה, ומוסיף הקשר עקרוני שאינו קיים בקליפים קצרים.", "why_watch_en": "The interview directly addresses Adventure riding and instruction, adding conceptual context unavailable in brief clips.",
        "fit_for_he": "לרוכבי אדוונצ'ר בכל הרמות שרוצים להבין עקרונות והחלטות; זהו ראיון ארוך ולא תרגיל מעשי יחיד.",
        "fit_for_en": "For Adventure riders at all levels seeking principles and decisions; this is a long interview, not a single practical drill.",
        "quality_score": 5, "quality_reason_he": "תיאור מפורט של מקור אדוונצ'ר ייעודי מזהה את המרואיין ואת ארבעת נושאי ההוראה.",
        "quality_reason_en": "A detailed description from a dedicated Adventure source identifies the guest and four teaching themes.",
        "evidence": ["description"], "contains_marketing": True, "related_video_ids": ["yt-h5YrGuIGgVI", "yt-X_Dwq8hmuJ0"]
    },
]


SHORT_SPECS: list[dict[str, Any]] = [
    {
        "youtube_video_id": "2Ir9XAcEoFw", "title_original": "Wheelie training with Chris Birch - Off Road Motorcycle Instructor #saynotoslow #shorts",
        "title_he": "קצר: התקדמות בתרגול הרמת גלגל עם כריס בירץ'", "channel_name": "ADVMotoSkillZ", "channel_id": "UCAhh41POT6froY75PsUl-MA",
        "published_date": "2022-11-16", "duration_seconds": 48, "domain": "offroad_adventure", "primary_category": "obstacles", "secondary_categories": ["riding_position", "controls_coordination"],
        "subtopics": ["logs_ledges", "weight_transfer", "friction_zone"], "tags": ["body_position", "clutch", "practice_drill", "adventure"],
        "summary_he": "קצר חזותי מאימון כריס בירץ' על אופנועי אדוונצ'ר גדולים, המציג התחלה מתנוחת גוף, חזרות והתקדמות הדרגתית בהרמת הגלגל.",
        "summary_en": "A visual Short from Chris Birch training on large Adventure motorcycles, showing a body-position starting point, repetitions and gradual front-wheel-lift progression.",
        "learning_points_he": ["להתחיל מתנוחת גוף לפני ניסיון להוסיף גובה", "לבנות את התנועה בחזרות מדורגות", "לקבל תיקון מאמן בין ניסיונות ולא להסיק הוראות מלאות מן הקצר"],
        "learning_points_en": ["Start with body position before adding height", "Build the movement through progressive repetitions", "Use coach feedback between attempts and do not infer a complete procedure from the Short"],
        "why_watch_he": "הסרטון נצפה במלואו; הכתוביות המוטמעות מציינות התחלה מתנוחת גוף והתקדמות מיומנות.",
        "why_watch_en": "The full clip was reviewed; embedded labels identify a body-position start and progressing skills.",
        "risk_level": "high", "quality_score": 4, "quality_reason_he": "הקשר האדוונצ'ר וההתקדמות אומתו חזותית, אך הקצר אינו מספק הוראות ביצוע מלאות ולכן הוא משמש כרענון בלבד.",
        "quality_reason_en": "Adventure context and progression were visually verified, but the Short lacks a complete procedure, so its score is capped.",
        "evidence": ["youtube_player_description", "visual_content_review"], "related_video_ids": ["yt-6oh95eTdsNs"]
    },
]


def build_path() -> dict[str, Any]:
    common_he = ["מיגון שטח מלא", "מגן מנוע", "שטח תרגול סגור"]
    common_en = ["Full off-road protective gear", "Engine protection", "Closed practice area"]
    warning_he = "צפו תחילה; תרגלו בהדרגה ורק לפי הרמה, התנאים והנחיית מדריך מוסמך."
    warning_en = "Study first; practise progressively and only within your level, conditions and qualified-instructor guidance."

    def step(order: int, goal_he: str, goal_en: str, explanation_he: str, explanation_en: str,
             primary: list[str], alternatives: list[str], shorts: list[str], risk: str) -> dict[str, Any]:
        return {
            "order": order,
            "goal_he": goal_he,
            "explanation_he": explanation_he,
            "primary_video_ids": primary,
            "alternative_video_ids": alternatives,
            "equipment_he": common_he,
            "risk_level": risk,
            "warning_he": warning_he,
            "goal_en": goal_en,
            "explanation_en": explanation_en,
            "equipment_en": common_en,
            "warning_en": warning_en,
            "short_video_ids": shorts,
        }

    return {
        "id": "chris-birch-adventure-masterclass",
        "name_he": "מסלול כריס בירץ' לאופנועי אדוונצ'ר",
        "description_he": "מסלול ממוקד מן היסודות ועד פניות, עליות, חילוץ, הרמה ותחזוקת שטח — רק תכנים שאומתו כאדוונצ'ר.",
        "skill_level": "intermediate",
        "name_en": "Chris Birch Adventure masterclass",
        "description_en": "A focused path from fundamentals through cornering, hills, recovery, lifting and field maintenance, using Adventure-verified sources only.",
        "steps": [
            step(1, "לבנות יסודות על אופנוע כבד", "Build fundamentals on a heavy bike",
                 "מתחילים מכיוון פקדים, תנוחה והחלטה מתי לשבת או לעמוד.",
                 "Start with controls setup, position and the decision to sit or stand.",
                 ["yt-BySQmyz62EI", "yt-y5-Kro247Qs"], ["yt-BKgVjALEDVk"], [], "medium"),
            step(2, "לחבר תנוחה, תאוצה ובלימה", "Connect position, acceleration and braking",
                 "לומדים תנועה מאוזנת על אופנוע כבד ותחושת בלם אחורי.",
                 "Study balanced movement on a heavy motorcycle and rear-brake feel.",
                 ["yt-X_Dwq8hmuJ0", "yt-h5YrGuIGgVI"], ["yt-BySQmyz62EI"], [], "medium"),
            step(3, "לבנות שגרת תרגול", "Build a practice routine",
                 "מבודדים יסודות בתרגילים וחוזרים עליהם לפני יציאה לשטח מורכב.",
                 "Isolate fundamentals in drills before moving to complex terrain.",
                 ["yt-waIHKJpQiB4", "yt-oZiD8uxH0hQ"], ["yt-mrLyIWGyUWo"], [], "medium"),
            step(4, "להבין החלקה בכניסה לפנייה", "Understand a slide into a corner",
                 "זהו פרק מתקדם לצפייה ולהדרכה מוסמכת, לא לתרגול עצמאי מן הסרטון.",
                 "This is advanced study for qualified coaching, not independent practice from video.",
                 ["yt-P3ckIVpbi9E"], ["yt-X_Dwq8hmuJ0"], [], "high"),
            step(5, "לנהל עליות ושיפוע צד", "Manage hills and off-camber terrain",
                 "לומדים גישה לעלייה, חילוץ לאחר עצירה ותנוחת גוף בשיפוע צד.",
                 "Study hill approach, recovery after a stall and off-camber body position.",
                 ["yt-M5yAd24z5y0"], ["yt-di8dBE6jkjM", "yt-OXsQaL28fgo"], [], "high"),
            step(6, "להרים גלגל קדמי באופן מדורג", "Build a progressive front-wheel lift",
                 "הפרק המלא קודם; הקצר משמש רק כתזכורת לתנוחת גוף ולהתקדמות.",
                 "Use the full lesson first; the Short is only a reminder of body position and progression.",
                 ["yt-6oh95eTdsNs"], ["yt-waIHKJpQiB4"], ["yts-2Ir9XAcEoFw"], "high"),
            step(7, "להרים ולחלץ אופנוע כבד", "Lift and recover a heavy motorcycle",
                 "מפרידים בין מכניקת הרמה נכונה לבין תכנון חילוץ בבוץ או בשיפוע.",
                 "Separate sound lifting mechanics from planning mud or slope recovery.",
                 ["yt-axhRmbeUy28"], ["yt-zMuVNBk9Ogw", "yt-di8dBE6jkjM"], [], "high"),
            step(8, "לטפל בצמיג בשטח", "Handle a tyre problem in the field",
                 "מסיימים בתמיכת אופנוע ללא רגלית אמצע ובהחלפת צמיג בכלים פשוטים.",
                 "Finish with supporting a bike without a center stand and changing a tyre with simple tools.",
                 ["yt-w_mg182B1OA"], ["yt-rCJmU0mIn_U"], [], "medium"),
        ],
    }


def build_source_audit() -> dict[str, Any]:
    selected = [
        {"youtube_video_id": spec["youtube_video_id"], "media_format": "full", "decision": "include", "reason": "adventure_instruction_verified"}
        for spec in FULL_SPECS
    ] + [
        {"youtube_video_id": spec["youtube_video_id"], "media_format": "short", "decision": "include", "reason": "adventure_instruction_verified_by_full_visual_review"}
        for spec in SHORT_SPECS
    ]
    excluded = [
        {"youtube_video_id": "XprOa7xx15o", "decision": "exclude", "reason": "participant_hill_climb_without_instruction"},
        {"youtube_video_id": "4kSGOxGgZQo", "decision": "exclude", "reason": "hill_climb_showcase_without_instruction"},
        {"youtube_video_id": "hR28mpLjlik", "decision": "exclude", "reason": "wheelie_showcase_without_teaching_steps"},
        {"youtube_video_id": "O1ZxB5Hm6gs", "decision": "exclude", "reason": "official_short_is_wheelie_showcase_without_instruction"},
        {"youtube_video_id": "F-Mts-Iwtrc", "decision": "exclude", "reason": "official_short_is_adventure_day_showcase"},
        {"youtube_video_id": "T_OXA6JdtzU", "decision": "exclude", "reason": "official_short_is_ride_showcase"},
        {"youtube_video_id": "RXNjYa5svAo", "decision": "exclude", "reason": "hard_enduro_not_adventure"},
        {"youtube_video_id": "CqboTvhGRxA", "decision": "exclude", "reason": "visual_review_shows_dirt_bike_lifter_training_not_adventure"},
        {"youtube_video_id": "OsNaBO78Y1Y", "decision": "exclude", "reason": "log_pivot_is_dirt_bike_focused"},
        {"youtube_video_id": "7oDyewNtTF0", "decision": "exclude", "reason": "dirt_bike_wheelie_episode_not_adventure"},
        {"youtube_video_id": "eNj0eHkV2BI", "decision": "exclude", "reason": "hard_enduro_training_not_adventure"},
        {"youtube_video_id": "YMDCtCmWXEA", "decision": "exclude", "reason": "commercial_series_trailer_not_tutorial"},
        {"youtube_video_id": "LzNBmzNqzPU", "decision": "exclude", "reason": "commercial_series_preview_not_tutorial"},
        {"youtube_video_id": "l4U8P0wsygA", "decision": "exclude", "reason": "product_accessories_promotion"},
        {"youtube_video_id": "BFki1Ud3O0A", "decision": "exclude", "reason": "product_heavy_model_setup"},
        {"youtube_video_id": "TAH2RlaK-mk", "decision": "exclude", "reason": "product_heavy_model_setup"},
        {"youtube_video_id": "tGG4T1Uqqvs", "decision": "exclude", "reason": "product_heavy_model_setup"},
        {"youtube_video_id": "knO0oDK6ol0", "decision": "exclude", "reason": "title_only_evidence_visual_review_blocked_by_advertising"},
        {"youtube_video_id": "YgCdnylSKNw", "decision": "exclude", "reason": "creator_explicitly_says_video_is_not_meant_to_teach"},
        {"youtube_video_id": "FQLfWAfldkM", "decision": "exclude", "reason": "brief_skill_demonstration_without_teaching_steps"},
        {"youtube_video_id": "NNzkdKk_bJU", "decision": "exclude", "reason": "not_a_youtube_short_and_no_source_description"},
    ]
    return {
        "document_title": "ביקורת מקורות — הרחבת Chris Birch לאופנועי אדוונצ'ר",
        "document_version": "1.0.0",
        "product_version": "3.4.0",
        "reviewed_on": CHECKED,
        "discovery_counts": {"official_channel_full": 103, "official_channel_shorts": 18, "initial_search_unique": 160, "deep_search_unique": 203, "combined_unique": 287},
        "detailed_metadata_reviewed": 66,
        "published_full": len(FULL_SPECS),
        "published_shorts": len(SHORT_SPECS),
        "policy_he": "תוכן נכנס רק כאשר ההדרכה והקשר לאופנוע אדוונצ'ר נתמכים בתיאור, פרקים, תמלול או בדיקה חזותית. ספק, אנדורו, ראווה או פרסום ממוקד גוררים הסרה.",
        "policy_en": "Content is included only when both instruction and Adventure-motorcycle relevance are supported by description, chapters, transcript or visual review. Doubt, Enduro, showcase or product-focused promotion means exclusion.",
        "selected": selected,
        "representative_exclusions": excluded,
    }


def build_visual_review() -> dict[str, Any]:
    return {
        "document_title": "בדיקה חזותית פרטנית — Chris Birch Adventure",
        "document_version": "1.0.0",
        "product_version": "3.4.0",
        "reviewed_on": CHECKED,
        "items": [
            {"youtube_video_id": "XprOa7xx15o", "decision": "exclude", "observations": ["BMW 1200GS visible", "participant hill-climb attempt", "no teaching steps"]},
            {"youtube_video_id": "2Ir9XAcEoFw", "decision": "include_short", "observations": ["large Adventure motorcycles", "body-position starting label", "progressing-skills label", "coach feedback"]},
            {"youtube_video_id": "NNzkdKk_bJU", "decision": "exclude", "observations": ["Chris briefs riders", "Adventure motorcycles present", "not a YouTube Short", "no source description"]},
            {"youtube_video_id": "CqboTvhGRxA", "decision": "exclude", "observations": ["dirt-bike obstacle context", "Adventure relevance not demonstrated"]},
            {"youtube_video_id": "axhRmbeUy28", "decision": "include_full", "observations": ["large KTM Adventure", "assess situation", "use legs and hips", "straighten back", "engage core"]},
            {"youtube_video_id": "BySQmyz62EI", "decision": "include_full", "observations": ["large Adventure motorcycles", "handlebar angle", "lever angle", "seated position", "elbow position", "steering"]},
            {"youtube_video_id": "P3ckIVpbi9E", "decision": "include_full", "observations": ["direct instructor briefing", "rear-brake slide", "slipper-clutch guidance", "explicit opt-out guidance"]},
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    videos_path = ROOT / "data/videos.json"
    shorts_path = ROOT / "data/shorts.json"
    paths_path = ROOT / "data/learning-paths.json"
    videos = load(videos_path)
    shorts = load(shorts_path)
    paths = load(paths_path)
    selected_full_ids = {spec["youtube_video_id"] for spec in FULL_SPECS}
    selected_short_ids = {spec["youtube_video_id"] for spec in SHORT_SPECS}
    videos = [item for item in videos if item["youtube_video_id"] not in selected_full_ids]
    shorts = [item for item in shorts if item["youtube_video_id"] not in selected_short_ids | {"NNzkdKk_bJU"}]
    added_full = [record(spec) for spec in FULL_SPECS]
    added_shorts = [record(spec, short=True) for spec in SHORT_SPECS]
    videos.extend(added_full)
    shorts.extend(added_shorts)
    path = build_path()
    paths = [item for item in paths if item["id"] != path["id"]] + [path]
    write(videos_path, videos)
    write(shorts_path, shorts)
    write(paths_path, paths)
    write(ROOT / "research/chris-birch-v3.4/source-audit.json", build_source_audit())
    write(ROOT / "research/chris-birch-v3.4/visual-review.json", build_visual_review())
    summary = {
        "document_title": "דוח הרחבת Chris Birch לאופנועי אדוונצ'ר",
        "document_version": "1.0.0",
        "product_version": "3.4.0",
        "added_full": len(FULL_SPECS),
        "added_shorts": len(SHORT_SPECS),
        "total_full": len(videos),
        "total_shorts": len(shorts),
        "total_items": len(videos) + len(shorts),
        "dedicated_learning_path_steps": len(path["steps"]),
        "selected_video_ids": [spec["youtube_video_id"] for spec in FULL_SPECS + SHORT_SPECS],
    }
    write(ROOT / "reports/chris-birch-v3.4.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
