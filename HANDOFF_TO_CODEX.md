# מסירה ל־Codex — לאחר Phase 03

## גבול הסבב

Phase 03 הושלם. אין להתחיל את Phase 04 בלי אישור מפורש של `reports/phase-03-review-bundle.zip`. קובץ המשימה הבא הוא `prompts/04_CODEX_INTEGRATE_AND_QA_V2.md`, בהתאם ל־`NEXT_ACTION.md`.

## מצב הנתונים המאושר

- `data/videos.json`: בדיוק 130 רשומות.
- 130 IDs פנימיים, 130 YouTube Video IDs ו־130 כתובות YouTube ייחודיים.
- שפות: 9 עברית, 119 אנגלית ו־2 יפנית.
- 46 ערוצים ייחודיים.
- 82 רשומות עם Chapters, בסך הכול 589 אובייקטים.
- בדיוק שני מסלולי למידה, 20 צעדים ו־85 הפניות תקינות.
- אין Placeholder, נתוני דמה, הפניות שבורות או כפילויות פעילות.

## Trust Audit של Wave 1

כל 60 דפי המקור נבדקו מחדש לפני הוספת רשומה חדשה. ארבעת השדות `quality_reason_he`, `why_watch_he`, `exercises_he`, `fit_for_he` עודכנו על בסיס ראיות; 50 רשומות נשארו עם `exercises_he=[]` משום שלא נמצא תרגיל מפורש. ב־`yt-DY7OFizK_eo` הוסרו שישה פרקים שהוכחו כהפניות לסרטונים אחרים. כל 60 הרשומות נשמרו, ושער 60 עבר עם 4,261/0. פירוט השינויים נמצא ב־`research/reports/wave-1-corrections.md`.

## Wave 2

- נוספו בדיוק 70 רשומות; 0 רשומות Wave 1 הוסרו.
- האצווה החדשה כוללת 68 סרטונים באנגלית ושני סרטוני JAF ביפנית.
- החלוקה החדשה לפי תחום: 23 שטח/אדוונצ'ר, 22 כביש, 13 בטיחות וחילוץ, 6 משולב ו־6 תרגול.
- 52 מן הרשומות החדשות כוללות 400 פרקים מדויקים; 18 מבוססות תיאור ללא פרקים.
- כל `why_watch_he`, ‏`fit_for_he` ו־`quality_reason_he` באצווה החדשה ייחודיים.
- לא נשמרו וידאו, שמע, תמלול, כתוביות או תיאור YouTube מלא.

ראיות המחקר:

- `research/approved/wave-2-approved-ids.txt`
- `research/approved/wave-2-youtube-metadata.json`
- `research/approved/wave-2-offroad-records.json`
- `research/approved/wave-2-road-records.json`
- `research/approved/wave-2-technical-records.json`
- `research/rejected/wave-2-rejected.csv`
- `research/reports/wave-2-report.md`

## חריג הקישור שטופל

בריצת הקישורים הראשונה `5SlHGlyzF7w` החזיר HTTP 401 מ־YouTube oEmbed, אף שדף הצפייה והמטא־דאטה נשארו public. מאחר שהאתר משתמש בנגן מוטמע, הרשומה הועברה לדחיות והוחלפה ב־`CI6h7XtyINY`, שעבר Full Metadata ו־oEmbed. התוצאה הסופית היא 130 active, ‏0 unavailable ו־0 indeterminate.

## הרחבות טקסונומיה

נוספו ארבע קטגוריות בלבד: `tires_setup`, `suspension_setup`, `electronic_aids`, `trip_preparation`; עשר תגיות תואמות; השפה `ja`; וחמישה מושגי חיפוש. אין לשנות מזהים אלה בלי migration מתועד של כל ההפניות.

## כלי תחזוקה שנוספו או הורחבו

- `tools/youtube_research.py` — מחקר מטא־דאטה בלבד; `yt-dlp` הוא תלות מחקר אופציונלית ואינו נדרש ל־runtime.
- `tools/apply_phase03_wave1.py` — תיקון Trust Audit עם guard ל־hash של בסיס 60.
- `tools/prepare_phase03_technical_records.py` — הפקת הרשומות הטכניות מתוך מטא־דאטה שנבדק.
- `tools/apply_phase03_wave2.py` — מיזוג חד־פעמי מוגן של האצווה המאושרת.
- `tools/replace_phase03_unembeddable.py` — תיעוד החלפת חריג oEmbed.
- `tools/build_audit.py` — תומך ב־`--link-report` תוך שמירת התנהגות קודמת.
- `tools/build_phase03_review_bundle.py` — בונה ומאמת ZIP עם allow-list, מניפסט ו־SHA-256.

## בדיקות סופיות

```powershell
python tools/validate_data.py --expected-count 130 --report reports/phase-03-data-validation.json
python tools/check_links.py --online --report reports/phase-03-link-check.json
python tools/build_audit.py
python tools/build_audit.py --link-report reports/phase-03-link-check.json
npm test
python -m unittest discover -s tests -p "test_*.py" -v
```

תוצאות סופיות:

- Data: ‏8,051 עברו, ‏0 נכשלו, ‏0 אזהרות.
- Node: ‏35 עברו, ‏0 נכשלו.
- Python: ‏15 עברו, ‏0 נכשלו.
- סך ייחודי ללא ספירה כפולה: 8,101 עברו, ‏0 נכשלו.
- Online links: ‏130 עברו, ‏0 נכשלו.
- Content Audit: PASS, ‏8,050 בדיקות חופפות עברו.

## מגבלות שנותרו

- זהו Snapshot של 130 ולא Release 1.0; יעד המפרט הוא לפחות 200.
- לא נוסף סרטון עברי חדש ב־Wave 2 משום שלא נמצא מועמד שעמד בשער הראיות בלי להוריד איכות; תשע הרשומות העבריות הקיימות נשמרו.
- זמינות YouTube עשויה להשתנות, ולכן יש להריץ בדיקת קישורים מקוונת מחדש לפני שחרור או לאחר שינוי נתונים.
- Phase 04 לא בוצע ולא נבדק במסגרת מסירה זו.
