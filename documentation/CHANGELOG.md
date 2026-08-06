# Changelog — גרסת מסמך 3.2.0

## 3.2.0 — 2026-08-06

- בוטל אישור 806 קצרים בביטחון נמוך לאחר גילוי התאמת מילת מפתח שגויה בין שם הצמיג Motoz Tractionator GPS לבין קטגוריית ניווט.
- כל 806 הרשומות נבדקו מחדש מול מקור YouTube; 11 עברו הסכמה בין כותרת, תיאור ובדיקה חזותית פרטנית, ו־795 הוסרו.
- מסלולי לימוד כוללים כעת עד שלושה קצרים ורק בהתאמת קטגוריה לסרטונים המלאים באותו שלב; 12 שלבים כוללים 28 הפניות לקצרים.
- נוספו שערי רגרסיה שמונעים החזרת `GPS Tire` או `GPX TSE` לניווט ומחייבים ביטחון גבוה וראיות מקור וחזות לכל קצר.
- גרסת האתר, ה־PWA, הסכמה וה־Standalone הועלתה ל־3.2.0; המאגר הציבורי כולל 422 פריטים.

## 3.0.0 — 2026-08-05

- המאגר הסופי כולל 411 סרטונים פעילים: 69 בעברית ו־342 באנגלית, מ־165 ערוצים.
- נוספו 17 מקורות ממוקדים בניווט, מיגון ודיבוריות; הוסרו 56 רשומות לא זמינות או כאלה שלא עברו את מדיניות הראיות המחמירה.
- נוספו מסננים בסיסיים ומתקדמים, כרטיסי החלטה עשירים וחלון פרטים עם תזכורת Like ותיעוד אימות.
- מסלולי הלימוד עוצבו מחדש: 17 מסלולים, 136 שלבים, מסלול אחד פתוח בכל פעם, התקדמות והמשך מהשלב הבא.
- מרכז הטיולים הורחב ל־10 השוואות ניווט, 6 מדריכי ידע, 7 צ׳קליסטים ו־34 הפניות לסרטונים.
- נוסף חיפוש סמנטי מקומי אופציונלי עם `Xenova/multilingual-e5-small`, ללא API, מפתח או Backend; החיפוש הרגיל נשאר fallback מלא.
- נוסף מונה טעינות חיצוני שקוף באמצעות Hits.sh, עם הסבר פרטיות ו־fallback כאשר השירות אינו זמין.
- הושלמה תמיכה דו־לשונית בממשק, בשגיאות runtime ובמשוב; משוב ובקשות הסרה עברו ל־GitHub כדי לא לחשוף שם משפחה.
- נוספו PWA canonical בשורש, חבילת HTML עצמאית, אינדקס סמנטי, בדיקות i18n, סנכרון root→`site/` ושערי CI לגרסה 3.0.0.

## 2.2.1 — 2026-08-05

- הורחב המאגר מ־250 ל־350 סרטונים.
- נוספו 100 סרטונים: 15 בעברית ו־85 באנגלית.
- נוסף תחום “טיולים ומסעות” וקטגוריות לתכנון, קבוצה, זיווד, ניווט, כלים, לינה וחו״ל.
- נוספו 5 מסלולי לימוד; סך הכול 13.
- נוסף מרכז טיולים עם 3 סוגי טיול, 7 צ׳קליסטים ו־5 כלי ניווט.
- תוקנו מסננים תלויי־תחום וקטגוריה.
- תוקנה התאמת חיפוש עברית כדי למנוע התאמות תת־מחרוזת שגויות.
- נוסף חיפוש חכם מקומי בשפה חופשית, ללא API וללא שליחת מידע.
- נוסף כפתור משוב; בגרסה 3.0.0 היעד הוחלף ל־GitHub מטעמי פרטיות.
- נוספו דיסקליימרים, תודה ליוצרים, הצהרת קהילה ללא רווח וללא פרסומות מטעם האתר.
- נוסף כפתור הורדת HTML עצמאי ושיפור קהילתי בעזרת AI.
- נוספו MIT לקוד ו־CC BY-NC-SA 4.0 לתוכן הקהילתי המקורי, עם החרגת צד שלישי.
- נוספו בדיקות Browser QA, סקלביליות ל־500 רשומות, אחסון טיולים ובדיקות מסננים.

## 1.0.1

- גרסת QA של מאגר 250 הסרטונים והאתר המקורי.


## 2.2.1 — Contrast and desktop dialog layout

- Repaired dark-theme contrast in the hero guide, footer, safety panels and selected path controls.
- Added theme-aware primary-button foreground colours.
- Enlarged the desktop video dialog.
- Replaced narrow multi-column detail cards with readable full-width rows.
- Removed the duplicated video title inside the dialog body and reset dialog scroll on every open.


## 2.2.1 — 450 tutorials, contextual taxonomy and visual refinement

- Added 100 curated tutorial records: 80 English and 20 Hebrew.
- Added an explicit three-level hierarchy: area, primary topic and focus/subtopic.
- Added a guidance-format facet and contextual option counts.
- Added fast domain tabs, topic/focus chips and an active context card.
- Added four learning paths based on the expanded library.
- Refined cards, hero, library toolbar, dark/light contrast and desktop density.


## 2.2.1 — polish and classification integrity

- Prevented taxonomy tag IDs from overriding Hebrew/English labels for domains, topics and focus areas.
- Fixed the bilingual header grid so language and theme controls stay in the header on desktop and mobile.
- Added bilingual active-filter labels and contextual empty-option labels.
- Replaced one duplicated manufacturer upload with a distinct Bennetts BikeSocial corner-braking explainer.
- Added Hebrew display labels for tags that previously appeared as raw English identifiers.
