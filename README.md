# מדריך הווידאו הקהילתי לרכיבת אדוונצ'ר — גרסת מסמך 3.0.0

אתר PWA דו־לשוני שניתן להתקנה, ובו 411 הדרכות רכיבה פעילות ומסווגות, 17 מסלולי לימוד, מרכז טיולים, חיפוש היררכי וחיפוש סמנטי מקומי אופציונלי. גרסת המוצר: **3.0.0**.

האתר החי: <https://galsec1999.github.io/adventure-riding-video-guide/>

[English README](README.en.md)

## מה חדש ב־3.0.0

- נוספו 17 סרטונים ממוקדים: 6 ניווט, 7 מיגון ו־4 דיבוריות; הוסרו 56 קישורים לא זמינים או רשומות שלא עברו את מדיניות הראיות המחמירה.
- נוספו מסננים בסיסיים ומתקדמים, כרטיסי סרטון עשירים, תזכורת Like בולטת ודיסקליימר אוצרות מלא.
- מסלולי הלימוד נפתחים אחד בכל פעם וכוללים התקדמות, שלב הבא וחלופות צפייה.
- מרכז הניווט כולל 10 השוואות, 6 מדריכי ידע, 7 צ׳קליסטים ו־34 הפניות לסרטונים.
- חיפוש סמנטי אופציונלי רץ במכשיר עם מודל רב־לשוני; אין API, מפתח או שרת AI. החיפוש הרגיל נשאר זמין תמיד.
- מונה הכניסות מציג טעינות של האתר החי באמצעות Hits.sh; זו אינה ספירת משתמשים ייחודיים.
- הקרדיט הציבורי הוא „אילן” בלבד. משוב ובקשות הסרה עוברים דרך GitHub ואינם חושפים שם משפחה.

## התקנה

- Chrome ב־Android: פתחו את האתר, פתחו את תפריט ⋮ ובחרו **התקנת האפליקציה** או **הוספה למסך הבית**.
- Chrome במחשב: לחצו על סמל ההתקנה בשורת הכתובת או בחרו **Install** בתפריט הדפדפן.
- iPhone/iPad: בחרו **Share → Add to Home Screen**.

לאחר טעינה ראשונה מוצלחת, הספרייה, החיפוש הרגיל, המסננים, הטיולים ומסלולי הלימוד זמינים גם ללא רשת. סרטוני YouTube והורדה ראשונה של מודל ה־AI המקומי דורשים אינטרנט.

## הפעלה מקומית

```powershell
python -m http.server 8080 --directory site
```

פתחו <http://localhost:8080/>. Service Worker פועל רק ב־`localhost` או ב־HTTPS.

## בנייה ואימות

```powershell
node tools/build_semantic_index.mjs
python tools/build_standalone.py
python tools/verify_site_sync.py --write
python tools/validate_data.py --expected-count 411
python tools/validate_pwa.py --site site --schema documentation/video.schema.json --expected-count 411
python -m unittest discover -s tests -p "test_*.py"
npm test
node tools/search_acceptance.mjs
```

שערי השחרור בודקים בין היתר 411 מזהים וקישורים ייחודיים, התאמה לסכמה, מסלולי לימוד, נתוני טיולים, אינדקס סמנטי, Manifest, אייקונים, Service Worker, Offline, חיפוש, מסננים, Storage ו־Lazy Loading ללא מאות iframes.

## מבנה Repository

- `site/` — התוצר הסטטי המדויק שמתפרסם ב־GitHub Pages.
- `data/` — 411 רשומות, טקסונומיה, מסלולים, טיולים ואינדקס סמנטי.
- `assets/` — ממשק, עיצוב, Worker, Transformers.js ו־ONNX Runtime.
- `downloads/Adventure-Riding-Video-Guide-v3.0.0-Standalone.html` — מהדורה עצמאית עם חיפוש רגיל, ללא המודל הסמנטי.
- `documentation/` — מפרטים, רישיונות, זכויות, הודעות צד שלישי והערות שחרור.
- `reports/site-upgrade-v3/` — דוחות, בדיקות וצילומי QA של גרסה 3.0.0.

## תוכן, זכויות ופרטיות

אין להוסיף סרטון לפי כותרת בלבד ואין להמציא מטא־דאטה, נקודות זמן או מסקנות. האתר הוא אינדקס אוצר בלבד: אינו הבעלים של הסרטונים, אינו מאשר כל טענה ואינו תחליף להדרכה מקצועית, לחוק או לספר היצרן.

קוד מקורי מופץ לפי MIT; טקסטים וסיווגים מקוריים לפי CC BY-NC-SA 4.0. סרטוני YouTube, תמונות ממוזערות, שמות ערוצים וסימני מסחר נשארים בבעלות יוצריהם. מצב משתמש נשמר בדפדפן בלבד. פרטי צד שלישי מופיעים ב־`documentation/THIRD_PARTY_NOTICES.md`.

משוב, תיקון או בקשת הסרה: <https://github.com/galsec1999/adventure-riding-video-guide/issues/new>
