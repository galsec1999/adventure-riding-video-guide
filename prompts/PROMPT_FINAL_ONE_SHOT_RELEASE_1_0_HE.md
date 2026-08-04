# פרומפט־על חד־פעמי — השלמת כל הפרויקט עד Release 1.0

## זהות המשימה וסמכות

אתה המבצע היחיד של הפרויקט הזה מתחילתו של הסבב הנוכחי ועד לתוצר הסופי.
אין להעביר עבודה ל־Codex, ל־Work אחר, לסוכן אחר או למשתמש. אין לעצור למסירת ביניים, אין לבקש אישור בין שלבים, ואין ליצור פינג־פונג.

עבוד ישירות מתוך תיקיית הפרויקט הקיימת:

```text
D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-Starter
```

הפרומפט הזה **מחליף וגובר** על כל `NEXT_ACTION.md`, על כל עצירת־שלב קודמת, ועל משימות 03B–08. קרא את החומרים ההיסטוריים כדי להבין את הפרויקט, אך אל תעצור בשערי אישור ישנים ואל תעביר את העבודה לפלטפורמה אחרת.

המשימה היא לסגור את כל הפרויקט בריצה אוטונומית אחת:

1. לבדוק ולתקן את 130 הסרטונים הקיימים.
2. להשלים מחקר ואוצרות תוכן עד **בדיוק 250 סרטונים פעילים, ייחודיים ואיכותיים**.
3. להשלים את האתר לגרסה סופית ומוכנה לפרסום.
4. לבצע בדיקות תוכן, קוד, UX, ביצועים, נגישות וקישורים.
5. לבצע ביקורת עצמית עצמאית וקשוחה.
6. לתקן בעצמך את כל הממצאים.
7. לחזור על הבדיקות עד שכל שערי השחרור עוברים.
8. ליצור חבילת Release אחת סופית.
9. לעצור רק לאחר יצירת התוצר הסופי.

אין להסתפק ב־200 סרטונים. יעד השחרור של המשימה הזאת הוא **250**.

---

# 1. כללי עבודה ללא מעורבות המשתמש

## 1.1 אין שאלות ואין אישורי ביניים

אל תשאל את המשתמש:

- איזה עיצוב הוא מעדיף.
- האם להמשיך לשלב הבא.
- האם לאשר סרטון מסוים.
- האם לתקן ממצא.
- האם לבחור חלופה.
- האם לפתוח ענף.
- האם להריץ בדיקות.
- האם להחליף מקור כושל.

בחר ברירות מחדל מקצועיות, תעד אותן ב־`DECISIONS.md`, והמשך.

מותר לעצור ב־`FAIL` רק כאשר קיימת חסימה חיצונית אמיתית שאי אפשר לעקוף לאחר ניסיונות חוזרים, כגון היעדר מוחלט של גישה לאינטרנט או חוסר הרשאה לכתוב בתיקייה. גם אז יש להשלים כל דבר אחר שניתן וליצור חבילת כשל מפורטת. אין לעצור בגלל חוסר נוחות, אורך המשימה, מספר הקבצים או צורך בביקורת ביניים.

## 1.2 עבודה רציפה עם State מתועד

צור בתחילת העבודה:

```text
AUTORUN_STATE.json
```

השדות יכללו לפחות:

- `project_root`
- `started_at`
- `current_stage`
- `current_batch`
- `records_before`
- `records_current`
- `approved_new`
- `rejected_candidates`
- `last_successful_gate`
- `pending_actions`
- `last_updated`
- `status`

עדכן את הקובץ אחרי כל אצווה של 20–25 מועמדים ואחרי כל שער בדיקות. אם הסביבה כופה הפסקה טכנית, המשך מאותו State באותה משימה בלי לבקש מן המשתמש פרומפט חדש ובלי להתחיל מחדש.

## 1.3 אל תסמוך על דוחות עצמיים קודמים

הדוחות הקיימים הם ראיות היסטוריות, לא אמת אוטומטית. הרץ מחדש בדיקות, קרא את הנתונים והקוד, ובדוק את המקורות החיים.

## 1.4 אין כתיבת תוכן באמצעות תבניות

אסור לכתוב שדות תוכן באמצעות:

- סבב של תבניות קבועות.
- החלפת כותרת או שלוש נקודות בתוך משפט מסגרת.
- מחולל נוסח אוטומטי.
- מיפוי מכני של רמה, תוואי וציון לטקסט.
- העתקה של אותו ניסוח לעשרות רשומות.
- ניסוחים “ייחודיים” שנבדלים רק בשם הנושא.

סקריפטים מותרים לאיסוף Metadata, אימות, Diff, איתור כפילויות, חישובים ודוחות. כתיבת הסיכום וההסברים לכל סרטון חייבת להתבסס על בדיקת המקור הספציפי.

---

# 2. מצב פתיחה ויעד סופי

## 2.1 מצב פתיחה ידוע

הפרויקט כולל כיום בקירוב:

- אתר סטטי ב־HTML/CSS/JavaScript.
- 130 רשומות ב־`data/videos.json`.
- 9 סרטונים בעברית.
- 119 באנגלית.
- 2 ביפנית.
- 2 מסלולי למידה.
- בדיקות Node ו־Python.
- כלי Schema, Link Check ו־Audit.
- דוחות מחקר היסטוריים.
- מספר בעיות תוכן וטכניקה שתועדו בביקורת.

אין להניח שהמספרים או איכות הרשומות נכונים עד שתבדוק אותם מחדש.

## 2.2 יעד Release 1.0

בסיום חייבים להיות:

- **בדיוק 250 סרטונים ב־Production.**
- כל הסרטונים בעברית או באנגלית בלבד.
- לפחות **25 סרטונים בעברית**, עם יעד רצוי של 30–50.
- כל יתר הסרטונים באנגלית.
- 0 סרטונים בשפה אחרת ב־Production.
- 0 כפילויות.
- 0 קישורים מתים.
- 0 סרטונים פרטיים או חסומים.
- 0 סרטונים שאינם ניתנים להטמעה כאשר האתר מציג נגן.
- 0 Placeholder.
- 0 שדות תוכן שנוצרו מתבנית.
- 0 Chapters מומצאים.
- אתר Release 1.0 מלא, מהיר, נגיש ומוכן לפרסום.
- חבילת Release אחת, חתומה ב־SHA-256 ומאומתת.

אם לאחר חיפוש עברי רחב, מתועד ואמיתי לא נמצאו 25 סרטונים עבריים באיכות מספקת, אל תכניס תוכן חלש. במקרה כזה מותר לסיים עם פחות מ־25, אך רק אם נבדקו לפחות 100 מועמדים עבריים ייחודיים, כל ההחלטות תועדו, והחריגה מוסברת בדוח הסופי. יעד 250 הכולל נשאר חובה.

---

# 3. קריאת מקורות האמת

לפני שינוי קוד או תוכן, קרא במלואם:

- `MASTER_SPEC.md`
- `AGENTS.md`
- `QUALITY_GATES.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `README.md`
- `schema/video.schema.json`
- `data/videos.json`
- `data/categories.json`
- `data/synonyms.json`
- `data/learning-paths.json`
- `data/site-config.json`
- כל הקבצים תחת `prompts/`
- כל הקבצים תחת `research/reports/`
- כל הקבצים תחת `research/approved/`
- כל הקבצים תחת `research/rejected/`
- כל הדוחות תחת `reports/`
- כל הקוד תחת `assets/`
- כל הבדיקות תחת `tests/`
- כל הכלים תחת `tools/`
- `package.json`
- `index.html`
- `run-local.bat`
- `run-local.sh`

צור לאחר הקריאה:

```text
reports/final-one-shot/source-inventory.md
```

הקובץ יפרט אילו מקורות נקראו, אילו חסרים ואילו סתירות נמצאו.

---

# 4. Git, גיבוי ו־Baseline

## 4.1 ענף

צור או עבור לענף:

```text
final-one-shot-release-v1
```

אל תמחק היסטוריה. אל תבצע Force Push. אל תבצע Push ללא Remote מאומת.

## 4.2 Snapshot

לפני שינוי:

- חשב SHA-256 לכל קובצי המקור המרכזיים.
- שמור את רשימת 130 ה־IDs הקיימים.
- שמור את סטטיסטיקות השפות, הערוצים, התחומים והקטגוריות.
- שמור עותק JSON של הנתונים הקיימים תחת:

```text
reports/final-one-shot/baseline/videos-before.json
```

אין להשתמש בעותק הזה כ־Production.

## 4.3 בדיקות Baseline

הרץ בפועל:

```powershell
python tools/validate_data.py --expected-count 130 --report reports/final-one-shot/baseline/data-validation.json
python tools/check_links.py --online --report reports/final-one-shot/baseline/link-check.json
python tools/build_audit.py --link-report reports/final-one-shot/baseline/link-check.json
npm test
python -m unittest discover -s tests -p "test_*.py" -v
node --check assets/js/app.js
```

שמור פלט מלא. אם בדיקה נכשלת, תעד ותקן בהמשך. אל תדווח שעברה אם לא הורצה.

---

# 5. ביקורת אמינות מלאה ל־130 הרשומות הקיימות

לפני הוספת סרטון חדש, בצע ביקורת אמיתית לכל 130 הרשומות.

## 5.1 Ledger ראיות

צור:

```text
research/final-one-shot/evidence-ledger.csv
```

שורה אחת לכל סרטון, עם לפחות:

- `id`
- `youtube_video_id`
- `youtube_url`
- `original_or_new`
- `language`
- `channel_name`
- `source_type`
- `metadata_checked`
- `description_checked`
- `youtube_chapters_checked`
- `captions_checked`
- `transcript_checked`
- `visual_review_performed`
- `visual_timestamp_ranges`
- `embed_checked`
- `evidence_types`
- `classification_confidence_before`
- `classification_confidence_after`
- `fields_reviewed`
- `fields_changed`
- `chapter_result`
- `decision`
- `decision_reason_he`
- `review_notes_he`
- `reviewed_at`

אין לשמור תמלול מלא. אם השתמשת בתמלול או כתוביות באופן זמני, מחק אותם לאחר חילוץ העובדות הדרושות.

## 5.2 רמת ראיות

לכל רשומה ב־Production נדרשת לפחות רמת ראיות בינונית:

### רמה גבוהה

אחת מהאפשרויות:

- Metadata + תיאור + Chapters אמיתיים + תמלול או כתוביות.
- Metadata + תיאור + צפייה ממוקדת בחלקים רלוונטיים.
- מקור בטיחות רשמי עם תיאור מפורט וצפייה ממוקדת.

### רמה בינונית

- Metadata + תיאור מפורט + Chapters תואמים.
- Metadata + תיאור רשמי מפורט כאשר אין Chapters, ובתנאי שהטקסט באתר מצומצם למה שנתמך.

### לא מספיק ל־Production

- כותרת בלבד.
- Thumbnail בלבד.
- תיאור שיווקי קצר ללא הסבר.
- רשומה עם סתירה בין הכותרת, התיאור והסיווג.
- טכניקת סיכון גבוהה המבוססת על תיאור קצר בלבד.
- Confidence נמוך.

בנושאי סיכון גבוה, כגון בלימת חירום, חציית מים, מעבר מכשול, חילוץ, רוח צד, ABS בשטח, עליות וירידות תלולות, נדרשת רמה גבוהה.

## 5.3 תיקון שדות תוכן

בדוק לכל רשומה:

- `summary_he`
- `learning_points_he`
- `fit_for_he`
- `why_watch_he`
- `exercises_he`
- `equipment_he`
- `safety_warnings_he`
- `common_mistakes_he`
- `quality_score`
- `quality_reason_he`
- `skill_level`
- `risk_level`
- `domain`
- `primary_category`
- `secondary_categories`
- `tags`
- `motorcycle_types`
- `motorcycle_weight_classes`
- `terrain_types`
- `road_conditions`
- `verification`
- `last_checked`

כללים:

- `summary_he`: סיכום עובדתי מקורי בעברית, בדרך כלל 45–100 מילים.
- `learning_points_he`: 3–6 נקודות אמיתיות.
- `why_watch_he`: ערך ייחודי של הסרטון, לא חזרה על הכותרת.
- `fit_for_he`: ניסיון קודם, סוג אופנוע ותנאי תרגול, רק כאשר רלוונטי.
- `exercises_he`: רק תרגילים שמוצגים או נתמכים במפורש; אחרת `[]`.
- `quality_reason_he`: חוזקות, מגבלות, רמת המקור והיבטי בטיחות.
- `safety_warnings_he`: אזהרות ספציפיות, לא טקסט כללי זהה.
- `verification.notes_he`: מה נבדק ומה לא, ללא ניסוח עמום.

אין לשנות עובדה נכונה רק כדי לייצר שונות. עם זאת, אין להשאיר תוכן שנוצר ממחולל התבניות ההיסטורי.

## 5.4 סקריפטים היסטוריים

סמן בראש:

```text
tools/apply_phase03_wave1.py
```

ובכל כלי דומה:

```text
HISTORICAL ONE-TIME MIGRATION.
DO NOT USE TO AUTHOR OR AUDIT CONTENT.
```

אין להשתמש בכלים האלה לכתיבת שדות אמון.

## 5.5 אוצרות Chapters

בדוק את כל מערכי `chapters`.

שמור רק נקודות זמן המסייעות ללמידה או לניווט לתוכן מקצועי.

בדרך כלל יש להסיר, לאחר בדיקת ההקשר:

- Intro
- Outro
- Sponsor
- Subscribe
- Welcome
- Bloopers
- Final thoughts כלליים
- פתיח נופי
- סיום מוזיקלי
- קידום חנות או Patreon
- פרק שאינו קשור לנושא הסרטון
- הפניה לסרטון אחר

כללים:

- אין להמציא Chapter.
- אין לשנות זמן.
- אין לשנות כותרת מקורית של Chapter מאומת.
- אין לתרגם את הכותרת בתוך הנתון אם הסכמה שומרת את המקור.
- מותר להסיר Chapter לא־לימודי.
- אם אין Chapter שימושי, השאר מערך ריק.

צור:

```text
research/final-one-shot/chapter-curation.csv
```

עם החלטה לכל Chapter שנבדק.

## 5.6 שפות אחרות

שני הסרטונים היפניים הקיימים אינם עומדים בדרישת העברית–אנגלית. החלף אותם בסרטונים עבריים או אנגליים באיכות שווה או טובה יותר, אלא אם `language` בפועל הוא אנגלית והמטא־דאטה הקודם היה שגוי. בסיום אין `ja` ב־Production.

## 5.7 החלפה

אם רשומה קיימת אינה עוברת את השער:

- העבר אותה לדוח דחיות.
- אל תמחק את הראיה ההיסטורית.
- החלף אותה במועמד מאומת.
- שמור את בסיס 130 לפני הרחבת המאגר.

צור Gate ביניים:

```powershell
python tools/validate_data.py --expected-count 130 --report reports/final-one-shot/gate-130/data-validation.json
python tools/check_links.py --online --report reports/final-one-shot/gate-130/link-check.json
```

אין לעבור למחקר ההרחבה לפני 130/130 פעילים, ייחודיים ותקינים.

---

# 6. כלי Quality Lint שאינו כותב תוכן

צור או הרחב:

```text
tools/content_quality_lint.py
```

הכלי הוא Audit בלבד ואסור לו לשנות `videos.json`.

הוא ידווח לפחות על:

- התאמות לתבניות ההיסטוריות.
- Exact duplicates בשדות טקסט.
- Near duplicates מעל סף מתועד.
- תקצירים קצרים או כלליים מדי.
- שדות `why_watch_he`, `fit_for_he`, `quality_reason_he` חשודים.
- `exercises_he` זהים או לא סבירים.
- Chapters גנריים.
- רשומות ללא ראיות מספיקות.
- רשומות Description-only.
- Confidence בינוני ונמוך.
- ריכוז ערוצים.
- שיעור תוכן שיווקי.
- ספירת שפות.
- קטגוריות עם כיסוי דל.
- סרטונים שאינם בעברית או באנגלית.
- חשד להעלאה חוזרת של אותו תוכן.
- Related IDs לא רלוונטיים או חסרים.

צור פלט:

```text
reports/final-one-shot/content-quality-lint.json
reports/final-one-shot/content-quality-lint.html
```

הוסף בדיקות יחידה לכלי.

שער חובה:

- 0 התאמות למחוללי התבניות ההיסטוריים.
- 0 Exact duplicates בלתי מוסברים בשדות ההסבר.
- כל Near duplicate עובר בדיקה ידנית ומתועד.
- 0 שפות שאינן `he` או `en`.
- 0 Confidence נמוך ב־Production.

---

# 7. מפת כיסוי לפני מחקר חדש

צור:

```text
research/final-one-shot/coverage-matrix-before.csv
```

המטריצה תכסה את כל התחומים, הקטגוריות ותתי־הנושאים שב־`MASTER_SPEC.md` וב־`data/categories.json`.

לכל נושא תעד:

- מספר סרטונים קיים.
- רמות רכיבה.
- שפות.
- סוגי אופנוע.
- מקורות.
- איכות ממוצעת.
- פער.
- עדיפות מחקר.

תן עדיפות לפערים הבאים, בלי להזניח את שאר המפרט:

- רכיבה בגשם ובכביש רטוב.
- רוח צד ומשבי רוח.
- רכיבת לילה.
- רכיבה עירונית.
- פניות, Trail Braking ובלימת חירום.
- חול, בוץ, חריצים, אבנים, דרדרת.
- עליות, ירידות וכישלון באמצע עלייה.
- הרמת אופנוע וחילוץ.
- לחץ אוויר וצמיגים.
- מתלים.
- ABS, Traction Control ומצבי רכיבה.
- אופנועי אדוונצ'ר כבדים.
- רכיבה עם מטען ומורכב.
- רכיבה בקבוצה.
- עייפות ומסע רב־יומי.
- מעבר מכביש לשטח.
- תרגילים במגרש.
- מצבים למתקדמים.

---

# 8. מחקר ההרחבה — מ־130 ל־250 באותה ריצה

## 8.1 יעד

הוסף **בדיוק 120 סרטונים חדשים**, או יותר מועמדים אם נדרשו החלפות, כך שבסיום יהיו בדיוק 250.

אל תעצור ב־200. אל תיצור Wave ביניים למסירה. מותר לעבוד פנימית באצוות, אך המשך אוטומטית עד 250.

## 8.2 מאגר מועמדים

סרוק לפחות:

- 400 מועמדים ייחודיים בסך הכול, או עד שנמצאו 120 מאושרים ועוד 40 חלופות איכותיות.
- לפחות 100 מועמדים עבריים ייחודיים, אלא אם תועד באופן ברור שכל שאילתות המקור הסבירות מוצו.
- מגוון רחב של ערוצים, בתי ספר, מדריכים, גופי בטיחות ויצרנים.

אין לספור אותו Video ID פעמיים. אין להציג רשימת תוצאות חיפוש כבדיקת תוכן.

## 8.3 חיפוש בעברית

בצע חיפוש ייעודי בעברית עבור כל משפחות הנושאים.

בדוק לפחות את ה־Seeds הבאים, בלי להניח שהם מתאימים:

- `3nwR3t6-Ftg`
- `lYBhzHlFmNU`
- `HWNbjhnBTMM`
- `05DDi3qweE0`
- `3uttfaaeYrA`
- `tBzG_y2mhHU`
- `mi6-lTRzFkI`
- `QkMjbG_6PzY`
- `zmw788huGuk`
- `jyRIPZ1olIs`
- `GqUgDGd04XE`
- `Nfox-7dggh4`

בדוק גם מקורות כגון:

- ProRiding Israel.
- Cohen Adventure / צביקה כהן.
- ADV Moto Life.
- בתי ספר ישראליים.
- מדריכי רכיבה מוסמכים.
- גופי בטיחות.
- ערוצים ישראליים העוסקים באדוונצ'ר, כביש וטכניקה.

צור:

```text
research/final-one-shot/hebrew-candidates.csv
```

עם החלטה מנומקת לכל מועמד.

## 8.4 חיפוש באנגלית

חפש לפי כל הנושאים שבמטריצת הכיסוי, תוך העדפת:

- בתי ספר מקצועיים.
- מדריכי רכיבה מוכרים.
- גופי בטיחות רשמיים.
- יצרנים כאשר התוכן טכני ולא רק שיווקי.
- ערוצים עצמאיים איכותיים עם הדגמה והסבר.

אין להסתמך רק על MOTOTREK או Bret Tkacs. הרחב את מקורות התוכן.

## 8.5 גיוון סופי

יעדים סופיים:

- לפחות 70 ערוצים ייחודיים.
- לא יותר מ־20 סרטונים מערוץ יחיד, אלא אם קיימת הצדקה חריגה בדוח.
- שני הערוצים הגדולים יחד לא יעלו על 15% מן המאגר.
- לפחות 60% מן המאגר ממקורות מקצועיים, בתי ספר, גופי בטיחות, מדריכים מוכרים או יצרנים בעלי תוכן הדרכתי ממשי.
- שיעור `contains_marketing=true` יעדיף להיות מתחת ל־60%.
- אל תמחק תוכן מצוין רק כדי לשפר סטטיסטיקה, אך בחר את החדשים כך שהריכוז והשיווק ירדו.
- לפחות 20 סרטונים ברמת Advanced או Intermediate-Advanced, אם הסכמה מאפשרת.
- כיסוי של מתחילים, בינוניים ומתקדמים.
- כיסוי של אופנועים קלים, בינוניים וכבדים.
- 0 סרטונים בשפה שאינה עברית או אנגלית.

## 8.6 מינימום כיסוי לפי Domain

במאגר הסופי של 250:

- `offroad_adventure`: לפחות 80.
- `road`: לפחות 60.
- `safety_recovery`: לפחות 30.
- `practice`: לפחות 25.
- `mixed`: לפחות 20.

היתרה גמישה לפי איכות ופערים. אין להכניס סרטון חלש כדי לעמוד במכסה; במקרה של פער אמיתי תעד חריגה, אך נסה חלופות לפני כן.

## 8.7 בדיקת כל מועמד

לכל מועמד:

1. אמת Video ID ו־URL.
2. אמת Title, Channel, Date, Duration ו־Language.
3. בדוק זמינות ציבורית.
4. בדוק oEmbed או דרך הטמעה מקבילה.
5. בדוק תיאור.
6. בדוק Chapters.
7. בדוק כתוביות או תמלול כאשר זמינים.
8. צפה בחלקים רלוונטיים כאשר נדרש.
9. בדוק אם זה Reupload.
10. בדוק ערך לימודי.
11. בדוק התאמה לאדוונצ'ר/כביש.
12. בדוק בטיחות.
13. בדוק שיווק.
14. כתוב תוכן עברי מקורי.
15. תעד ראיות ב־Ledger.
16. אישור או דחייה עם סיבה.

צור:

```text
research/final-one-shot/approved-new.csv
research/final-one-shot/rejected-candidates.csv
research/final-one-shot/reserve-candidates.csv
```

## 8.8 זכויות יוצרים

אין לשמור בפרויקט:

- וידאו.
- שמע.
- תמלול מלא.
- כתוביות מלאות.
- תיאור YouTube מלא.
- תמונת מקור שהורדה שלא דרך Thumbnail הרשמי.
- תוכן המוגן בזכויות מעבר למטא־דאטה הדרוש.

מותר לעבד זמנית תמלול או כתוביות בתיקייה זמנית מחוץ לפרויקט. מחק אותם בסיום.

## 8.9 איכות רשומה חדשה

כל רשומה חדשה חייבת לעבור את אותו Schema ואת אותם כללי אמינות של הרשומות הקיימות.

Production לא יקבל:

- Quality Score מתחת ל־3 מתוך 5.
- Confidence נמוך.
- טכניקה מסוכנת ללא אזהרה.
- סרטון שיווקי ללא ערך הדרכתי.
- סרטון Enduro קל שמוצג בטעות כמדריך מלא לאדוונצ'ר כבד.
- תוכן כפול.
- קישור שאינו ניתן להטמעה.
- תקציר כללי או תבניתי.

---

# 9. איחוד סופי של הנתונים

לאחר המחקר:

- שמור בדיוק 250 רשומות ב־`data/videos.json`.
- עדכן `categories.json`, `synonyms.json` ו־Schema רק אם יש צורך מוכח.
- אל תשנה IDs קיימים בלי Migration מתועד.
- עדכן `related_video_ids` לפי קשר אמיתי.
- הסר הפניות לרשומות שנדחו.
- סדר את הנתונים באופן יציב.
- ודא שכל `last_checked` מעודכן.
- ודא שכל URL מתאים ל־Video ID.
- ודא שאין Thumbnail או Channel URL לא תקין.

צור:

```text
reports/final-one-shot/id-diff.json
reports/final-one-shot/final-language-stats.json
reports/final-one-shot/final-channel-stats.json
reports/final-one-shot/final-coverage-matrix.csv
```

---

# 10. מסלולי למידה

הרחב את `data/learning-paths.json` לפחות לשמונה מסלולים מלאים:

1. מתחילים בשטח.
2. מתחילים בכביש.
3. שליטה באופנוע אדוונצ'ר כבד.
4. חול ובוץ.
5. פניות ובלימה בכביש.
6. מעבר מכביש לשטח.
7. הכנה למסע רב־יומי.
8. חילוץ, נפילות ובטיחות.

מותר להוסיף מסלולים נוספים אם הם מועילים.

כללים:

- 8–12 שלבים לכל מסלול.
- בכל שלב 2–5 סרטונים לבחירה כאשר אפשר.
- סדר פדגוגי הגיוני.
- אין הפניה ל־ID שאינו קיים.
- אין להציג תרגיל מתקדם לפני יסודות.
- לכל שלב הסבר קצר, ציוד, רמת סיכון ואזהרה כאשר נדרש.
- אין להמציא תוכן שאינו נמצא בסרטונים.

---

# 11. השלמת האתר לגרסה 1.0

שמור על הארכיטקטורה הסטטית הקיימת. אין לבצע Rewrite או מעבר Framework בלי צורך מוכח.

## 11.1 תכונות חובה

ודא שהאתר כולל ועובד עם 250 רשומות:

- דף בית ברור.
- הפרדה בין שטח, כביש, משולב, בטיחות ותרגול.
- ספרייה מלאה.
- חיפוש בעברית ובאנגלית.
- מילים נרדפות.
- שגיאות כתיב קלות.
- מסננים משולבים.
- מיון.
- ספירת תוצאות.
- טעינה מדורגת.
- מועדפים.
- סימון נצפה.
- שמירת התקדמות.
- “המשך מהמקום שבו עצרת”.
- מסלולי למידה.
- סרטונים קשורים.
- Deep Link לסרטון.
- Deep Link למסננים.
- העתקת קישור.
- פתיחה ישירה ב־YouTube.
- נגן `youtube-nocookie.com`.
- אין Autoplay.
- אין iframe לפני לחיצה.
- הסרת iframe בסגירה.
- מצב בהיר וכהה.
- RTL מלא.
- Mobile First.
- Desktop, Tablet ו־Mobile.
- עמוד זכויות ומקורות.
- אזהרת בטיחות.
- מנגנון לדיווח על קישור שבור ללא Backend: יצירת טקסט דיווח והעתקה, או שימוש ב־Contact כאשר מוגדר.
- תצורת שם, מחבר, קהילה, לוגו ופרטי קשר.
- Fallback לוגו בטוח.
- אין פרסומות ואין Affiliate.

## 11.2 תיקונים ידועים

תקן לפחות:

1. גישת `localStorage`:
   - עצם הקריאה ל־`window.localStorage` חייבת להיות בתוך `try/catch`.
   - אם `SecurityError` נזרק, עבור ל־Memory fallback.
2. תקן את השם השגוי `exercise_suggestions_he` בכל תיעוד, והשתמש ב־`exercises_he`.
3. ודא ש־`document.title`, Meta Description ו־Open Graph נגזרים מהתצורה.
4. ודא שכל מידע מעורב עברית/אנגלית/מספרים משתמש ב־Bidi isolation.
5. ודא שכל Overlay נועל רקע, נסגר ב־Escape ומחזיר מיקוד.
6. ודא שאין Scroll כפול במובייל.
7. ודא שלא נותר טקסט קשיח של 60 או 130.
8. ודא שהאתר עובד גם עם Fixture של 300.
9. ודא שאין `innerHTML` לא בטוח המבוסס על JSON.
10. הוסף `rel="noopener noreferrer"` לקישורים חיצוניים.
11. ודא שהתמונות משתמשות ב־Lazy Loading.
12. ודא שטקסט חלופי קיים.
13. ודא שאין קישורים שבורים בתפריטים.
14. ודא שמצב ריק, כשל טעינה וכשל קישור מוצגים בצורה ברורה.

## 11.3 ביצועים

- אל תיצור 250 iframes.
- הצג מספר ראשוני מוגבל של כרטיסים.
- טען עוד באצוות.
- חיפוש עם Debounce.
- סינון בצד לקוח.
- אין ספריות Runtime כבדות שלא נדרשות.
- בדוק 250 ו־300 רשומות.
- תעד זמן חיפוש וסינון, אך אל תיצור Threshold שביר התלוי במחשב.
- אין גלילה אופקית.

## 11.4 נגישות

בדוק:

- שימוש מלא במקלדת.
- Focus visible.
- החזרת Focus.
- Labels.
- `aria` מתאים.
- ניגודיות.
- Dialog semantics.
- `lang="he"` ו־`dir="rtl"`.
- `<bdi>` עבור טקסט מעורב.
- Alt לתמונות.
- Reduced Motion כאשר רלוונטי.
- כותרות היררכיות.
- כפתורים בגודל נוח בטלפון.

---

# 12. חיפוש וסינון — בדיקות תוכן אמיתיות

מנוע החיפוש חייב להחזיר תוצאה ישירה ורלוונטית בראש הרשימה עבור לפחות:

- חול
- בוץ
- פניות בכביש
- בלימת חירום
- הרמת אופנוע
- גשם
- עלייה תלולה
- רכיבה איטית
- רוח צד
- רכיבת לילה
- לחץ אוויר
- מתלים
- ABS בשטח
- רכיבה עם מורכב
- מטען
- עייפות
- Countersteering
- Trail Braking
- Sand
- Mud
- Emergency braking
- Cornering
- Crosswind
- Suspension
- Tire pressure

אין להסתפק בכך שקיימת תוצאה כלשהי. שלוש התוצאות הראשונות חייבות להיות רלוונטיות ממש לנושא.

בדוק לפחות:

- שילוב של 3 מסננים.
- שילוב של 5 מסננים.
- איפוס מסננים.
- URL מסונן ושיתוף.
- חיפוש עם שגיאת כתיב קלה.
- חיפוש עברי שמוצא סרטון באנגלית באמצעות מילון.
- חיפוש באנגלית שמוצא סרטון עברי כאשר התגיות תואמות.

---

# 13. בדיקות אוטומטיות

הרחב את הבדיקות כך שיכסו 250 ו־300 רשומות.

הרץ בסוף:

```powershell
python tools/validate_data.py --expected-count 250 --report reports/final-one-shot/final-data-validation.json
python tools/content_quality_lint.py --report reports/final-one-shot/final-content-quality-lint.json --html reports/final-one-shot/final-content-quality-lint.html
python tools/check_links.py --online --report reports/final-one-shot/final-link-check.json
python tools/build_audit.py --link-report reports/final-one-shot/final-link-check.json
npm test
python -m unittest discover -s tests -p "test_*.py" -v
node --check assets/js/app.js
```

בדיקת קישורים:

- בצע Retry עם Backoff לכשל זמני.
- הבחֵן בין unavailable, indeterminate ו־rate limited.
- כשל אמיתי מחייב החלפת הסרטון.
- בסיום נדרשים 250 active, 0 unavailable ו־0 indeterminate.
- הרץ בדיקת קישורים נוספת לאחר כל תיקון אחרון.

הוסף בדיקות ל:

- 250 רשומות.
- Fixture של 300.
- LocalStorage חסום.
- Config מותאם.
- Logo בטוח ולא בטוח.
- Deep Links.
- Modal.
- Menu.
- Filter Drawer.
- Focus.
- Escape.
- Bidi.
- No iframe before click.
- `youtube-nocookie.com`.
- Removal of iframe.
- Search relevance.
- Synonyms.
- Typos.
- Combined filters.
- Learning paths.
- Related IDs.
- Empty states.
- Error states.
- No duplicate DOM IDs.
- No horizontal overflow.
- No JavaScript errors.

---

# 14. בדיקות דפדפן אמיתיות

הפעל את האתר מן הנתיב האמיתי, הכולל עברית:

```text
D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-Starter
```

אל תבדוק רק עותק בתיקיית ASCII.

השתמש בשרת המקומי המצורף או בשרת מקומי בטוח.

בדוק לפחות:

- 1440×900.
- 1024×768.
- 390×844.
- 360×800.

בדוק:

- דף הבית.
- ספרייה.
- תוצאות חיפוש.
- מסננים.
- חלון סרטון.
- מסלולי למידה.
- מצב בהיר.
- מצב כהה.
- תצורה מותאמת.
- שגיאת קישור.
- רענון לאחר מועדף/נצפה/התקדמות.
- Back/Forward בדפדפן.
- Focus.
- Keyboard.
- Mobile Drawer.
- Scroll Lock.
- Console.
- Network.
- No horizontal overflow.

שמור Screenshots אמיתיים תחת:

```text
reports/final-one-shot/screenshots/
```

לפחות:

- `desktop-home.png`
- `desktop-library.png`
- `desktop-search.png`
- `desktop-video-dialog.png`
- `desktop-learning-path.png`
- `desktop-dark-mode.png`
- `tablet-library.png`
- `mobile-home.png`
- `mobile-library.png`
- `mobile-filters.png`
- `mobile-video-dialog.png`
- `mobile-learning-path.png`
- `config-customization.png`
- `error-state.png`

אין לדווח על צילום או בדיקה שלא בוצעו.

אם Playwright או Chromium זמינים, השתמש בהם. מותר להוסיף Dependency לפיתוח בלבד אם נחוץ, אך אין להוסיף ספריית Runtime כבדה. אם כלי מסוים אינו זמין, השתמש בחלופה אמיתית ותעד אותה.

---

# 15. ביקורת Red Team פנימית

לאחר שהכול נראה גמור, אל תארוז מיד.

בצע שתי ביקורות עצמאיות בתוך אותה משימה:

## 15.1 Reviewer A — תוכן ואמינות

קרא את `MASTER_SPEC.md` מחדש כאילו לא השתתפת בביצוע.

בדוק:

- 100% מה־IDs והקישורים.
- 100% מה־Languages.
- 100% מה־Chapters.
- 100% משדות האמון מול כלי Lint.
- 100% מן הקטגוריות וההפניות.
- כל הרשומות ברמת סיכון גבוהה.
- מדגם אקראי של לפחות 50 סרטונים מכלל המאגר, מפוזר לפי שפה, תחום ורמה, מול דף המקור.
- כל הסרטונים בעברית.
- כל הסרטונים שסומנו Marketing=false מערוצים מסחריים.
- כל הסרטונים עם Quality Score 5.
- כל הרשומות עם Confidence בינוני.

צור:

```text
reports/final-one-shot/red-team-content.md
reports/final-one-shot/red-team-content-defects.json
```

## 15.2 Reviewer B — קוד, UX ושחרור

בדוק מחדש:

- כל דרישות האתר שב־MASTER_SPEC.
- אבטחה.
- נגישות.
- ביצועים.
- מובייל.
- חיפוש.
- מסננים.
- Storage.
- Deep Links.
- נגן.
- זכויות.
- README.
- פרסום סטטי.
- ניקיון החבילה.
- Git.
- גרסה.
- קבצי הגדרות.
- קובצי Release.

צור:

```text
reports/final-one-shot/red-team-technical.md
reports/final-one-shot/red-team-technical-defects.json
```

סווג ממצאים:

- `P0` — חוסם שחרור.
- `P1` — פגיעה מהותית.
- `P2` — חשוב.
- `P3` — קוסמטי.

---

# 16. לולאת תיקון אוטומטית

לאחר Red Team:

1. תקן את כל P0.
2. תקן את כל P1.
3. תקן את כל P2 שניתן לתקן בלי לפגוע באמינות.
4. הרץ מחדש את כל הבדיקות.
5. הרץ מחדש את בדיקת הקישורים.
6. הרץ מחדש את Lint.
7. הרץ מחדש Smoke בדפדפן.
8. עדכן את דוחות Red Team.
9. חזור על התהליך עד:
   - 0 P0.
   - 0 P1.
   - כל הבדיקות עוברות.
   - 250/250 קישורים פעילים.
   - 0 שגיאות Console.
   - 0 שפות שאינן עברית/אנגלית.
   - 0 תבניות היסטוריות.
   - 0 כפילויות.
   - 0 Placeholder.
   - 0 Chapters מומצאים.
   - 0 Confidence נמוך.

אל תבקש מן המשתמש להחליט אם לתקן. תקן.

אם סרטון כושל בבדיקה האחרונה, החלף אותו במועמד מן ה־Reserve, עדכן את כל ההפניות והריץ הכול מחדש.

---

# 17. מסמכי Release

עדכן:

- `README.md`
- `MASTER_SPEC.md` רק אם נדרש לתעד מימוש, לא כדי להחליש דרישה.
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `package.json`
- `data/site-config.json`
- `CHANGELOG.md`

בסיום:

## `PROJECT_STATUS.md`

- גרסה `1.0.0`.
- 8 מתוך 8.
- 100%.
- בדיוק 250 סרטונים.
- מספר עברית ואנגלית.
- כל שערי השחרור עברו.
- אין שלב נוסף.

## `NEXT_ACTION.md`

כתוב:

```text
הפרויקט הושלם. אין משימת המשך פתוחה.
```

אל תפנה ל־Work או Codex.

## `HANDOFF_TO_CODEX.md`

הפוך אותו למסמך היסטורי או Rename ל:

```text
archive/HANDOFF_TO_CODEX_PHASE03.md
```

אין להשאיר הוראה פעילה למסירה נוספת.

## `README.md`

כלול:

- הפעלה מקומית.
- שימוש ב־`run-local.bat`.
- פרסום באחסון סטטי.
- הוספת סרטון.
- שינוי קטגוריה.
- בדיקת קישורים.
- שינוי שם, מחבר, קהילה ולוגו.
- מבנה הנתונים.
- הרצת בדיקות.
- זכויות יוצרים.
- אזהרת בטיחות.
- מנגנון דיווח על קישור שבור.
- תחזוקה עתידית.
- דרישות מערכת.
- פתרון תקלות.

---

# 18. Git סופי

לפני Commit:

```powershell
git diff --check
git status --short --branch
```

תקן כל בעיית Whitespace או קובץ זמני.

צור Commit סופי ברור, לדוגמה:

```text
release: complete adventure riding video guide v1.0 with 250 verified videos
```

לאחר Commit שמור:

```powershell
git status --short --branch > reports/final-one-shot/git-status.txt
git log -1 --oneline > reports/final-one-shot/git-log.txt
git show --stat --oneline HEAD > reports/final-one-shot/git-show-stat.txt
git diff --check > reports/final-one-shot/git-diff-check.txt
```

הפק את הקבצים אחרי ה־Commit הסופי.

אין לבצע Push או Force Push ללא Remote מאומת.

---

# 19. חבילת Release אחת

צור תיקייה:

```text
release/Adventure-Riding-Video-Guide-v1.0.0/
```

בתוכה:

```text
site/
source/
reports/
README-FIRST.md
FINAL_RELEASE_REPORT.md
FINAL_RELEASE_MANIFEST.md
```

## `site/`

עותק נקי ומוכן לפרסום של האתר בלבד:

- `index.html`
- `assets/`
- `data/`
- קבצים סטטיים נדרשים
- ללא tests, tools, research או reports

## `source/`

כל קוד המקור והתחזוקה:

- האתר.
- data.
- schema.
- tools.
- tests.
- prompts הרלוונטיים.
- README.
- מסמכי הפרויקט.
- מחקר ודוחות נחוצים.
- ללא תמלולים מלאים או מדיה.

## `reports/`

- כל דוחות Release הסופיים.
- Content Audit.
- Link Check.
- Data Validation.
- Quality Lint.
- Browser Acceptance.
- Red Team.
- Screenshots.
- Git evidence.
- Evidence Ledger.
- Coverage Matrix.
- Rejected/Approved summaries.

## `FINAL_RELEASE_REPORT.md`

כלול:

- תוצאה PASS/FAIL.
- מספר סרטונים.
- שפות.
- תחומים.
- קטגוריות.
- ערוצים.
- Marketing.
- מסלולי למידה.
- בדיקות.
- קישורים.
- ביצועים.
- נגישות.
- ממצאי Red Team ותיקונים.
- מגבלות אמיתיות שנותרו.
- Commit Hash.
- הוראות פרסום.

## `FINAL_RELEASE_MANIFEST.md`

כלול:

- כל הקבצים.
- גודל.
- SHA-256.
- זמן יצירה UTC.
- מספר קבצים.
- מספר בתים כולל.

לאחר מכן צור ZIP יחיד:

```text
release/Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip
```

בדוק את ה־ZIP לאחר יצירתו:

- אין `..`.
- אין נתיב מוחלט.
- אין `.git/`.
- אין `node_modules/`.
- אין `__pycache__/`.
- אין Cache.
- אין קבצים זמניים.
- אין ZIP ישן בתוך ה־ZIP.
- אין Secrets.
- אין API Keys.
- אין תמלול מלא.
- אין וידאו או שמע.
- כל קובץ במניפסט קיים.
- כל Hash מתאים.
- אין קובץ עודף.
- ניתן לחלץ.
- `site/index.html` קיים.
- `source/data/videos.json` מכיל בדיוק 250.

---

# 20. שער Release סופי

הכרז `PASS` רק אם כל התנאים מתקיימים:

## תוכן

- [ ] בדיוק 250 סרטונים.
- [ ] כל הסרטונים פעילים.
- [ ] כל הסרטונים ניתנים להטמעה.
- [ ] כל הסרטונים ייחודיים.
- [ ] כל הסרטונים בעברית או באנגלית.
- [ ] לפחות 25 בעברית, או חריגה מתועדת אחרי בדיקת 100 מועמדים עבריים.
- [ ] לכל סרטון תקציר עברי.
- [ ] לכל סרטון רמה וסיכון.
- [ ] לכל סרטון ראיות.
- [ ] 0 Confidence נמוך.
- [ ] 0 שדות תבניתיים.
- [ ] 0 Chapters מומצאים.
- [ ] 0 Placeholder.
- [ ] 0 Reupload ידוע.
- [ ] קטגוריות והפניות תקינות.
- [ ] לפחות 8 מסלולי למידה.

## אתר

- [ ] האתר עובד עם 250.
- [ ] Fixture 300 עובר.
- [ ] חיפוש עברית ואנגלית עובד.
- [ ] כל שאילתות הקבלה רלוונטיות.
- [ ] מסננים משולבים עובדים.
- [ ] מועדפים ונצפה נשמרים.
- [ ] Progress נשמר.
- [ ] iframe רק לאחר לחיצה.
- [ ] `youtube-nocookie.com`.
- [ ] Mobile/Desktop/Tablet עברו.
- [ ] RTL ו־Bidi תקינים.
- [ ] נגישות בסיסית עברה.
- [ ] 0 שגיאות Console.
- [ ] 0 Overflow אופקי.
- [ ] אין Scroll כפול.
- [ ] זכויות ובטיחות מוצגים.
- [ ] README מלא.

## QA ו־Release

- [ ] Data Validation עבר.
- [ ] Content Quality Lint עבר.
- [ ] Link Check עבר 250/250.
- [ ] Node Tests עברו.
- [ ] Python Tests עברו.
- [ ] Browser Acceptance עבר.
- [ ] Red Team: 0 P0 ו־0 P1.
- [ ] Git נקי.
- [ ] Commit סופי קיים.
- [ ] Manifest תקין.
- [ ] ZIP סופי תקין.

אם תנאי נכשל, אל תסיים. תקן והריץ מחדש.

---

# 21. הפלט היחיד בצ'אט בסיום

בסוף הצג רק:

1. `PASS` או `FAIL`.
2. מספר הסרטונים לפני ואחרי.
3. מספר הסרטונים בעברית ובאנגלית.
4. מספר מועמדים שנבדקו, אושרו ונדחו.
5. מספר רשומות קיימות שתוקנו או הוחלפו.
6. מספר Chapters לפני, אחרי וכמה הוסרו.
7. מספר מסלולי הלמידה.
8. מספר בדיקות שעברו ונכשלו.
9. תוצאת Link Check.
10. מספר ממצאי P0/P1/P2/P3 שנותרו.
11. Commit Hash.
12. הנתיב המדויק:

```text
D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-Starter\release\Adventure-Riding-Video-Guide-v1.0.0-FINAL.zip
```

לאחר מכן עצור. אין לפתוח Phase נוסף ואין לבקש ביקורת ביניים.
