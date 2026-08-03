# משימת תיקון 02B — Codex: מוכנות להתרחבות, אמינות ו־UX

עבוד ישירות בתוך תיקיית הפרויקט המקומית הפתוחה של:

`Adventure-Riding-Video-Guide`

זוהי משימת תיקון ממוקדת לסבב 02. אין לבנות את האתר מחדש, אין להתחיל את סבב 03, אין לחפש סרטונים חדשים ואין להוסיף נתוני דמה ל־Production.

## מטרה

לתקן את החסימות שמונעות מהאתר לגדול מ־60 ל־130, 200 ו־300 סרטונים; להשלים את חיבור קובץ ההגדרות; לתקן ניהול Overlay ו־RTL; ולהכין ל־Work דוח תוכן מדויק לבדיקת האצווה הקיימת.

עבוד עצמאית. אל תשאל שאלות שגרתיות. בחר ברירות מחדל מקצועיות, תעד אותן ב־`DECISIONS.md`, והרף רק במקרה של חסימה אמיתית שאין דרך בטוחה לעקוף.

---

## 1. קריאה ובדיקת בסיס

לפני שינוי קוד, קרא במלואם:

- `MASTER_SPEC.md`
- `AGENTS.md`
- `QUALITY_GATES.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `README.md`
- `prompts/02_CODEX_BUILD_SITE_V1.md`
- `prompts/03_WORK_WAVE_2.md`
- כל הקבצים תחת `assets/`
- כל הקבצים תחת `data/`
- כל הקבצים תחת `schema/`
- כל הקבצים תחת `tests/`
- כל הקבצים תחת `tools/`
- כל הדוחות תחת `reports/`

לאחר הקריאה, הרץ ושמור את תוצאות הבסיס:

```bash
python tools/validate_data.py
npm test
python -m unittest discover -s tests -p "test_*.py" -v
python tools/validate_wave1.py
python tools/build_audit.py
```

אם בדיקת בסיס נכשלת, תעד אותה ותקן כחלק מהמשימה. אל תדווח על בדיקה שלא הורצה.

---

## 2. חסימת Scalability — הסר תלות במספר 60

### 2.1 Runtime

מצא והסר כל תנאי Runtime שמחייב שמספר הרשומות יהיה בדיוק 60.

בפרט, אין להשאיר לוגיקה מהסוג:

```js
videos.length !== 60
```

האתר צריך לטעון כל מערך לא־ריק שעבר את מבנה הנתונים הנדרש.

דרישות:

- הספירה בדף הבית, בספרייה, בכפתורי המסננים ובטקסטי התוצאה תיגזר תמיד מ־`state.videos.length` או ממספר התוצאות.
- ב־HTML ההתחלתי השתמש ב־`—` או ערך ניטרלי, לא ב־60.
- הפרד בין:
  - מספר התוכן הכולל.
  - גודל עמוד או `visibleLimit`.
- הגדר קבועים בעלי שם כגון:
  - `INITIAL_VISIBLE_LIMIT`
  - `LOAD_MORE_BATCH_SIZE`
- אין להשתמש במספר 60 כתחליף לגודל עמוד.
- “טען עוד” חייב לעבוד עם 130 ו־300 רשומות.
- האתר חייב להציג הודעת שגיאה ברורה אם הנתונים ריקים, אינם Array או אינם תקינים — אך לא בגלל שהמספר שונה מ־60.

### 2.2 כלי אימות

שנה את `tools/validate_data.py` כך ש:

- ברירת המחדל מאמתת שלמות נתונים בלי לדרוש מספר קבוע.
- קיימת אפשרות CLI:

```bash
python tools/validate_data.py --expected-count 60
python tools/validate_data.py --expected-count 130
python tools/validate_data.py --minimum-count 200
```

- `--expected-count` ו־`--minimum-count` לא יופעלו יחד.
- פלט ה־JSON וה־Console יתעד את ציפיית הספירה שהופעלה.
- כל שאר בדיקות ה־Schema, IDs, URLs, הפניות, קטגוריות ומסלולים נשארות פעילות.

טפל ב־`tools/validate_wave1.py` כך שלא יכשיל את הפרויקט לאחר הרחבת המאגר:

- אפשרות מועדפת: הפוך אותו לכלי Legacy מפורש שמקבל `--expected-count`, או גורם לו להאציל ל־`validate_data.py`.
- עדכן README כך שיהיה ברור שאין להריץ בדיקת Wave 1 כבדיקת Release אחרי סבב 03.
- אין להשאיר כלי פעיל שמניח תמיד 60.

### 2.3 בדיקות

עדכן את הבדיקות כך שלא יהיו תלויות גלובלית ב־60:

- `tests/data-integrity.test.mjs`
- `tests/filters.test.mjs`
- `tests/smoke.test.mjs`
- `tests/test_tools.py`
- כל בדיקה נוספת שמקבעת 60.

מותר לבדוק שהמאגר הנוכחי כולל 60 באמצעות פרמטר Phase־specific, אך הלוגיקה הכללית חייבת לעבוד בכל גודל.

צור בדיקות Scalability המבוססות על Fixture זמני בלבד:

- 130 רשומות.
- 300 רשומות.

אסור להכניס רשומות מזויפות ל־`data/videos.json`.

ה־Fixture יכול להיווצר בזמן הבדיקה מתוך רשומות חוקיות עם IDs זמניים וייחודיים, או באמצעות Factory ייעודי תחת `tests/fixtures/`. הוא לא ייכלל ב־Production ולא יוצג למשתמש.

בדוק לפחות:

- הכנה ואינדוקס של 130 ו־300 רשומות.
- חיפוש.
- שילוב מסננים.
- מיון.
- ספירת תוצאות.
- Pagination / Load more.
- שאין שגיאת Runtime.
- שאין כפילויות ב־DOM.
- זמן סינון סביר; תעד מדידה, אך אל תיצור סף שביר התלוי בחומרה.

---

## 3. חבר במלואו את `data/site-config.json`

ממש בפועל את כל השדות המתועדים:

### `site_name_he`

- שם המותג בכותרת האתר.
- `document.title`.
- `<meta name="description">` או תיאור מותאם מה־Config, אם קיים.
- מקומות נוספים המסומנים ב־`data-site-name`.

### `author_name`

- הצגה במיקום הקיים.
- הסתרה נקייה אם ריק.

### `community_name`

- הוסף אלמנט אמיתי עם `data-community-name`.
- הצג אותו רק כאשר אינו ריק.
- אל תציג Placeholder מומצא.

### `logo_path`

- אם הוגדר נתיב יחסי בטוח תחת הפרויקט, הצג `<img>` בכותרת ובמקום המתאים.
- אם ריק או אם טעינת התמונה נכשלת, השתמש בסמל המובנה הקיים כ־Fallback.
- אין לטעון כתובת `javascript:`, `data:` לא צפויה או נתיב מחוץ לפרויקט.
- הוסף `alt` מתאים.

### `contact` ו־`safety_warning_he`

- ודא שהם ממשיכים לעבוד.
- אל תציג כתובת קשר מומצאת אם השדה ריק.

הוסף בדיקות אוטומטיות עם Config זמני המאמתות:

- שם אתר מותאם.
- שם קהילה.
- לוגו מקומי.
- Fallback כאשר `logo_path` ריק או שגוי.
- הסתרת שדות ריקים.

עדכן את README בהתאם להתנהגות בפועל בלבד.

---

## 4. תקן Overlay, גלילת רקע ומיקוד

קיים CSS עבור:

- `body[data-modal-open="true"]`
- `body[data-filters-open="true"]`
- `body[data-menu-open="true"]`

אך ה־JavaScript אינו מעדכן אותם. צור מנהל Overlay מרכזי ופשוט.

דרישות:

### Video dialog ו־Rights dialog

- בעת פתיחה, נעל גלילת רקע.
- שמור את מיקום הגלילה.
- בעת סגירה, החזר את הגלילה בלי קפיצה.
- החזר מיקוד לפקד שפתח את החלון.
- `Escape` יסגור בצורה תקינה.
- ניקוי URL והיסטוריה יישאר תקין.
- לא יישאר `iframe` לאחר סגירת חלון הסרטון.

### Mobile menu ו־Filter drawer

- בעת פתיחה במובייל, נעל גלילת רקע.
- `Escape` יסגור.
- מעבר לתצוגה אחרת יסגור וינקה State.
- מיקוד יעבור לפקד הראשון הרלוונטי ויחזור לכפתור הפתיחה בסגירה.
- כאשר אפשר, השתמש ב־`inert` או פתרון שקול למניעת אינטראקציה עם הרקע.
- ב־Desktop אין לנעול גלילה בגלל תפריט הניווט הרגיל.

### בדיקות

בדוק ב־390x844:

- אין שני אזורי גלילה פעילים במקביל בחלון הסרטון.
- הרקע אינו זז בזמן גלילת Dialog/Drawer.
- סגירה ב־Escape עובדת.
- המיקוד חוזר למקום הנכון.
- אין גלילה אופקית.
- אין Console errors או warnings.

---

## 5. תקן Bidi במידע משולב

אל תרנדר שם ערוץ, משך ותאריך כמחרוזת טקסט מעורבת אחת.

צור רכיבי DOM נפרדים:

- שם ערוץ.
- משך.
- תאריך.

השתמש ב־`<bdi dir="auto">`, `dir="ltr"` עבור זמן/תאריך כאשר מתאים, או CSS עם `unicode-bidi: isolate`.

החל את אותו עיקרון בכל מקום שבו עברית, אנגלית, מספרים ותאריך משולבים.

בדוק בתצוגת Mobile ו־Desktop עם:

- שם ערוץ באנגלית.
- כותרת בעברית.
- תאריך מספרי.
- משך הכולל דקות ושניות.

---

## 6. ממצאי אמינות תוכן — אל תמציא תיקון

קודקס אינו אמור לכתוב מחדש סיכומים, דירוגים, תרגילים או Chapters על סמך ניחוש.

צור:

`reports/content-findings-for-work.md`

הדוח חייב לכלול לפחות:

### 6.1 Chapters

- זיהוי הרשומה `yt-DY7OFizK_eo`.
- הצגת חוסר ההתאמה בין נושא הסרטון “How to Ride a Motorcycle in the Rain” לבין הכותרות:
  - `Can-Am Spyder F3-S Review`
  - `KTM 1290 Super Adventure R Review`
  - `Motorcycle Life Hacks`
  - `Yamaha SCR950 Review`
- דרישה ל־Work לבדוק מחדש את כל 31 הרשומות עם Chapters.
- איסור להציג נקודת זמן כמאומתת בלי מקור ברור.
- המלצה להוסיף בעתיד Provenance לכל Chapter:
  - `youtube_chapter`
  - `transcript_timestamp`
  - `manual_visual_review`
- אין להוסיף Provenance שלא אומת.

עד ש־Work משלים את הבדיקה, שנה ב־UI את הכותרת:

`פרקים מאומתים`

לכותרת שמרנית:

`פרקים / נקודות זמן מתועדות`

### 6.2 שדות תבניתיים

תעד:

- `quality_reason_he` כולל רק חמישה נוסחים שונים ב־60 רשומות.
- `why_watch_he` הוא נוסח תבניתי המבוסס בעיקר על החלפת הכותרת.
- `exercises_he` הוא נוסח תבניתי גם בסרטונים שאינם מציגים תרגיל.
- `fit_for_he` כללי מאוד.

דרוש מ־Work:

- לבדוק את 60 הרשומות הקיימות על סמך תיאור, Chapters אמיתיים, תמלול וצפייה.
- לכתוב `quality_reason_he` שמסביר את הציון הספציפי, כולל חוזקות ומגבלות.
- לכתוב `why_watch_he` שמסביר ערך ייחודי ולא חוזר על הכותרת.
- לכתוב Exercises אמיתיים רק כאשר הסרטון מציג תרגול; אחרת להשתמש במערך ריק או בנוסח עובדתי מתאים לפי ה־Schema.
- לחדד `fit_for_he` לפי מיומנות קודמת, סוג אופנוע ותנאי תרגול.
- לא להמציא מידע חסר.

### 6.3 גיוון וכיסוי

תעד:

- MOTOTREK: 15.
- Bret Tkacs ADV: 11.
- יחד: 26 מתוך 60.
- 41 מתוך 60 מסומנים עם תוכן שיווקי.
- 9 מתוך 60 בעברית.
- קטגוריות דקות: רוח, לילה, עירוני, צמיגים, מתלים ונושאים נוספים שמופיעים בדוחות.

אין למחוק סרטון איכותי רק כדי להשיג מכסה. בסבב 03 יש להעדיף גיוון מקורות, עברית וקטגוריות חסרות, בלי לפגוע באיכות.

---

## 7. עדכן את פרומפט Work לסבב 03

עדכן את:

`prompts/03_WORK_WAVE_2.md`

כך שהמשימה תהיה גדולה ומלאה, ללא מיקרו־ניהול מצד המשתמש.

לפני הוספת 70 סרטונים חדשים, Work חייב לבצע “Wave 1 Trust Audit” על 60 הקיימים:

1. לקרוא את `reports/content-findings-for-work.md`.
2. לבדוק את כל 31 מערכי Chapters.
3. להסיר Chapters שאינם מתאימים או שאין להם בסיס.
4. לא להמציא נקודות זמן.
5. לתקן את השדות התבניתיים לפי ראיות.
6. לתעד כל שינוי קיים ב:
   - `research/reports/wave-1-corrections.md`
   - `research/rejected/wave-1-corrections.csv` כאשר הוסרה רשומה.
7. להריץ:
   ```bash
   python tools/validate_data.py --expected-count 60
   ```
   לאחר סיום תיקון 60 הרשומות.
8. רק אז להוסיף 70 סרטונים חדשים ולהגיע בדיוק ל־130.
9. להריץ:
   ```bash
   python tools/validate_data.py --expected-count 130
   ```
10. להרחיב עברית וגיוון מקורות, אך לא להוסיף תוכן חלש לצורך מכסה.
11. לעדכן מסלולי לימוד ודוחות רק עם IDs קיימים.
12. ליצור `REVIEW_PACKET.md` מלא ולשנות את `NEXT_ACTION.md` לסבב 04.

אל תבצע את משימת Work בעצמך. עדכן רק את הפרומפט ואת מסמכי המסירה.

---

## 8. בדיקות קבלה לאחר התיקון

הרץ מחדש:

```bash
python tools/validate_data.py --expected-count 60
npm test
python -m unittest discover -s tests -p "test_*.py" -v
python tools/build_audit.py
```

בנוסף:

- הרץ בדיקות Scalability של 130 ו־300.
- הפעל את האתר בשרת מקומי.
- בדוק 1440x900 ו־390x844.
- בדוק שמונת החיפושים:
  - חול
  - בוץ
  - פניות בכביש
  - בלימת חירום
  - הרמת אופנוע
  - גשם
  - עלייה תלולה
  - רכיבה איטית
- בדוק חיפוש באנגלית.
- בדוק שילוב של לפחות שלושה מסננים.
- בדוק מועדפים, נצפה והתקדמות לאחר רענון.
- בדוק שאין iframe לפני לחיצה.
- בדוק iframe מ־`youtube-nocookie.com` לאחר לחיצה.
- בדוק שאין iframe לאחר סגירה.
- בדוק Config מותאם באמצעות Fixture מקומי.
- בדוק Body scroll lock, Escape ו־Focus return.
- בדוק Bidi.
- בדוק שאין Console errors/warnings.
- בדוק שאין Horizontal overflow.

צלם מחדש ושמור לפחות:

- `reports/screenshots/phase-02b-desktop-home.png`
- `reports/screenshots/phase-02b-desktop-library.png`
- `reports/screenshots/phase-02b-desktop-video-dialog.png`
- `reports/screenshots/phase-02b-mobile-home.png`
- `reports/screenshots/phase-02b-mobile-library.png`
- `reports/screenshots/phase-02b-mobile-video-dialog.png`
- `reports/screenshots/phase-02b-mobile-filter-drawer.png`
- `reports/screenshots/phase-02b-config-customization.png`

אין לדווח על צילום או בדיקה שלא בוצעו בפועל.

---

## 9. Git, תיעוד וחבילת סקירה

צור ענף:

`phase-02b-scalability-trust-repair`

אם הענף כבר קיים, עבוד עליו בלי למחוק היסטוריה.

עדכן:

- `README.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `REVIEW_BUNDLE_MANIFEST.md`
- `reports/test-summary.json`
- `reports/browser-acceptance.json`
- `reports/content-findings-for-work.md`
- `prompts/03_WORK_WAVE_2.md`

ב־`PROJECT_STATUS.md` השאר את הפרויקט בסבב 2/8 עד אישור הביקורת. אל תסמן את סבב 03 כבוצע.

ב־`NEXT_ACTION.md` הפנה ל־Work ול־`prompts/03_WORK_WAVE_2.md`, אך ציין שההפעלה מותרת רק לאחר אישור חבילת 02B.

שמור תחת `reports/`:

```bash
git status --short --branch > reports/git-status.txt
git log -1 --oneline > reports/git-log.txt
git show --stat --oneline HEAD > reports/git-show-stat.txt
git diff --check > reports/git-diff-check.txt
```

שים לב: לאחר ה־Commit, הפק את קובצי ה־Git מחדש כדי שישקפו את ה־Commit הסופי. אם `git diff --check` אינו ריק, תקן לפני מסירה.

צור Commit מסודר. אל תבצע Push או Force Push ללא Remote מאומת.

צור:

`reports/phase-02b-review-bundle.zip`

ה־ZIP חייב לכלול:

- כל קובצי האתר.
- `assets/`
- `data/`
- `schema/`
- `tests/`
- `tools/`
- `prompts/03_WORK_WAVE_2.md`
- כל דוחות Phase 02B.
- כל צילומי המסך Phase 02B.
- `README.md`
- `MASTER_SPEC.md`
- `QUALITY_GATES.md`
- `PROJECT_STATUS.md`
- `DECISIONS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `REVIEW_BUNDLE_MANIFEST.md`
- ארבעת קובצי הראיות של Git.

אל תכלול:

- `.git/`
- `node_modules/`
- `__pycache__/`
- cache
- קבצים זמניים
- Secrets
- API keys
- Fixture זמני שנוצר רק להרצה, אלא אם הוא קובץ בדיקה בטוח ומוצהר.

---

## 10. תנאי סיום

המשימה נחשבת מלאה רק כאשר:

- האתר נטען עם 60 בלי תנאי קשיח.
- בדיקות Fixture של 130 ו־300 עוברות.
- אין טקסט סטטי מטעה של 60.
- `validate_data.py --expected-count` עובד.
- Config מיושם בפועל.
- גלילת רקע נעולה בכל Overlay במובייל.
- Escape ו־Focus return עובדים.
- Bidi תקין.
- כותרת Chapters שמרנית.
- דוח התוכן ל־Work קיים.
- פרומפט סבב 03 עודכן.
- כל הבדיקות עברו.
- הצילומים נוצרו.
- Commit נוצר.
- `reports/phase-02b-review-bundle.zip` נוצר.

בסיום הצג בצ'אט רק:

1. `PASS` או `FAIL`.
2. מספר בדיקות שעברו ונכשלו.
3. האם Fixtures של 130 ו־300 עברו.
4. Commit hash.
5. הנתיב המדויק של:
   `reports/phase-02b-review-bundle.zip`

לאחר מכן עצור. אין להתחיל את סבב 03.
