# דוח פריסה — v2.3.0 PWA

## תוצאה

**PASS** — האתר פורסם, נטען ומציע התקנה ב־Chrome דרך GitHub Pages.

## מקור שנבחר

- חבילה: `D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-v2.2.1-Bilingual-Web-Package.zip`
- SHA-256: `319228D0BAB6699079FE0A45FA1B83AA1A0FD59F910EF3C7E3DECFFEEAD178AC`
- סיבה: החבילה כוללת אתר דו־לשוני מלא עם 450 רשומות ייחודיות, 175 ערוצים ו־17 מסלולי לימוד.
- ZIP ה־Starter שנבדק: SHA-256 `1FECD9DDD4F1106E72680EBD0BF77C51B248ED76490E5EB0E1109EC8348AE771`; הוא מכיל 250 רשומות בלבד ולכן לא נבחר לפרסום.
- HTML עצמאי: `D:\Michael2015\אופנוע\Adventure-Riding-Video-Guide-v2.2.1-Standalone-Bilingual.html`
- SHA-256 של HTML עצמאי: `294FD1FE898D28CA3ADF35710CF3E6E0999441CBEC2A48D206D4D89DE9256BFD`

## יעד וגרסה

- Repository: <https://github.com/galsec1999/adventure-riding-video-guide>
- אתר חי: <https://galsec1999.github.io/adventure-riding-video-guide/>
- גרסת אתר: `2.3.0`
- Tag ו־Release: `v2.3.0-pwa`
- Commit של קוד האתר שנפרס ונבדק: `94a7a1439588e82feb48352294cf274a7d3347fa`
- GitHub Validate run: `31008965959` — `success`
- GitHub Pages run: `31008966092` — `success`
- Pages: `workflow`, ‏HTTPS enforced

## תוצאות אימות

- 450/450 רשומות, 450 IDs ייחודיים ו־450 YouTube IDs ייחודיים.
- 66 רשומות עבריות ו־384 אנגליות; 175 ערוצים ו־17 מסלולים.
- 957 בדיקות PWA סטטיות עברו, 0 נכשלו.
- 62 בדיקות Node עברו, 0 נכשלו.
- כל קובצי JavaScript, ה־Service Worker ושני קובצי ה־Workflow עברו בדיקת תחביר.
- שמונה כתובות חיות החזירו HTTP 200: בסיס, Manifest, Service Worker, שלושה אייקונים, נתוני הסרטונים, offline ו־404.
- נמצאו 0 הפניות mixed-content ו־0 נתיבי root מוחלטים לנכסי האתר.

## בדיקת Chrome חיה

- עברית: `lang=he`, ‏`dir=rtl`, ‏450 רשומות.
- אנגלית: `lang=en`, ‏`dir=ltr`, ‏450 רשומות.
- Desktop: ‏1440×900; Mobile: ‏390×844.
- 0 גלישה אופקית בכל התצורות שנבדקו.
- אירוע `beforeinstallprompt` אמיתי התקבל וכפתור ההתקנה הוצג.
- Service Worker הופעל ושלט באתר; app shell ונתוני הספרייה נטענו גם לאחר עצירת שרת המקור בבדיקה המקומית.
- עדכון Service Worker ממתין הוצג למשתמש, הופעל רק לאחר הסכמה ורענן פעם אחת.
- אין טענה לאירוע `appinstalled`, מפני שהתקנה בפועל בפרופיל Chrome לא הושלמה.

## הוראות התקנה קצרות

- **Android / Chrome:** פתחו את האתר, לחצו על כפתור `התקנת האפליקציה` או על תפריט Chrome ואז `התקנת אפליקציה`, ואשרו.
- **Desktop / Chrome:** פתחו את האתר, לחצו `Install app` בכותרת או על סמל ההתקנה בשורת הכתובת, ואשרו.

## מגבלות

- סרטוני YouTube עצמם דורשים חיבור לאינטרנט ואינם נשמרים במטמון.
- זמינות סרטונים ושירותי צד שלישי יכולה להשתנות.
- הצגת אפשרות ההתקנה תלויה במדיניות וב־engagement של Chrome; התנאים והאירוע נצפו בבדיקה החיה.
