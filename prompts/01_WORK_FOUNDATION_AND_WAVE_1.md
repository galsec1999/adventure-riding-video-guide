# משימה 01 — Work: תשתית תוכן ואצווה ראשונה

## התפקיד שלך

אתה עורך תוכן ראשי, חוקר אינטרנט ומנהל מידע עבור פרויקט ספריית לימוד לרכיבת אופנועי אדוונצ'ר. עבוד ישירות בתוך התיקייה המקומית הפתוחה. קרא תחילה את:

- `MASTER_SPEC.md`
- `AGENTS.md`
- `DECISIONS.md`
- `QUALITY_GATES.md`
- `PROJECT_STATUS.md`

## תוצאה נדרשת בסבב הזה

בנה את ארכיטקטורת התוכן המלאה והכן **60 סרטוני YouTube אמיתיים, פעילים, ייחודיים ומאומתים**, בעברית ובאנגלית. זהו סבב מחקר ותוכן; אין לבנות עדיין את ממשק האתר.

חלוקה רצויה לאצווה:

- 30 סרטוני אדוונצ'ר/שטח.
- 20 סרטוני כביש.
- 10 סרטוני משולב, תרגול, בטיחות או חילוץ.
- שאף ל־8–15 סרטונים איכותיים בעברית. אין להוסיף סרטון חלש כדי לעמוד במכסה.
- כלול מתחילים, בינוניים ומתקדמים, אך תן משקל גבוה לתוכן בסיסי ובטוח.
- כלול אופנועי אדוונצ'ר בינוניים וכבדים, ולא רק אנדורו קל.

## שיטת מחקר מחייבת

לכל סרטון:

1. פתח את דף הסרטון או מקור אמין שמוביל אליו.
2. אמת שהסרטון פעיל וציבורי.
3. אמת לפחות את הכותרת, הערוץ, URL ו־Video ID.
4. בדוק תיאור, Chapters, כתוביות/תמלול כאשר זמינים, ובמידת האפשר קטעים רלוונטיים מהווידאו.
5. אל תסווג לפי הכותרת בלבד.
6. אל תמציא משך, תאריך, כתוביות, נקודות זמן או תוכן. ערך שלא אומת יהיה `null` או מערך ריק בהתאם לסכמה.
7. כתוב תקציר עברי מקורי; אין להעתיק תיאור או תמלול.
8. תעד מה שימש כראיית תוכן: description, chapters, transcript, visual review או שילוב.
9. דחה פרסומות ללא ערך הדרכתי, stunts, העלאות חוזרות, תוכן מסוכן ללא הקשר, וסרטונים שאינם רלוונטיים בפועל.
10. אל תשתמש במספר צפיות או נתון פופולריות כקריטריון איכות מרכזי.

## קבצים שיש ליצור או להשלים

### 1. `data/categories.json`

Taxonomy מלאה, סופית ועקבית ככל האפשר:

- domains
- categories
- subcategories
- terrain_types
- road_conditions
- skill_levels
- risk_levels
- motorcycle_types
- motorcycle_weight_classes
- source_types
- languages
- controlled_tags

לכל ערך יהיו `id`, שם עברי, שם אנגלי ותיאור עברי קצר. אין ליצור מאות תגיות חופשיות; בנה מילון מבוקר.

### 2. `data/synonyms.json`

מילון חיפוש עברית–אנגלית הכולל:

- מילים מקבילות.
- כתיבים חלופיים.
- תעתיקים נפוצים.
- יחיד/רבים.
- מונחים מקצועיים כגון Countersteering, Trail Braking, Rut, Hill Climb, Weight Transfer, Target Fixation ועוד.

### 3. `schema/video.schema.json`

JSON Schema מלא לרשומת סרטון. כלול לפחות:

- `id`
- `youtube_video_id`
- `youtube_url`
- `title_original`
- `title_he`
- `channel_name`
- `channel_url`
- `published_date`
- `duration_seconds`
- `language`
- `subtitle_languages`
- `domain`
- `primary_category`
- `secondary_categories`
- `tags`
- `skill_level`
- `risk_level`
- `motorcycle_types`
- `motorcycle_weight_classes`
- `terrain_types`
- `road_conditions`
- `summary_he`
- `learning_points_he`
- `fit_for_he`
- `why_watch_he`
- `exercises_he`
- `equipment_he`
- `safety_warnings_he`
- `common_mistakes_he`
- `chapters`
- `quality_score`
- `quality_reason_he`
- `source_type`
- `contains_marketing`
- `related_video_ids`
- `verification`
- `last_checked`

ב־`verification` כלול לפחות:

- `link_status`
- `metadata_verified`
- `content_evidence_types`
- `classification_confidence`
- `notes_he`

### 4. `data/videos.json`

מערך של 60 רשומות שעוברות את כל שערי האיכות. דרישות לכל רשומה:

- תקציר עברי ברור ומדויק.
- 3–6 נקודות "מה לומדים".
- התאמת קהל ורמה.
- סיבה לצפייה.
- אזהרות בטיחות רלוונטיות.
- דירוג איכות 1–5 והסבר.
- תגיות רק מתוך המילון המבוקר.
- תאריך בדיקה בפורמט ISO.
- URL מלא ו־Video ID ייחודי.

### 5. `data/learning-paths.json`

צור לפחות שני מסלולים ראשוניים על בסיס 60 הסרטונים המאושרים בלבד:

- מתחילים בשטח ואדוונצ'ר.
- מתחילים בכביש.

לכל שלב במסלול יהיו מטרה, הסבר, סרטונים ראשיים וסרטונים חלופיים. אין להפנות ל־ID שאינו קיים.

### 6. `research/rejected/wave-1-rejected.csv`

כלול סרטונים משמעותיים שנבדקו ונדחו, עם:

- URL
- כותרת אם ידועה
- ערוץ אם ידוע
- סיבת הדחייה
- תאריך בדיקה

### 7. `research/reports/wave-1-report.md`

דוח מפורט הכולל:

- מתודולוגיית המחקר.
- מקורות וערוצים שנבדקו.
- מספר הסרטונים שנבדקו, אושרו ונדחו.
- חלוקה לפי שפה, תחום, קטגוריה ורמה.
- פערים בולטים.
- סיכונים ומגבלות אימות.
- קישורים למקורות המרכזיים.

### 8. `reports/content-audit.json` ו־`reports/content-audit.csv`

נתוני ביקורת הניתנים לעיבוד: ספירות, חלוקות, כפילויות, שדות חסרים, קטגוריות דלות ורמת ביטחון.

### 9. `HANDOFF_TO_CODEX.md`

הסבר קצר ומדויק לקודקס:

- אילו קבצים הם מקור אמת.
- מבנה הנתונים.
- החלטות UI שמשתמעות מה־Taxonomy.
- מה אסור לקודקס לשנות בתוכן.
- בעיות ידועות.

## בדיקות חובה לפני סיום

- בדיוק 60 רשומות מאושרות ב־`data/videos.json`.
- 60 מזהי YouTube ייחודיים.
- אפס URL ריקים או מומצאים.
- כל הרשומות עוברות את `schema/video.schema.json`.
- כל category/tag מפנה לערך קיים.
- כל related ID ו־learning-path ID מפנה לרשומה קיימת.
- אין נקודות זמן שלא אומתו.
- כל תקציר הוא בעברית מקורית.
- כל סרטון כולל רמת אימות וסיווג.

אם אין בסביבה כלי להרצת JSON Schema, בצע בדיקה שיטתית בעצמך ותעד זאת; אל תטען שהורצה בדיקה שלא הורצה.

## עדכון סטטוס וסיום

בסיום:

1. עדכן `PROJECT_STATUS.md` ל־1 מתוך 8 סבבים ולמספרי התוכן האמיתיים.
2. הוסף החלטות חדשות ל־`DECISIONS.md`.
3. צור `REVIEW_PACKET.md` לפי `AGENTS.md`.
4. החלף את `NEXT_ACTION.md` כך שיצביע על:
   - מצב: Codex
   - קובץ: `prompts/02_CODEX_BUILD_SITE_V1.md`
5. בהודעת הסיום בצ'אט הצג רק תקציר קצר והפנה ל־`REVIEW_PACKET.md`.
6. עצור. אל תתחיל לבנות את האתר בסבב הזה.
