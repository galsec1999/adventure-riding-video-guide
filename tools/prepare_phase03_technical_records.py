#!/usr/bin/env python3
"""Build the ten curated Phase 03 technical records from live YouTube metadata.

The script is intentionally metadata-only: it consumes the compact yt-dlp research
report produced by ``youtube_research.py`` and never downloads media or transcripts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SELECTED_IDS = (
    "CI6h7XtyINY",
    "QXl542xFnhU",
    "CCCl2KBpP5g",
    "sJg_rAPp0Rg",
    "zsKLdi_nYYQ",
    "_zQoFML9xPk",
    "oW7eVgdCC58",
    "YlseO0ceUcw",
    "dPmq8jpUL5s",
    "KC0Rv0aM7OI",
    "uscjPZXNyMc",
)


CURATION: dict[str, dict[str, Any]] = {
    "CI6h7XtyINY": {
        "title_he": "מבוא לכיוון מתלים באופנוע אדוונצ'ר",
        "domain": "mixed",
        "primary_category": "suspension_setup",
        "secondary_categories": ["ergonomics"],
        "tags": ["suspension", "preload", "damping", "controls_setup"],
        "skill_level": "advanced_beginner",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel"],
        "road_conditions": ["dry_pavement"],
        "summary_he": "מבוא קצר המשתמש ב־Yamaha Ténéré 700 כדי להציג את שלושת כיווני היסוד שהיוצר מתאר: קדם־עומס, שיכוך דחיסה ושיכוך החזרה, ואת תפקידם הכללי במתלה.",
        "learning_points_he": [
            "להבדיל בין קדם־עומס לבין כיוון שיכוך",
            "לזהות את ההפרדה בין שיכוך דחיסה לשיכוך החזרה",
            "להשתמש בספר הרכב כדי לאתר את הכיוונים הספציפיים לדגם",
            "להבין שזהו מבוא קהילתי ולא תחליף לכיוון מקצועי",
        ],
        "fit_for_he": "מתאים לרוכבי אדוונצ'ר בתחילת ההיכרות הטכנית שרוצים מילון מושגים בסיסי לפני קריאת ספר הרכב או פנייה לאיש מתלים.",
        "why_watch_he": "ארבעת הפרקים מחלקים את המבוא לקדם־עומס, דחיסה והחזרה, והיוצר מצהיר בשקיפות שאינו מומחה—מגבלה שחשוב לשמור לצד הערך ההסברי.",
        "exercises_he": [],
        "equipment_he": ["ספר רכב", "כלי כיוון שמאושר לדגם", "דף רישום של מצב הכיוון המקורי"],
        "safety_warnings_he": ["אין לשנות כיוון מתלים מעבר לטווח היצרן או בלי לתעד את מצב המוצא; לאחר שינוי יש לבדוק את האופנוע בהדרגה ובסביבה בטוחה."],
        "common_mistakes_he": ["בלבול בין קדם־עומס לקשיחות הקפיץ", "שינוי כמה כיוונים יחד בלי רישום", "העתקת כיוון של רוכב או דגם אחר"],
        "quality_score": 3,
        "quality_reason_he": "תיאור מפורט וארבעה פרקים מאמתים את שלושת מושגי הכיוון; הציון מוגבל ל־3 מפני שהיוצר מצהיר שאינו מומחה והסרטון כולל קישורי שותפים.",
        "source_type": "community_educator",
        "contains_marketing": True,
        "related_video_ids": ["yt-CCCl2KBpP5g", "yt-sJg_rAPp0Rg"],
    },
    "QXl542xFnhU": {
        "title_he": "בחירת לחץ אוויר לצמיגי אדוונצ'ר ודו־שימושי",
        "domain": "mixed",
        "primary_category": "tires_setup",
        "secondary_categories": ["gravel_dirt", "sand"],
        "tags": ["tire_pressure", "traction", "planning", "heavy_bike"],
        "skill_level": "advanced_beginner",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["light", "medium", "heavy"],
        "terrain_types": ["dirt", "gravel", "sand"],
        "road_conditions": ["dry_pavement"],
        "summary_he": "השוואה בין שלוש דרכים לקביעת לחץ אוויר: טווחים כלליים לפי משקל האופנוע, הוראות היצרן וכיוון מדורג לפי עומס, צמיג, גלגל, טמפרטורה ותוואי.",
        "learning_points_he": [
            "להתחיל מהמלצת יצרן האופנוע והצמיג ולא ממספר אוניברסלי",
            "להבין כיצד משקל, מורכב, מטען וחום משנים את נקודת המוצא",
            "לזהות את פשרות האחיזה, החום, השחיקה והגנת החישוק",
            "להחזיר לחץ מיד לאחר קטע קצר שבו הופחת לצורך אחיזה מיוחדת",
        ],
        "fit_for_he": "מתאים לרוכבי אדוונצ'ר ודו־שימושי שרוצים להבין כיצד לבחור נקודת מוצא שמרנית ללחץ אוויר לפני כביש, שביל או חול.",
        "why_watch_he": "הסרטון אינו נותן מספר קסם בלבד; הוא מפרק את המשתנים ואת הנזקים האפשריים מלחץ נמוך או גבוה מדי, ומדגיש מדידה וניפוח מחדש.",
        "exercises_he": ["רשום את ערכי היצרן לעומס הרגיל שלך והשווה אותם למדידה קרה במד לחץ תקין, בלי לשנות לחץ לפני עיון בספר האופנוע."],
        "equipment_he": ["מד לחץ אוויר תקין", "משאבה מתאימה", "ספר רכב או מדבקת לחצים", "ציוד מיגון מלא"],
        "safety_warnings_he": ["אין להעתיק ערכי PSI מסרטון לאופנוע אחר; לחץ נמוך מדי עלול לגרום לתקר, נזק לחישוק או אובדן אטימה."],
        "common_mistakes_he": ["התעלמות ממשקל מטען או מורכב", "הפחתת לחץ בלי אפשרות לנפח מחדש", "מדידה מיד לאחר התחממות הצמיג"],
        "quality_score": 5,
        "quality_reason_he": "תיאור מפורט ושמונה פרקים מאמתים שלוש שיטות בחירה, משתני עומס וסיכונים מכניים; ההמלצות המספריות מוצגות כטווחים ולא כתחליף להוראות היצרן.",
        "source_type": "training_channel",
        "contains_marketing": True,
        "related_video_ids": ["yt-oW7eVgdCC58", "yt-CCCl2KBpP5g"],
    },
    "CCCl2KBpP5g": {
        "title_he": "קדם־עומס ושקיעת מתלים באופנוע אדוונצ'ר",
        "domain": "mixed",
        "primary_category": "suspension_setup",
        "secondary_categories": ["ergonomics"],
        "tags": ["suspension", "preload", "sag", "heavy_bike"],
        "skill_level": "intermediate",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "touring", "sport_touring"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel"],
        "road_conditions": ["dry_pavement", "rural_twisty"],
        "summary_he": "שיחה טכנית עם מומחה מתלים על תפקיד הקפיץ, קדם־עומס ושקיעה שלילית, ועל הקשר בין קצב הקפיץ, טווח הכיוון והתחושה שהרוכב מקבל מן האופנוע.",
        "learning_points_he": [
            "להבחין בין שינוי קדם־עומס לבין שינוי קצב הקפיץ עצמו",
            "להבין מדוע נדרש מהלך שלילי כדי שהגלגל יוכל לעקוב אחר שקע",
            "לקשר בין עומס הרוכב והמטען לבין טווח הכיוון הזמין",
            "לזהות מתי כיוון קיצוני מעיד שהקפיץ אינו מתאים לעומס",
        ],
        "fit_for_he": "מיועד לרוכבים בעלי בסיס טכני שמעמיסים ציוד או מורכב ורוצים להבין את מדידת השקיעה לפני שינויי מתלים.",
        "why_watch_he": "הערך המרכזי הוא ההפרדה הברורה בין קפיץ, קדם־עומס ומהלך מתלה, בעזרת פרקים ייעודיים על טווח, תחושה והתאמה.",
        "exercises_he": [],
        "equipment_he": ["ספר רכב", "כלי כיוון ייעודי ליצרן", "סרט מדידה", "אדם נוסף לסיוע במדידה"],
        "safety_warnings_he": ["אין לשנות קדם־עומס או חלקי מתלה מעבר לטווח היצרן; כיוון שגוי עלול לפגוע ביציבות ובמרווח המהלך."],
        "common_mistakes_he": ["התייחסות לקדם־עומס כאילו הוא מקשיח את קצב הקפיץ", "כיוון לפי תחושה בלבד בלי למדוד עומס ושקיעה"],
        "quality_score": 5,
        "quality_reason_he": "שמונה פרקים ותיאור מקור ממוקד מאמתים דיון שיטתי בקפיץ, מהלך שלילי, טווחי כיוון ותחושה, בהשתתפות מומחה מתלים מזוהה.",
        "source_type": "professional_instructor",
        "contains_marketing": True,
        "related_video_ids": ["yt-sJg_rAPp0Rg", "yt-QXl542xFnhU"],
    },
    "sJg_rAPp0Rg": {
        "title_he": "בולמי זעזועים ושיכוך באופנוע אדוונצ'ר",
        "domain": "mixed",
        "primary_category": "suspension_setup",
        "secondary_categories": ["ergonomics"],
        "tags": ["suspension", "damping", "heavy_bike", "planning"],
        "skill_level": "intermediate",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "touring", "sport_touring"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel", "loose_rock"],
        "road_conditions": ["dry_pavement", "rural_twisty"],
        "summary_he": "המשך טכני לסדרת המתלים, המתמקד בבולם ובשיכוך: כיוון החזרה, השפעת חום ולחץ, מבני בולם שונים והצורך להתאים את החומרה לסוג השימוש.",
        "learning_points_he": [
            "להבין מה עושה שיכוך החזרה לאחר דחיסת הקפיץ",
            "לזהות כיצד חימום הבולם עשוי לשנות את התנהגותו",
            "להכיר את תפקיד המאגר והבוכנה המפרידה בבולם",
            "לבחור מתלה לפי עומס ויישום ולא לפי שם מוצר בלבד",
        ],
        "fit_for_he": "מתאים לרוכבים בינוניים שרוצים להבין את רכיבי הבולם לפני פנייה למכוון מקצועי או לפני הערכת התנהגות תחת עומס.",
        "why_watch_he": "הסרטון מחבר בין מושגי שיכוך לבין חום, לחץ ומבנה פנימי, וכך מסביר מדוע בולם שמתאים לטיול קל אינו בהכרח מתאים לעומס או שטח ממושך.",
        "exercises_he": [],
        "equipment_he": ["ספר רכב", "דף רישום לכיווני המתלה", "ציוד מיגון מלא"],
        "safety_warnings_he": ["פתיחת בולם או שינוי פנימי דורשים איש מקצוע; אין לעבוד על רכיב בלחץ או לבצע כיוון שאינו מתועד בספר היצרן."],
        "common_mistakes_he": ["שינוי כמה כיוונים בבת אחת בלי תיעוד", "בחירת בולם ללא התאמה לעומס ולסוג הרכיבה"],
        "quality_score": 5,
        "quality_reason_he": "תשעה פרקים מאמתים כיסוי מפורט של שיכוך החזרה, חום, לחץ, בוכנה מפרידה ומאגר; מומחה מתלים מזוהה משתתף בהסבר.",
        "source_type": "professional_instructor",
        "contains_marketing": True,
        "related_video_ids": ["yt-CCCl2KBpP5g", "yt-QXl542xFnhU"],
    },
    "zsKLdi_nYYQ": {
        "title_he": "מתי להשתמש ב־ABS ובבקרת אחיזה",
        "domain": "mixed",
        "primary_category": "electronic_aids",
        "secondary_categories": ["road_braking", "offroad_braking"],
        "tags": ["abs", "traction_control", "braking", "traction", "safety"],
        "skill_level": "intermediate",
        "risk_level": "high",
        "motorcycle_types": ["adventure", "dual_sport", "street"],
        "motorcycle_weight_classes": ["medium", "heavy", "general"],
        "terrain_types": ["dirt", "gravel", "sand"],
        "road_conditions": ["dry_pavement", "wet_pavement"],
        "summary_he": "דיון מובנה בהבדל בין שימוש ב־ABS ובבקרת אחיזה על אספלט לבין מצבים מחוץ לכביש, ובחשיבות הכרת מצבי הרכיבה והאפשרויות הספציפיות של האופנוע.",
        "learning_points_he": [
            "להפריד בין דרישות בלימה על אספלט לבין משטח רופף",
            "להבין שמצבי אלקטרוניקה שונים מתנהגים אחרת בין דגמים",
            "לבדוק מראש אילו מערכות חוזרות לברירת מחדל לאחר התנעה",
            "לא להשתמש בכיבוי מערכת כתחליף למיומנות בלימה ורגישות בגז",
        ],
        "fit_for_he": "מיועד לרוכבי אדוונצ'ר שכבר שולטים בבלימה בסיסית ורוצים לקבל מסגרת החלטה לפני מעבר בין כביש לשטח.",
        "why_watch_he": "ארבעת הפרקים מפרידים במפורש בין מצבי כביש ושטח ומציגים את מערכות העזר ככלי תלוי הקשר, לא ככלל גורף של תמיד להפעיל או תמיד לכבות.",
        "exercises_he": [],
        "equipment_he": ["ספר רכב", "ציוד מיגון מלא", "מגרש או שטח הדרכה סגור"],
        "safety_warnings_he": ["אין לכבות ABS או בקרת אחיזה בכביש ציבורי בעקבות המלצה כללית; יש לפעול לפי ספר היצרן והדין המקומי."],
        "common_mistakes_he": ["הנחה שכל דגמי ה־ABS פועלים באותה צורה", "שינוי מצב אלקטרוני תוך כדי תרחיש לחץ בלי להכיר את הבקרות"],
        "quality_score": 4,
        "quality_reason_he": "התיאור וארבעה פרקים מאמתים חלוקה מפורשת לכביש ולשטח והצגת שיקולים בעד ונגד; קיימת מעטפת מסחרית נרחבת ולכן ההדרכה נבחנת בנפרד.",
        "source_type": "riding_school",
        "contains_marketing": True,
        "related_video_ids": ["yt-_zQoFML9xPk", "yt-18eqTsDfzDU"],
    },
    "_zQoFML9xPk": {
        "title_he": "בחינת התנהגות ABS בשטח",
        "domain": "offroad_adventure",
        "primary_category": "electronic_aids",
        "secondary_categories": ["offroad_braking"],
        "tags": ["abs", "offroad_braking", "braking", "gravel", "safety"],
        "skill_level": "intermediate",
        "risk_level": "high",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel"],
        "road_conditions": [],
        "summary_he": "בחינה של העצה הגורפת לכבות ABS בשטח, באמצעות השוואת מצבי האלקטרוניקה בשני אופנועי אדוונצ'ר; המיקוד הוא בהתנהגות המערכת ולא בהשוואת הדגמים עצמם.",
        "learning_points_he": [
            "להטיל ספק בכלל הגורף של כיבוי ABS בכל יציאה לשטח",
            "להבחין בין ABS כביש למצב ABS ייעודי לשטח",
            "לבדוק את הגדרות האופנוע לפני ירידה ממשטח סלול",
            "להעריך את תגובת המערכת על משטח צפוי ורק במסגרת הדרכה",
        ],
        "fit_for_he": "מתאים לרוכבים בינוניים על אופנועי אדוונצ'ר מודרניים, לאחר שליטה בבלימה בשטח והיכרות עם ספר הרכב.",
        "why_watch_he": "במקום לחזור על עצת רוכבים נפוצה, הסרטון מגדיר ניסוי השוואתי בין מערכות קיימות ומדגיש שהאלקטרוניקה תלויה בדגם ובמצב הנבחר.",
        "exercises_he": [],
        "equipment_he": ["ספר רכב", "ציוד מיגון מלא", "מתחם הדרכה סגור עם מדריך"],
        "safety_warnings_he": ["בדיקת מרחקי עצירה על עפר היא תרגול בסיכון גבוה; אין לבצע אותה בכביש ציבורי או ללא מרחב ומדריך מתאימים."],
        "common_mistakes_he": ["כיבוי אוטומטי של ABS בלי לבדוק אם קיים מצב שטח", "הסקת מסקנה מאופנוע אחד לכל הדגמים"],
        "quality_score": 4,
        "quality_reason_he": "תיאור המקור מגדיר במדויק את שאלת הבדיקה, שני אופנועי הניסוי ומגבלת ההשוואה; אין פרקי YouTube ולכן הסיווג נשמר ברמת ביטחון בינונית.",
        "source_type": "professional_instructor",
        "contains_marketing": True,
        "related_video_ids": ["yt-zsKLdi_nYYQ", "yt-hN0vylh__lo"],
    },
    "oW7eVgdCC58": {
        "title_he": "לחץ אוויר בצמיגי אופנוע: עקרונות ויישומים",
        "domain": "mixed",
        "primary_category": "tires_setup",
        "secondary_categories": ["gravel_dirt"],
        "tags": ["tire_pressure", "traction", "planning", "long_distance"],
        "skill_level": "intermediate",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "dual_sport", "street", "general_motorcycle"],
        "motorcycle_weight_classes": ["light", "medium", "heavy", "general"],
        "terrain_types": ["dirt", "gravel"],
        "road_conditions": ["dry_pavement", "highway"],
        "summary_he": "שיעור רחב על לחץ אוויר, משינויי טמפרטורה ונשיאת עומס ועד כתם המגע, שחיקה, אחיזה בכביש והפחתת לחץ מבוקרת לרכיבת דו־שימושי ושטח.",
        "learning_points_he": [
            "להבין כיצד טמפרטורה משנה את מדידת הלחץ",
            "לקשר בין לחץ, נשיאת עומס וכתם המגע של הצמיג",
            "להפריד בין דרישות כביש לבין סיבה להפחתת לחץ בשטח",
            "להשתמש בהמלצות יצרן כנקודת מוצא לפני התאמה זהירה",
        ],
        "fit_for_he": "מתאים לרוכבים שרוצים בסיס טכני רחב לפני קביעת שגרת בדיקה לאופנוע כביש, דו־שימושי או אדוונצ'ר.",
        "why_watch_he": "שמונה הפרקים בונים רצף מן הפיזיקה הבסיסית ועד טווחי שימוש בכביש ובשטח, ולכן מאפשרים להבין את הפשרה ולא רק לזכור מספר לחץ.",
        "exercises_he": ["מדוד ורשום לחץ כשהצמיג קר, ואז השווה לערך היצרן; אין לשנות את הערך בלי להבין את העומס והתנאים."],
        "equipment_he": ["מד לחץ תקין", "משאבה", "ספר רכב", "ציוד מיגון מלא"],
        "safety_warnings_he": ["ערכי לחץ שאינם מתאימים לעומס, לצמיג ולמהירות עלולים לפגוע ביציבות, באטימה וביכולת נשיאת העומס."],
        "common_mistakes_he": ["השוואת מדידה חמה לערך קר", "העתקת לחץ מאופנוע בעל משקל וצמיג שונים", "התעלמות ממטען ומהירות כביש"],
        "quality_score": 4,
        "quality_reason_he": "תיאור מפורט ושמונה פרקים מאמתים כיסוי של טמפרטורה, עומס, אחיזה והבדלי כביש־שטח; ריבוי קישורי שותפים מסחריים מחייב להפרידם מן ההסבר.",
        "source_type": "experienced_rider",
        "contains_marketing": True,
        "related_video_ids": ["yt-QXl542xFnhU", "yt-CCCl2KBpP5g"],
    },
    "YlseO0ceUcw": {
        "title_he": "מיון ואריזת ציוד למסע אופנוע",
        "domain": "safety_recovery",
        "primary_category": "trip_preparation",
        "secondary_categories": [],
        "tags": ["luggage", "planning", "long_distance", "safety"],
        "skill_level": "beginner",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "touring", "sport_touring"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": [],
        "road_conditions": ["dry_pavement", "highway"],
        "summary_he": "הצגה מעשית של תכולת מטען למסעות ארוכים ושל תהליך הפריסה והמיון לפני יציאה, על בסיס משקל כולל מדווח של תיקי האוכף ותיק המכל.",
        "learning_points_he": [
            "לפרוס את כל הציוד לפני האריזה כדי לזהות כפילויות",
            "למדוד את משקל המטען בפועל במקום להסתמך על תחושה",
            "להפריד בין ציוד נגיש במהלך היום לבין ציוד למחנה",
            "לבחון כל פריט לפי צורך חוזר במסע ולא לפי רשימת קניות",
        ],
        "fit_for_he": "מתאים לרוכבי טיולים שמגבשים רשימת ציוד אישית ורוצים לראות דוגמה מתועדת של מטען מצומצם יחסית למסע ארוך.",
        "why_watch_he": "הסרטון מציג את הציוד בפועל ואת משקלו ולא מסתפק ברשימה כללית, אך יש להתאים את הבחירות לאקלים, למסלול ולמגבלות היצרן.",
        "exercises_he": ["פרוס את ציוד המסע, שקול כל תיק ורשום ליד כל פריט מתי השתמשת בו במסע האחרון; אין להעמיס על האופנוע בשלב התרגיל."],
        "equipment_he": ["משקל ביתי או משקל מזוודות", "רשימת ציוד", "תיקים מאושרים לאופנוע", "רצועות תקינות"],
        "safety_warnings_he": ["הסרטון מציג תכולה אישית ואינו מאמת מגבלות עומס; יש לבדוק משקל מותר, חלוקה ועיגון לפי יצרן האופנוע והתיקים."],
        "common_mistakes_he": ["העתקת רשימת ציוד בלי להתאים למסלול", "אי־שקילת התיקים", "הוספת פריטים בלי לבדוק מגבלת עומס"],
        "quality_score": 3,
        "quality_reason_he": "התיאור מאמת תהליך פריסה, תכולה ומשקלים מדווחים מניסיון מסעות רב; אין פרקים, והסרטון כולל קידום קורסים וקישורי תמיכה רבים.",
        "source_type": "experienced_rider",
        "contains_marketing": True,
        "related_video_ids": ["yt-dPmq8jpUL5s", "yt-2XP_qr9NNcc"],
    },
    "dPmq8jpUL5s": {
        "title_he": "ציוד חירום של מדריך ומוביל רכיבות אדוונצ'ר",
        "domain": "safety_recovery",
        "primary_category": "trip_preparation",
        "secondary_categories": ["recovery"],
        "tags": ["emergency_kit", "first_aid", "hydration", "planning", "recovery"],
        "skill_level": "advanced_beginner",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel"],
        "road_conditions": ["rural_twisty"],
        "summary_he": "סיור בציוד שהמדריך נושא בהובלת קבוצות: מים ומזון, מענה רפואי, כלי עבודה, סדים ומשאבה, תוך הדגשת ההבדל בין ערכת מדריך לצרכים של רוכב יחיד.",
        "learning_points_he": [
            "לחלק את ערכת החירום בין צורכי גוף לתקלות מכניות",
            "לכלול מים ומזון כחלק מן המוכנות ולא כתוספת נוחות",
            "להבין מדוע מדריך קבוצה נושא ציוד רפואי וכלים נוספים",
            "להתאים נפח ומשקל לתרחישים וליכולת השימוש האמיתית",
        ],
        "fit_for_he": "מתאים לרוכבי אדוונצ'ר ולמובילי קבוצה שבונים רשימת מוכנות בסיסית, תוך התאמה להכשרה, למסלול ולמספר המשתתפים.",
        "why_watch_he": "חמשת הפרקים חושפים ערכה אמיתית של מדריך ומפרידים בין כלי עבודה, סדים ומשאבה, כך שאפשר לבחון צרכים ולא לקנות רשימה עיוורת.",
        "exercises_he": ["ערוך ביקורת שולחן לערכה הקיימת וסמן לכל פריט תרחיש שימוש, תאריך תפוגה ומי בקבוצה יודע להשתמש בו."],
        "equipment_he": ["מים ומזון חירום", "ערכת עזרה ראשונה בהתאם להכשרה", "ערכת כלים מותאמת לאופנוע", "משאבה", "אמצעי תקשורת"],
        "safety_warnings_he": ["ציוד רפואי אינו מחליף הכשרה; אין להשתמש בסד, תרופה או כלי שאינך מוסמך ומיומן להפעיל."],
        "common_mistakes_he": ["נשיאת ציוד ללא ידע שימוש", "התעלמות מתוקף ציוד רפואי", "ערכת כלים שאינה מתאימה לברגים ולאביזרים באופנוע"],
        "quality_score": 4,
        "quality_reason_he": "התיאור וחמישה פרקים מאמתים כיסוי של מים, מזון, תקלות, סדים ומשאבה מתוך עבודת מדריך; קישורי מוצרים מסומנים כשיווק.",
        "source_type": "professional_instructor",
        "contains_marketing": True,
        "related_video_ids": ["yt-YlseO0ceUcw", "yt-dRvofOL3eaI"],
    },
    "KC0Rv0aM7OI": {
        "title_he": "שלוש טעויות יסוד ברכיבת אדוונצ'ר בשטח",
        "domain": "offroad_adventure",
        "primary_category": "offroad_basics",
        "secondary_categories": ["riding_position", "controls_coordination"],
        "tags": ["common_mistakes", "standing", "throttle", "balance", "beginner"],
        "skill_level": "beginner",
        "risk_level": "medium",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["medium", "heavy"],
        "terrain_types": ["dirt", "gravel", "sand"],
        "road_conditions": [],
        "summary_he": "שיעור תיקון טעויות לרוכבי אדוונצ'ר חדשים: תנוחת עמידה, גז לא עקבי והורדת רגליים מן הרגליות, עם הדגמות על שביל חולי ובכניסה לשטח משתנה.",
        "learning_points_he": [
            "לבנות תנוחת עמידה שמאפשרת לאופנוע לנוע מתחת לרוכב",
            "לשמור פקודת גז צפויה במקום פתיחה וסגירה חדות",
            "להשאיר את הרגליים על הרגליות כל עוד אפשר לשלוט באופנוע",
            "להיכנס לשינוי תוואי עם מבט ותכנית ולא בתגובה מאוחרת",
        ],
        "fit_for_he": "מתאים למתחילים שיוצאים לדרך עפר על אופנוע אדוונצ'ר ורוצים לזהות הרגלים שמערערים יציבות עוד לפני תוואי מורכב.",
        "why_watch_he": "הסרטון קושר כל טעות לתיקון נראה לעין, ושבעת הפרקים כוללים הדגמות בשביל חולי ולא רק הסבר תיאורטי.",
        "exercises_he": [],
        "equipment_he": ["קסדה תקנית", "מגפי רכיבה", "מיגון גוף", "שטח אימון רחב וצפוי"],
        "safety_warnings_he": ["אין לתרגל בחול עמוק לפני שליטה בעמידה ובגז על עפר שטוח; יש להתקדם עם מדריך ובמהירות נמוכה."],
        "common_mistakes_he": ["עמידה נוקשה", "סגירת גז פתאומית", "הורדת שתי רגליים מן הרגליות בתנועה"],
        "quality_score": 5,
        "quality_reason_he": "תיאור המקור מונה במפורש שלוש טעויות ושבעת הפרקים מאמתים עמידה, שביל חולי וכניסה לתוואי; המקור הוא בית ספר לרכיבת שטח.",
        "source_type": "riding_school",
        "contains_marketing": True,
        "related_video_ids": ["yt-UsOGqaTH3d0", "yt-fqm0Oj9G8QU", "yt-uscjPZXNyMc"],
    },
    "uscjPZXNyMc": {
        "title_he": "שלוש מיומנויות שטח שכדאי לתרגל",
        "domain": "practice",
        "primary_category": "drills",
        "secondary_categories": ["offroad_turning", "obstacles", "hills"],
        "tags": ["practice_drill", "cornering", "obstacle", "hill_climb", "body_position"],
        "skill_level": "intermediate",
        "risk_level": "high",
        "motorcycle_types": ["adventure", "dual_sport"],
        "motorcycle_weight_classes": ["light", "medium", "heavy"],
        "terrain_types": ["dirt", "hill", "obstacle"],
        "road_conditions": [],
        "summary_he": "שלושה נושאי תרגול מודגמים על אופנוע אדוונצ'ר: פנייה אינסטינקטיבית, ספיגת מכשולים באמצעות הגוף ומיקום גוף בעלייה, כחלק מבניית שליטה בטוחה בשטח.",
        "learning_points_he": [
            "לתרגל פנייה בשטח עד שהמבט ותנועת הגוף מתחברים",
            "לאפשר לרגליים ולמתלים לספוג שינויי גובה ומכשול",
            "להתאים את מיקום הגוף לשיפוע העלייה ולשמירת אחיזה",
            "לבודד כל מיומנות לפני שמחברים אותה למסלול מלא",
        ],
        "fit_for_he": "מיועד לרוכבים בינוניים שכבר שולטים בעמידה, מצמד וגז ורוצים לבנות אימון מדורג לפנייה, מכשול ועלייה.",
        "why_watch_he": "חמשת הפרקים מחלקים את ההדגמה לאיזון, סחף קרקע ועלייה, ומציגים שלושה תרגולים נפרדים במקום רצף רכיבה בלתי מוסבר.",
        "exercises_he": ["בחר מיומנות אחת בלבד ובנה לה אזור תרגול פשוט עם מדריך; אל תחבר מכשול ועלייה באותו סבב ראשון."],
        "equipment_he": ["קסדה תקנית", "מגפי שטח", "מיגון גוף", "אופנוע עם מגני מנוע מתאימים"],
        "safety_warnings_he": ["תרגול מכשולים ועליות הוא בסיכון גבוה; יש לבצעו בתוואי סגור, עם מדריך ועם נתיב מילוט ברור."],
        "common_mistakes_he": ["ניסיון של שלוש המיומנויות יחד לפני שליטה בכל אחת", "מבט על המכשול", "תנוחת גוף קבועה שאינה משתנה עם השיפוע"],
        "quality_score": 5,
        "quality_reason_he": "התיאור וחמישה פרקים מאמתים במפורש פנייה, ספיגת מכשול ומיקום גוף בעלייה; ההדגמות מחולקות לנושאי תרגול ברורים.",
        "source_type": "professional_instructor",
        "contains_marketing": True,
        "related_video_ids": ["yt-KC0Rv0aM7OI", "yt-UHkVHDFNUqU", "yt-Z4G8NxyI4I8"],
    },
}


def subtitle_languages(metadata: dict[str, Any]) -> list[str]:
    manual = set(metadata.get("subtitle_languages") or [])
    result: list[str] = []
    if "iw" in manual or "he" in manual:
        result.append("he")
    if "en" in manual:
        result.append("en")
    return result


def build_record(metadata: dict[str, Any], curated: dict[str, Any]) -> dict[str, Any]:
    video_id = metadata["youtube_video_id"]
    chapters = metadata.get("chapters") or []
    evidence = ["description"]
    if chapters:
        evidence.append("chapters")
    automatic = set(metadata.get("automatic_caption_languages") or [])
    caption_note = " נמצאו כתוביות אוטומטיות באנגלית." if "en" in automatic else ""
    chapter_note = (
        f" נשמרו {len(chapters)} פרקי YouTube שנשלפו מן המקור."
        if chapters
        else " לא נמצאו פרקי YouTube לשמירה."
    )
    record = {
        "id": f"yt-{video_id}",
        "youtube_video_id": video_id,
        "youtube_url": metadata["youtube_url"],
        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "title_original": metadata["title_original"],
        "title_he": curated["title_he"],
        "channel_name": metadata["channel_name"],
        "channel_url": metadata["channel_url"],
        "published_date": metadata["published_date"],
        "duration_seconds": metadata["duration_seconds"],
        "language": "en",
        "subtitle_languages": subtitle_languages(metadata),
        "domain": curated["domain"],
        "primary_category": curated["primary_category"],
        "secondary_categories": curated["secondary_categories"],
        "tags": curated["tags"],
        "skill_level": curated["skill_level"],
        "risk_level": curated["risk_level"],
        "motorcycle_types": curated["motorcycle_types"],
        "motorcycle_weight_classes": curated["motorcycle_weight_classes"],
        "terrain_types": curated["terrain_types"],
        "road_conditions": curated["road_conditions"],
        "summary_he": curated["summary_he"],
        "learning_points_he": curated["learning_points_he"],
        "fit_for_he": curated["fit_for_he"],
        "why_watch_he": curated["why_watch_he"],
        "exercises_he": curated["exercises_he"],
        "equipment_he": curated["equipment_he"],
        "safety_warnings_he": curated["safety_warnings_he"],
        "common_mistakes_he": curated["common_mistakes_he"],
        "chapters": chapters,
        "quality_score": curated["quality_score"],
        "quality_reason_he": curated["quality_reason_he"],
        "source_type": curated["source_type"],
        "contains_marketing": curated["contains_marketing"],
        "related_video_ids": curated["related_video_ids"],
        "verification": {
            "link_status": "active_public",
            "metadata_verified": True,
            "content_evidence_types": evidence,
            "classification_confidence": "high" if chapters else "medium",
            "notes_he": (
                "ב־2026-08-03 נפתח מקור YouTube ונבדקו זמינות ציבורית, כותרת, "
                "ערוץ, תאריך, משך ותיאור." + chapter_note + caption_note
            ),
        },
        "last_checked": "2026-08-03",
    }
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.metadata.read_text(encoding="utf-8"))
    by_id = {
        item["youtube_video_id"]: item
        for item in report.get("results", [])
        if item.get("status") == "pass"
    }
    missing = sorted(set(SELECTED_IDS) - set(by_id))
    if missing:
        raise SystemExit(f"Missing verified metadata: {missing}")
    records = []
    for video_id in SELECTED_IDS:
        metadata = by_id[video_id]
        if metadata.get("availability") != "public":
            raise SystemExit(f"Candidate is not public: {video_id}")
        if not metadata.get("description_present"):
            raise SystemExit(f"Candidate has no description evidence: {video_id}")
        records.append(build_record(metadata, CURATION[video_id]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} curated records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
