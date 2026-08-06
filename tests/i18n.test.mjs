import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { translateExact } from "../assets/js/i18n.js";


const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const HEBREW_TEXT = /[\u0590-\u05ff]/u;

const V3_CASES = new Map([
  ["גרסה", "Version"],
  ["ספריית הקצרים", "Shorts Library"],
  ["לקצרים", "Open Shorts"],
  ["קצרים מאומתים", "Verified Shorts"],
  ["יש לי דקה ללמוד", "I have one minute to learn"],
  ["קצרים מאומתים וממוינים לרעיון אחד בכל צפייה.", "Curated Shorts for one idea per watch."],
  ["החיפוש הרגיל מזהה כוונה, מילים נרדפות וקטגוריות בכל", "Regular search detects intent, synonyms and categories across all"],
  ["הסרטונים והקצרים. אם תפעילו AI מקומי, מודל רב־לשוני ידרג את הסרטונים המלאים לפי משמעות והחיפוש ישלב גם קצרים מתאימים. אין API, מפתח או צ׳אט מרוחק; המודל אינו ממציא הדרכות אלא רק מאתר רשומות קיימות.", "videos and Shorts. If local AI is enabled, a multilingual model ranks full videos by meaning while local search also blends in matching Shorts. No API, key or remote chat is used; the model does not create guidance — it only finds existing records."],
  ["כתבו שאלה רגילה וקבלו סרטונים וקצרים מתאימים.", "Write a normal question and get matching videos and Shorts."],
  ["הדרכות פעילות ומסווגות, ובהן", "active curated tutorials, including"],
  ["קצרים לחזרה מהירה — כהשלמה לקורסים, אימון וטיולים אמיתיים.", "Shorts for quick review — as a supplement to courses, practice and real rides."],
  ["הדרך שלך לרכיבה", "Your path to"],
  ["בטוחה ומדויקת יותר", "safer, more precise riding"],
  ["הדרכות פעילות ומסווגות בעברית ובאנגלית, עם ניווט לפי תחום, נושא ומיקוד — כהשלמה לקורסים, אימון וטיולים אמיתיים.", "active, curated tutorials in Hebrew and English, organised by area, topic and focus — as a supplement to courses, practice and real rides."],
  ["מונה כניסות גלובלי", "Global site visit counter"],
  ["כניסות שנמדדו", "Recorded visits"],
  ["מונה חיצוני סופר טעינות של האתר החי, לא אנשים ייחודיים; רענונים ובוטים עשויים להיספר.", "An external counter records loads of the live site, not unique people; refreshes and bots may be counted."],
  ["המונה אינו זמין כרגע", "Counter currently unavailable"],
  ["פתיחת פנייה ב־GitHub", "Open a GitHub request"],
  ["בחירת תחום מהירה", "Quick area selection"],
  ["מסננים מתקדמים", "Advanced filters"],
  ["סיכון, אופנוע, תנאים ומאפייני מקור", "Risk, motorcycle, conditions and source attributes"],
  ["קיצורי נושאים", "Topic shortcuts"],
  ["בחירת מסלול לימוד", "Learning path selection"],
  ["השוו לפי שימוש, עבודה ללא קליטה, GPX, התקנה, חשמל ומגבלות — לא לפי שם המותג בלבד.", "Compare by use case, offline capability, GPX, mounting, power and limitations — not by brand name alone."],
  ["מחליטים לפי צורך, לא לפי מחיר בלבד", "Choose by need, not price alone"],
  ["מדריכי ניווט, מיגון ודיבוריות", "Navigation, protection and intercom guides"],
  ["הפעלת AI מקומי", "Enable local AI"],
  ["טלפון או GPS?", "Phone or GPS?"],
  ["איזה מיגון?", "What protective gear?"],
  ["Bluetooth או Mesh?", "Bluetooth or Mesh?"],
  ["טלפון או GPS ייעודי לטיול עם GPX ומפות אופליין", "Phone or dedicated GPS for a trip with GPX and offline maps"],
  ["איזה מיגון חשוב לרוכב אדוונצ'ר מתחיל", "Which protection matters for a beginner adventure rider"],
  ["דיבורית Bluetooth או Mesh לקבוצת רוכבים", "Bluetooth or Mesh intercom for a group ride"],
  ["פניות בכביש רטוב לרוכב מתחיל", "Cornering on a wet road for a beginner rider"],
  ["חיפוש חכם זמין תמיד", "Smart search is always available"],
  ["AI סמנטי מקומי הוא אפשרות נוספת. בהפעלה הראשונה יורד מודל של כ־140MB; לאחר מכן השאלות מעובדות במכשיר.", "Local semantic AI is optional. On first activation, a model of about 140MB is downloaded; queries are then processed on the device."],
  ["החיפוש הרגיל מזהה כוונה, מילים נרדפות וקטגוריות ונשאר זמין בכל מכשיר. אם תפעילו AI מקומי, מודל רב־לשוני ייטען למכשיר וידרג את", "Regular search detects intent, synonyms and categories and remains available on every device. If you enable local AI, a multilingual model is loaded onto the device and ranks the"],
  ["הרשומות לפי משמעות. אין API, מפתח או צ׳אט מרוחק; המודל אינו ממציא הדרכות אלא רק מאתר רשומות קיימות.", "records by meaning. No API, key or remote chat is used; the model does not create guidance — it only finds existing records."],
  ["הספרייה אוצרת קישורים לתוכן צד שלישי. היא מרחיבה ידע ומציעה רעיונות לתרגול, אך אינה תחליף לקורס, למדריך מקצועי, לספר היצרן, לחוק או להערכת התנאים בשטח.", "The library curates links to third-party content. It expands knowledge and suggests practice ideas, but does not replace a course, professional instructor, the manufacturer’s manual, applicable law or on-site assessment."],
  ["אוצרות בלבד — לא אישור או אחריות", "Curation only — no endorsement or responsibility"],
  ["האתר הוא אינדקס אוצר של תוכן צד שלישי. הוא אינו מאשר כל טענה, אינו יכול לבדוק ברציפות דיוק, עדכניות, איכות או בטיחות, ואינו מעניק הסמכה, אחריות או המלצה מסחרית. דעות היוצרים אינן דעות האתר.", "This site is a curated index of third-party content. It does not endorse every claim, cannot continuously verify accuracy, currency, quality or safety, and provides no certification, warranty or commercial recommendation. Creators’ opinions are not those of the site."],
  ["האתר, התקצירים והסרטונים נועדו להעשרה בלבד. רכיבה מתקדמת לומדים בקורסים ובאימונים אצל מדריכים מוסמכים, עם ציוד, שטח ומשוב מתאימים. החוק, ספר היצרן והחלטה שמרנית בשטח תמיד גוברים.", "The site, summaries and videos are for enrichment only. Advanced riding should be learned through courses and practice with qualified instructors, appropriate equipment, terrain and feedback. The law, manufacturer’s manual and a conservative decision on the ground always take precedence."],
  ["אין באתר פרסומות, Affiliate או תשלום עבור הצגת סרטון. ייתכן שבתוך סרטון חיצוני תופיע חסות של היוצר; היא מסומנת ככל שניתן. סימון „ללא שיווק” מתאר את הראיות שנאספו ואינו אישור לעצמאות מוחלטת.", "The site carries no ads, affiliate links or paid placement. An external video may include creator sponsorship; this is marked when known. A ‘no marketing’ label describes the evidence collected and is not a guarantee of complete independence."],
  ["הוראות התקנה", "Installation instructions"],
  ["באתר החי", "On the live site"],
]);

const SMART_EXAMPLES = [
  {
    labelHe: "טלפון או GPS?",
    labelEn: "Phone or GPS?",
    queryHe: "טלפון או GPS ייעודי לטיול עם GPX ומפות אופליין",
    queryEn: "Phone or dedicated GPS for a trip with GPX and offline maps",
  },
  {
    labelHe: "איזה מיגון?",
    labelEn: "What protective gear?",
    queryHe: "איזה מיגון חשוב לרוכב אדוונצ'ר מתחיל",
    queryEn: "Which protection matters for a beginner adventure rider",
  },
  {
    labelHe: "Bluetooth או Mesh?",
    labelEn: "Bluetooth or Mesh?",
    queryHe: "דיבורית Bluetooth או Mesh לקבוצת רוכבים",
    queryEn: "Bluetooth or Mesh intercom for a group ride",
  },
  {
    labelHe: "פניות בגשם",
    labelEn: "Cornering in rain",
    queryHe: "פניות בכביש רטוב לרוכב מתחיל",
    queryEn: "Cornering on a wet road for a beginner rider",
  },
];


function parseV3Translations(source) {
  const block = source.match(/const V3_TRANSLATIONS = Object\.freeze\(\{([\s\S]*?)\n\}\);/u);
  assert.ok(block, "V3_TRANSLATIONS block is missing");
  const translations = new Map();
  const entryPattern = /^\s*("(?:\\.|[^"\\])*"):\s*("(?:\\.|[^"\\])*")[,]?\s*$/gmu;
  for (const match of block[1].matchAll(entryPattern)) {
    translations.set(JSON.parse(match[1]), JSON.parse(match[2]));
  }
  return translations;
}


test("every v3 interface string has the approved English translation", async () => {
  const source = await read("assets/js/i18n.js");
  const declared = parseV3Translations(source);
  assert.deepEqual(declared, V3_CASES, "V3 translation table and regression cases differ");

  for (const [hebrew, english] of V3_CASES) {
    assert.match(hebrew, HEBREW_TEXT, `Hebrew source is missing Hebrew text: ${hebrew}`);
    assert.equal(translateExact(hebrew), english, `incorrect English translation for: ${hebrew}`);
    assert.doesNotMatch(english, HEBREW_TEXT, `English UI text still contains Hebrew: ${english}`);
  }
});


test("smart examples expose matching Hebrew and English labels and queries", async () => {
  const html = await read("index.html");
  const examples = [...html.matchAll(/<button\b[^>]*\bdata-smart-example="([^"]+)"[^>]*>([^<]+)<\/button>/gu)]
    .map((match) => ({ queryHe: match[1], labelHe: match[2].trim() }));

  assert.equal(examples.length, SMART_EXAMPLES.length, "unexpected number of smart examples");
  assert.deepEqual(
    examples,
    SMART_EXAMPLES.map(({ labelHe, queryHe }) => ({ queryHe, labelHe })),
    "smart example labels or queries changed without updating i18n coverage",
  );

  for (const example of SMART_EXAMPLES) {
    assert.equal(translateExact(example.labelHe), example.labelEn);
    assert.equal(translateExact(example.queryHe), example.queryEn);
    assert.doesNotMatch(example.labelEn, HEBREW_TEXT, `English smart label contains Hebrew: ${example.labelEn}`);
    assert.doesNotMatch(example.queryEn, HEBREW_TEXT, `English smart query contains Hebrew: ${example.queryEn}`);
  }
});


test("runtime translation includes user-visible v3 attributes", async () => {
  const source = await read("assets/js/i18n.js");
  assert.match(source, /\["placeholder", "aria-label", "title", "alt", "data-smart-example"\]/u);
});
