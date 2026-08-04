# Phase 03B — Work: תיקון אמינות תוכן, Chapters וחיפוש עברי

עבוד ישירות בתוך תיקיית הפרויקט המקומית הפתוחה:

`Adventure-Riding-Video-Guide-Starter`

זהו סבב תיקון תוכן ממוקד. אין לפתוח פרויקט חדש, אין לבנות מחדש את האתר, אין להתחיל את Phase 04 ואין להגדיל את המאגר מעבר ל־130.

## מטרה מחייבת

לתקן את שער אמינות התוכן של Phase 03:

1. לבצע ביקורת מקור פרטנית אמיתית ל־60 רשומות Wave 1.
2. להסיר את הנוסחים שנוצרו באמצעות תבניות.
3. לבדוק את 70 רשומות Wave 2, בדגש על 18 רשומות המבוססות תיאור בלבד.
4. לאצור את כל ה־Chapters כך שיוצגו רק נקודות זמן לימודיות.
5. לבצע חיפוש עברי ממוקד ומתועד לקראת Phase 05.
6. לסיים עם בדיוק 130 רשומות מאומתות ועם חבילת סקירה מלאה.

עבוד עצמאית. אל תשאל שאלות שגרתיות. אל תעצור לאחר הכנת דוח או רשימת מועמדים. כאשר נמצא כשל, תקן והריץ מחדש. אין להמציא עובדות ואין להוריד את סף האיכות.

---

## 1. קריאת מקור האמת

לפני שינוי כלשהו, קרא במלואם:

- `MASTER_SPEC.md`
- `AGENTS.md`
- `QUALITY_GATES.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- `prompts/03_WORK_WAVE_2.md`
- `prompts/PROMPT_03_WORK_EXECUTE_AND_PACKAGE_HE.md`
- `reports/content-findings-for-work.md`
- `research/reports/wave-1-corrections.md`
- `research/reports/wave-2-report.md`
- `reports/phase-03-wave1-youtube-audit.json`
- `research/approved/wave-2-youtube-metadata.json`
- `reports/phase-03-link-check.json`
- `schema/video.schema.json`
- כל הקבצים תחת `data/`
- כל הקבצים תחת `research/`
- כל כלי הבדיקה תחת `tools/`
- כל הבדיקות תחת `tests/`

קרא גם את הקובץ הזה במלואו לפני תחילת העבודה.

---

## 2. בדיקות בסיס ושמירת Snapshot

לפני שינוי תוכן:

```bash
python tools/validate_data.py --expected-count 130 --report reports/phase-03b-baseline-validation.json
npm test
python -m unittest discover -s tests -p "test_*.py" -v
python tools/build_audit.py --link-report reports/phase-03-link-check.json
```

צור:

- `reports/phase-03b-before-sha256.json`
- `reports/phase-03b-template-match-before.json`

`phase-03b-template-match-before.json` חייב לתעד באמצעות בדיקה משוחזרת:

- כמה מ־60 רשומות Wave 1 תואמות בדיוק לפונקציית `why_watch()` שב־`tools/apply_phase03_wave1.py`.
- כמה תואמות ל־`fit_for()`.
- כמה תואמות ל־`quality_reason()`.
- כמה תואמות למילון `EXERCISES`.

המספר הצפוי לפי הביקורת החיצונית הוא 60/60 בכל ארבעת הסעיפים. אם מתקבל מספר אחר, תעד את ההבדל ואל תסתיר אותו.

סמן בראש `tools/apply_phase03_wave1.py` באופן ברור:

```text
HISTORICAL ONE-TIME MIGRATION.
NOT AN AUTHORING OR CONTENT-AUDIT TOOL.
DO NOT REUSE TO WRITE TRUST FIELDS.
```

אין למחוק את הקובץ ואין לשכתב היסטוריה.

---

## 3. איסור על יצירת תוכן תבניתי

בשלב זה אסור:

- להשתמש ברשימת תבניות מסתובבת.
- להחליף שמות נושא בתוך משפט קבוע.
- לחבר אוטומטית את שלוש נקודות הלמידה למשפט `why_watch_he`.
- ליצור `fit_for_he` מתוך מיפוי אוטומטי של רמה, משקל ותוואי בלבד.
- ליצור `quality_reason_he` מתוך ציון, סוג ראיה ו־contains_marketing בלבד.
- להשתמש ב־LLM או בסקריפט כדי לכתוב 60 נוסחים ללא פתיחת מקור פרטנית.
- להכריז על נוסח כייחודי רק מפני שהוחלפו בו מילים.

מותר להשתמש בסקריפטים רק עבור:

- שלמות נתונים.
- Diff.
- איתור כפילויות.
- דוחות.
- בדיקת תבניות.
- בדיקת קישורים.
- אריזת החבילה.

כתיבת תוכן חייבת להיות מבוססת מקור לכל רשומה.

---

## 4. Ledger ראיות לכל 130 הרשומות

צור:

`research/reports/phase-03b-evidence-ledger.csv`

שדות חובה:

- `id`
- `youtube_video_id`
- `youtube_url`
- `wave`
- `language`
- `source_type`
- `evidence_checked`
- `description_checked`
- `youtube_chapters_checked`
- `captions_or_transcript_checked`
- `visual_segments_checked`
- `visual_timestamp_ranges`
- `metadata_match`
- `chapter_curation_result`
- `content_fields_reviewed`
- `fields_changed`
- `classification_confidence_before`
- `classification_confidence_after`
- `review_notes_he`
- `reviewed_at`

כללי Ledger:

- שורה אחת לכל אחת מ־130 הרשומות.
- אין לשמור תמלול מלא.
- אין לצטט יותר ממשפט קצר מן המקור.
- `visual_timestamp_ranges` יכיל רק טווחים שנצפו בפועל, לא זמנים מומצאים.
- כאשר לא בוצעה צפייה, רשום `not_performed` ולא ניסוח עמום.
- כאשר כתוביות קיימות אך לא נקראו, אין לסמן `transcript`.
- כל שינוי ב־JSON חייב להיות ניתן למעקב מן ה־Ledger.

---

## 5. ביקורת אמיתית ל־60 רשומות Wave 1

עבור כל אחת מ־60 הרשומות הראשונות:

1. פתח את דף YouTube.
2. בדוק מטא־דאטה, תיאור ו־Chapters.
3. השתמש בתמלול או כתוביות כאשר הם זמינים.
4. כאשר הראיות עדיין אינן מספיקות, צפה בחלקים ממוקדים.
5. בדוק מחדש:
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
   - `verification`
6. שנה רק שדה שמצריך תיקון.
7. אל תשנה עובדה נכונה רק כדי להראות פעילות.

### דרישות ניסוח

#### `why_watch_he`

- להסביר מה הערך הייחודי של הסרטון לעומת סרטונים אחרים באותה קטגוריה.
- לא לחזור על הכותרת.
- לא לחבר אוטומטית שלוש נקודות למידה למשפט.
- לציין מגבלה כאשר הסרטון צר, ישן, שיווקי או תלוי בדגם.

#### `fit_for_he`

- לתאר ניסיון קודם אמיתי שנדרש.
- לציין סוג אופנוע או תוואי רק כאשר הם רלוונטיים לסרטון.
- לא להשתמש בסיומת בטיחות זהה לעשרות רשומות.
- להבחין בין מי שיכול לצפות לבין מי שיכול לתרגל.

#### `quality_reason_he`

- להסביר מה הופך את הסרטון לטוב או מוגבל.
- לציין איכות מקור, מבנה הסבר, הדגמה, בטיחות ומגבלות.
- הציון אינו יכול להישען רק על מספר Chapters.
- שיווק אינו הורדה אוטומטית בציון, אך חייב להיות מסומן.

#### `exercises_he`

- להוסיף תרגיל רק אם הוא מוצג או נתמך במפורש.
- אם הסרטון עיוני בלבד, להשאיר `[]`.
- אין להמציא Drill “בטוח” שנשמע הגיוני אך אינו מופיע במקור.

#### `verification.notes_he`

- לכתוב מה נבדק בפועל ומה לא.
- לציין אי־ודאות.
- לא להשתמש בהערה זהה או כמעט זהה לכל הרשומות.

צור:

`research/reports/phase-03b-wave1-content-corrections.md`

הדוח יכלול לכל רשומה:

- מקור הראיות.
- שדות שנבדקו.
- שדות ששונו.
- נימוק קצר.
- מגבלות שנותרו.

---

## 6. בדיקת 70 רשומות Wave 2

בדוק את כל 70 הרשומות החדשות לפחות ברמת התאמה בין:

- תיאור.
- Chapters.
- תקציר.
- נקודות למידה.
- סיווג.
- רמה.
- סיכון.
- התאמה לאדוונצ'ר או כביש.

### 18 רשומות המבוססות תיאור בלבד

עבור כל רשומה שבה:

```json
"content_evidence_types": ["description"]
```

נסה להשיג ראיה נוספת:

- כתוביות.
- תמלול זמין.
- צפייה ממוקדת.
- תיאור רשמי מפורט במיוחד ממקור בטיחות מוסדי.

כאשר אין ראיה נוספת:

- השאר `classification_confidence` ברמה `medium`, אלא אם מדובר בתרחיש רשמי קצר שהתיאור מפרט במלואו.
- צמצם טענות שאינן מופיעות בתיאור.
- אל תציג רשימת שלבים או טכניקה מפורטת שאין לה ראיה.

בדוק במיוחד:

- בלימת חירום.
- חציית מים.
- חילוץ מחול.
- רוח צד.
- ABS בשטח.
- מעבר מכשולים.
- סרטוני Enduro קלים שמוצגים כמקור לאדוונצ'ר כבד.

כאשר סרטון Enduro נשמר:

- כתוב במפורש אילו עקרונות ניתנים להעברה.
- כתוב מה אינו מועבר אוטומטית לאופנוע אדוונצ'ר כבד.
- אל תסווג אותו כמקור כללי לאדוונצ'ר בלי הסתייגות.

צור:

`research/reports/phase-03b-wave2-content-audit.md`

---

## 7. אוצרות Chapters לכל המאגר

בדוק את כל:

- 82 הרשומות עם Chapters.
- 589 אובייקטי Chapter.

המטרה אינה להעתיק את כל חלוקת YouTube. המטרה היא לשמור נקודות זמן חשובות ללמידה ולניווט.

### יש לבדוק ולהסיר כאשר אינם לימודיים

- `Intro`
- `Outro`
- `Sponsor`
- `Subscribe`
- `Welcome`
- `Conclusion`
- `Final thoughts`
- `Bloopers`
- פתיח נופי.
- קטע מוזיקלי.
- קידום ערוץ, Patreon, חנות או מוצר.
- סיכום שאינו מוסיף נקודת ניווט שימושית.

אל תסיר באופן עיוור לפי מילה בלבד. בדוק את ההקשר. עם זאת, פרק גנרי שאינו עוזר לרוכב למצוא חומר לימודי אינו צריך להישמר.

כללים:

- אין לשנות `start_seconds`.
- אין לשנות `end_seconds`.
- אין לתרגם או לשכתב את `title` של Chapter שמקורו ב־YouTube.
- אין להמציא Chapter חלופי.
- מותר להסיר אובייקט מן הרשומה.
- שמור רק Chapters התואמים למשך הסרטון ולסדר המקור.

צור:

`research/reports/phase-03b-chapter-curation.csv`

שדות:

- `video_id`
- `chapter_start`
- `chapter_end`
- `chapter_title`
- `decision`
- `reason_he`
- `source_verified`
- `reviewed_at`

צור גם דוח סיכום:

`reports/phase-03b-chapter-summary.json`

הדוח יכלול:

- מספר Chapters לפני.
- מספר לאחר.
- מספר שהוסרו.
- חלוקה לפי סיבה.
- מספר סרטונים שנשארו ללא Chapters.
- 0 נקודות זמן מומצאות.

---

## 8. חיפוש עברי ממוקד ומתועד

בצע חיפוש ייעודי בעברית, לא רק חיפוש כללי באנגלית.

### מינימום תהליך

- בדוק לפחות 30 מועמדים עבריים ייחודיים.
- חפש לפי נושאים, ערוצים ובתי ספר.
- אל תאשר סרטון רק משום שהוא בעברית.
- אל תפסול סרטון משום שאין לו Chapters; בדוק תיאור, כתוביות וצפייה ממוקדת.
- אל תכניס סרטון קורס או פרסומת שאין בו ערך הדרכתי ממשי.
- בשלב זה אל תגדיל את Production מעבר ל־130.

### Seeds שחובה לבדוק

בדוק לפחות את מזהי YouTube הבאים, בלי להניח שהם ראויים:

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

בדוק גם ערוצים ומקורות כגון:

- ProRiding Israel.
- Cohen Adventure / צביקה כהן השטח.
- ADV Moto Life.
- מדריכי רכיבה ישראליים נוספים.
- בתי ספר או גופי בטיחות בישראל.

צור:

`research/reports/hebrew-candidate-backlog.csv`

שדות:

- `youtube_video_id`
- `youtube_url`
- `title`
- `channel`
- `topic`
- `evidence_checked`
- `quality_assessment`
- `marketing_assessment`
- `decision`
- `decision_reason_he`
- `recommended_phase`
- `last_checked`

ערכי `decision`:

- `strong_candidate`
- `hold_more_evidence`
- `reject`
- `already_in_production`

צור גם:

`research/reports/phase-05-hebrew-and-coverage-plan.md`

התוכנית צריכה:

- להסביר כיצד לשאוף להגיע לפחות ל־30 סרטונים בעברית עד מאגר 200, בלי להוריד איכות.
- להציג כמה מועמדים חזקים קיימים בפועל.
- להציג פערים לפי נושא.
- לציין במפורש אם היעד אינו ריאלי, עם ראיות ולא עם אמירה כללית.

שני סרטוני JAF ביפנית:

- אינם נספרים כחלק מיעד העברית–אנגלית.
- ניתן להשאירם רק אם כתוביות אנגלית פעילות והערך שלהם ייחודי.
- תעד את ההצדקה ב־Ledger.

---

## 9. בדיקת תבניות לאחר התיקון

צור כלי Audit בלבד:

`tools/content_quality_lint.py`

הכלי לא משנה נתונים.

הוא חייב לדווח:

- התאמות מדויקות לתבניות ההיסטוריות של Wave 1.
- טקסטים זהים.
- טקסטים כמעט זהים מעל סף מתועד.
- פרקי Chapter גנריים.
- ספירת שפות.
- ריכוז ערוצים.
- שיעור תוכן שיווקי.
- רשומות מבוססות תיאור בלבד.
- רשומות ברמת ביטחון בינונית.
- קטגוריות עם פחות משלושה סרטונים.
- סרטונים שאינם בעברית או באנגלית.

צור:

- `reports/phase-03b-content-quality-lint.json`
- `reports/phase-03b-content-quality-lint.html`

תנאי מחייב:

- 0 מתוך 60 `why_watch_he` תואמים למחולל ההיסטורי.
- 0 מתוך 60 `fit_for_he` תואמים למחולל ההיסטורי.
- 0 מתוך 60 `quality_reason_he` תואמים למחולל ההיסטורי.
- מותר ש־`exercises_he=[]` יישאר כאשר אין תרגיל, אך ההחלטה חייבת להיות מתועדת ב־Ledger.
- אין Exact Duplicates בשדות ההסבר.
- כל Near Duplicate דורש בדיקה והצדקה.

הוסף בדיקות יחידה לכלי. אין להשתמש בכלי ככותב תוכן.

---

## 10. שמירת 130 רשומות

בסיום חייבות להיות בדיוק 130 רשומות.

אם רשומה אינה ניתנת לאימות:

1. העבר אותה ל:
   `research/rejected/phase-03b-removed.csv`
2. תעד את הסיבה והראיות.
3. החלף אותה ברשומה מאומתת באיכות שווה או טובה יותר.
4. מותר לתת עדיפות למועמד עברי חזק.
5. אין להוסיף מעבר ל־130.
6. אין להסיר רשומה רק כדי לשנות סטטיסטיקה.

צור:

`reports/phase-03b-id-diff.json`

---

## 11. בדיקות סופיות

הרץ בפועל:

```bash
python tools/validate_data.py --expected-count 130 --report reports/phase-03b-data-validation.json
python tools/content_quality_lint.py --report reports/phase-03b-content-quality-lint.json --html reports/phase-03b-content-quality-lint.html
python tools/check_links.py --online --report reports/phase-03b-link-check.json
python tools/build_audit.py --link-report reports/phase-03b-link-check.json
npm test
python -m unittest discover -s tests -p "test_*.py" -v
```

הפעל את האתר מקומית ובצע Smoke בסיסי:

- כל 130 הרשומות נטענות.
- שמונת החיפושים בעברית מחזירים תוצאה ישירה ורלוונטית:
  - חול
  - בוץ
  - פניות בכביש
  - בלימת חירום
  - הרמת אופנוע
  - גשם
  - עלייה תלולה
  - רכיבה איטית
- חיפוש באנגלית עובד.
- שילוב של שלושה מסננים עובד.
- אין שגיאות JavaScript.
- אין iframe לפני לחיצה.
- iframe נוצר מ־`youtube-nocookie.com` אחרי לחיצה.
- iframe מוסר בסגירה.

אין לדווח על בדיקה שלא בוצעה.

---

## 12. מסמכים ומצב

עדכן:

- `README.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`

ב־`PROJECT_STATUS.md` כתוב:

- Phase 03B הושלם וממתין לביקורת חיצונית.
- Production נשאר 130.
- Phase 04 לא התחיל.
- אל תסמן 4/8.

ב־`NEXT_ACTION.md`:

- הפנה ל־Codex ול־`prompts/04_CODEX_INTEGRATE_AND_QA_V2.md`.
- כתוב במפורש שההפעלה אסורה עד אישור `phase-03b-review-bundle.zip`.

אל תבצע את Phase 04.

---

## 13. Git

צור ענף:

`phase-03b-content-integrity-repair`

אל תמחק היסטוריה ואל תבצע Force Push.

לפני Commit:

```bash
git diff --check
```

צור Commit מסודר.

לאחר ה־Commit שמור:

```bash
git status --short --branch > reports/phase-03b-git-status.txt
git log -1 --oneline > reports/phase-03b-git-log.txt
git show --stat --oneline HEAD > reports/phase-03b-git-show-stat.txt
git diff --check > reports/phase-03b-git-diff-check.txt
```

אל תמציא Commit Hash אם Git אינו זמין.

הוסף ל־`.gitignore` דוחות ZIP שנוצרים ב־`reports/`, כדי שחבילות סקירה ישנות לא ילכלכו את סטטוס Git. אל תמחק חבילת משתמש קיימת בלי צורך.

---

## 14. חבילת סקירה

צור:

`reports/phase-03b-review-bundle.zip`

החבילה חייבת לכלול:

- האתר וה־assets.
- כל `data/`.
- `schema/`.
- `tests/`.
- `tools/`.
- כל דוחות Phase 03B.
- כל `research/reports/` הרלוונטיים.
- Backlog עברי.
- Ledger הראיות.
- דוחות תיקוני Wave 1 ו־Wave 2.
- דוח אוצרות Chapters.
- דוח Lint.
- קובצי ראיות Git.
- `README.md`
- `MASTER_SPEC.md`
- `QUALITY_GATES.md`
- `DECISIONS.md`
- `PROJECT_STATUS.md`
- `NEXT_ACTION.md`
- `HANDOFF_TO_CODEX.md`
- `REVIEW_PACKET.md`
- הפרומפט הנוכחי.

צור:

`PHASE_03B_REVIEW_BUNDLE_MANIFEST.md`

המניפסט יכלול:

- כל קבצי ה־Payload.
- גודל.
- SHA-256.
- מספר קבצים.
- זמן יצירה UTC.

בדוק את ה־ZIP לאחר יצירתו:

- אין `..`.
- אין קובץ חסר.
- אין קובץ עודף.
- כל Hash מתאים.
- אין ZIP אחר בתוך ה־ZIP.
- אין `.git/`.
- אין `node_modules/`.
- אין תמלולים מלאים.
- אין סרטון, שמע או כתוביות שהורדו.
- אין Secrets או API keys.

---

## 15. תנאי סיום

המשימה נחשבת PASS רק כאשר:

- Production כולל בדיוק 130 רשומות.
- כל 130 עוברות Schema.
- כל 130 הקישורים נבדקו מקוונת.
- 60 רשומות Wave 1 עברו ביקורת מקור פרטנית.
- 0 שדות Trust תואמים למחוללי התבניות ההיסטוריים.
- 70 רשומות Wave 2 עברו Audit.
- 18 רשומות Description-only נבדקו במחמיר.
- כל 82 מערכי Chapters נבדקו.
- Chapters לא־לימודיים הוסרו ותועדו.
- לפחות 30 מועמדים עבריים נבדקו ותועדו.
- Backlog עברי ותוכנית Phase 05 קיימים.
- כל הבדיקות עברו.
- Commit נוצר.
- `reports/phase-03b-review-bundle.zip` נוצר ואומת.
- Phase 04 לא התחיל.

בסיום הצג בצ'אט רק:

1. `PASS` או `FAIL`.
2. מספר הרשומות לפני ואחרי.
3. מספר רשומות Wave 1 שנבדקו ושונו.
4. התאמות לתבניות לפני ואחרי.
5. מספר רשומות Wave 2 שנבדקו ושונו.
6. Chapters לפני, אחרי וכמה הוסרו.
7. מספר מועמדים עבריים שנבדקו ומספר המועמדים החזקים.
8. מספר בדיקות שעברו ונכשלו.
9. מספר קישורים שעברו, נכשלו או נשארו לא־מוכרעים.
10. Commit hash.
11. הנתיב המדויק של:
    `reports/phase-03b-review-bundle.zip`

לאחר מכן עצור.
