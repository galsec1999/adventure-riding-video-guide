# משימת Work מלאה — Phase 03: Trust Audit, הרחבה ל־130 וחבילת מסירה

עבוד ישירות בתוך תיקיית הפרויקט המקומית הפתוחה של:

`Adventure-Riding-Video-Guide`

אל תפתח פרויקט חדש, אל תעתיק את הנתונים לתיקייה אחרת ואל תתחיל את סבב 04.

## המשימה המחייבת

1. קרא במלואם:
   - `NEXT_ACTION.md`
   - `prompts/03_WORK_WAVE_2.md`
   - `reports/content-findings-for-work.md`
   - `MASTER_SPEC.md`
   - `AGENTS.md`
   - `QUALITY_GATES.md`
   - `DECISIONS.md`
   - `PROJECT_STATUS.md`
   - `HANDOFF_TO_CODEX.md`
   - `REVIEW_PACKET.md`
   - `schema/video.schema.json`
   - כל הקבצים תחת `data/`
   - דוחות המחקר, הדחיות וה־Audit הקיימים
   - `prompts/01_WORK_FOUNDATION_AND_WAVE_1.md`

2. ודא ש־`NEXT_ACTION.md` מפנה לסבב 03. אם קיימת סתירה, תעד אותה ב־`REVIEW_PACKET.md`, אך בצע את המשימה הנוכחית בלבד.

3. בצע את `prompts/03_WORK_WAVE_2.md` במלואו, לפי הסדר:
   - קודם Wave 1 Trust Audit מלא ל־60 הרשומות.
   - תיקון רק על בסיס ראיות.
   - אימות מוצלח של בדיוק 60.
   - רק לאחר מכן מחקר, אימות והוספה של בדיוק 70 סרטונים חדשים.
   - סיום עם בדיוק 130 רשומות מאושרות.

## כללי עצמאות

- עבוד עצמאית ואל תשאל אותי שאלות שגרתיות.
- בחר ברירות מחדל מקצועיות ותעד אותן ב־`DECISIONS.md`.
- אל תעצור לאחר הכנת רשימת מועמדים או לאחר Trust Audit.
- אם שער נכשל, תקן והריץ שוב.
- אם אין אפשרות להגיע ל־130 בלי להכניס תוכן חלש או לא מאומת, עצור ב־FAIL ותעד במדויק את הפער. אין להמציא נתונים ואין להוריד את סף האיכות.
- אם אשלח `.` או `?`, החזר סטטוס קצר והמשך אוטומטית.

## אימות תוכן מחייב

לכל רשומה קיימת שתוקנה ולכל סרטון חדש:

- אין להסתמך על כותרת או Thumbnail בלבד.
- בדוק דף YouTube, תיאור, Chapters, כתוביות או תמלול כאשר זמינים, ובמידת הצורך צפייה בחלקים רלוונטיים.
- אל תמציא משך, תאריך, כתוביות, Chapters, נקודות זמן, ערוץ, תרגיל, אזהרה או טענה לגבי תוכן.
- אל תשמור תמלול מלא, סרטון או עותק של תוכן YouTube בפרויקט.
- כתוב את הסיכומים בעברית במילים מקוריות.
- בדוק התאמה אמיתית לרכיבת אדוונצ'ר, כביש, תרגול או בטיחות.
- אל תוסיף העלאה חוזרת, כפילות, סרטון פרטי, סרטון חסום או פרסומת ללא ערך לימודי.
- סמן תוכן שיווקי בשקיפות.
- תעד את ראיות הסיווג ורמת הביטחון.
- כאשר מידע אינו ניתן לאימות, השאר אותו ריק או `null` לפי הסכמה.

## Wave 1 Trust Audit

לפני הוספת סרטון חדש:

1. בדוק מחדש את כל 31 הרשומות עם Chapters.
2. בדוק במיוחד את `yt-DY7OFizK_eo`.
3. הסר Chapter רק כאשר הוכח שאינו מתאים או שאין לו בסיס.
4. אל תמציא כותרות או נקודות זמן.
5. בדוק את כל 60 הרשומות עבור:
   - `quality_reason_he`
   - `why_watch_he`
   - `exercises_he`
   - `fit_for_he`
6. הפוך את השדות לספציפיים לסרטון על סמך ראיות, לא באמצעות תבנית.
7. תעד כל שינוי ב־`research/reports/wave-1-corrections.md`.
8. צור `research/rejected/wave-1-corrections.csv` רק אם הוסרה רשומה שלמה.
9. אם הוסרה רשומה, החלף אותה ברשומה מאומתת והחזר את הבסיס ל־60 לפני Wave 2.
10. הרץ:

```bash
python tools/validate_data.py --expected-count 60 --report reports/phase-03-wave1-validation.json
```

אין לעבור להרחבה לפני PASS מלא.

## Wave 2 — 70 סרטונים חדשים

לאחר מעבר שער 60:

- הוסף בדיוק 70 סרטונים חדשים ומאומתים.
- הגע בדיוק ל־130.
- הרחב מקורות מעבר לריכוז הקיים.
- תן עדיפות לתוכן עברי איכותי, אך לא על חשבון איכות.
- מלא קטגוריות דקות ופערי מפרט, במיוחד:
  - רוח ורוח צד.
  - רכיבת לילה.
  - רכיבה עירונית.
  - צמיגים ולחץ אוויר.
  - מתלים.
  - גשם וכביש רטוב.
  - רכיבה עם מטען ומורכב.
  - חול, בוץ, עליות, ירידות וחילוץ.
  - רכיבה איטית, בלימה ופניות.
  - אופנועי אדוונצ'ר כבדים.
- שמור איזון בין שטח, כביש, משולב, תרגול ובטיחות.
- אין מכסה מלאכותית שמחייבת הכנסת סרטון חלש.

צור ועדכן:

- `research/rejected/wave-2-rejected.csv`
- `research/reports/wave-2-report.md`
- `data/videos.json`
- `data/categories.json` ו־`data/synonyms.json` רק כאשר נדרש ועל בסיס החלטה מתועדת
- `data/learning-paths.json`
- כל דוחות ה־Audit
- `HANDOFF_TO_CODEX.md`
- `PROJECT_STATUS.md`
- `DECISIONS.md`
- `NEXT_ACTION.md`
- `REVIEW_PACKET.md`

## בדיקות סופיות מחייבות

הרץ בפועל:

```bash
python tools/validate_data.py --expected-count 130 --report reports/phase-03-data-validation.json
python tools/check_links.py --online --report reports/phase-03-link-check.json
python tools/build_audit.py
npm test
python -m unittest discover -s tests -p "test_*.py" -v
```

אם פקודה אינה זמינה טכנית, תעד את הסיבה המדויקת. אין לדווח שהיא עברה.

ודא:

- בדיוק 130 רשומות.
- 130 IDs פנימיים ייחודיים.
- 130 YouTube Video IDs ייחודיים.
- 0 נתוני דמה ו־0 Placeholder.
- כל הרשומות עוברות Schema.
- כל URL מתאים ל־Video ID.
- כל הקטגוריות, התגיות, הסרטונים הקשורים ומסלולי הלימוד מפנים ל־IDs קיימים.
- לכל רשומה תקציר עברי, רמה, תחום ותיעוד אימות.
- כל 130 הקישורים נבדקו מקוונת; כשל נבדק ולא מוסתר.
- האתר והבדיקות הטכניות אינם נשברים בעקבות 130 הרשומות.

## Git

צור ענף:

`phase-03-work-wave2`

אם הענף כבר קיים, עבוד עליו בלי למחוק היסטוריה.

צור Commit מסודר רק לאחר שכל הבדיקות עברו. אל תבצע Push או Force Push ללא Remote מאומת.

לאחר ה־Commit שמור:

```bash
git status --short --branch > reports/phase-03-git-status.txt
git log -1 --oneline > reports/phase-03-git-log.txt
git show --stat --oneline HEAD > reports/phase-03-git-show-stat.txt
git diff --check > reports/phase-03-git-diff-check.txt
```

אם Git אינו זמין, תעד זאת ב־`REVIEW_PACKET.md` ואל תמציא Hash.

## חבילת סקירה מחייבת

צור:

`reports/phase-03-review-bundle.zip`

החבילה צריכה לכלול את תיקיית הפרויקט המלאה הדרושה לביקורת, ובפרט:

- `data/`
- `schema/`
- `research/`
- `reports/` ללא קובצי ZIP אחרים
- `tools/`
- `tests/`
- `assets/`
- `index.html`
- `package.json`
- `README.md`
- `MASTER_SPEC.md`
- `AGENTS.md`
- `QUALITY_GATES.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `prompts/01_WORK_FOUNDATION_AND_WAVE_1.md`
- `prompts/03_WORK_WAVE_2.md`
- `prompts/04_CODEX_INTEGRATE_AND_QA_V2.md`
- קובצי ראיות Git, אם קיימים

צור בתוך החבילה:

`PHASE_03_REVIEW_BUNDLE_MANIFEST.md`

המניפסט יכלול:

- רשימת כל הקבצים בחבילה.
- גודל כל קובץ.
- SHA-256 לכל קובץ.
- מספר הקבצים הכולל.
- תאריך ושעת יצירה.

אל תכלול:

- `.git/`
- `node_modules/`
- `__pycache__/`
- cache
- קבצים זמניים
- תמלולים מלאים
- סרטונים או קובצי מדיה שהורדו מ־YouTube
- Secrets
- API keys
- קובצי ZIP אחרים
- Fixtures זמניים שאינם חלק בטוח ומוצהר מבדיקות

בדוק את ה־ZIP לאחר יצירתו:

- אין נתיבי `..`.
- אין קבצים חסרים מהמניפסט.
- כל ה־Hashes מתאימים.
- אין קבצים עודפים.

## מצב ומסירה

רק לאחר מעבר שער 130:

- עדכן את `PROJECT_STATUS.md` ל־3 מתוך 8 ול־37.5%.
- עדכן את `NEXT_ACTION.md` ל־Codex ול־`prompts/04_CODEX_INTEGRATE_AND_QA_V2.md`.
- אל תבצע את סבב 04.
- אל תשנה את האתר מעבר להתאמות תוכן הכרחיות.
- עצור לאחר יצירת החבילה.

בסיום הצג בצ'אט רק:

1. `PASS` או `FAIL`.
2. מספר הרשומות לפני ואחרי.
3. מספר תיקוני Wave 1.
4. מספר הסרטונים החדשים.
5. מספר בדיקות שעברו ונכשלו.
6. מספר קישורים מקוונים שעברו ונכשלו.
7. Commit hash, או הסבר ש־Git לא היה זמין.
8. הנתיב המדויק של:
   `reports/phase-03-review-bundle.zip`

לאחר מכן עצור.
