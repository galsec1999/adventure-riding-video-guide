# מפת מקורות — Final One-Shot Release 1.0

**מועד מעבר הקריאה:** 2026-08-04T08:04:05Z
**שורש הפרויקט:** `D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-Starter`
**תוצאה:** כל מקורות החובה נמצאו ונקראו; 141 קבצים ו־6,764,667 בתים נקראו במעבר מלא. 100 קובצי טקסט עברו פענוח UTF-8 ללא שגיאה ו־41 קבצים בינאריים נקראו וחושבו כחלק מן המלאי.

## מקורות אמת שנקראו במלואם

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
- כל חמשת קובצי `data/`: `videos.json`, `categories.json`, `synonyms.json`, `learning-paths.json`, `site-config.json`
- כל הקבצים תחת `prompts/`, לרבות `PROMPT_FINAL_ONE_SHOT_RELEASE_1_0_HE.md`
- כל הקבצים תחת `research/reports/`, `research/approved/` ו־`research/rejected/`
- כל הקבצים תחת `reports/`, לרבות דוחות JSON/CSV/HTML, ראיות Git, צילומי PNG וחבילות ZIP היסטוריות
- כל הקוד תחת `assets/`
- כל הבדיקות וה־fixtures תחת `tests/`
- כל כלי התחזוקה והמחקר תחת `tools/`
- `package.json`, `index.html`, `run-local.bat`, `run-local.sh`

הדוחות והחבילות ההיסטוריים נקראו כראיות בלבד. טענות על בדיקות, זמינות קישורים או איכות תוכן אינן נחשבות עד להרצה מחדש בסבב הנוכחי.

## מקורות חסרים

לא חסר אף מקור שנדרש בסעיף 3 של פרומפט ה־one-shot.

תוצרי Release שטרם היו קיימים בתחילת הסבב ואינם נחשבים מקור חסר: `AUTORUN_STATE.json`, כלי Content Quality Lint, דוחות `final-one-shot`, מסלולי הלמידה המורחבים, מסמכי Release, תיקיית Release ו־ZIP סופי.

## סתירות ופערים שנמצאו

1. `NEXT_ACTION.md` והפרומפטים 03B–08 דורשים עצירות ואישורי ביניים; פרומפט ה־one-shot הנוכחי גובר עליהם ודורש ריצה רציפה עד Release 1.0.
2. `MASTER_SPEC.md` ו־`QUALITY_GATES.md` מגדירים מינימום 200 ויעד 250, בעוד פרומפט ה־one-shot מחייב בדיוק 250. היעד המחמיר והמאוחר — בדיוק 250 — הוא שער השחרור הפעיל.
3. המאמת והבדיקות הקיימים דורשים בדיוק שני מסלולי למידה, אך פרומפט ה־one-shot מחייב לפחות שמונה. המאמת והבדיקות יעודכנו לדרישה החדשה בלי להחליש שלמות הפניות.
4. הטקסונומיה מאפשרת `ja` ושתי רשומות Production מסומנות יפנית, אך Release 1.0 מתיר רק `he` ו־`en`. שתי הרשומות ייבדקו ויוחלפו או יתוקנו רק אם המקור מוכיח שהשפה בפועל אנגלית.
5. הדוחות ההיסטוריים מציגים Trust Audit שעבר, אך כלי ההגירה `tools/apply_phase03_wave1.py` מוכיח ששדות אמון רבים נוצרו מתבניות. כל 130 הרשומות נדרשות לביקורת מחודשת וכל התאמה לתבניות תוסר על בסיס מקור.
6. `assets/js/storage.js` קורא כרגע `window.localStorage` לפני שהגישה עצמה נכנסת ל־`try/catch`; זה סותר דרישת ה־SecurityError המפורשת ויתוקן עם בדיקה ייעודית.
7. `index.html` כולל Meta Description סטטי שמתעדכן בזמן ריצה, אך חסרים תגי Open Graph מחוברים לתצורה. הם יתווספו וייבדקו.
8. `tools/check_links.py` מבחין ב־unavailable וב־indeterminate, אך אינו כולל Retry עם Backoff וסיווג rate-limited מפורש כנדרש. הכלי יורחב לפני שער הקישורים הסופי.
9. עץ העבודה בתחילת הסבב לא היה נקי: נשמרו שינוי קיים ב־`REVIEW_BUNDLE_MANIFEST.md`, שני פרומפטים לא־עקובים וראיות/חבילות היסטוריות לא־עקובות. הם נשמרו ללא מחיקה והעבודה הועברה לענף `final-one-shot-release-v1`.

## החלטת ביצוע שמרנית

לא ייעשה שימוש בדוחות קודמים כהוכחת Release, לא ייכתב תוכן על בסיס כותרת בלבד, ולא יומצאו Chapters, תמלול, משך, שפה או ראיות. כלי אוטומציה ישמשו לאיסוף, השוואה, Lint, דוחות ואריזה; שדות תוכן יאושרו רק מול מקור ספציפי.
