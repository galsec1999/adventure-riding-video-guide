import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (relative) => JSON.parse(fs.readFileSync(path.join(ROOT, relative), "utf8"));
const writeJson = (relative, value) => fs.writeFileSync(path.join(ROOT, relative), `${JSON.stringify(value, null, 2)}\n`, "utf8");

const evidenceReport = readJson("reports/site-upgrade-v3/selected-video-evidence.json");
const evidenceById = new Map(evidenceReport.results.map((item) => [item.youtube_video_id, item]));
const checkedDate = evidenceReport.generated_at.slice(0, 10);

const taxonomyItems = {
  categories: [
    ["intercoms_communications", "דיבוריות ותקשורת", "Intercoms and communication", "בחירה, התקנה ושימוש בטוח בדיבוריות לרוכב יחיד, מורכב וקבוצה.", "Choosing, installing and safely using intercoms for solo riders, passengers and groups."],
  ],
  subcategories: [
    ["phone_vs_dedicated_gps", "טלפון מול GPS ייעודי", "Phone vs dedicated GPS", "השוואת עמידות, תפעול, עלות, מסך וגיבוי.", "Comparing durability, controls, cost, display and backup options."],
    ["rugged_phone_navigation", "טלפון מוקשח לניווט", "Rugged phone navigation", "טלפון מוקשח כמכשיר ניווט ייעודי לרכיבה.", "Using a rugged phone as a dedicated riding navigator."],
    ["navigation_apps", "אפליקציות ניווט", "Navigation apps", "בחירת אפליקציות למפות, מסלולים ושימוש לא מקוון.", "Choosing apps for maps, routes and offline use."],
    ["osmand", "OsmAnd", "OsmAnd", "עבודה עם מפות לא מקוונות, פרופילים וקובצי GPX ב־OsmAnd.", "Using offline maps, profiles and GPX files in OsmAnd."],
    ["offline_navigation", "ניווט לא מקוון", "Offline navigation", "הכנת מפות ומסלול לגישה ללא קליטה.", "Preparing maps and routes for use without coverage."],
    ["gpx_workflow", "תהליך עבודה עם GPX", "GPX workflow", "יצירה, בדיקה, ייבוא, ייצוא ושיתוף של קובצי GPX.", "Creating, checking, importing, exporting and sharing GPX files."],
    ["route_vs_track", "Route לעומת Track", "Route vs track", "הבדלים מעשיים בין מסלול מחושב לעקבות קבועות.", "Practical differences between a calculated route and a fixed track."],
    ["gaia_gps", "Gaia GPS", "Gaia GPS", "תכנון, שכבות מפה וייצוא מסלולים ב־Gaia GPS.", "Planning, map layers and route export in Gaia GPS."],
    ["local_mapping", "מיפוי מקומי", "Local mapping", "המרה והצגת נתוני מסלול במערכות מיפוי מקומיות.", "Converting and displaying route data in local mapping systems."],
    ["helmet_testing", "בדיקות קסדה", "Helmet testing", "שיטות בדיקה והשוואת ביצועי קסדות.", "Methods for testing and comparing helmet performance."],
    ["helmet_ratings", "דירוגי קסדות", "Helmet ratings", "הבנת דירוגים ותוצאות בדיקה מעבר לתווית התקן.", "Understanding ratings and test results beyond a standards label."],
    ["helmet_fit", "התאמת קסדה", "Helmet fit", "מידה, צורת ראש, מיקום ושדה ראייה.", "Size, head shape, position and field of view."],
    ["gear_standards", "תקני ציוד רכיבה", "Riding-gear standards", "קריאת סימוני תקן ובדיקת הסמכה של ביגוד מגן.", "Reading standards markings and checking protective-apparel certification."],
    ["abrasion_resistance", "עמידות בשחיקה", "Abrasion resistance", "הבדלים בחומרים, תפרים ורמות עמידות בהחלקה.", "Differences in materials, seams and slide resistance."],
    ["body_armor_standards", "תקני מיגון גוף", "Body-armour standards", "רמות ובדיקות של מגני פגיעה לגפיים ולגב.", "Levels and tests for limb and back impact protectors."],
    ["abrasion_vs_impact", "שחיקה לעומת פגיעה", "Abrasion vs impact", "ההבדל בין הגנה בהחלקה לספיגת אנרגיית מכה.", "The difference between slide protection and impact-energy absorption."],
    ["beginner_gear", "מיגון לרוכב מתחיל", "Beginner protective gear", "בחירת מעטפת מיגון בסיסית לפי שימוש והתאמה.", "Choosing a basic protection system by use and fit."],
    ["protective_boots", "מגפי מיגון", "Protective boots", "איזון בין קיבוע קרסול, הגנה, נוחות ומים.", "Balancing ankle support, protection, comfort and weather resistance."],
    ["crash_case_study", "מקרה בוחן לאחר תאונה", "Post-crash case study", "בדיקת ציוד לאחר אירוע אמיתי ללא הסקת מסקנות סטטיסטיות.", "Reviewing gear after a real incident without treating it as statistical proof."],
    ["bluetooth_vs_mesh", "Bluetooth לעומת Mesh", "Bluetooth vs mesh", "הבדלים בחיבור יחיד, מורכב וקבוצה.", "Differences for one-to-one, passenger and group connections."],
    ["safe_intercom_use", "שימוש בטוח בדיבורית", "Safe intercom use", "צמצום הסחת דעת והגדרת המערכת לפני רכיבה.", "Reducing distraction and configuring the system before riding."],
    ["budget_vs_premium", "תקציבי לעומת פרימיום", "Budget vs premium", "השוואת יכולות, אמינות, תמיכה ועלות כוללת.", "Comparing capability, reliability, support and total cost."],
    ["budget_bluetooth", "דיבורית Bluetooth תקציבית", "Budget Bluetooth intercom", "הבנת גבולות טווח, שמע וחיבור בדגמים בסיסיים.", "Understanding range, audio and connection limits in entry-level units."],
    ["installation_fit_audio", "התקנה, התאמה ושמע", "Installation, fit and audio", "מיקום רמקולים, מיקרופון ויחידה בלי לפגוע בהתאמת הקסדה.", "Positioning speakers, microphone and unit without compromising helmet fit."],
    ["multi_brand_comparison", "השוואה בין מותגים", "Multi-brand comparison", "השוואת מערכות לפי צורך ולא לפי שם מותג בלבד.", "Comparing systems by need rather than brand name alone."],
    ["group_mesh", "רשת תקשורת קבוצתית", "Group mesh", "תקשורת יציבה יותר לקבוצה והתנהגות בעת התנתקות וחזרה.", "Group communication and behaviour when riders disconnect and rejoin."],
    ["helmet_compatibility", "תאימות לקסדה", "Helmet compatibility", "בדיקת מקום לרמקולים, מיקרופון ותושבת לפי דגם קסדה.", "Checking speaker, microphone and mount space for a helmet model."],
  ],
  controlled_tags: [
    ["smartphone_navigation", "ניווט בטלפון", "Smartphone navigation"],
    ["dedicated_gps", "GPS ייעודי", "Dedicated GPS"],
    ["rugged_phone", "טלפון מוקשח", "Rugged phone"],
    ["route_vs_track", "Route לעומת Track", "Route vs track"],
    ["helmet_testing", "בדיקות קסדה", "Helmet testing"],
    ["helmet_fit", "התאמת קסדה", "Helmet fit"],
    ["gear_standards", "תקני ציוד", "Gear standards"],
    ["abrasion_resistance", "עמידות בשחיקה", "Abrasion resistance"],
    ["body_armor", "מיגון גוף", "Body armour"],
    ["impact_protection", "הגנת פגיעה", "Impact protection"],
    ["crash_case_study", "מקרה בוחן תאונה", "Crash case study"],
    ["intercom", "דיבורית", "Intercom"],
    ["bluetooth", "Bluetooth", "Bluetooth"],
    ["mesh", "Mesh", "Mesh"],
    ["helmet_audio", "שמע בקסדה", "Helmet audio"],
    ["distraction_management", "ניהול הסחת דעת", "Distraction management"],
    ["budget_comparison", "השוואת מחיר ויכולת", "Price and capability comparison"],
  ],
  source_types: [
    ["official_safety_program", "תוכנית בטיחות רשמית", "Official safety programme", "גוף ציבורי או תוכנית בטיחות רשמית שמפרסמים מידע לציבור.", "A public body or official safety programme publishing information for riders."],
  ],
};

const navDefaults = {
  domain: "touring_travel",
  primary_category: "route_navigation",
  secondary_categories: ["touring_planning"],
  skill_level: "beginner",
  risk_level: "low",
  motorcycle_types: ["adventure", "dual_sport", "touring"],
  motorcycle_weight_classes: ["general"],
  terrain_types: [],
  road_conditions: [],
  exercises_he: [], exercises_en: [],
  equipment_he: ["טלפון או מכשיר ניווט טעון", "מפות ומסלול שהורדו מראש", "מקור חשמל ואמצעי ניווט גיבוי"],
  equipment_en: ["A charged phone or navigation device", "Maps and route downloaded in advance", "Power supply and a backup navigation method"],
  safety_warnings_he: ["אין לתפעל מסך תוך כדי רכיבה; עוצרים במקום בטוח ובודקים שהמסלול חוקי ומתאים לתנאים."],
  safety_warnings_en: ["Do not operate a screen while moving; stop safely and verify that the route is legal and suitable for current conditions."],
  common_mistakes_he: ["יציאה בלי מפה לא מקוונת או גיבוי", "הנחה שקובץ GPX מבטיח שהדרך פתוחה, חוקית או עבירה"],
  common_mistakes_en: ["Leaving without an offline map or backup", "Assuming a GPX file proves that a route is open, legal or passable"],
};

const protectionDefaults = {
  domain: "safety_recovery",
  primary_category: "protective_gear",
  secondary_categories: [],
  skill_level: "beginner",
  risk_level: "low",
  motorcycle_types: ["general_motorcycle"],
  motorcycle_weight_classes: ["general"],
  terrain_types: [],
  road_conditions: [],
  exercises_he: [], exercises_en: [],
  equipment_he: ["פריט המיגון הנבדק", "תווית התקן והוראות היצרן", "סיוע ממתאים מקצועי כאשר נדרש"],
  equipment_en: ["The protective item being evaluated", "Its standards label and manufacturer instructions", "Professional fitting help where appropriate"],
  safety_warnings_he: ["תקן, התאמה ומצב פיזי פועלים יחד; סרטון או דירוג אינם מבטיחים הגנה בכל תאונה."],
  safety_warnings_en: ["Standard, fit and physical condition work together; no video or rating guarantees protection in every crash."],
  common_mistakes_he: ["בחירה לפי מחיר או מראה בלבד", "התעלמות מהתאמה, בלאי, תאריך ייצור והוראות היצרן"],
  common_mistakes_en: ["Choosing only by price or appearance", "Ignoring fit, wear, manufacturing date and manufacturer instructions"],
};

const commsDefaults = {
  domain: "touring_travel",
  primary_category: "intercoms_communications",
  secondary_categories: ["group_riding"],
  skill_level: "beginner",
  risk_level: "low",
  motorcycle_types: ["general_motorcycle"],
  motorcycle_weight_classes: ["general"],
  terrain_types: [],
  road_conditions: [],
  exercises_he: [], exercises_en: [],
  equipment_he: ["קסדה תואמת", "דיבורית טעונה", "טלפון רק אם נדרש להגדרה", "בדיקת שמע בעמידה"],
  equipment_en: ["A compatible helmet", "A charged intercom", "A phone only when needed for setup", "A stationary audio check"],
  safety_warnings_he: ["מגדירים ומצמדים לפני היציאה, שומרים על עוצמה שמאפשרת לשמוע את הסביבה ואינם מנהלים הגדרות תוך כדי רכיבה."],
  safety_warnings_en: ["Configure and pair before departure, keep volume low enough to hear the environment, and never change settings while moving."],
  common_mistakes_he: ["בחירה לפי טווח מוצהר בלבד", "התקנה שפוגעת בהתאמת הקסדה או ממקמת רמקולים לא נכון", "שימוש בשיחה שמסיחה מן הדרך"],
  common_mistakes_en: ["Choosing only by advertised range", "Compromising helmet fit or speaker placement", "Allowing conversation to distract from the road"],
};

const specs = [
  {
    ...navDefaults, id: "OiOgLX5AwLQ", source_type: "experienced_rider", content_type: "explainer", quality_score: 4, confidence: "high",
    title_he: "GPS ייעודי מול טלפון לניווט ברכיבת דו־שימושי", title_en: "Dual-sport navigation: dedicated GPS vs smartphone",
    subtopics: ["phone_vs_dedicated_gps", "offline_navigation"], tags: ["navigation", "smartphone_navigation", "dedicated_gps", "offline_maps"],
    summary_he: "השוואה מעשית בין GPS ייעודי לטלפון לרכיבת אדוונצ׳ר ושטח: עמידות, כפתורים וכפפות, מסך, עלות, מהירות עבודה וגיבוי תקשורת.",
    summary_en: "A practical comparison of dedicated GPS and smartphone navigation for dual-sport travel, covering durability, glove controls, display, cost, speed and communication backup.",
    learning_points_he: ["מתי כפתורים ועמידות של GPS ייעודי הם יתרון", "מתי מסך ואפליקציות בטלפון מפשטים את העבודה", "למה כדאי לבנות מערכת עם גיבוי ולא להסתמך על מכשיר יחיד"],
    learning_points_en: ["When dedicated-GPS buttons and durability matter", "When a phone display and apps simplify the workflow", "Why a backup matters more than relying on one device"],
    fit_for_he: "מתאים למי שבוחר בין טלפון, GPS ייעודי או שילוב ביניהם לטיולי כביש ושטח.", fit_for_en: "For riders deciding between a phone, a dedicated GPS or a combined setup for road and off-road trips.",
    why_watch_he: "הסרטון מציג יתרונות וחסרונות לשני הכיוונים ואינו מנסה למכור מכשיר מסוים.", why_watch_en: "It presents trade-offs in both directions without selling a particular device.",
    related: ["UOI7yWHv07w", "0Oa8Hc9AG4c"],
  },
  {
    ...navDefaults, id: "0Oa8Hc9AG4c", source_type: "experienced_rider", content_type: "case_study", quality_score: 3, confidence: "medium",
    title_he: "טלפון Android מוקשח כמכשיר ניווט לאופנוע", title_en: "Using a rugged Android phone for motorcycle navigation",
    subtopics: ["rugged_phone_navigation", "navigation_apps"], tags: ["navigation", "smartphone_navigation", "rugged_phone", "offline_maps"],
    summary_he: "מקרה בוחן של מעבר מטלפון יומיומי ומכשיר Garmin לטלפון Android מוקשח לניווט, עם דגש על מזג אוויר, כפפות, שחיקת המכשיר ואפליקציות מפה.",
    summary_en: "A case study of moving from a daily phone and Garmin backup to a rugged Android navigator, with attention to weather, gloves, device wear and mapping apps.",
    learning_points_he: ["למה להפריד בין הטלפון האישי למכשיר הניווט", "אילו מגבלות של מסך וכפפות צריך לבדוק", "כיצד לשמור גיבוי גם לאחר מעבר לטלפון מוקשח"],
    learning_points_en: ["Why separating the personal phone from navigation can help", "Which screen and glove limitations to test", "How to retain a backup after moving to a rugged phone"],
    fit_for_he: "מתאים לרוכבים ששוקלים טלפון מוקשח במקום מכשיר GPS ייעודי.", fit_for_en: "For riders considering a rugged phone instead of a dedicated GPS unit.",
    why_watch_he: "נותן ניסיון שימוש ממשי ומציג גם את הבעיות שגרמו לשינוי המערכת.", why_watch_en: "It provides a real-use perspective and explains the problems that drove the change.",
    related: ["OiOgLX5AwLQ", "UOI7yWHv07w"],
  },
  {
    ...navDefaults, id: "UOI7yWHv07w", source_type: "community_educator", content_type: "touring_guide", quality_score: 5, confidence: "high",
    title_he: "OsmAnd+ לניווט שטח: מפות לא מקוונות ומעקב GPX", title_en: "OsmAnd+ for off-road navigation, offline maps and GPX tracks",
    subtopics: ["osmand", "offline_navigation", "gpx_workflow"], tags: ["navigation", "gpx", "offline_maps", "route_sharing"],
    summary_he: "מדריך פרקי ל־OsmAnd+ שמכסה הורדת מפות ו־POI, ייבוא ומעקב GPX, הנחיות פנייה, העדפת דרכי עפר, פרופילים מותאמים והקלטת עקבות.",
    summary_en: "A chaptered OsmAnd+ guide covering offline maps and POIs, GPX import and following, turn guidance, unpaved-road preference, custom profiles and track recording.",
    learning_points_he: ["להוריד מפות ונתוני עניין לפני היציאה", "לייבא GPX ולהגדיר מעקב שמתאים לרכיבה", "לבנות פרופיל עפר ולהקליט את הנתיב בפועל"],
    learning_points_en: ["Download maps and POIs before departure", "Import a GPX file and configure track following", "Build an off-road profile and record the ridden track"],
    fit_for_he: "מתאים למתחילים ב־OsmAnd ולרוכבים שרוצים להפוך טלפון ישן לכלי ניווט לא מקוון.", fit_for_en: "For OsmAnd beginners and riders turning an older phone into an offline navigator.",
    why_watch_he: "כולל רצף עבודה ברור, פרקים וכתוביות אנגלית ידניות, בלי קישורי מכירה.", why_watch_en: "It offers a clear workflow, chapters and manual English captions without sales links.",
    related: ["N5DsF-4q98c", "OiOgLX5AwLQ"],
  },
  {
    ...navDefaults, id: "N5DsF-4q98c", source_type: "community_educator", content_type: "touring_guide", quality_score: 5, confidence: "high",
    title_he: "קובצי GPX לרכיבת אדוונצ׳ר: Gaia GPS, Route ו־Track", title_en: "GPX files for adventure riding: Gaia GPS, routes and tracks",
    subtopics: ["gpx_workflow", "route_vs_track", "gaia_gps"], tags: ["navigation", "gpx", "route_sharing", "route_vs_track"],
    summary_he: "מדריך מעשי לתהליך GPX: יצירה ועריכה ב־Gaia GPS, ההבדל בין Route ל־Track, נקודות ציון, ייצוא, שיתוף ופתיחה ב־REVER וב־OsmAnd.",
    summary_en: "A practical GPX workflow: create and edit in Gaia GPS, understand route versus track, add waypoints, export, share and open files in REVER and OsmAnd.",
    learning_points_he: ["להבחין בין Route מחושב ל־Track קבוע", "לערוך מסלול ונקודות ציון לפני שיתוף", "לבדוק מעבר של אותו GPX בין כמה אפליקציות"],
    learning_points_en: ["Distinguish a calculated route from a fixed track", "Edit a route and waypoints before sharing", "Check how one GPX file moves between several apps"],
    fit_for_he: "מתאים לרוכבים שמתחילים לעבוד עם GPX ורוצים להבין את כל השרשרת מתכנון עד ניווט.", fit_for_en: "For riders new to GPX who want the whole chain from planning to navigation.",
    why_watch_he: "הסרטון מתועד ב־18 פרקים ומדגים כמה כלים במקום לקדם פלטפורמה יחידה.", why_watch_en: "The 18 documented chapters demonstrate several tools instead of promoting one platform.",
    related: ["UOI7yWHv07w", "_4xaX5MT94Y"],
  },
  {
    ...navDefaults, id: "_4xaX5MT94Y", source_type: "community_educator", content_type: "touring_guide", quality_score: 3, confidence: "medium", language: "he",
    title_he: "הצגת קובץ GPX על גבי GOVMAP", title_en: "Displaying a GPX file on GOVMAP",
    subtopics: ["gpx_workflow", "local_mapping"], tags: ["navigation", "gpx", "route_planning", "offline_maps"],
    summary_he: "הסבר עברי קצר להמרת נקודות מקובץ GPX לקואורדינטות ITM, יצירת CSV וטעינתו כשכבה ב־GOVMAP לצורך הצגת המסלול.",
    summary_en: "A short Hebrew guide to converting GPX points to ITM coordinates, creating a CSV file and loading it as a GOVMAP layer.",
    learning_points_he: ["להבין מדוע GOVMAP דורש המרה לפורמט מתאים", "להמיר נקודות ל־ITM וליצור קובץ CSV", "לטעון את הקובץ כשכבה ולבדוק את התוצאה"],
    learning_points_en: ["Understand why GOVMAP needs a compatible coordinate format", "Convert points to ITM and create a CSV file", "Load the file as a layer and verify the result"],
    fit_for_he: "מתאים למשתמשי GOVMAP בישראל שכבר מחזיקים קובץ GPX.", fit_for_en: "For GOVMAP users in Israel who already have a GPX file.",
    why_watch_he: "מוסיף מדריך עברי ממוקד לתהליך מקומי שאינו מכוסה היטב במקורות בינלאומיים.", why_watch_en: "It adds focused Hebrew guidance for a local mapping workflow rarely covered by international sources.",
    safety_warnings_he: ["אין להשתמש בכלי ההמרה הלא־מאובטח המקושר בתיאור בלי לבדוק אותו; העדיפו כלי HTTPS אמין ואל תעלו קובץ שמכיל מידע רגיש."],
    safety_warnings_en: ["Do not use the unsecured conversion tool linked in the description without checking it; prefer a trusted HTTPS tool and never upload a file containing sensitive data."],
    related: ["N5DsF-4q98c", "UOI7yWHv07w"],
  },
  {
    ...navDefaults, id: "uJwRnbm74E4", source_type: "community_educator", content_type: "course_overview", quality_score: 3, confidence: "medium", language: "he",
    title_he: "אופרוד: התקנה והסבר על אפליקציית ניווט שטח", title_en: "Offroad app: installation and use for trail navigation",
    subtopics: ["navigation_apps", "offline_navigation"], tags: ["navigation", "offline_maps", "route_planning", "smartphone_navigation"],
    summary_he: "הדרכה עברית להתקנה הראשונית ולשימוש באפשרויות של אפליקציית אופרוד לניווט שטח עבור רוכבים, נהגים והולכי רגל.",
    summary_en: "A Hebrew walkthrough of initial installation and use of the Offroad navigation app for trail riders, drivers and hikers.",
    learning_points_he: ["להכיר את שלבי ההתקנה הראשוניים", "לזהות את אפשרויות הניווט העיקריות באפליקציה", "לבדוק את הממשק והזמינות העדכניים לפני הסתמכות בטיול"],
    learning_points_en: ["Understand the initial installation steps", "Identify the app's main navigation options", "Check current availability and interface before relying on it for a trip"],
    fit_for_he: "מתאים למי שמעדיף הדרכה בעברית ומוכן לבדוק שהאפליקציה עדיין זמינה ועדכנית.", fit_for_en: "For Hebrew-speaking users who will first verify that the app remains current and available.",
    why_watch_he: "מספק הסבר עברי מפורט, אך בגלל גיל הסרטון יש לראות בו מבוא ולא תיעוד ממשק עדכני.", why_watch_en: "It provides detailed Hebrew guidance, but its age makes it an introduction rather than current interface documentation.",
    related: ["_4xaX5MT94Y", "UOI7yWHv07w"],
  },
  {
    ...protectionDefaults, id: "v94eMFeojhc", source_type: "official_safety_program", content_type: "explainer", quality_score: 5, confidence: "high",
    title_he: "כיצד תוכנית CRASH בודקת בטיחות של קסדות אופנוע", title_en: "How the CRASH programme tests motorcycle-helmet safety",
    subtopics: ["helmet_testing", "helmet_ratings"], tags: ["protective_gear", "helmet", "helmet_testing", "safety"],
    summary_he: "הסבר רשמי של Transport for NSW על תוכנית CRASH ועל בדיקות מעבדה המשמשות לדירוג קסדות לפי בטיחות ונוחות לצרכן.",
    summary_en: "An official Transport for NSW explanation of the CRASH programme and the laboratory testing used to rate motorcycle helmets for safety and comfort.",
    learning_points_he: ["להבין מה מוסיף דירוג צרכני מעבר לעמידה בתקן", "להכיר את תפקיד בדיקות המעבדה בהשוואת קסדות", "להשתמש בדירוג ככלי נוסף לצד התאמה, תקן ומצב הקסדה"],
    learning_points_en: ["Understand what consumer ratings add beyond minimum compliance", "Recognise the role of laboratory testing in helmet comparison", "Use ratings alongside fit, standards and helmet condition"],
    fit_for_he: "מתאים לכל רוכב שבוחר קסדה ורוצה להבין את מקור ציוני הבטיחות.", fit_for_en: "For any rider choosing a helmet and wanting to understand where safety ratings come from.",
    why_watch_he: "מקור ציבורי רשמי וקצר שמסביר את שיטת הדירוג בלי למכור קסדה.", why_watch_en: "A concise official public source that explains the rating process without selling a helmet.",
    related: ["dSdKgAG-J-U", "dP4MoF5l3IE"],
  },
  {
    ...protectionDefaults, id: "dSdKgAG-J-U", source_type: "professional_instructor", content_type: "technique", quality_score: 4, confidence: "high",
    title_he: "התאמה נכונה של קסדת אופנוע", title_en: "Correct fitment of a motorcycle helmet",
    subtopics: ["helmet_fit", "beginner_gear"], tags: ["protective_gear", "helmet", "helmet_fit", "fit"],
    summary_he: "הדרכה לבחירת מידה ומבנה קסדה לפי צורת הראש, מיקום על הראש, שדה ראייה, סוג הרכיבה והאקלים, עם הסבר כיצד התאמה שגויה פוגעת ברכיבה.",
    summary_en: "Guidance on helmet size and shape, position, field of view, riding purpose and climate, including how poor fit can affect riding performance.",
    learning_points_he: ["לבדוק מידה וצורת ראש ולא רק היקף", "לוודא מיקום נכון ושדה ראייה היקפי", "להתאים את הקסדה לסוג השימוש ולאקלים"],
    learning_points_en: ["Check head shape as well as circumference", "Verify position and peripheral vision", "Match the helmet to use and climate"],
    fit_for_he: "מתאים לרוכבים לפני קניית קסדה או כאשר הקסדה הקיימת לוחצת, זזה או מגבילה ראייה.", fit_for_en: "For riders buying a helmet or troubleshooting pressure, movement or restricted vision.",
    why_watch_he: "מתמקד בהתאמה ובתפקוד ולא בדגם מסוים, ללא רכיב שיווקי מתועד.", why_watch_en: "It focuses on fit and function rather than a particular model, with no documented marketing component.",
    related: ["v94eMFeojhc", "dP4MoF5l3IE"],
  },
  {
    ...protectionDefaults, id: "dP4MoF5l3IE", source_type: "training_channel", content_type: "explainer", quality_score: 5, confidence: "high",
    title_he: "בחירת ציוד מגן: הסבר על שיטת תקני CE", title_en: "Choosing protective gear: the CE system explained",
    subtopics: ["gear_standards", "abrasion_resistance"], tags: ["protective_gear", "gear_standards", "abrasion_resistance", "safety"],
    summary_he: "הסבר פרקי על מערכת הסיווג האירופית לביגוד רכיבה, בדיקות שחיקה, קריעה ותפרים, רמות A/AA/AAA והצורך לבדוק שהמוצר אכן מוסמך.",
    summary_en: "A chaptered explanation of European protective-apparel classes, abrasion, tear and seam tests, A/AA/AAA levels and the need to verify actual certification.",
    learning_points_he: ["לקרוא את רמות A, AA ו־AAA בהקשר הנכון", "להבין אילו תכונות נבדקות מעבר לעובי הבד", "לוודא הצהרת הסמכה ולא להסתפק בטקסט פרסומי"],
    learning_points_en: ["Read A, AA and AAA levels in context", "Understand what is tested beyond fabric thickness", "Verify certification rather than relying on marketing copy"],
    fit_for_he: "מתאים למי שבוחר מעיל, מכנסיים או ג׳ינס רכיבה ורוצה להשוות רמת מיגון באופן שיטתי.", fit_for_en: "For riders comparing jackets, trousers or riding jeans by documented protection level.",
    why_watch_he: "מפריד בין טענת מוצר לבין סימון תקן ומלווה בכתוביות ידניות בעברית ובאנגלית.", why_watch_en: "It separates product claims from certification markings and includes manual Hebrew and English captions.",
    related: ["MnzwssLF1Po", "PQnTLz-CoTQ"],
  },
  {
    ...protectionDefaults, id: "MnzwssLF1Po", source_type: "training_channel", content_type: "explainer", quality_score: 4, confidence: "medium",
    title_he: "כיצד לבחור ציוד מגן ומיגון גוף", title_en: "How to choose protective gear and body armour",
    subtopics: ["body_armor_standards", "abrasion_vs_impact"], tags: ["protective_gear", "body_armor", "impact_protection", "abrasion_resistance"],
    summary_he: "הסבר על ההבדל בין עמידות בשחיקה לספיגת פגיעה, סימוני EN למגני גפיים וגב, תפרים, חום ואוורור ברכיבת אדוונצ׳ר.",
    summary_en: "An explanation of abrasion resistance versus impact absorption, EN markings for limb and back protectors, seams, heat and ventilation in adventure riding.",
    learning_points_he: ["להפריד בין הגנת שחיקה להגנת פגיעה", "לבדוק סימוני מגן ורמת כיסוי", "לאזן מיגון עם חום, אוורור והתאמה לשימוש"],
    learning_points_en: ["Separate abrasion protection from impact protection", "Check protector markings and coverage", "Balance protection with heat, ventilation and intended use"],
    fit_for_he: "מתאים לרוכבים שרוצים להבין מה באמת עושה מגן גוף בתוך בגד רכיבה.", fit_for_en: "For riders wanting to understand what armour inside riding apparel actually does.",
    why_watch_he: "נותן בסיס מושגי שימושי, אך יש לבדוק את נוסח התקנים העדכני משום שהסרטון ותיק.", why_watch_en: "It offers a useful conceptual foundation, but current standards wording should be checked because the video is older.",
    related: ["PQnTLz-CoTQ", "dP4MoF5l3IE"],
  },
  {
    ...protectionDefaults, id: "PQnTLz-CoTQ", source_type: "community_educator", content_type: "explainer", quality_score: 4, confidence: "high",
    title_he: "מיגון גוף מוסבר לרוכבים חדשים", title_en: "Motorcycle armour explained for new riders",
    subtopics: ["abrasion_vs_impact", "beginner_gear"], tags: ["protective_gear", "body_armor", "impact_protection", "safety"],
    summary_he: "מבוא לרוכבים חדשים על שריון בתוך ציוד רכיבה, סימוני CE וההבדל בין הגנת פגיעה לבין עמידות הבגד בשחיקה.",
    summary_en: "An introduction for new riders to armour in motorcycle gear, CE markings and the difference between impact protection and garment abrasion resistance.",
    learning_points_he: ["להבין מהו מגן פגיעה ומה אינו עושה", "להבחין בין שריון פנימי לבין מעטפת הבגד", "לשאול שאלות נכונות בעת קניית ציוד ראשון"],
    learning_points_en: ["Understand what impact armour does and does not do", "Distinguish internal armour from the garment shell", "Ask better questions when buying first riding gear"],
    fit_for_he: "מתאים במיוחד לרוכבים חדשים שמרגישים אבודים בין מונחי CE, שריון ושחיקה.", fit_for_en: "Especially useful to new riders navigating CE, armour and abrasion terminology.",
    why_watch_he: "מפרק מושגים בסיסיים בשפה נגישה בלי לקשור את ההסבר למוצר מסוים.", why_watch_en: "It breaks down basic concepts in accessible language without tying the explanation to one product.",
    related: ["MnzwssLF1Po", "dP4MoF5l3IE"],
  },
  {
    ...protectionDefaults, id: "EeT3531XRn4", source_type: "training_channel", content_type: "explainer", quality_score: 5, confidence: "high",
    title_he: "בחירת מגפי אדוונצ׳ר ודו־שימושי", title_en: "Choosing adventure and dual-sport boots",
    subtopics: ["protective_boots", "budget_vs_premium"], tags: ["protective_gear", "boots", "fit", "budget_comparison"],
    summary_he: "שמונה שיקולים לבחירת מגפי אדוונצ׳ר: הגנה מול נוחות, סגנון רכיבה ותוואי, קשיחות קרסול ושוק, עמידות, סוליה, מים, גובה ומידה.",
    summary_en: "Eight considerations for adventure boots: protection versus comfort, riding style and terrain, ankle and shin stiffness, durability, sole, water resistance, height and sizing.",
    learning_points_he: ["לאזן תנועתיות עם הגנת קרסול ושוק", "לבחון סוליה, חיבור, עמידות למים ואורך חיים", "למדוד בפועל עם הגרביים והציוד שבהם רוכבים"],
    learning_points_en: ["Balance mobility with ankle and shin protection", "Evaluate sole, construction, water resistance and longevity", "Try boots with the socks and equipment used for riding"],
    fit_for_he: "מתאים למי שמתלבט בין מגף אדוונצ׳ר נוח למגף שטח קשיח ומגן יותר.", fit_for_en: "For riders choosing between a comfortable adventure boot and a stiffer, more protective off-road boot.",
    why_watch_he: "הסרטון מבקר סקירות קמעונאיות ומציע מבחני בחירה שאפשר לבצע בלי להיצמד למותג.", why_watch_en: "It challenges retailer-led reviews and proposes brand-neutral checks riders can perform.",
    related: ["dP4MoF5l3IE", "XukrXZdtYds"],
  },
  {
    ...protectionDefaults, id: "XukrXZdtYds", source_type: "experienced_rider", content_type: "case_study", quality_score: 4, confidence: "high",
    title_he: "ציוד מיגון לאחר שתי תאונות: מקרה בוחן", title_en: "Protective riding gear after two crashes: a case study",
    subtopics: ["crash_case_study", "abrasion_vs_impact"], tags: ["protective_gear", "crash_case_study", "helmet", "boots"],
    summary_he: "צוות מבחנים מציג ציוד שנלבש בשתי תאונות אמיתיות ובוחן את מצב הפריטים וההגנה שסיפקו לרוכבים לאחר האירוע.",
    summary_en: "A test-riding team reviews the gear worn in two real crashes and examines the condition of the items and the protection they provided.",
    learning_points_he: ["לבדוק אילו אזורים ומנגנונים עבדו באירוע אמיתי", "לזהות בלאי ונזק שמחייבים החלפה", "להבדיל בין מקרה בוחן אישי לבין הוכחה כללית לביצועי מוצר"],
    learning_points_en: ["Observe which areas and mechanisms worked in a real incident", "Recognise wear or damage that requires replacement", "Distinguish a personal case study from general product-performance proof"],
    fit_for_he: "מתאים לרוכבים שרוצים להבין כיצד בוחנים ציוד אחרי נפילה בלי להפוך סיפור אישי להמלצת קנייה.", fit_for_en: "For riders learning how to inspect gear after a crash without turning an anecdote into a buying recommendation.",
    why_watch_he: "מציג תוצאה בעולם האמיתי ומאפשר ללמוד מן הנזק, תוך שמירה על ההקשר המצומצם של שני מקרים.", why_watch_en: "It shows real-world outcomes while retaining the limited context of two incidents.",
    related: ["EeT3531XRn4", "v94eMFeojhc"],
  },
  {
    ...commsDefaults, id: "msN_yCSN3dM", source_type: "training_channel", content_type: "explainer", quality_score: 5, confidence: "high",
    title_he: "דיבוריות לאופנוע: שימושי או עוד גאדג׳ט מסיח?", title_en: "Motorcycle intercoms: useful tool or distracting gadget?",
    subtopics: ["bluetooth_vs_mesh", "safe_intercom_use", "budget_vs_premium"], tags: ["communication", "intercom", "bluetooth", "mesh", "distraction_management"],
    summary_he: "סקירה לא־ממומנת של דיבוריות אדוונצ׳ר: Bluetooth מול Mesh, רוכב־מורכב וקבוצה, איכות שמע, סוללה, תפעול בכפפות, מחיר והסחת דעת.",
    summary_en: "A non-sponsored overview of adventure intercoms: Bluetooth versus mesh, rider-passenger and groups, audio, battery, glove controls, price and distraction.",
    learning_points_he: ["להבחין בין חיבור Bluetooth נקודתי לרשת Mesh קבוצתית", "להבין מה מקבלים במערכת פשוטה לעומת יקרה", "לקבוע כללי שימוש שמצמצמים הסחת דעת"],
    learning_points_en: ["Distinguish point-to-point Bluetooth from group mesh", "Understand what entry-level and premium systems add", "Set usage rules that reduce distraction"],
    fit_for_he: "מתאים למי ששואל האם הוא בכלל צריך דיבורית ומה ההבדל בין מערכת זולה ליקרה.", fit_for_en: "For riders asking whether they need an intercom and what premium systems add over basic units.",
    why_watch_he: "הערוץ מצהיר על הימנעות מחסויות והסרטון מציג גם יתרונות וגם סיכוני הסחת דעת.", why_watch_en: "The channel states that it avoids sponsorships, and the video covers benefits as well as distraction risk.",
    related: ["K9tcqL8KOgk", "7wVIvMGTMFs"],
  },
  {
    ...commsDefaults, id: "K9tcqL8KOgk", source_type: "experienced_rider", content_type: "case_study", quality_score: 4, confidence: "high",
    title_he: "Cardo Spirit: סקירה לא־ממומנת, התקנה ובדיקת כביש", title_en: "Cardo Spirit: non-sponsored review, installation and road test",
    subtopics: ["budget_bluetooth", "installation_fit_audio"], tags: ["communication", "intercom", "bluetooth", "helmet_audio"],
    summary_he: "סקירה שמצהירה שאינה ממומנת ומכסה מיקום דגם Cardo Spirit בטווח המחירים, פתיחת האריזה, התקנה בקסדה ובדיקת שמע על הכביש במהירות.",
    summary_en: "A stated non-sponsored review covering the Cardo Spirit's place in the range, unboxing, helmet installation and an at-speed road audio test.",
    learning_points_he: ["לזהות אילו יכולות בסיסיות מספיקות לשימוש אישי או זוגי", "לראות את רצף ההתקנה לפני פתיחת הקסדה", "להבין מדוע בדיקת שמע בעמידה אינה מספיקה לבדה"],
    learning_points_en: ["Identify which basic features may be enough for solo or pair use", "See the installation sequence before opening the helmet", "Understand why a stationary audio check alone is insufficient"],
    fit_for_he: "מתאים למי ששוקל דיבורית Bluetooth בסיסית ואינו צריך רשת Mesh לקבוצה גדולה.", fit_for_en: "For riders considering a basic Bluetooth intercom without large-group mesh needs.",
    why_watch_he: "משלב התקנה ובדיקת כביש ומסמן במפורש שהסקירה אינה ממומנת.", why_watch_en: "It combines installation with a road test and explicitly states that the review is not sponsored.",
    related: ["wQkrAP1KEAg", "msN_yCSN3dM"],
  },
  {
    ...commsDefaults, id: "7wVIvMGTMFs", source_type: "community_educator", content_type: "explainer", quality_score: 3, confidence: "medium",
    title_he: "השוואת דיבוריות לקבוצות: Sena, Cardo, BluArmor ו־EJEAS", title_en: "Group-riding intercom comparison: Sena, Cardo, BluArmor and EJEAS",
    subtopics: ["multi_brand_comparison", "group_mesh", "budget_vs_premium"], tags: ["communication", "intercom", "mesh", "budget_comparison", "group_riding"],
    summary_he: "השוואת אפשרויות לדיבור קבוצתי לפי גודל קבוצה, טווח ויציבות חיבור, מיקרופון וסינון רעש, סוללה, תאימות קסדה והבדלי תקציב.",
    summary_en: "A group-intercom comparison by group size, range and connection stability, microphone and noise control, battery, helmet compatibility and budget.",
    learning_points_he: ["להגדיר קודם את גודל הקבוצה ודפוס החיבור", "להשוות טווח, חזרה לרשת, שמע וסוללה ולא רק מחיר", "לבדוק תאימות בין החברים לפני רכישה"],
    learning_points_en: ["Define group size and connection pattern first", "Compare range, rejoining, audio and battery rather than price alone", "Check interoperability among riders before purchase"],
    fit_for_he: "מתאים לקבוצה שמנסה לבנות רשימת דרישות לפני השוואת כמה מותגים.", fit_for_en: "For a group building requirements before comparing several brands.",
    why_watch_he: "מרחיב מעבר לשני המותגים הבולטים, אך תיאור שיטת הבדיקה מוגבל ולכן הרשומה מסומנת בביטחון בינוני.", why_watch_en: "It broadens the field beyond two leading brands, but limited test-method detail keeps the classification confidence at medium.",
    related: ["msN_yCSN3dM", "K9tcqL8KOgk"],
  },
  {
    ...commsDefaults, id: "wQkrAP1KEAg", source_type: "community_educator", content_type: "maintenance_howto", quality_score: 4, confidence: "high", language: "he",
    title_he: "התקנת דיבורית PackTalk Edge בקסדה, צעד אחר צעד", title_en: "Installing a PackTalk Edge intercom in a helmet, step by step",
    subtopics: ["installation_fit_audio", "helmet_compatibility"], tags: ["communication", "intercom", "helmet_audio", "fit"],
    summary_he: "מדריך עברי להתקנת דיבורית PackTalk Edge בקסדות Arai ו־Shoei, עם שלבי מיקום, התאמה וטיפים למניעת טעויות נפוצות.",
    summary_en: "A Hebrew step-by-step guide to installing a PackTalk Edge in Arai and Shoei helmets, including placement, fit and tips for avoiding common mistakes.",
    learning_points_he: ["להכין את הקסדה והחלקים לפני ההתקנה", "למקם רמקולים ומיקרופון בלי ליצור נקודות לחץ", "לבדוק נוחות ושמע בעמידה לפני יציאה לכביש"],
    learning_points_en: ["Prepare the helmet and parts before installation", "Position speakers and microphone without creating pressure points", "Check comfort and audio while stationary before riding"],
    fit_for_he: "מתאים לדוברי עברית שמתקינים יחידה דומה בקסדת Arai או Shoei ובודקים התאמה לפי הוראות היצרן.", fit_for_en: "For Hebrew-speaking users installing a similar unit in an Arai or Shoei helmet while following manufacturer instructions.",
    why_watch_he: "ממלא פער בהדרכה עברית ומדגים התקנה בפועל ללא קישור רכישה, חסות או קוד הנחה מתועדים.", why_watch_en: "It fills a Hebrew-language gap and demonstrates installation with no documented purchase link, sponsorship or discount code.",
    related: ["K9tcqL8KOgk", "msN_yCSN3dM"],
  },
];

function normaliseLanguage(spec, evidence) {
  if (spec.language) return spec.language;
  return evidence.language === "iw" || /[\u0590-\u05ff]/u.test(evidence.title_original) ? "he" : "en";
}

function supportedSubtitleLanguages(evidence) {
  const values = new Set();
  for (const value of evidence.subtitle_languages || []) {
    if (value === "iw" || value === "he") values.add("he");
    if (value === "en" || value.startsWith("en-")) values.add("en");
  }
  return [...values];
}

function makeVideo(spec) {
  const evidence = evidenceById.get(spec.id);
  if (!evidence || evidence.status !== "pass" || evidence.availability !== "public") {
    throw new Error(`Missing active-public evidence for ${spec.id}`);
  }
  const contentEvidence = ["description"];
  if (evidence.chapters?.length) contentEvidence.push("chapters");
  const evidenceLabelHe = contentEvidence.includes("chapters") ? "תיאור ופרקים מתועדים" : "תיאור מפורט";
  const evidenceLabelEn = contentEvidence.includes("chapters") ? "description and documented chapters" : "a detailed description";
  return {
    id: `yt-${spec.id}`,
    youtube_video_id: spec.id,
    youtube_url: evidence.youtube_url,
    thumbnail_url: `https://i.ytimg.com/vi/${spec.id}/hqdefault.jpg`,
    title_original: evidence.title_original,
    title_he: spec.title_he,
    channel_name: evidence.channel_name,
    channel_url: evidence.channel_url,
    published_date: evidence.published_date,
    duration_seconds: evidence.duration_seconds,
    language: normaliseLanguage(spec, evidence),
    subtitle_languages: supportedSubtitleLanguages(evidence),
    domain: spec.domain,
    primary_category: spec.primary_category,
    secondary_categories: spec.secondary_categories,
    tags: spec.tags,
    skill_level: spec.skill_level,
    risk_level: spec.risk_level,
    motorcycle_types: spec.motorcycle_types,
    motorcycle_weight_classes: spec.motorcycle_weight_classes,
    terrain_types: spec.terrain_types,
    road_conditions: spec.road_conditions,
    summary_he: spec.summary_he,
    learning_points_he: spec.learning_points_he,
    fit_for_he: spec.fit_for_he,
    why_watch_he: spec.why_watch_he,
    exercises_he: spec.exercises_he,
    equipment_he: spec.equipment_he,
    safety_warnings_he: spec.safety_warnings_he,
    common_mistakes_he: spec.common_mistakes_he,
    chapters: evidence.chapters || [],
    quality_score: spec.quality_score,
    quality_reason_he: `הרשומה נשענת על ${evidenceLabelHe}, מטא־דאטה ציבורית ובדיקת קישור חוזרת. לא הורדו הסרטון או תמליל, ולא תועדה צפייה מלאה. ביטחון הסיווג: ${spec.confidence === "high" ? "גבוה" : "בינוני"}.`,
    source_type: spec.source_type,
    contains_marketing: false,
    related_video_ids: spec.related.map((id) => `yt-${id}`),
    verification: {
      link_status: "active_public",
      metadata_verified: true,
      content_evidence_types: contentEvidence,
      classification_confidence: spec.confidence,
      notes_he: `הקישור והמטא־דאטה אומתו מחדש באמצעות yt-dlp ב־${checkedDate}. הסיווג מבוסס על ${evidenceLabelHe}; לא הורדו הסרטון, השמע או תמליל, ולא נטענה צפייה מלאה. לא נמצא רכיב שיווקי בתיאור שנבדק.`,
      notes_en: `The public link and metadata were rechecked with yt-dlp on ${checkedDate}. Classification uses ${evidenceLabelEn}; no video, audio or transcript was downloaded, and no full viewing is claimed. No marketing component was found in the reviewed description.`,
    },
    last_checked: checkedDate,
    title_en: spec.title_en,
    summary_en: spec.summary_en,
    learning_points_en: spec.learning_points_en,
    fit_for_en: spec.fit_for_en,
    why_watch_en: spec.why_watch_en,
    exercises_en: spec.exercises_en,
    equipment_en: spec.equipment_en,
    safety_warnings_en: spec.safety_warnings_en,
    common_mistakes_en: spec.common_mistakes_en,
    quality_reason_en: `This entry is grounded in ${evidenceLabelEn}, public metadata and a fresh link check. No video or transcript was downloaded and no full viewing is claimed. Classification confidence: ${spec.confidence}.`,
    subtopics: spec.subtopics,
    content_type: spec.content_type,
  };
}

function addTaxonomyItem(collection, item) {
  if (collection.some((entry) => entry.id === item.id)) return;
  collection.push(item);
}

const categories = readJson("data/categories.json");
for (const [collectionName, rows] of Object.entries(taxonomyItems)) {
  for (const row of rows) {
    const [id, name_he, name_en, description_he, description_en] = row;
    addTaxonomyItem(categories[collectionName], {
      id,
      name_he,
      name_en,
      description_he: description_he || `תג מבוקר: ${name_he}.`,
      description_en: description_en || `Controlled topic tag: ${name_en}.`,
    });
  }
}
for (const collection of Object.values(categories)) {
  if (!Array.isArray(collection)) continue;
  for (const item of collection) {
    if (!item || typeof item !== "object" || !item.id || !item.name_he || !item.name_en) continue;
    item.description_he ||= `מונח מבוקר במדריך: ${item.name_he}.`;
    item.description_en ||= `Controlled guide term: ${item.name_en}.`;
  }
}
categories.domain_category_map.touring_travel ||= [];
if (!categories.domain_category_map.touring_travel.includes("intercoms_communications")) {
  categories.domain_category_map.touring_travel.push("intercoms_communications");
}
categories.version = "3.0.0";
categories.updated = checkedDate;

let videos = readJson("data/videos.json");
const existingIds = new Set(videos.map((video) => video.youtube_video_id));
const additions = specs.map(makeVideo).filter((video) => !existingIds.has(video.youtube_video_id));
videos.push(...additions);

// A full release-gate check on 2026-08-05 found these older records no longer
// publicly embeddable. Keep the public catalogue honest: remove the dead
// records and every internal relationship that pointed at them.
const unavailableIds = new Set(["yt-M6d1cWB-4gY", "yt-6hgkx7ZScqY", "yt-5SlHGlyzF7w"]);
const removedUnavailableCount = videos.filter((video) => unavailableIds.has(video.id)).length;
videos = videos.filter((video) => !unavailableIds.has(video.id));
for (const video of videos) {
  video.related_video_ids = (video.related_video_ids || []).filter((id) => !unavailableIds.has(id));
}

for (const video of videos) {
  if (video.primary_category === "training_courses") {
    video.subtopics = (video.subtopics || []).filter((id) => !["rain_strategy", "water_assessment"].includes(id));
    if (!video.subtopics.includes("course_selection")) video.subtopics.unshift("course_selection");
  }
}

for (const id of ["yt-hDX4TBsPKLU", "yt-lcauMhznleg", "yt-TujQZ4bRgjQ", "yt-kInjwfYnVYU"]) {
  const video = videos.find((item) => item.id === id);
  if (!video) continue;
  if (!video.secondary_categories.includes(video.primary_category)) video.secondary_categories.unshift(video.primary_category);
  video.domain = "touring_travel";
  video.primary_category = "route_navigation";
}

for (const id of ["yt-_G0C8nEi5Yg", "yt-jkkKIyAJH_k"]) {
  const video = videos.find((item) => item.id === id);
  if (!video) continue;
  video.source_type = "manufacturer";
  video.contains_marketing = true;
}

writeJson("data/categories.json", categories);
writeJson("data/videos.json", videos);

const learningPaths = readJson("data/learning-paths.json");
const videoById = new Map(videos.map((video) => [video.id, video]));
const step = (order, goal_he, goal_en, explanation_he, explanation_en, primary, alternatives, risk = "low") => ({
  order,
  goal_he,
  goal_en,
  explanation_he,
  explanation_en,
  primary_video_ids: primary,
  alternative_video_ids: alternatives,
  equipment_he: ["ציוד מיגון מלא", "סביבה בטוחה המתאימה לשלב"],
  equipment_en: ["Full protective gear", "A safe environment appropriate to the step"],
  risk_level: risk,
  warning_he: risk === "high"
    ? "אין לבצע את השלב לבד או ללא הערכת תנאים; הדרכה מקצועית ותוכנית יציאה קודמות לתרגול."
    : "אין לעבור לשלב הבא לפני שהבסיס יציב; קורס והדרכה מעשית עדיפים על ניסוי עצמי.",
  warning_en: risk === "high"
    ? "Do not attempt this alone or without assessing conditions; professional instruction and an exit plan come first."
    : "Do not advance before the foundation is stable; professional instruction is preferable to self-experimentation.",
});

const navigationStep = (order, goal_he, goal_en, explanation_he, explanation_en, primary, alternatives) => ({
  ...step(order, goal_he, goal_en, explanation_he, explanation_en, primary, alternatives),
  equipment_he: ["טלפון או GPS טעון", "מקור כוח וקיבוע המתאימים למכשיר", "קובץ GPX ומפת גיבוי לבדיקה"],
  equipment_en: ["A charged phone or GPS", "Power and mounting appropriate to the device", "A GPX file and backup map for testing"],
  warning_he: "את ההתקנה, ההקלדה ושינויי המסלול מבצעים בעמידה בלבד; בזמן רכיבה הקשב נשאר בדרך ובתוואי.",
  warning_en: "Install, type and change routes only while stopped; while riding, keep attention on the road and terrain.",
});

const pathSteps = {
  "navigation-gpx": [
    navigationStep(1, "מגדירים יעד, נקודות מפתח ומגבלות", "Define the destination, key points and constraints", "מתחילים ביעד, דלק, מים, נקודות יציאה ותנאי הדרך ורק אחר כך בוחרים אפליקציה או מכשיר.", "Start with the destination, fuel, water, exit points and route constraints before choosing an app or device.", ["yt-lcauMhznleg", "yt-iHz2GH6L7AY"], ["yt-hDX4TBsPKLU"]),
    navigationStep(2, "בוחרים טלפון או GPS ייעודי", "Choose a phone or dedicated GPS", "משווים עמידות, עבודה בכפפות, קריאות מסך, עלות, מזג אוויר וגיבוי במקום לבחור לפי גודל המסך בלבד.", "Compare durability, glove use, screen readability, cost, weather exposure and backup rather than choosing by screen size alone.", ["yt-OiOgLX5AwLQ", "yt-0Oa8Hc9AG4c"], ["yt-hDX4TBsPKLU"]),
    navigationStep(3, "מכינים מכשיר, כוח וקיבוע", "Prepare the device, power and mounting", "בודקים מראש אספקת חשמל, קיבוע, גשם, כפפות וקריאות; טלפון אישי נשאר גיבוי אם משתמשים במכשיר ניווט נפרד.", "Check power, mounting, rain, gloves and readability in advance; keep the personal phone as backup when using a separate navigation device.", ["yt-hDX4TBsPKLU", "yt-0Oa8Hc9AG4c"], ["yt-OiOgLX5AwLQ"]),
    navigationStep(4, "מבינים Route, Track ו־GPX", "Understand Route, Track and GPX", "לומדים להבדיל בין מסלול מחושב לבין עקבה קבועה, ומוודאים שהאפליקציה אינה מחשבת מחדש תוואי שונה.", "Distinguish a calculated route from a fixed track and verify that the app does not recalculate a different course.", ["yt-N5DsF-4q98c", "yt-UOI7yWHv07w"], ["yt-_4xaX5MT94Y"]),
    navigationStep(5, "יוצרים, עורכים, ממירים ומשתפים GPX", "Create, edit, convert and share GPX", "עורכים נקודות ציון, מייצאים קובץ, בודקים אותו באפליקציה נוספת וממירים פורמט רק כאשר כלי היעד דורש זאת.", "Edit waypoints, export the file, check it in another app and convert format only when the target tool requires it.", ["yt-N5DsF-4q98c", "yt-_4xaX5MT94Y"], ["yt-iHz2GH6L7AY"]),
    navigationStep(6, "מתקינים ומגדירים אפליקציית ניווט", "Install and configure a navigation app", "עוברים על התקנה ראשונית, בחירת פרופיל, ייבוא מסלול ואפשרויות ניווט לפני שמסתמכים על האפליקציה בטיול.", "Complete initial installation, profile selection, route import and navigation settings before relying on the app during a trip.", ["yt-uJwRnbm74E4", "yt-UOI7yWHv07w"], ["yt-hDX4TBsPKLU"]),
    navigationStep(7, "מורידים מפות ובודקים עבודה לא מקוונת", "Download maps and test offline use", "מורידים מראש מפות ונתוני עניין, פותחים את ה־GPX ומבצעים בדיקת שולחן בלי קליטה לפני היציאה.", "Download maps and points of interest, open the GPX and perform a stationary no-signal test before departure.", ["yt-UOI7yWHv07w", "yt-hDX4TBsPKLU"], ["yt-lcauMhznleg"]),
    navigationStep(8, "בונים גיבוי ומשתפים עם הקבוצה", "Build a backup and share with the group", "שומרים עותק נוסף של המסלול, משתפים נקודות מפגש ומוודאים שהניווט נשאר אפשרי גם אם המכשיר הראשי או הקליטה נכשלים.", "Keep another route copy, share meeting points and verify that navigation remains possible if the primary device or reception fails.", ["yt-OiOgLX5AwLQ", "yt-lcauMhznleg"], ["yt-N5DsF-4q98c"]),
  ],
  "road-control-lab": [
    step(7, "לנהל אחיזה בכביש רטוב", "Manage grip on wet roads", "לומדים לזהות שינויי אחיזה, להחליק פעולות ולהגדיל מרווחים — ואת התרגול מבצעים רק בתנאים מבוקרים.", "Learn to recognise grip changes, smooth inputs and increase margins; practise only in controlled conditions.", ["yt-wu01iLFdTE0", "yt-Qx6G0gkQ048"], ["yt-ko70RgiF5OQ"], "medium"),
    step(8, "לבנות אסטרטגיית זיהוי סכנות", "Build a hazard-perception strategy", "מחברים מיקום נתיב, צמתים, ראייה קדימה ותכנון מוצא לפני שמגבירים קצב.", "Connect lane position, intersections, forward vision and escape planning before increasing pace.", ["yt-NN1twMtJrlA", "yt-PLH1U7SnnZA"], ["yt-l_vLv-Fds5g"], "medium"),
  ],
  "offroad-surface-progression": [
    step(7, "לנהל בוץ וקרקע רטובה", "Manage mud and wet terrain", "עוברים בהדרגה מתוואי יבש לאחיזה משתנה, עם קצב נמוך, מרחק עצירה ותוכנית נסיגה.", "Progress from dry terrain to changing grip with low speed, stopping distance and a retreat plan.", ["yt-wsokPULhmv0", "yt-MqIxMyAUURM"], ["yt-rlcGpTJl16U"], "high"),
    step(8, "להעריך מעבר מים", "Assess a water crossing", "לומדים לבדוק עומק, זרימה, קרקע, כניסה ויציאה, ומוותרים כשאין ודאות מספקת.", "Assess depth, flow, bed, entry and exit, and turn back when uncertainty remains.", ["yt-WkeMWUDkqgc", "yt-VKCEzq_fUNg"], ["yt-n5d2muv5OtE"], "high"),
  ],
  "adventure-setup-pretrip": [
    step(7, "לבנות מערכת ניווט וגיבוי", "Build navigation and backup", "בוחרים טלפון או GPS לפי הצורך, מורידים מפות ומסלול ובודקים מקור חשמל וגיבוי לפני יציאה.", "Choose phone or GPS by need, download maps and route, and verify power and backup before departure.", ["yt-OiOgLX5AwLQ", "yt-UOI7yWHv07w"], ["yt-N5DsF-4q98c"]),
    step(8, "להתאים את מערכת המיגון", "Fit the protection system", "מסיימים את ההכנה בבדיקת תקן, התאמת קסדה, מגפיים ומיגון גוף לפי סוג הרכיבה.", "Finish preparation by checking standards and fitting helmet, boots and body protection to the ride.", ["yt-v94eMFeojhc", "yt-dSdKgAG-J-U"], ["yt-dP4MoF5l3IE"]),
  ],
  "group-tour-readiness": [
    step(7, "להגדיר תקשורת קבוצתית", "Configure group communication", "מחליטים אם נדרש Bluetooth או Mesh, מתקינים ובודקים בעמידה וקובעים כלל להפסקת שיחה כשעומס הרכיבה עולה.", "Choose Bluetooth or mesh, install and test while stationary, and agree to stop talking when riding workload rises.", ["yt-msN_yCSN3dM", "yt-K9tcqL8KOgk"], ["yt-wQkrAP1KEAg"]),
    step(8, "לשתף מסלול ולבנות גיבוי", "Share the route and build backup", "משתפים GPX ונקודות מפגש, מוודאים מפות לא מקוונות וקובעים מה עושים אם הקבוצה מתפצלת.", "Share GPX and meeting points, verify offline maps, and agree what happens if the group splits.", ["yt-OiOgLX5AwLQ", "yt-N5DsF-4q98c"], ["yt-UOI7yWHv07w"]),
  ],
};

for (const pathItem of learningPaths) {
  if (pathItem.id === "navigation-gpx") {
    pathItem.description_he = "מסלול מעשי בן שמונה צעדים: תכנון, טלפון מול GPS, כוח וקיבוע, GPX, התקנת אפליקציה, מפות לא מקוונות וגיבוי.";
    pathItem.description_en = "An eight-step practical path covering planning, phone versus GPS, power and mounting, GPX, app setup, offline maps and backup.";
  }
  const additionsForPath = pathSteps[pathItem.id] || [];
  for (const addition of additionsForPath) {
    const existing = pathItem.steps.find((item) => item.order === addition.order);
    if (existing) Object.assign(existing, addition);
    else pathItem.steps.push(addition);
  }
  for (const pathStep of pathItem.steps) {
    pathStep.primary_video_ids = (pathStep.primary_video_ids || []).filter((id) => !unavailableIds.has(id));
    pathStep.alternative_video_ids = (pathStep.alternative_video_ids || []).filter((id) => !unavailableIds.has(id));
  }
  pathItem.steps.sort((left, right) => left.order - right.order);
  if (!pathSteps[pathItem.id]) continue;
  for (const pathStep of pathItem.steps) {
    const primaryCategory = videoById.get(pathStep.primary_video_ids[0])?.primary_category;
    if (!primaryCategory) continue;
    const candidates = videos
      .filter((video) => video.primary_category === primaryCategory)
      .sort((left, right) => Number(left.contains_marketing) - Number(right.contains_marketing) || right.quality_score - left.quality_score || left.id.localeCompare(right.id));
    while (pathStep.primary_video_ids.length + pathStep.alternative_video_ids.length < 2) {
      const candidate = candidates.find((video) => !pathStep.primary_video_ids.includes(video.id) && !pathStep.alternative_video_ids.includes(video.id));
      if (!candidate) break;
      pathStep.primary_video_ids.push(candidate.id);
    }
    if (!pathStep.alternative_video_ids.length) {
      const candidate = candidates.find((video) => !pathStep.primary_video_ids.includes(video.id));
      if (candidate) pathStep.alternative_video_ids.push(candidate.id);
    }
  }
  if (pathItem.id === "group-tour-readiness") {
    const packingStep = pathItem.steps.find((item) => item.order === 5);
    if (packingStep && !packingStep.alternative_video_ids.length && videoById.has("yt-jevfjCDOddA")) {
      packingStep.alternative_video_ids.push("yt-jevfjCDOddA");
    }
  }
}
learningPaths.version = "3.0.0";
learningPaths.updated = checkedDate;
writeJson("data/learning-paths.json", learningPaths);

const travel = readJson("data/travel-guides.json");
travel.navigation_apps = [
  {
    name: "OsmAnd", type_he: "אפליקציית מפות וניווט", type_en: "Mapping and navigation app",
    best_for_he: "מפות לא מקוונות, מעקב אחר Track, ייבוא GPX, פרופילים ונתוני מפה עשירים.", best_for_en: "Offline maps, track following, GPX import, profiles and detailed map data.",
    capabilities_he: ["מפות לא מקוונות", "ייבוא GPX", "פרופילים", "הקלטת עקבות"], capabilities_en: ["Offline maps", "GPX import", "Profiles", "Track recording"],
    advantages_he: ["גמיש מאוד לשטח ולכביש", "מאפשר להכין את כל הנתונים מראש", "זמין ב־Android וב־iOS"], advantages_en: ["Highly flexible for road and trail use", "Supports advance offline preparation", "Available on Android and iOS"],
    limitations_he: ["עקומת לימוד וממשק צפוף", "הגדרה לא נכונה עלולה לחשב Route שונה מן ה־Track"], limitations_en: ["Learning curve and dense interface", "A poor configuration can calculate a route that differs from the track"],
    setup_he: "מורידים מפה, מייבאים GPX, מציגים אותו, מפעילים מצב טיסה ובודקים שהכול נשאר זמין.", setup_en: "Download the map, import and display the GPX, enable airplane mode and verify that everything remains available.",
    caution_he: "לא מניחים שהמסלול חוקי או עביר רק מפני שהוא מופיע על המפה.", caution_en: "A line on the map does not prove that the route is legal or passable.",
    source_url: "https://www.osmand.net/docs/user/personal/tracks/manage-tracks/", video_ids: ["yt-UOI7yWHv07w", "yt-N5DsF-4q98c"],
  },
  {
    name: "אופרוד / Off-Road", type_he: "אפליקציית ניווט שטח ישראלית", type_en: "Israeli off-road navigation app",
    best_for_he: "מפות שטח בישראל, עבודה ללא קליטה, מסלולים קהילתיים, הקלטה ושיתוף מיקום בקבוצה.", best_for_en: "Israeli trail maps, offline use, community routes, track recording and group location sharing.",
    capabilities_he: ["מפות לא מקוונות", "מסלולים ונקודות עניין", "הקלטה", "ניווט קבוצתי"], capabilities_en: ["Offline maps", "Routes and POIs", "Track recording", "Group navigation"],
    advantages_he: ["ממשק ותוכן מקומי בעברית", "מאגר מסלולים ויכולות קבוצה", "סרטון התקנה ושימוש בעברית"], advantages_en: ["Hebrew interface and local content", "Route library and group features", "A Hebrew setup and use tutorial"],
    limitations_he: ["ממוקדת בעיקר בישראל", "סרטון ההדרכה מ־2019 ולכן הממשק והיכולות עשויים להשתנות"], limitations_en: ["Primarily focused on Israel", "The tutorial is from 2019, so the interface and capabilities may have changed"],
    setup_he: "מורידים מפה ומסלול, בודקים הרשאות מיקום וסוללה, פותחים הכול ללא קליטה ומגדירים שיתוף קבוצתי רק אם נדרש.", setup_en: "Download the map and route, check location and battery permissions, test everything without coverage and enable group sharing only when needed.",
    caution_he: "מסלול קהילתי אינו אישור לחוקיות או לעבירות; בודקים מגבלות, שערים ותנאים ומחזיקים גיבוי.", caution_en: "A community route is not proof of legality or passability; check restrictions, gates and conditions and keep a backup.",
    source_url: "https://off-road.io/user_updates", video_ids: ["yt-uJwRnbm74E4"],
  },
  {
    name: "REVER", type_he: "תכנון ושיתוף רכיבות", type_en: "Ride planning and sharing",
    best_for_he: "תכנון רכיבות, שיתוף, מעקב, GPX ומפות לא מקוונות בתוך קהילה.", best_for_en: "Ride planning, sharing, tracking, GPX and offline maps within a community-oriented service.",
    capabilities_he: ["תכנון מסלול", "שיתוף", "GPX", "מפות לא מקוונות"], capabilities_en: ["Route planning", "Sharing", "GPX", "Offline maps"],
    advantages_he: ["תכנון ושיתוף באותה מערכת", "כלי קהילה ומעקב"], advantages_en: ["Planning and sharing in one service", "Community and tracking tools"],
    limitations_he: ["חלק מהיכולות תלויות חשבון או מנוי", "העברת מסלול ל־Garmin נעשית דרך ייצוא GPX"], limitations_en: ["Some capabilities depend on an account or subscription", "Transfer to Garmin uses GPX export rather than built-in sync"],
    setup_he: "מייצאים עותק GPX, מורידים Route ומפת בסיס לשימוש לא מקוון ובודקים אותם בלי קליטה.", setup_en: "Export a GPX backup, download the route and basemap for offline use, then test without coverage.",
    caution_he: "בודקים מראש אילו תכונות כלולות בחשבון הפעיל ולא מסתמכים על סנכרון יחיד.", caution_en: "Check which features are included in the active plan and keep a separate backup.",
    source_url: "https://www.rever.co/help/using-rever", video_ids: ["yt-N5DsF-4q98c"],
  },
  {
    name: "Gaia GPS", type_he: "מפות שכבתיות ותכנון שטח", type_en: "Layered maps and outdoor planning",
    best_for_he: "שכבות מפה, תכנון Route, נקודות ציון, GPX ומפות שהורדו מראש.", best_for_en: "Map layers, route planning, waypoints, GPX and maps downloaded in advance.",
    capabilities_he: ["שכבות מפה", "ייבוא GPX", "נקודות ציון", "מפות לא מקוונות"], capabilities_en: ["Map layers", "GPX import", "Waypoints", "Offline maps"],
    advantages_he: ["שילוב שכבות ותוואי בתכנון", "תהליך GPX ברור בין web למכשיר"], advantages_en: ["Layer and terrain context for planning", "Clear GPX workflow between web and device"],
    limitations_he: ["כיסוי ורישוי משתנים בין שכבות", "יש להוריד בפועל ולא להסתמך על מטמון"], limitations_en: ["Coverage and licensing vary by layer", "Maps must be downloaded rather than assumed to be cached"],
    setup_he: "מייבאים GPX, מורידים את שכבות המפה לאזור הנסיעה ומוודאים שהקובץ והמפה זמינים במצב טיסה.", setup_en: "Import the GPX, download map layers for the ride area and verify both file and map in airplane mode.",
    caution_he: "שכבת מפה יפה אינה תחליף לבדיקת חוקיות, שערים, מזג אוויר ותנאי מעבר.", caution_en: "A detailed map layer does not replace checks for legality, gates, weather and passability.",
    source_url: "https://help.gaiagps.com/hc/en-us/articles/115003639448-Does-Gaia-GPS-work-offline", video_ids: ["yt-N5DsF-4q98c"],
  },
  {
    name: "DMD2", type_he: "Dashboard וניווט ל־Android", type_en: "Android riding dashboard and navigation",
    best_for_he: "ממשק רכיבה למכשירי Android מוקשחים או טאבלטים ייעודיים, עם דגש על תפעול מהכידון.", best_for_en: "A riding interface for rugged Android phones or dedicated tablets, with emphasis on handlebar operation.",
    capabilities_he: ["Dashboard", "Android", "חומרה ייעודית", "תפעול מהכידון"], capabilities_en: ["Dashboard", "Android", "Dedicated hardware", "Handlebar control"],
    advantages_he: ["מסך וממשק שמיועדים לרכיבה", "יכול לאחד ניווט ונתוני אופנוע במערכת אחת"], advantages_en: ["Display and interface designed around riding", "Can combine navigation and motorcycle data in one system"],
    limitations_he: ["דורש התאמת חומרה, הספק והתקנה", "יקר ומורכב יותר מאפליקציה בטלפון הקיים"], limitations_en: ["Requires compatible hardware, power and installation", "More costly and complex than an app on an existing phone"],
    setup_he: "בודקים תאימות מכשיר ובקר, קיבוע, חיווט, עדכונים ותצוגה בשמש לפני טיול.", setup_en: "Check device and controller compatibility, mounting, wiring, updates and sunlight visibility before a trip.",
    caution_he: "אין כאן המלצת מוצר; משווים מערכת מלאה, תמיכה וחלקי חילוף ולא רק מפרט מסך.", caution_en: "This is not a product endorsement; compare the complete system, support and replaceable parts, not only screen specifications.",
    source_url: "https://drivemodedashboard.com/Manuals/Specifications_T665.pdf", video_ids: ["yt-OiOgLX5AwLQ", "yt-0Oa8Hc9AG4c"],
  },
  {
    name: "Kurviger", type_he: "תכנון כבישי רכיבה מפותלים", type_en: "Twisty-road route planning",
    best_for_he: "תכנון כביש מפותל, מסלולים מעגליים, הקלטה, שיתוף ומפות לא מקוונות.", best_for_en: "Twisty-road planning, round trips, recording, sharing and offline maps.",
    capabilities_he: ["מסלולים מפותלים", "GPX", "מפות לא מקוונות", "CarPlay / Android Auto"], capabilities_en: ["Twisty routing", "GPX", "Offline maps", "CarPlay / Android Auto"],
    advantages_he: ["תכנון ייעודי לאופנוע בכביש", "אפשרויות עיקול והימנעות מפורטות"], advantages_en: ["Road-motorcycle-specific planning", "Detailed curvature and avoidance controls"],
    limitations_he: ["חישוב Route חדש דורש חיבור גם כאשר המפה והמסלול הורדו", "ייבוא GPX לא מקוון אינו זהה לניווט מלא בקובץ Kurviger"], limitations_en: ["New route calculation needs connectivity even with downloaded maps", "Offline GPX import is not identical to full navigation with a Kurviger file"],
    setup_he: "שומרים קובץ Kurviger מקומי, מורידים את אזורי המפה ובודקים סטייה וחזרה למסלול ללא רשת.", setup_en: "Save a local Kurviger file, download map regions and test leaving and rejoining the route without a network.",
    caution_he: "מכירים מראש את מגבלות החישוב הלא־מקוון ושומרים GPX גיבוי.", caution_en: "Understand offline-recalculation limits and keep a GPX backup.",
    source_url: "https://docs.kurviger.com/offlinenavigation", video_ids: ["yt-OiOgLX5AwLQ", "yt-N5DsF-4q98c"],
  },
  {
    name: "calimoto", type_he: "תכנון רכיבות כביש", type_en: "Road-ride planning",
    best_for_he: "מסלולים מפותלים, נסיעות מעגליות, ניווט קולי, הקלטה וייבוא/ייצוא GPX.", best_for_en: "Twisty and round-trip routes, voice navigation, recording and GPX import/export.",
    capabilities_he: ["מסלולים מפותלים", "GPX", "הקלטת רכיבה", "CarPlay / Android Auto"], capabilities_en: ["Twisty routing", "GPX", "Ride recording", "CarPlay / Android Auto"],
    advantages_he: ["ממשק שמכוון לרכיבת כביש", "תכנון, ניווט והיסטוריה במקום אחד"], advantages_en: ["Road-motorcycle-oriented interface", "Planning, navigation and ride history in one place"],
    limitations_he: ["מפות לא מקוונות הן תכונת Premium", "אינו מיועד לאימות עבירות של שבילי שטח"], limitations_en: ["Offline maps are a Premium feature", "Not designed to verify off-road trail passability"],
    setup_he: "בודקים את תוכנית המנוי, מורידים מפות מראש ומייצאים GPX גיבוי.", setup_en: "Check the subscription tier, download maps in advance and export a GPX backup.",
    caution_he: "מפרידים בין תכנון כביש מהנה לבין ניווט שטח וציות להגבלות דרך.", caution_en: "Separate enjoyable road planning from off-road navigation and road-access compliance.",
    source_url: "https://calimoto.com/en/pricing", video_ids: ["yt-OiOgLX5AwLQ", "yt-N5DsF-4q98c"],
  },
  {
    name: "Locus Map", type_he: "מפות ונתיבי שטח מתקדמים", type_en: "Advanced outdoor maps and tracks",
    best_for_he: "ייבוא GPX, ספריית Tracks, מפות חיצוניות ולא מקוונות וזרימות עבודה מתקדמות ב־Android.", best_for_en: "GPX import, track library, external and offline maps, and advanced Android workflows.",
    capabilities_he: ["GPX", "מפות חיצוניות", "מפות לא מקוונות", "ספריית Tracks"], capabilities_en: ["GPX", "External maps", "Offline maps", "Track library"],
    advantages_he: ["גמישות גבוהה במקורות מפה ובפורמטים", "ארגון מפורט של מסלולים ונקודות"], advantages_en: ["High flexibility in map sources and formats", "Detailed organisation of tracks and points"],
    limitations_he: ["עקומת לימוד גבוהה", "מודלים ויכולות שונים בין Android ל־iOS ובין מסלולי מנוי"], limitations_en: ["Steep learning curve", "Models and capabilities differ by platform and subscription"],
    setup_he: "מייבאים GPX, מורידים מפה ונתוני ניתוב לאזור, מבודדים פרופיל מתאים ובודקים ללא רשת.", setup_en: "Import GPX, download map and routing data, select the right profile and test offline.",
    caution_he: "מתעדים את תהליך ההכנה; ריבוי אפשרויות הוא יתרון רק אם ניתן לשחזר את ההגדרה.", caution_en: "Document the setup; flexibility helps only when the configuration can be reproduced.",
    source_url: "https://docs.locusmap.app/doku.php?id=manual:user_guide:tracks:import", video_ids: ["yt-N5DsF-4q98c", "yt-UOI7yWHv07w"],
  },
  {
    name: "Garmin zūmo / Tread", type_he: "GPS ייעודי לאופנוע", type_en: "Dedicated motorcycle GPS",
    best_for_he: "חומרה עמידה למזג אוויר ולרעידות, מסך כפפות, Track/Route וחיבור לאביזרים ייעודיים.", best_for_en: "Weather- and vibration-resistant hardware, glove display, tracks/routes and dedicated accessories.",
    capabilities_he: ["חומרה ייעודית", "GPX", "מפות כביש וטופוגרפיה", "מסך כפפות"], capabilities_en: ["Dedicated hardware", "GPX", "Road and topographic maps", "Glove-friendly display"],
    advantages_he: ["עמידות והתקנה קבועה", "תפעול שמתוכנן לאור שמש ולכפפות"], advantages_en: ["Durability and fixed installation", "Controls designed for sunlight and gloves"],
    limitations_he: ["עלות גבוהה יותר", "תהליך עדכון, חיווט ואקוסיסטם נפרד מן הטלפון"], limitations_en: ["Higher cost", "A separate update, wiring and ecosystem workflow from the phone"],
    setup_he: "מתקינים לפי הוראות היצרן עם נתיך וחיבור מתאים, מעבירים GPX ובודקים מפות, חשמל וגיבוי.", setup_en: "Install to manufacturer instructions with appropriate fused power, transfer GPX and verify maps, power and backup.",
    caution_he: "אין להעתיק חיווט מסרטון של דגם אחר; ספר השירות והוראות היצרן גוברים.", caution_en: "Do not copy wiring from another motorcycle model; the service manual and manufacturer instructions take precedence.",
    source_url: "https://www.garmin.com/en-US/p/867974/", video_ids: ["yt-OiOgLX5AwLQ", "yt-lcauMhznleg"],
  },
  {
    name: "Waze / Google Maps", type_he: "ניווט כביש יומיומי", type_en: "Everyday road navigation",
    best_for_he: "תנועה, כתובות, דלק וניווט כביש פשוט כשיש קליטה ותוכנית גיבוי.", best_for_en: "Traffic, addresses, fuel and simple road navigation with coverage and a backup plan.",
    capabilities_he: ["תנועה", "כתובות", "יעדים", "כביש"], capabilities_en: ["Traffic", "Addresses", "Destinations", "Road use"],
    advantages_he: ["מוכר וזמין בטלפון הקיים", "טוב ליעדי כביש ושינויים יומיומיים"], advantages_en: ["Familiar and available on an existing phone", "Useful for road destinations and everyday changes"],
    limitations_he: ["GPX ו־Track אינם ליבת המוצר", "לא נועדו להערכת שביל שטח או עבירות"], limitations_en: ["GPX and track following are not the core workflow", "Not intended to assess off-road trails or passability"],
    setup_he: "שומרים יעדים חשובים, מורידים מפה אם האפשרות זמינה ומשתפים נקודות מפגש בנפרד מן ה־GPX.", setup_en: "Save key destinations, download maps where available and share meeting points separately from the GPX workflow.",
    caution_he: "משתמשים בהם לכביש ולגישה, ולא כתחליף למפת שטח, Track ובדיקת חוקיות.", caution_en: "Use them for road access, not as a substitute for a trail map, track and legality checks.",
    source_url: "https://support.google.com/maps/answer/6291838", video_ids: ["yt-hDX4TBsPKLU", "yt-lcauMhznleg"],
  },
];

travel.knowledge_guides = [
  {
    id: "navigation-hardware-choice", eyebrow_he: "טלפון, GPS או תצוגת שיקוף", eyebrow_en: "Phone, GPS or mirrored display",
    title_he: "בוחרים מערכת — לא רק מסך", title_en: "Choose a system, not just a screen",
    summary_he: "החלטה טובה מתחילה בתוואי, כפפות, חום, רעידות, גשם, חשמל וגיבוי. תצוגת CarPlay/Android Auto משאירה את האפליקציות בטלפון; GPS ייעודי מוסיף חומרה עמידה; טלפון מוקשח נותן גמישות במחיר ביניים.",
    summary_en: "Start with terrain, gloves, heat, vibration, rain, power and backup. A CarPlay/Android Auto display mirrors phone apps; dedicated GPS adds rugged hardware; a rugged phone offers flexible middle ground.",
    best_when_he: ["טלפון: תקציב, גמישות ואפליקציות רבות", "GPS ייעודי: שימוש ממושך, כפפות, גשם ורעידות", "תצוגת שיקוף: רוצים מסך רכיבה בלי לחשוף את הטלפון"],
    best_when_en: ["Phone: budget, flexibility and many apps", "Dedicated GPS: sustained glove, rain and vibration use", "Mirrored display: a riding screen without exposing the phone"],
    tradeoffs_he: ["טלפון אישי חשוף לחום, מצלמה ורעידות", "GPS ייעודי יקר ודורש זרימת GPX נפרדת", "שיקוף תלוי בטלפון, בחיבור ובתאימות האפליקציה"],
    tradeoffs_en: ["A personal phone faces heat, camera and vibration risk", "Dedicated GPS costs more and has a separate GPX workflow", "Mirroring depends on the phone, connection and app support"],
    setup_checks_he: ["בדיקת קריאות בשמש ובכפפות", "חיבור מכני עם רצועת ביטחון", "חשמל מוגן ונתיך לפי היצרן", "מפת offline ומכשיר גיבוי"],
    setup_checks_en: ["Sunlight and glove readability", "Mechanical mount with safety tether", "Protected fused power to manufacturer guidance", "Offline map and backup device"],
    video_ids: ["yt-OiOgLX5AwLQ", "yt-0Oa8Hc9AG4c", "yt-UOI7yWHv07w"],
  },
  {
    id: "gpx-offline-workflow", eyebrow_he: "מתכנון עד שטח", eyebrow_en: "From planning to the trail",
    title_he: "GPX ומפות לא מקוונות בלי הפתעות", title_en: "GPX and offline maps without surprises",
    summary_he: "קובץ GPX הוא מעטפת שיכולה להכיל Track, Route ונקודות. לפני הטיול פותחים אותו באפליקציה היעד, בודקים קו ו־waypoints, מורידים מפות ומבצעים בדיקת מצב טיסה.",
    summary_en: "A GPX file can contain tracks, routes and waypoints. Before the trip, open it in the target app, inspect the line and waypoints, download maps and run an airplane-mode test.",
    best_when_he: ["Track: רוצים לעקוב אחר קו מתוכנן בלי חישוב מחדש", "Route: רוצים הוראות פנייה וחישוב, עם הבנת השינויים", "Waypoints: דלק, מים, יציאה, לינה ומפגש"],
    best_when_en: ["Track: follow a planned line without recalculation", "Route: turn guidance and calculation, with awareness of changes", "Waypoints: fuel, water, exits, lodging and meetings"],
    tradeoffs_he: ["אפליקציות מפרשות Route ו־Track אחרת", "מפה שהוצגה פעם אינה בהכרח הורדה מלאה", "GPX אינו מאמת חוקיות או עבירות"],
    tradeoffs_en: ["Apps interpret routes and tracks differently", "A previously viewed map may not be fully downloaded", "GPX does not verify legality or passability"],
    setup_checks_he: ["פתיחה במכשיר האמיתי", "בדיקת מצב טיסה", "ייצוא עותק נוסף", "שיתוף עם רוכב נוסף"],
    setup_checks_en: ["Open on the actual device", "Airplane-mode test", "Export another copy", "Share with another rider"],
    video_ids: ["yt-N5DsF-4q98c", "yt-UOI7yWHv07w", "yt-_4xaX5MT94Y"],
  },
  {
    id: "helmet-choice", eyebrow_he: "תקן, דירוג והתאמה", eyebrow_en: "Standard, rating and fit",
    title_he: "קסדה בוחרים על הראש, לא לפי מדבקה בלבד", title_en: "Choose a helmet on your head, not by sticker alone",
    summary_he: "תקן הוא סף, דירוג בדיקה מוסיף השוואה, והתאמה קובעת כיצד הקסדה יושבת ונשארת במקום. בודקים צורת ראש, לחץ אחיד, תנועה, רצועה, שדה ראייה ואוורור.",
    summary_en: "A standard is a threshold, a test rating adds comparison, and fit determines how the helmet sits and stays in place. Check head shape, even pressure, movement, strap, vision and ventilation.",
    best_when_he: ["קנייה ראשונה או החלפת קסדה", "כאב נקודתי או קסדה שזזה", "השוואת תוצאות בדיקה מעבר לשיווק"],
    best_when_en: ["First purchase or helmet replacement", "Pressure points or excessive movement", "Comparing test results beyond marketing"],
    tradeoffs_he: ["דירוג גבוה אינו מפצה על התאמה גרועה", "מידה זהה אינה מבטיחה אותה צורת פנים", "שקט, אוורור ומשקל משפיעים על עייפות"],
    tradeoffs_en: ["A high rating cannot compensate for poor fit", "The same size does not guarantee the same internal shape", "Noise, ventilation and weight affect fatigue"],
    setup_checks_he: ["בדיקת תווית והוראות", "מדידה ממושכת בחנות", "שדה ראייה ורצועה", "אין שימוש בקסדה פגומה או אחרי אירוע לפי הוראות היצרן"],
    setup_checks_en: ["Check label and instructions", "Wear it for a sustained fitting period", "Field of view and strap", "Follow manufacturer replacement guidance after damage or impact"],
    video_ids: ["yt-v94eMFeojhc", "yt-dSdKgAG-J-U"],
  },
  {
    id: "body-protection-system", eyebrow_he: "שחיקה, פגיעה ומגפיים", eyebrow_en: "Abrasion, impact and boots",
    title_he: "מיגון הוא מערכת שכבות", title_en: "Protection is a layered system",
    summary_he: "בד עמיד ותפרים מטפלים בהחלקה; מגני CE מטפלים באנרגיית פגיעה; מגפיים מגבילים תנועה לא רצויה. כל שכבה צריכה להתאים לגוף, לאקלים ולסוג הרכיבה.",
    summary_en: "Abrasion-resistant material and seams address sliding; CE armour addresses impact energy; boots limit unwanted movement. Every layer must suit body, climate and riding use.",
    best_when_he: ["בונים סט ראשון", "עוברים מכביש לשטח או להפך", "מחליפים פריט בלוי"],
    best_when_en: ["Building a first kit", "Moving between road and off-road use", "Replacing a worn item"],
    tradeoffs_he: ["יותר קשיחות יכולה להפחית נוחות ותנועתיות", "חום עלול לגרום לאי־שימוש במיגון", "מקרה תאונה בודד אינו מבחן מעבדה"],
    tradeoffs_en: ["More stiffness can reduce comfort and mobility", "Heat can lead riders not to wear protection", "One crash case is not a laboratory test"],
    setup_checks_he: ["סימון תקן ורמת מגן", "כיסוי כשהגוף בתנוחת רכיבה", "תפרים וסגירות", "בלאי, סדקים ולחץ מקומי"],
    setup_checks_en: ["Standards marking and protector level", "Coverage in riding position", "Seams and closures", "Wear, cracks and pressure points"],
    video_ids: ["yt-dP4MoF5l3IE", "yt-PQnTLz-CoTQ", "yt-EeT3531XRn4", "yt-XukrXZdtYds"],
  },
  {
    id: "intercom-choice", eyebrow_he: "14 דולר מול מאות", eyebrow_en: "Budget versus premium",
    title_he: "איזו דיבורית באמת מתאימה לכם?", title_en: "Which intercom actually fits your use?",
    summary_he: "לרוכב יחיד או מורכב Bluetooth בסיסי עשוי להספיק. קבוצה שמשתנה בתנועה נהנית לעיתים מ־Mesh, חזרה אוטומטית לרשת ובקרות טובות יותר. המחיר כולל גם שמע, סוללה, עמידות, עדכונים ותמיכה.",
    summary_en: "Basic Bluetooth may be enough for a solo rider or passenger pair. A moving group may benefit from mesh, automatic rejoining and better controls. Price also covers audio, battery, durability, updates and support.",
    best_when_he: ["זול: ניווט קולי, טלפון ורוכב־מורכב מזדמן", "יקר: קבוצה, שימוש תכוף, רעש, מזג אוויר ותמיכה", "Mesh: קבוצה שמתפצלת וחוזרת"],
    best_when_en: ["Budget: voice prompts, phone and occasional passenger", "Premium: groups, frequent use, noise, weather and support", "Mesh: groups that split and rejoin"],
    tradeoffs_he: ["טווח מוצהר אינו טווח בעולם אמיתי", "מערכות בין מותגים עשויות לרדת למצב Bluetooth מוגבל", "עוד שיחה אינה תמיד עוד בטיחות"],
    tradeoffs_en: ["Advertised range is not real-world range", "Cross-brand systems may fall back to limited Bluetooth", "More conversation is not always safer"],
    setup_checks_he: ["מספר רוכבים ותאימות", "זמן סוללה וטעינה", "תפעול בכפפות", "כלל קבוצתי להפסקת דיבור"],
    setup_checks_en: ["Rider count and compatibility", "Battery and charging", "Glove controls", "A group rule for stopping conversation"],
    video_ids: ["yt-msN_yCSN3dM", "yt-K9tcqL8KOgk", "yt-7wVIvMGTMFs"],
  },
  {
    id: "intercom-installation", eyebrow_he: "נוחות ובטיחות לפני שמע", eyebrow_en: "Comfort and safety before audio",
    title_he: "מתקינים בלי לפגוע בהתאמת הקסדה", title_en: "Install without compromising helmet fit",
    summary_he: "רמקול שאינו מול האוזן נשמע חלש; רמקול או כבל שיוצרים לחץ פוגעים בנוחות ובריכוז. מתקינים לפי מבנה הקסדה והוראות היצרנים, ואז בודקים בעמידה ובעוצמה שמאפשרת לשמוע את הסביבה.",
    summary_en: "A speaker away from the ear sounds weak; a speaker or cable creating pressure hurts comfort and concentration. Install to helmet and intercom instructions, then test while stationary at an environment-aware volume.",
    best_when_he: ["התקנה ראשונה", "שמע חלש או לא מאוזן", "החלפת קסדה או מיקרופון"],
    best_when_en: ["First installation", "Weak or unbalanced audio", "Helmet or microphone change"],
    tradeoffs_he: ["מיקום מושלם שונה בין קסדות וראשים", "שינוי ריפוד עלול להשפיע על התאמת הקסדה", "עוצמה גבוהה מגדילה עומס שמיעה והסחת דעת"],
    tradeoffs_en: ["Ideal position differs by helmet and head", "Changing padding can affect helmet fit", "High volume increases hearing load and distraction"],
    setup_checks_he: ["אין נקודת לחץ", "כבלים אינם ליד מנגנון רצועה", "מיקרופון אינו חוסם או מתחכך", "בדיקת שמע ושיחה בעמידה"],
    setup_checks_en: ["No pressure point", "Wires clear of the retention system", "Microphone does not obstruct or rub", "Stationary audio and call test"],
    video_ids: ["yt-wQkrAP1KEAg", "yt-K9tcqL8KOgk"],
  },
];
travel.version = "3.0.0";
travel.updated = checkedDate;
writeJson("data/travel-guides.json", travel);
console.log(`Added ${additions.length} verified videos; removed ${removedUnavailableCount} unavailable videos; total ${videos.length}.`);
