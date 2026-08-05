# בדיקת PWA מקומית — v2.3.0

## תוצאה

**PASS** — האתר מוכן לפרסום ל־GitHub Pages תחת subpath.

## ראיות

- `tools/validate_pwa.py`: ‏957 בדיקות עברו, 0 נכשלו; 450/450 רשומות ו־450 מזהי YouTube ייחודיים.
- `npm test`: ‏62 בדיקות עברו, 0 נכשלו.
- כל קובצי JavaScript וה־Service Worker עברו `node --check`.
- שני קובצי ה־Workflow עברו פענוח YAML מקומי.
- Chrome טען את האתר בכתובת `http://127.0.0.1:8765/adventure-riding-video-guide/`.
- נבדקו Desktop ‏1440×900 ו־Mobile ‏390×844, עברית RTL ואנגלית LTR, מצב בהיר וכהה.
- `data-horizontal-overflow=false` במובייל ו־0 שגיאות Console.
- Manifest ואייקון 512 החזירו HTTP 200; מידות כל האייקונים אומתו.
- Service Worker היה `activated`, שלט בדף, ומנגנון “עדכון עכשיו” הפעיל Worker ממתין ורענן פעם אחת בלבד.
- Chrome ירה בפועל `beforeinstallprompt`, וכפתור ההתקנה המותאם הוצג.
- לאחר עצירת שרת המקור, Chrome רענן את האתר מן ה־Service Worker, טען את כל 450 הרשומות והציג `450 סרטונים נמצאו`.
- ענף הודעת ה־Offline של נגן YouTube עבר בדיקת Node. לא בוצע ניתוק רשת מלא של Chrome המחובר, ולכן אין טענה לצילום נגן Offline בדפדפן.

## התקנה

התקנת PWA בפועל לא בוצעה על Origin ה־localhost כדי לא להשאיר אפליקציית בדיקה בפרופיל המשתמש. זמינות ההתקנה אומתה באמצעות אירוע Chrome אמיתי, Manifest תקין ו־Service Worker פעיל. בדיקת האתר החי תבוצע לאחר ה־Deployment.

## צילומי מסך

- `reports/screenshots/pwa-local/local-desktop-he.png`
- `reports/screenshots/pwa-local/local-desktop-en.png`
- `reports/screenshots/pwa-local/local-mobile-he.png`
- `reports/screenshots/pwa-local/local-mobile-en.png`
