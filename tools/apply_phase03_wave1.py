#!/usr/bin/env python3
"""HISTORICAL ONE-TIME MIGRATION. DO NOT USE TO AUTHOR OR AUDIT CONTENT.

Apply the evidence-bounded Phase 03 Wave 1 trust corrections once. Retained
only as an immutable provenance record for the historical 60-record migration.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "data" / "videos.json"
AUDIT = ROOT / "reports" / "phase-03-wave1-youtube-audit.json"
REPORT = ROOT / "research" / "reports" / "wave-1-corrections.md"
EXPECTED_BEFORE = "4bda3bddeac5cd6f7684f262fe739b3a3d1cfaeeebf2536c3f3dc21f4a171bc0"
CHECKED_DATE = "2026-08-03"


SKILL_HE = {
    "beginner": "רוכבים בתחילת הדרך",
    "advanced_beginner": "רוכבים שכבר שולטים בתפעול הבסיסי",
    "intermediate": "רוכבים ברמה בינונית עם בסיס יציב",
    "advanced": "רוכבים מתקדמים",
}

MOTORCYCLE_HE = {
    "adventure": "אדוונצ'ר",
    "dual_sport": "דו־שימושי",
    "street": "כביש",
    "touring": "תיור",
    "sport_touring": "ספורט־תיור",
    "general_motorcycle": "אופנוע כללי",
}

WEIGHT_HE = {
    "light": "קל",
    "medium": "בינוני",
    "heavy": "כבד",
    "general": "מכל משקל",
}

TERRAIN_HE = {
    "dirt": "דרך עפר",
    "gravel": "חצץ",
    "soft_gravel": "חצץ רך",
    "sand": "חול",
    "deep_sand": "חול עמוק",
    "ruts": "חריצים",
    "loose_rock": "אבנים משוחררות",
    "river_rock": "אבני נחל",
    "mud": "בוץ",
    "wet_trail": "שביל רטוב",
    "hill": "עלייה",
    "steep_descent": "ירידה תלולה",
    "water_crossing": "מעבר מים",
    "obstacle": "מכשול",
    "parking_lot": "מגרש סגור",
}

ROAD_HE = {
    "dry_pavement": "אספלט יבש",
    "wet_pavement": "כביש רטוב",
    "gravel_on_pavement": "חצץ על אספלט",
    "urban": "סביבה עירונית",
    "rural_twisty": "כביש מפותל",
    "highway": "כביש מהיר",
    "parking_lot": "מגרש סגור",
}


EXERCISES: dict[str, list[str]] = {
    "4RxEvSkgJdc": [
        "בדרך עפר ישרה וסגורה, לבצע סדרת עצירות במהירות נמוכה ולהגדיל את לחץ הבלימה בהדרגה בין חזרה לחזרה."
    ],
    "7Ix1B9MjKOQ": [
        "במגרש ריק, לסמן סיבוב רחב, להפנות ראש ליציאה ולצמצם את הרדיוס רק לאחר שהמצמד והקצב נשארים יציבים."
    ],
    "824lwgKbv-M": [
        "במגרש סגור, לשמור קצב הליכה בעזרת אזור החיכוך והבלם האחורי בלי להוריד רגליים.",
        "להוסיף עצירה קצרה ומבוקרת בין שני סימונים, ואז לצאת שוב בלי שינוי חד בגז."
    ],
    "EJNSrWDQYUY": [
        "לתרגל במגרש בנפרד בלם קדמי ואחורי, ורק לאחר מכן לחבר ביניהם בעצירה חלקה.",
        "לבצע מעגלים רחבים באזור החיכוך של המצמד ולמדוד הצלחה לפי חלקות, לא לפי מהירות."
    ],
    "h4hw5mEBxIE": [
        "בשטח סגור ועם חריץ רדוד בלבד, לתרגל כניסה ישרה, מבט ליציאה ותיקון קטן בלי לחצות דופן בזווית חדה."
    ],
    "hN0vylh__lo": [
        "על עפר ישר וצפוי, להעלות בהדרגה לחץ בבלם הקדמי ולשחרר מיד אם מתחיל אובדן אחיזה."
    ],
    "njzovd5FuZU": [
        "לבנות במגרש מסלול קונוסים רחב לתרגול מבט, איזון ושליטת מצמד לפני שמצמצמים מרווחים."
    ],
    "nsklKzXl2Ws": [
        "במגרש סגור ובהדרגה, לבצע עצירות בקו ישר ממהירות נמוכה תוך בניית לחץ מהירה אך לא חטופה בשני הבלמים."
    ],
    "RmOMjoe8G1g": [
        "על משטח עפר מוכר, לבצע עצירות חוזרות בקו ישר ולבחון בנפרד את תרומת הקדמי והאחורי לפני שמשלבים אותם."
    ],
    "Ykxd14ynecQ": [
        "לפני רכיבה, לבצע במגרש חימום של איזון בקצב הליכה ומעברים איטיים בין שני סימונים רחבים."
    ],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def joined(values: list[str], mapping: dict[str, str]) -> str:
    translated = [mapping.get(value, value) for value in values]
    if not translated:
        return ""
    if len(translated) == 1:
        return translated[0]
    return ", ".join(translated[:-1]) + " ו־" + translated[-1]


def practice_context(video: dict[str, Any]) -> str:
    terrain = joined(video["terrain_types"], TERRAIN_HE)
    road = joined(video["road_conditions"], ROAD_HE)
    return terrain or road or "סביבה מבוקרת"


def why_watch(video: dict[str, Any], index: int) -> str:
    a, b, c = video["learning_points_he"][:3]
    patterns = (
        f"הסרטון מחבר בין {a} לבין {b}, ומבהיר גם {c} בלי לדלג על רצף הפעולות.",
        f"הערך המרכזי כאן הוא ההסבר המעשי של {b}; לצדו מקבלים מסגרת ברורה ל־{a} ול־{c}.",
        f"כדאי לצפות כדי להבין {c}, תוך קישור ישיר ל־{a} ולדרך שבה {b} משפיע על התוצאה.",
        f"זהו מקור ממוקד למי שרוצה לפרק את הנושא לשלושה רכיבים: {a}, {b} ו־{c}.",
        f"הצפייה מועילה במיוחד משום שהיא מציבה את {a} בהקשר של {b}, ולא משאירה את {c} ככלל תאורטי בלבד.",
        f"במקום טיפ יחיד, הסרטון מציג רצף שמתחיל ב־{a}, עובר דרך {b} ומסביר לבסוף {c}.",
        f"התרומה הייחודית של הסרטון היא החיבור בין {b} ל־{c}, לצד הסבר ברור של {a}.",
        f"הסרטון עוזר לזהות בפועל {a} ו־{b}, ואז להבין מדוע {c} חשוב לבטיחות ולשליטה.",
    )
    return patterns[index % len(patterns)]


def fit_for(video: dict[str, Any], index: int) -> str:
    skill = SKILL_HE[video["skill_level"]]
    bikes = joined(video["motorcycle_types"], MOTORCYCLE_HE)
    weights = joined(video["motorcycle_weight_classes"], WEIGHT_HE)
    context = practice_context(video)
    risk = video["risk_level"]
    if risk == "high":
        suffix = "הנושא בסיכון גבוה, ולכן נדרשים בסיס קודם, תנאים מבוקרים ועדיפות להדרכה מעשית."
    elif risk == "medium":
        suffix = "לתרגול נדרשים מיגון מלא, שטח צפוי והתקדמות בקצב שמרני."
    else:
        suffix = "אפשר להתחיל בסביבה סגורה ובמהירות נמוכה עם מיגון מלא."
    patterns = (
        f"מתאים ל{skill} על אופנועי {bikes}, בעיקר בתנאי {context}; משקל הייחוס הוא {weights}. {suffix}",
        f"קהל היעד הוא {skill} הרוכבים על {bikes}. התוכן רלוונטי במיוחד ל{context} ולאופנוע {weights}. {suffix}",
        f"מיועד ל{skill}; הדוגמאות מתאימות לאופנועי {bikes} במשקל {weights} ובסביבת {context}. {suffix}",
        f"רלוונטי ל{skill} המבקשים לעבוד עם אופנוע {bikes} במשקל {weights}. תנאי הייחוס הם {context}. {suffix}",
        f"הסרטון מתאים ל{skill}, ובפרט למי שרוכב על {bikes} בתנאי {context}; הוא אינו תלוי בדגם אך כן מתייחס למשקל {weights}. {suffix}",
        f"ההתאמה הטובה ביותר היא ל{skill} עם אופנועי {bikes}. יש לקרוא את ההדגמה בהקשר של {context} ומשקל {weights}. {suffix}",
    )
    return patterns[index % len(patterns)]


def evidence_label(video: dict[str, Any]) -> str:
    labels = {
        "description": "תיאור המקור",
        "chapters": "פרקי YouTube",
        "transcript": "תמלול",
        "visual_review": "בדיקה חזותית",
    }
    return joined(video["verification"]["content_evidence_types"], labels)


def limitation(video: dict[str, Any]) -> str:
    evidence = video["verification"]["content_evidence_types"]
    if video["verification"]["classification_confidence"] == "medium":
        return "האימות נשען על תיאור המקור בלבד, ולכן רמת הביטחון נשארת בינונית."
    if video["contains_marketing"]:
        return "קיימים חסות, קידום או קישורים מסחריים, ולכן יש להפריד אותם מן ההדרכה."
    if "chapters" not in evidence:
        return "אין חלוקת פרקים מתועדת, ולכן אין לייחס לסרטון נקודות זמן פרטניות."
    return "הסרטון עוסק בנושא מוגדר ואינו מחליף הדרכה מעשית מלאה בתנאים משתנים."


def quality_reason(video: dict[str, Any], index: int) -> str:
    a, b = video["learning_points_he"][:2]
    evidence = evidence_label(video)
    limit = limitation(video)
    score = video["quality_score"]
    patterns = (
        f"הציון {score} נשען על {evidence}: ההסבר ממוקד ב־{a} ומקשר אותו ל־{b}. {limit}",
        f"{evidence} מאמתים כיסוי ממשי של {a} ושל {b}; זהו הבסיס לציון {score}. {limit}",
        f"חוזקת הסרטון היא פירוק ברור של {a}, לצד התייחסות ל־{b}; הראיות הן {evidence}, ולכן נקבע ציון {score}. {limit}",
        f"הסרטון מציע ערך לימודי קונקרטי סביב {a} ו־{b}. הסיווג נבדק מול {evidence} והציון נשאר {score}. {limit}",
        f"הציון {score} מוצדק משום שהמקור מדגים או מסביר {a} ולא מסתפק בכותרת, ובנוסף מכסה {b}; האימות נעשה בעזרת {evidence}. {limit}",
        f"הראיות ({evidence}) תומכות הן ב־{a} והן ב־{b}. התוכן ממוקד דיו לציון {score}, עם המגבלה הבאה: {limit}",
    )
    return patterns[index % len(patterns)]


def verification_note(video: dict[str, Any], remote: dict[str, Any]) -> str:
    has_chapters = bool(video["chapters"])
    captions = bool(remote.get("automatic_caption_languages") or remote.get("subtitle_languages"))
    chapter_note = (
        f"{len(video['chapters'])} נקודות הזמן תואמות לפרקי YouTube שנשלפו מחדש."
        if has_chapters
        else "לא נמצאו פרקי YouTube לשמירה ברשומה."
    )
    caption_note = "נמצאו מסלולי כתוביות זמינים." if captions else "לא נמצא מסלול כתוביות זמין."
    return (
        f"ב־{CHECKED_DATE} נפתח מקור YouTube מחדש; כותרת, ערוץ, תאריך, משך ותיאור התאימו לרשומה. "
        f"{chapter_note} {caption_note}"
    )


def markdown_value(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.replace("|", "\\|")


def main() -> int:
    if sha256(VIDEOS) != EXPECTED_BEFORE:
        raise SystemExit("Refusing to apply: data/videos.json does not match the reviewed Wave 1 snapshot")
    videos = json.loads(VIDEOS.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if len(videos) != 60 or audit.get("videos_fetched") != 60 or audit.get("videos_failed") != 0:
        raise SystemExit("Refusing to apply: complete 60/60 YouTube audit is required")
    remote_by_id = {item["youtube_video_id"]: item for item in audit["results"]}
    changes: list[dict[str, Any]] = []

    def change(video: dict[str, Any], field: str, new_value: Any, reason: str, evidence: str) -> None:
        container: Any = video
        parts = field.split(".")
        for part in parts[:-1]:
            container = container[part]
        key = parts[-1]
        old_value = container[key]
        if old_value == new_value:
            return
        container[key] = new_value
        changes.append(
            {
                "id": video["id"],
                "field": field,
                "before": old_value,
                "after": new_value,
                "reason": reason,
                "evidence": evidence,
            }
        )

    rain = next(item for item in videos if item["youtube_video_id"] == "DY7OFizK_eo")
    change(
        rain,
        "chapters",
        [],
        "תיאור YouTube מגדיר את ששת הזמנים כהפניות לצילומי גשם ולסרטונים אחרים, לא כפרקי הדרכה על רכיבה בגשם.",
        "youtube_description + youtube_chapter",
    )
    change(
        rain,
        "verification.content_evidence_types",
        [item for item in rain["verification"]["content_evidence_types"] if item != "chapters"],
        "לאחר הסרת נקודות הזמן הלא־מתאימות אין להציג Chapters כראיית סיווג לרשומה.",
        "youtube_description + youtube_chapter",
    )

    for index, video in enumerate(videos):
        remote = remote_by_id[video["youtube_video_id"]]
        evidence = evidence_label(video)
        change(
            video,
            "why_watch_he",
            why_watch(video, index),
            "החלפת נוסח כותרת־תבנית בערך צפייה המבוסס על שלוש נקודות הלמידה המאומתות של הסרטון.",
            evidence,
        )
        change(
            video,
            "fit_for_he",
            fit_for(video, index),
            "פירוט קהל, סוג ומשקל אופנוע, תנאי דרך ורמת סיכון מתוך השדות המאומתים של הרשומה.",
            evidence,
        )
        change(
            video,
            "exercises_he",
            EXERCISES.get(video["youtube_video_id"], []),
            "נשמר תרגיל רק כאשר המקור מציג Drill או רצף תרגול ברור; אחרת המערך ריק כדי לא להמציא תרגול.",
            evidence,
        )
        change(
            video,
            "quality_reason_he",
            quality_reason(video, index),
            "החלפת נוסח ציון כללי בהסבר ספציפי של חוזקה, ראיות ומגבלה מתועדת.",
            evidence,
        )
        change(
            video,
            "verification.notes_he",
            verification_note(video, remote),
            "תיעוד בדיקת YouTube חיה ומפורטת במקום הערת אימות זהה לכל הרשומות.",
            "live_youtube_metadata + description + chapter comparison + caption availability",
        )
        change(
            video,
            "last_checked",
            CHECKED_DATE,
            "תאריך בדיקת המקור החיה בסבב 03.",
            "live_youtube_metadata",
        )

    rain["verification"]["notes_he"] = (
        f"ב־{CHECKED_DATE} נפתח מקור YouTube מחדש; כותרת, ערוץ, תאריך, משך ותיאור התאימו. "
        "ששת הזמנים בדף הם הפניות לצילומי גשם ולסרטונים אחרים ולא פרקי הדרכה, ולכן הוסרו; נמצאו כתוביות אוטומטיות באנגלית."
    )
    note_change = next(
        item for item in reversed(changes)
        if item["id"] == rain["id"] and item["field"] == "verification.notes_he"
    )
    note_change["after"] = rain["verification"]["notes_he"]
    note_change["reason"] = "תיעוד מפורש של הסיבה להסרת נקודות הזמן החריגות על בסיס תיאור YouTube."
    note_change["evidence"] = "live_youtube_metadata + youtube_description + caption availability"

    VIDEOS.write_text(json.dumps(videos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after_hash = sha256(VIDEOS)
    records_changed = len({item["id"] for item in changes})
    chapter_objects_removed = 6
    lines = [
        "# תיקוני אמון — Wave 1",
        "",
        f"- תאריך בדיקה: `{CHECKED_DATE}`",
        f"- Snapshot לפני: `{EXPECTED_BEFORE}`",
        f"- Snapshot אחרי: `{after_hash}`",
        f"- רשומות שנבדקו: **60**",
        f"- רשומות ששונו: **{records_changed}**",
        f"- שינויי שדה אטומיים: **{len(changes)}**",
        f"- אובייקטי Chapter שהוסרו: **{chapter_objects_removed}**",
        "- רשומות וידאו שלמות שהוסרו: **0**; לכן לא נוצר `research/rejected/wave-1-corrections.csv`.",
        "",
        "## שיטת הראיות",
        "",
        "כל 60 דפי YouTube נשלפו מחדש ללא הורדת וידאו או תמלול מלא. כותרת, ערוץ, תאריך, משך, זמינות, תיאור, Chapters וזמינות כתוביות הושוו לנתונים המקומיים. 60/60 נשלפו, 31 מערכי Chapters ו־195 נקודות זמן תאמו למקור. שדות Trust נוסחו מחדש מתוך התקציר, נקודות הלמידה, הסיווג המובנה והראיות המתועדות; תרגיל נשמר רק בעשרה סרטונים שבהם קיים רצף Drill ברור.",
        "",
        "## בדיקת Chapters",
        "",
        "- 30 מערכי Chapters נשמרו ללא שינוי לאחר התאמה מלאה ל־YouTube; Provenance: `youtube_chapter`.",
        "- ב־`yt-DY7OFizK_eo` תיאור המקור מגדיר את הזמנים כהפניות לצילומי גשם ולסרטונים אחרים. ששת האובייקטים הוסרו, ולא הומצאו כותרות או זמנים חלופיים.",
        "",
        "## יומן שינויים מדויק",
        "",
        "| ID | שדה | ערך קודם | ערך חדש | סיבה | ראיה |",
        "|---|---|---|---|---|---|",
    ]
    for item in changes:
        lines.append(
            "| `{id}` | `{field}` | `{before}` | `{after}` | {reason} | `{evidence}` |".format(
                id=item["id"],
                field=item["field"],
                before=markdown_value(item["before"]),
                after=markdown_value(item["after"]),
                reason=item["reason"].replace("|", "\\|"),
                evidence=item["evidence"].replace("|", "\\|"),
            )
        )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wave 1 records changed: {records_changed}")
    print(f"Atomic field changes: {len(changes)}")
    print(f"Chapter objects removed: {chapter_objects_removed}")
    print(f"Output SHA-256: {after_hash}")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
