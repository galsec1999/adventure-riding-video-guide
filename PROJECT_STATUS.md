# מצב הפרויקט — גרסת מסמך 3.0.2

- **גרסת מוצר:** 3.0.0
- **מצב:** שוחרר ואומת באתר החי ב־2026-08-06
- **תוצאת שחרור:** שערי הנתונים, הקישורים, הקוד, ה־PWA, הסנכרון וה־Design QA עברו. בדיקת Content Quality Legacy נשארה `FAIL` כחריגה לא חוסמת ומתועדת; אין טענה שכל שערי האיכות עברו.
- **Repository ציבורי:** <https://github.com/galsec1999/adventure-riding-video-guide>
- **אתר ציבורי:** <https://galsec1999.github.io/adventure-riding-video-guide/>
- **Commit מוצר:** `67d5e5f73e10759bd252f344c3a18abb14c678f3`
- **Commit CI סופי:** `9d2d63b96dda136fde6eb9f37ac66951426a6f30`
- **GitHub Actions:** Validate ‏`31079027172` — success; Deploy Pages ‏`31079027055` — success
- **סרטונים פעילים:** 411 — מהם 69 בעברית ו־342 באנגלית
- **ערוצים ייחודיים:** 165
- **מסלולי למידה:** 17 מסלולים, 136 שלבים ו־416 הפניות לסרטונים
- **מרכז טיולים:** 3 סוגי טיול, 42 פריטי checklist, ‏10 כלי ניווט ו־6 מדריכי ידע
- **קישורי YouTube:** ‏411/411 פעילים; 0 unavailable, ‏0 indeterminate ו־0 rate-limited
- **PWA:** ‏896 בדיקות עברו, 0 נכשלו
- **בדיקות Python:** ‏32/32 עברו
- **בדיקות Node:** ‏76/76 עברו
- **בדיקות חיפוש:** ‏25/25 עברו
- **אימות נתונים וסכמה:** ‏25,132 בדיקות עברו, 0 נכשלו ו־0 אזהרות
- **ביקורת תוכן מבנית:** ‏25,131 בדיקות עברו, 0 נכשלו
- **תחביר JavaScript:** ‏13/13 קבצים עברו
- **סנכרון פרסום:** ‏33/33 קבצים תואמים בין המקור לבין `site/`, ללא חסרים, עודפים או הבדלי hash
- **Standalone:** ‏411 רשומות מוטמעות; הקובץ תואם לגרסת מוצר 3.0.0 ולנתוני האתר
- **AI מקומי:** חיפוש סמנטי אופציונלי במכשיר, ללא API או Backend; החיפוש הרגיל נשאר זמין תמיד
- **אימות חי:** HTTP 200, גרסה 3.0.0, ‏411 רשומות, מונה חי, HE/EN, ‏Dark/Light, ‏0 overflow ו־12 תוצאות AI סמנטיות ללא שגיאות Console
- **פרטיות:** הקרדיט הציבורי הוא „אילן” בלבד; השם המלא, כתובת האימייל האישית ושורת © אישית אינם מוצגים
- **Design QA:** עברית/אנגלית, RTL/LTR, מצב כהה/בהיר, Desktop ‏1440×900 ו־Mobile ‏390×844 נבדקו; 0 גלישה אופקית

## חריגת Content Quality Legacy

הכלי `content_quality_lint.py` מדווח במכוון על חוב תוכן ותיק: **7,137 שגיאות ו־382 אזהרות**. הממצאים כוללים תקצירים קצרים, ניסוחים זהים או דומים וחוסרי ראיות ב־Legacy. הדוח לא הוסתר ולא סומן כ־PASS. החריגה אינה מבטלת את תוצאות שערי הנתונים, הסכמה, הקישורים, הקוד, ה־PWA וה־Design QA, אך היא נשארת חוב עריכה מפורש לסבב עתידי.

## ראיות מרכזיות

- `reports/site-upgrade-v3/final-link-check.json`
- `reports/site-upgrade-v3/pwa-validation.json`
- `reports/site-upgrade-v3/search-acceptance.json`
- `reports/site-upgrade-v3/content-audit.json`
- `reports/site-upgrade-v3/content-quality.json`
- `reports/site-upgrade-v3/design-qa.md`
- `reports/site-upgrade-v3/design-comparison.png`
- `reports/site-upgrade-v3/screenshots/`
- `documentation/SITE_UPGRADE_PLAN_HE.md`
- `documentation/THIRD_PARTY_NOTICES.md`
- `.github/workflows/validate.yml`
- `.github/workflows/deploy-pages.yml`
- `documentation/DEPLOYMENT_REPORT_3.0.0_HE.md`

## המשך עתידי

המשך העבודה מוגבל לחוב Content Quality Legacy ולהרחבת תוכן מאומתת בעתיד, כמפורט ב־`NEXT_ACTION.md`. אין לבצע אותו כחלק מסבב שחרור 3.0.0.
