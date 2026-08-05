# מדריך הווידאו הקהילתי לרכיבת אדוונצ'ר

אתר PWA דו־לשוני שניתן להתקנה, ובו 450 הדרכות רכיבה מסווגות, מנגנון חיפוש ומסננים היררכי, 17 מסלולי לימוד, מרכז טיולים, מועדפים והתקדמות מקומית.

האתר החי: <https://galsec1999.github.io/adventure-riding-video-guide/>

[English README](README.en.md)

## התקנה

- Chrome ב־Android: פתחו את האתר, פתחו את תפריט ⋮ ובחרו **התקנת האפליקציה** או **הוספה למסך הבית**.
- Chrome במחשב: לחצו על סמל ההתקנה בשורת הכתובת או בחרו **Install** בתפריט הדפדפן.
- iPhone/iPad: בחרו **Share → Add to Home Screen**.

לאחר טעינה ראשונה מוצלחת, הספרייה, החיפוש, המסננים ומסלולי הלימוד זמינים גם ללא רשת. הפעלת סרטוני YouTube עדיין דורשת אינטרנט.

## הפעלה מקומית

```powershell
python -m http.server 8080 --directory site
```

לאחר מכן פתחו <http://localhost:8080/>. Service Worker פועל רק ב־`localhost` או ב־HTTPS.

## בדיקות

```powershell
python -m pip install jsonschema==4.26.0
python tools/validate_pwa.py --site site --schema documentation/video.schema.json --expected-count 450
npm test
```

שער האימות בודק בין היתר:

- בדיוק 450 רשומות, IDs וקישורי YouTube ייחודיים.
- התאמה לסכמה הדו־לשונית.
- Manifest, אייקונים ומידות PNG.
- קיום כל נכסי האתר ונתיבים יחסיים המתאימים ל־GitHub Pages.
- Service Worker, מצב Offline, מנגנון עדכון והתקנה.
- חיפוש, מסננים, Storage, Lazy Loading ומניעת טעינת מאות iframes.

## מבנה Repository

- `site/` — התוצר הסטטי המדויק שמתפרסם ב־GitHub Pages.
- `site/data/` — מאגר 450 ההדרכות והמילונים המבוקרים.
- `documentation/` — רישיונות, Schema, Changelog והערות מקור v2.2.1.
- `tools/validate_pwa.py` — שער השחרור שחוזר ב־CI.
- `reports/` — ראיות QA ודוחות פריסה.
- `.github/workflows/` — אימות ופרסום אוטומטי.

## עדכון תוכן

אין להוסיף סרטון לפי כותרת בלבד. יש לאמת תיאור, Chapters, כתוביות/תמלול או קטע רלוונטי, ואין להמציא מטא־דאטה, נקודות זמן או מסקנות. לאחר שינוי מריצים את כל הבדיקות ודואגים ש־`site/` נשאר מוכן לפרסום ללא Build.

Push ל־`main` מפעיל אימות מלא ולאחריו פרסום רשמי של `site/` ל־GitHub Pages. גרסאות מסומנות ב־Semantic Versioning; גרסת ה־PWA הראשונה היא `v2.3.0-pwa`.

## מטרה, זכויות ופרטיות

זהו פרויקט קהילתי ללא מטרת רווח וללא פרסומות מטעם האתר. קוד מקורי מופץ לפי MIT; תקצירים וסיווגים מקוריים לפי CC BY-NC-SA 4.0. סרטוני YouTube, תמונות ממוזערות, שמות ערוצים וסימני מסחר נשארים בבעלות יוצריהם ואינם כלולים ברישיונות הפרויקט.

מצב המשתמש נשמר בדפדפן בלבד. אין חשבון משתמש, Backend או סנכרון בין מכשירים.

משוב, תיקון או בקשת הסרה: [Ilan.nachman@gmail.com](mailto:Ilan.nachman@gmail.com)
