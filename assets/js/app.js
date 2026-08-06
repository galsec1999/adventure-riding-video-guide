import { applySearchAndFilters, normalizeText, prepareVideos, scoreSearchMatch, uniqueDisplayTaxonomyIds } from "./search.js";
import { browserStorage } from "./storage.js";
import { localizedField, getStoredLanguage, isEnglish, saveLanguage, startEnglishObserver, translateDocument, translateExact } from "./i18n.js?v=3.1.0-20260806d";
import {
  INITIAL_VISIBLE_LIMIT,
  LOAD_MORE_BATCH_SIZE,
  clampVisibleLimit,
  nextVisibleLimit,
} from "./pagination.js";

const MOBILE_OVERLAY_QUERY = "(max-width: 59.999rem)";
const DEFAULT_SITE_NAME = "מדריך הווידאו לרכיבת אדוונצ'ר";
const DEFAULT_SAFETY_WARNING = "יש לתרגל בהדרגה, במקום בטוח ועם ציוד מיגון מתאים.";
const SAFE_LOGO_EXTENSION = /\.(?:avif|gif|jpe?g|png|svg|webp)$/i;
const DATA_CACHE_REVISION = "3.1.0-20260806d";
const SEMANTIC_META_URL = "data/semantic-index.json";
const SEMANTIC_WORKER_URL = `assets/js/semantic-worker.js?v=${DATA_CACHE_REVISION}`;

const DATA_FILES = Object.freeze({
  videos: "data/videos.json",
  shorts: "data/shorts.json",
  taxonomy: "data/categories.json",
  paths: "data/learning-paths.json",
  synonyms: "data/synonyms.json",
  config: "data/site-config.json",
  travel: "data/travel-guides.json",
});

const EMBEDDED_DATA_IDS = Object.freeze({
  [DATA_FILES.videos]: "embedded-data-videos",
  [DATA_FILES.shorts]: "embedded-data-shorts",
  [DATA_FILES.taxonomy]: "embedded-data-categories",
  [DATA_FILES.paths]: "embedded-data-learning-paths",
  [DATA_FILES.synonyms]: "embedded-data-synonyms",
  [DATA_FILES.config]: "embedded-data-site-config",
  [DATA_FILES.travel]: "embedded-data-travel-guides",
});

const VALID_VIEWS = Object.freeze(["home", "library", "shorts", "paths", "trips", "smart", "safety"]);
const FEEDBACK_URL = "https://github.com/galsec1999/adventure-riding-video-guide/issues/new";

const FILTER_IDS = Object.freeze({
  domain: "filter-domain",
  category: "filter-category",
  subcategory: "filter-subcategory",
  format: "filter-format",
  language: "filter-language",
  skill: "filter-skill",
  risk: "filter-risk",
  motorcycle: "filter-motorcycle",
  weight: "filter-weight",
  terrain: "filter-terrain",
  road: "filter-road-condition",
  duration: "filter-duration",
});

const CHECKBOX_FILTERS = Object.freeze({
  subtitles: ["filter-subtitles", "yes"],
  professional: ["filter-professional", "yes"],
  marketing: ["filter-no-marketing", "no"],
  favorite: ["filter-favorites", "yes"],
  practical: ["filter-practical", "yes"],
  warnings: ["filter-safety", "yes"],
  beginner: ["filter-beginner", "yes"],
});

const URL_FILTER_KEYS = [
  "q", "domain", "category", "subcategory", "format", "language", "skill", "risk", "motorcycle",
  "weight", "terrain", "road", "duration", "subtitles", "professional",
  "marketing", "favorite", "watched", "practical", "warnings", "beginner", "sort",
];

const state = {
  config: {},
  taxonomy: {},
  paths: [],
  travel: {},
  synonyms: {},
  videos: [],
  shorts: [],
  allVideos: [],
  videosById: new Map(),
  labels: new Map(),
  synonymIndex: null,
  filters: { sort: "recommended" },
  favorites: new Set(),
  watched: new Set(),
  pathProgress: {},
  tripChecklist: new Set(),
  selectedTripType: "day",
  selectedPathId: "",
  smartQuery: "",
  smartResults: [],
  smartMatches: [],
  semantic: {
    enabled: false,
    ready: false,
    loading: false,
    worker: null,
    meta: null,
    matrix: null,
    pending: new Map(),
    requestSequence: 0,
  },
  currentView: "home",
  visibleLimit: INITIAL_VISIBLE_LIMIT,
  activeVideoId: null,
  ready: false,
  uiLanguage: getStoredLanguage(),
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function createOverlayManager() {
  const active = new Map();
  const mobileMedia = window.matchMedia(MOBILE_OVERLAY_QUERY);
  let scrollLock = null;

  function setInertOutside(root) {
    if (!(root instanceof HTMLElement)) return [];
    const records = [];
    let current = root;
    while (current?.parentElement && current !== document.body) {
      const parent = current.parentElement;
      [...parent.children].forEach((sibling) => {
        if (!(sibling instanceof HTMLElement) || sibling === current || sibling.id === "toast-region") return;
        records.push({
          element: sibling,
          hadInert: sibling.hasAttribute("inert"),
          inertValue: sibling.inert,
          ariaHidden: sibling.getAttribute("aria-hidden"),
        });
        if ("inert" in sibling) sibling.inert = true;
        else sibling.setAttribute("aria-hidden", "true");
        sibling.dataset.overlayInert = "true";
      });
      current = parent;
    }
    return records;
  }

  function restoreInert(records = []) {
    records.forEach(({ element, hadInert, inertValue, ariaHidden }) => {
      if (!element.isConnected) return;
      if ("inert" in element) element.inert = inertValue;
      if (hadInert) element.setAttribute("inert", "");
      else element.removeAttribute("inert");
      if (ariaHidden == null) element.removeAttribute("aria-hidden");
      else element.setAttribute("aria-hidden", ariaHidden);
      delete element.dataset.overlayInert;
    });
  }

  function locksScroll(name) {
    return name === "video" || name === "rights" || name === "feedback" || mobileMedia.matches;
  }

  function syncBody() {
    const modalOpen = active.has("video") || active.has("rights") || active.has("feedback");
    const filtersOpen = active.has("filters");
    const menuOpen = active.has("menu");
    document.body.dataset.modalOpen = String(modalOpen);
    document.body.dataset.filtersOpen = String(filtersOpen);
    document.body.dataset.menuOpen = String(menuOpen);
    const shouldLock = [...active.keys()].some(locksScroll);
    if (shouldLock && !scrollLock) {
      scrollLock = { x: window.scrollX, y: window.scrollY };
      document.body.style.setProperty("--overlay-scroll-y", `${scrollLock.y}px`);
      document.body.dataset.scrollLocked = "true";
    } else if (!shouldLock && scrollLock) {
      const position = scrollLock;
      scrollLock = null;
      document.body.dataset.scrollLocked = "false";
      document.body.style.removeProperty("--overlay-scroll-y");
      const previousBehavior = document.documentElement.style.scrollBehavior;
      document.documentElement.style.scrollBehavior = "auto";
      window.scrollTo(position.x, position.y);
      document.documentElement.style.scrollBehavior = previousBehavior;
    }
  }

  function close(name, { restoreFocus = true } = {}) {
    const entry = active.get(name);
    if (!entry) return false;
    active.delete(name);
    entry.onClose?.();
    restoreInert(entry.inertRecords);
    syncBody();
    if (restoreFocus && entry.opener instanceof HTMLElement && entry.opener.isConnected) {
      entry.opener.focus({ preventScroll: true });
    }
    return true;
  }

  function open(name, { root, opener = document.activeElement, firstFocus, inertBackground = false, onClose } = {}) {
    if (active.has(name)) return active.get(name);
    if (name === "menu") close("filters", { restoreFocus: false });
    if (name === "filters") close("menu", { restoreFocus: false });
    if (name === "video" || name === "rights" || name === "feedback") {
      close("menu", { restoreFocus: false });
      close("filters", { restoreFocus: false });
    }
    if (name === "rights") close("feedback", { restoreFocus: false });
    if (name === "feedback") close("rights", { restoreFocus: false });
    const entry = {
      opener: opener instanceof HTMLElement && opener !== document.body ? opener : null,
      inertRecords: inertBackground ? setInertOutside(root) : [],
      onClose,
    };
    active.set(name, entry);
    syncBody();
    const focusTarget = () => {
      const target = typeof firstFocus === "function" ? firstFocus() : firstFocus;
      if (target instanceof HTMLElement && target.isConnected) target.focus({ preventScroll: true });
    };
    focusTarget();
    window.requestAnimationFrame(focusTarget);
    window.setTimeout(() => {
      if (active.get(name) === entry) focusTarget();
    }, 250);
    return entry;
  }

  function closeTransient({ restoreFocus = false } = {}) {
    close("filters", { restoreFocus });
    close("menu", { restoreFocus });
  }

  function handleBreakpoint() {
    if (!mobileMedia.matches) closeTransient({ restoreFocus: false });
  }

  mobileMedia.addEventListener?.("change", handleBreakpoint);
  return { active: (name) => active.has(name), close, closeTransient, mobileMedia, open, syncBody };
}

const overlayManager = createOverlayManager();

function createElement(tag, options = {}) {
  const element = document.createElement(tag);
  if (options.className) element.className = options.className;
  if (options.text != null) element.textContent = String(options.text);
  if (options.attrs) {
    Object.entries(options.attrs).forEach(([name, value]) => {
      if (value != null) element.setAttribute(name, String(value));
    });
  }
  return element;
}

function createButton(text, action, attrs = {}) {
  const { className = "button button--secondary", ...attributes } = attrs;
  const button = createElement("button", {
    className,
    text,
    attrs: { type: "button", "data-action": action, ...attributes },
  });
  return button;
}

function currentLanguage() { return state.uiLanguage === "en" ? "en" : "he"; }
function englishMode() { return isEnglish(currentLanguage()); }
function ui(he, en) { return englishMode() ? en : he; }
function localField(record, base) { return localizedField(record, base, currentLanguage()); }
function localArray(record, base) {
  const value = englishMode() ? (record?.[`${base}_en`] || record?.[`${base}_he`]) : record?.[`${base}_he`];
  return Array.isArray(value) ? value : [];
}
function videoTitle(video) { return englishMode() ? (video.title_en || video.title_original) : video.title_he; }
function videoSummary(video) { return englishMode() ? (video.summary_en || video.summary_he) : video.summary_he; }
function videoArray(video, base) {
  const value = englishMode() ? video[`${base}_en`] : video[`${base}_he`];
  return Array.isArray(value) ? value : [];
}
function videoText(video, base) { return englishMode() ? (video[`${base}_en`] || video[`${base}_he`] || "") : (video[`${base}_he`] || ""); }
function applyLanguageShell() {
  document.documentElement.lang = currentLanguage();
  document.documentElement.dir = englishMode() ? "ltr" : "rtl";
  const toggle = $("#language-toggle");
  if (toggle) {
    toggle.textContent = englishMode() ? "עברית" : "English";
    toggle.setAttribute("aria-label", englishMode() ? "Switch site language to Hebrew" : "Switch site language to English");
    toggle.setAttribute("aria-pressed", String(englishMode()));
  }
  if (englishMode()) startEnglishObserver();
}

function cleanConfigText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeSiteConfig(config) {
  if (!config || Array.isArray(config) || typeof config !== "object") {
    throw new Error(ui("קובץ הגדרות האתר חייב להיות אובייקט JSON תקין.", "The site configuration must be a valid JSON object."));
  }
  const language = cleanConfigText(config.default_language);
  const direction = cleanConfigText(config.direction);
  return {
    site_name_he: cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    site_name_en: cleanConfigText(config.site_name_en) || "Community Adventure Riding Video Guide",
    author_name: cleanConfigText(config.author_name),
    community_name: cleanConfigText(config.community_name),
    community_name_en: cleanConfigText(config.community_name_en) || "Adventure Riding Community",
    contact: cleanConfigText(config.contact),
    logo_path: cleanConfigText(config.logo_path),
    safety_warning_he: cleanConfigText(config.safety_warning_he) || DEFAULT_SAFETY_WARNING,
    safety_warning_en: cleanConfigText(config.safety_warning_en) || "This guide supplements professional instruction and progressive practice; it does not replace them.",
    release_version: cleanConfigText(config.release_version) || "3.0.0",
    feedback_url: cleanConfigText(config.feedback_url) || FEEDBACK_URL,
    standalone_filename: cleanConfigText(config.standalone_filename) || "Adventure-Riding-Video-Guide-v3.0.0-Standalone.html",
    code_license: cleanConfigText(config.code_license) || "MIT",
    content_license: cleanConfigText(config.content_license) || "CC BY-NC-SA 4.0",
    nonprofit: config.nonprofit !== false,
    site_ads: config.site_ads === true,
    meta_title_he: cleanConfigText(config.meta_title_he) || cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    meta_title_en: cleanConfigText(config.meta_title_en) || cleanConfigText(config.site_name_en) || "Community Adventure Riding Video Guide",
    meta_description_he: cleanConfigText(config.meta_description_he || config.description_he),
    meta_description_en: cleanConfigText(config.meta_description_en || config.description_en),
    og_title_he: cleanConfigText(config.og_title_he || config.meta_title_he) || cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    og_title_en: cleanConfigText(config.og_title_en || config.meta_title_en || config.site_name_en) || "Community Adventure Riding Video Guide",
    og_description_he: cleanConfigText(config.og_description_he || config.meta_description_he || config.description_he),
    og_description_en: cleanConfigText(config.og_description_en || config.meta_description_en || config.description_en),
    default_language: /^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/i.test(language) ? language : "he",
    direction: direction === "ltr" || direction === "rtl" ? direction : "rtl",
  };
}

function resolveSafeLogoUrl(path) {
  const raw = cleanConfigText(path);
  if (!raw || raw.startsWith("/") || raw.startsWith("\\") || raw.includes("\\") || raw.includes("?") || raw.includes("#")) return null;
  if (/^[a-z][a-z0-9+.-]*:/i.test(raw) || raw.startsWith("//")) return null;
  let decoded;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return null;
  }
  if (decoded.includes("\\") || decoded.startsWith("/") || decoded.split("/").some((segment) => segment === "." || segment === "..")) return null;
  if (!decoded.startsWith("assets/")) return null;
  if (!SAFE_LOGO_EXTENSION.test(decoded)) return null;
  const base = new URL(".", document.baseURI);
  const resolved = new URL(raw, base);
  if (resolved.protocol !== base.protocol || resolved.origin !== base.origin || !resolved.pathname.startsWith(base.pathname)) return null;
  return resolved.href;
}

function applyLogoConfig(config) {
  const logoUrl = resolveSafeLogoUrl(config.logo_path);
  $$('[data-site-logo-container]').forEach((container) => {
    const image = $("[data-site-logo]", container);
    const fallback = $("[data-logo-fallback]", container);
    if (!image || !fallback) return;
    const showFallback = () => {
      image.onerror = null;
      image.hidden = true;
      image.removeAttribute("src");
      fallback.hidden = false;
    };
    image.onerror = showFallback;
    if (!logoUrl) {
      showFallback();
      return;
    }
    image.alt = englishMode() ? `${config.site_name_en} logo` : `לוגו ${config.site_name_he}`;
    fallback.hidden = true;
    image.hidden = false;
    image.src = logoUrl;
  });
}

function applySiteConfig(config) {
  applyLanguageShell();
  const siteName = englishMode() ? config.site_name_en : config.site_name_he;
  const metaTitle = englishMode() ? config.meta_title_en : config.meta_title_he;
  const metaDescription = englishMode() ? config.meta_description_en : config.meta_description_he;
  const ogTitleText = englishMode() ? config.og_title_en : config.og_title_he;
  const ogDescriptionText = englishMode() ? config.og_description_en : config.og_description_he;
  document.title = metaTitle;
  const description = $('meta[name="description"]');
  const descriptionText = metaDescription || (englishMode() ? `${siteName} — a curated video library for adventure, off-road and road riding.` : `${siteName} — ספריית וידאו מקצועית בעברית ללימוד רכיבת אדוונצ'ר, שטח וכביש.`);
  if (description) description.setAttribute("content", descriptionText);
  const ogTitle = $('meta[property="og:title"]');
  const ogDescription = $('meta[property="og:description"]');
  const twitterTitle = $('meta[name="twitter:title"]');
  const twitterDescription = $('meta[name="twitter:description"]');
  if (ogTitle) ogTitle.setAttribute("content", ogTitleText || metaTitle);
  if (ogDescription) ogDescription.setAttribute("content", ogDescriptionText || descriptionText);
  if (twitterTitle) twitterTitle.setAttribute("content", ogTitleText || metaTitle);
  if (twitterDescription) twitterDescription.setAttribute("content", ogDescriptionText || descriptionText);
  $$('[data-site-name]').forEach((node) => { node.textContent = siteName; });
  $$('[data-site-home-link]').forEach((node) => {
    node.setAttribute("aria-label", englishMode() ? `${siteName} — home` : `${siteName} — דף הבית`);
  });
  $$('[data-author-name]').forEach((node) => { node.textContent = config.author_name; });
  $$('[data-author-block]').forEach((node) => { node.hidden = !config.author_name; });
  $$('[data-community-name]').forEach((node) => {
    const communityName = englishMode() ? config.community_name_en : config.community_name;
    node.textContent = communityName;
    node.hidden = !communityName;
  });
  $$('[data-contact]').forEach((node) => {
    node.textContent = config.contact;
    node.dir = "auto";
  });
  $$('[data-contact-block]').forEach((node) => { node.hidden = !config.contact; });
  $$('[data-safety-warning]').forEach((node) => { node.textContent = englishMode() ? config.safety_warning_en : config.safety_warning_he; });
  $$('[data-release-version]').forEach((node) => { node.textContent = config.release_version; });
  document.documentElement.dataset.release = config.release_version;
  $$('[data-current-year]').forEach((node) => { node.textContent = String(new Date().getFullYear()); });
  applyLogoConfig(config);
}

function initializeVisitCounter() {
  const image = $("#visit-counter");
  if (!(image instanceof HTMLImageElement)) return;
  const canonicalHost = "galsec1999.github.io";
  const canonicalPath = "/adventure-riding-video-guide";
  const isCanonical = window.location.hostname === canonicalHost
    && window.location.pathname.startsWith(canonicalPath);
  if (!isCanonical) {
    const placeholder = createElement("span", {
      className: "visit-counter__placeholder",
      text: ui("באתר החי", "On the live site"),
    });
    image.replaceWith(placeholder);
    return;
  }
  image.addEventListener("error", () => {
    const fallback = createElement("span", {
      className: "visit-counter__placeholder",
      text: ui("המונה אינו זמין כרגע", "Counter currently unavailable"),
      attrs: { role: "status" },
    });
    image.replaceWith(fallback);
  }, { once: true });
  image.src = "https://hits.sh/galsec1999.github.io/adventure-riding-video-guide.svg?style=flat-square&label=&color=cc5a2c";
}

function validateRuntimeVideos(videos) {
  if (!Array.isArray(videos)) throw new Error(ui("נתוני הסרטונים חייבים להיות מערך JSON.", "Video data must be a JSON array."));
  if (videos.length === 0) throw new Error(ui("ספריית הסרטונים ריקה. נדרשת לפחות רשומה תקינה אחת.", "The video library is empty. At least one valid record is required."));
  const requiredStrings = [
    "id", "youtube_video_id", "youtube_url", "thumbnail_url", "title_he", "title_original",
    "channel_name", "channel_url", "summary_he", "fit_for_he", "why_watch_he", "quality_reason_he",
    "domain", "primary_category", "skill_level", "risk_level", "language", "source_type", "last_checked",
  ];
  const requiredArrays = [
    "secondary_categories", "tags", "learning_points_he", "exercises_he", "equipment_he",
    "safety_warnings_he", "common_mistakes_he", "subtitle_languages", "motorcycle_types",
    "motorcycle_weight_classes", "terrain_types", "road_conditions", "chapters", "related_video_ids",
  ];
  const ids = new Set();
  const youtubeIds = new Set();
  videos.forEach((video, index) => {
    if (!video || Array.isArray(video) || typeof video !== "object") {
      throw new Error(ui(`רשומת הסרטון ${index + 1} אינה אובייקט תקין.`, `Video record ${index + 1} is not a valid object.`));
    }
    requiredStrings.forEach((field) => {
      if (typeof video[field] !== "string" || !video[field].trim()) {
        throw new Error(ui(`רשומת הסרטון ${index + 1} חסרה ערך טקסט תקין בשדה ${field}.`, `Video record ${index + 1} is missing a valid text value in ${field}.`));
      }
    });
    requiredArrays.forEach((field) => {
      if (!Array.isArray(video[field])) throw new Error(ui(`רשומת הסרטון ${video.id} חייבת לכלול מערך בשדה ${field}.`, `Video record ${video.id} must include an array in ${field}.`));
    });
    if (!video.verification || typeof video.verification !== "object"
      || typeof video.verification.notes_he !== "string"
      || typeof video.verification.classification_confidence !== "string"
      || !Array.isArray(video.verification.content_evidence_types)) {
      throw new Error(ui(`רשומת הסרטון ${video.id} חסרה תיעוד אימות תקין.`, `Video record ${video.id} is missing valid verification evidence.`));
    }
    if (!Number.isFinite(video.quality_score) || (video.duration_seconds != null && !Number.isFinite(video.duration_seconds))) {
      throw new Error(ui(`רשומת הסרטון ${video.id} כוללת ערך מספרי לא תקין.`, `Video record ${video.id} contains an invalid numeric value.`));
    }
    if (ids.has(video.id)) throw new Error(ui(`מזהה הסרטון ${video.id} מופיע יותר מפעם אחת.`, `Video ID ${video.id} appears more than once.`));
    if (youtubeIds.has(video.youtube_video_id)) throw new Error(ui(`YouTube Video ID ${video.youtube_video_id} מופיע יותר מפעם אחת.`, `YouTube Video ID ${video.youtube_video_id} appears more than once.`));
    ids.add(video.id);
    youtubeIds.add(video.youtube_video_id);
  });
}

function appendSeparatedParts(container, parts) {
  parts.filter(Boolean).forEach((part, index) => {
    if (index > 0) container.append(createElement("span", { text: "·", attrs: { "aria-hidden": "true" } }));
    container.append(createElement(part.tag || "span", {
      text: part.text,
      attrs: { dir: part.dir || "auto", ...part.attrs },
    }));
  });
  return container;
}

function createVideoMeta(video, { includeCategory = false, includeDate = false, className = "" } = {}) {
  const parts = [
    { tag: "bdi", text: video.channel_name, dir: "auto", attrs: { class: "mixed-meta__channel" } },
    { text: formatDuration(video.duration_seconds), dir: "ltr", attrs: { class: "mixed-meta__duration" } },
  ];
  if (includeCategory) parts.push({ tag: "bdi", text: label(video.primary_category), dir: "auto", attrs: { class: "mixed-meta__category" } });
  if (includeDate) {
    parts.push(video.published_date
      ? { tag: "time", text: formatDate(video.published_date), dir: "ltr", attrs: { datetime: video.published_date, class: "mixed-meta__date" } }
      : { text: ui("תאריך לא זמין", "Date unavailable"), dir: "auto", attrs: { class: "mixed-meta__date" } });
  }
  return appendSeparatedParts(createElement("p", { className: `mixed-meta ${className}`.trim() }), parts);
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return ui("משך לא זמין", "Duration unavailable");
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function formatDate(value) {
  if (!value) return ui("תאריך לא זמין", "Date unavailable");
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.valueOf())) return value;
  return englishMode() ? new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(date) : `${String(date.getUTCDate()).padStart(2, "0")}.${String(date.getUTCMonth() + 1).padStart(2, "0")}.${date.getUTCFullYear()}`;
}

function label(id) {
  const item = state.labels.get(id);
  return (englishMode() ? item?.name_en : item?.name_he) || id || ui("לא צוין", "Not specified");
}

function setLabels() {
  state.labels.clear();
  const orderedGroups = [
    "domains", "categories", "subcategories", "content_types", "terrain_types", "road_conditions",
    "skill_levels", "risk_levels", "motorcycle_types", "motorcycle_weight_classes",
    "source_types", "languages", "controlled_tags",
  ];
  orderedGroups.forEach((key) => {
    const items = state.taxonomy[key];
    if (!Array.isArray(items)) return;
    items.forEach((item) => {
      if (item?.id && !state.labels.has(item.id)) state.labels.set(item.id, item);
    });
  });
}

async function fetchJson(path) {
  const embeddedId = EMBEDDED_DATA_IDS[path];
  const embedded = embeddedId ? document.getElementById(embeddedId) : null;
  if (embedded) {
    try {
      return JSON.parse(embedded.textContent || "null");
    } catch (error) {
      throw new Error(ui(`הנתונים המוטמעים עבור ${path} אינם JSON תקין: ${error.message}`, `Embedded data for ${path} is not valid JSON: ${error.message}`));
    }
  }
  const requestUrl = new URL(path, document.baseURI);
  requestUrl.searchParams.set("v", DATA_CACHE_REVISION);
  const response = await fetch(requestUrl, { cache: "no-store" });
  if (!response.ok) throw new Error(ui(`טעינת ${path} נכשלה (${response.status})`, `Loading ${path} failed (${response.status}).`));
  return response.json();
}

function announce(message) {
  const liveRegion = $("#live-region") || $("[role='status']");
  if (liveRegion) liveRegion.textContent = message;
}

function showToast(message) {
  let toast = $("#toast");
  if (!toast) {
    toast = createElement("div", {
      className: "toast",
      attrs: { id: "toast" },
    });
    ($("#toast-region") || document.body).append(toast);
  }
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(showToast.timeoutId);
  showToast.timeoutId = window.setTimeout(() => { toast.hidden = true; }, 2600);
}

function showFatalError(error) {
  console.error(error);
  const app = $("#app") || document.body;
  const panel = createElement("section", {
    className: "error-panel",
    attrs: { role: "alert", "aria-labelledby": "load-error-title" },
  });
  panel.append(
    createElement("h1", { text: ui("לא הצלחנו לטעון את המדריך", "We could not load the guide"), attrs: { id: "load-error-title" } }),
    createElement("p", { text: error.message || ui("אירעה שגיאה לא צפויה.", "An unexpected error occurred.") }),
    createElement("p", { text: ui("יש לפתוח את האתר דרך השרת המקומי: run-local.bat או python tools/serve_local.py", "Open the guide through the local server: run-local.bat or python tools/serve_local.py") }),
  );
  app.replaceChildren(panel);
  app.hidden = false;
  if ($("#app-status")) $("#app-status").hidden = true;
  announce(ui("טעינת האתר נכשלה. מוצגות הוראות להפעלה מקומית.", "The guide failed to load. Local launch instructions are shown."));
}

function applyTheme(theme) {
  const preferred = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const activeTheme = theme || browserStorage.getTheme() || preferred;
  document.documentElement.dataset.theme = activeTheme;
  document.documentElement.style.colorScheme = activeTheme;
  const toggle = $("#theme-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", String(activeTheme === "dark"));
    toggle.setAttribute("aria-label", activeTheme === "dark" ? ui("מעבר למצב בהיר", "Switch to light mode") : ui("מעבר למצב כהה", "Switch to dark mode"));
    const text = $("[data-theme-label], .theme-toggle__label", toggle);
    if (text) text.textContent = activeTheme === "dark" ? ui("מצב בהיר", "Light") : ui("מצב כהה", "Dark");
  }
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  browserStorage.setTheme(next);
  applyTheme(next);
  showToast(next === "dark" ? ui("מצב כהה הופעל", "Dark mode enabled") : ui("מצב בהיר הופעל", "Light mode enabled"));
}

function populateSelect(id, items, emptyLabel, preferredValue = "") {
  const select = $(`#${id}`);
  if (!select) return "";
  const options = [createElement("option", { text: emptyLabel, attrs: { value: "" } })];
  items.forEach((item) => {
    const base = englishMode() ? (item.name_en || item.name_he) : item.name_he;
    const count = Number.isFinite(item._count) ? ` (${item._count})` : "";
    options.push(createElement("option", { text: `${base}${count}`, attrs: { value: item.id } }));
  });
  select.replaceChildren(...options);
  const valid = items.some((item) => item.id === preferredValue);
  select.value = valid ? preferredValue : "";
  return select.value;
}

function taxonomyItems(collection, allowedIds) {
  const allowed = allowedIds instanceof Set ? allowedIds : new Set(allowedIds || []);
  return (state.taxonomy[collection] || []).filter((item) => allowed.has(item.id));
}

function currentCollectionVideos() {
  return state.currentView === "shorts" ? state.shorts : state.videos;
}

function contextualVideos({ includeCategory = true } = {}) {
  const domain = state.filters.domain || "";
  const category = includeCategory ? (state.filters.category || "") : "";
  return currentCollectionVideos().filter((video) => {
    if (domain && video.domain !== domain) return false;
    if (category && video.primary_category !== category) return false;
    return true;
  });
}

function countedItems(collection, allowedIds, videos, field) {
  return taxonomyItems(collection, allowedIds).map((item) => ({
    ...item,
    _count: videos.filter((video) => Array.isArray(video[field]) ? video[field].includes(item.id) : video[field] === item.id).length,
  })).sort((a, b) => (b._count - a._count) || label(a.id).localeCompare(label(b.id), englishMode() ? "en" : "he"));
}

function refreshContextualFilters() {
  const domainVideos = contextualVideos({ includeCategory: false });
  const categoryIds = new Set(domainVideos.map((video) => video.primary_category));
  state.filters.category = populateSelect(
    FILTER_IDS.category,
    countedItems("categories", categoryIds, domainVideos, "primary_category"),
    state.filters.domain ? ui("כל הנושאים בתחום", "All topics in this area") : ui("כל הנושאים", "All topics"),
    state.filters.category || "",
  );

  const categoryVideos = contextualVideos({ includeCategory: true });
  const subtopicIds = new Set(categoryVideos.flatMap((video) => video.subtopics || []));
  state.filters.subcategory = populateSelect(
    FILTER_IDS.subcategory,
    countedItems("subcategories", subtopicIds, categoryVideos, "subtopics"),
    state.filters.category ? ui("כל המיקודים בנושא", "All focus areas in this topic") : ui("כל המיקודים", "All focus areas"),
    state.filters.subcategory || "",
  );
  const focusControl = $(`#${FILTER_IDS.subcategory}`);
  if (focusControl) focusControl.disabled = subtopicIds.size === 0;

  const formatIds = new Set(categoryVideos.map((video) => video.content_type).filter(Boolean));
  state.filters.format = populateSelect(
    FILTER_IDS.format,
    countedItems("content_types", formatIds, categoryVideos, "content_type"),
    ui("כל סוגי ההדרכה", "All guidance formats"),
    state.filters.format || "",
  );

  const terrainIds = new Set(categoryVideos.flatMap((video) => video.terrain_types || []));
  state.filters.terrain = populateSelect(
    FILTER_IDS.terrain,
    countedItems("terrain_types", terrainIds, categoryVideos, "terrain_types"),
    terrainIds.size ? ui("כל סוגי הקרקע הרלוונטיים", "All relevant terrain") : ui("אין סוגי קרקע רלוונטיים", "No relevant terrain"),
    state.filters.terrain || "",
  );
  const terrainControl = $(`#${FILTER_IDS.terrain}`);
  if (terrainControl) terrainControl.disabled = terrainIds.size === 0;

  const roadIds = new Set(categoryVideos.flatMap((video) => video.road_conditions || []));
  state.filters.road = populateSelect(
    FILTER_IDS.road,
    countedItems("road_conditions", roadIds, categoryVideos, "road_conditions"),
    roadIds.size ? ui("כל תנאי הדרך הרלוונטיים", "All relevant road conditions") : ui("אין תנאי דרך רלוונטיים", "No relevant road conditions"),
    state.filters.road || "",
  );
  const roadControl = $(`#${FILTER_IDS.road}`);
  if (roadControl) roadControl.disabled = roadIds.size === 0;
}
function populateFilters() {
  populateSelect(FILTER_IDS.domain, state.taxonomy.domains || [], ui("כל התחומים", "All areas"), state.filters.domain || "");
  populateSelect(FILTER_IDS.language, state.taxonomy.languages || [], ui("כל השפות", "All languages"), state.filters.language || "");
  populateSelect(FILTER_IDS.skill, state.taxonomy.skill_levels || [], ui("כל הרמות", "All levels"), state.filters.skill || "");
  populateSelect(FILTER_IDS.risk, state.taxonomy.risk_levels || [], ui("כל רמות הסיכון", "All risk levels"), state.filters.risk || "");
  populateSelect(FILTER_IDS.motorcycle, state.taxonomy.motorcycle_types || [], ui("כל סוגי האופנוע", "All motorcycle types"), state.filters.motorcycle || "");
  populateSelect(FILTER_IDS.weight, state.taxonomy.motorcycle_weight_classes || [], ui("כל המשקלים", "All weight classes"), state.filters.weight || "");
  refreshContextualFilters();
}

function getFiltersFromControls() {
  const filters = { q: $("#library-search")?.value.trim() || "" };
  Object.entries(FILTER_IDS).forEach(([key, id]) => {
    filters[key] = $(`#${id}`)?.value || "";
  });
  Object.entries(CHECKBOX_FILTERS).forEach(([key, [id, value]]) => {
    filters[key] = $(`#${id}`)?.checked ? value : "";
  });
  if ($("#filter-watched")?.checked) filters.watched = "yes";
  else if ($("#filter-unwatched")?.checked) filters.watched = "no";
  else filters.watched = "";
  filters.sort = $("#sort-select")?.value || "recommended";
  return filters;
}

function syncControlsFromFilters() {
  refreshContextualFilters();
  if ($("#library-search")) $("#library-search").value = state.filters.q || "";
  Object.entries(FILTER_IDS).forEach(([key, id]) => {
    const control = $(`#${id}`);
    if (!control) return;
    const wanted = state.filters[key] || "";
    const exists = [...control.options].some((option) => option.value === wanted);
    control.value = exists ? wanted : "";
    if (!exists) state.filters[key] = "";
  });
  Object.entries(CHECKBOX_FILTERS).forEach(([key, [id, value]]) => {
    const control = $(`#${id}`);
    if (control) control.checked = state.filters[key] === value;
  });
  if ($("#filter-watched")) $("#filter-watched").checked = state.filters.watched === "yes";
  if ($("#filter-unwatched")) $("#filter-unwatched").checked = state.filters.watched === "no";
  if ($("#sort-select")) $("#sort-select").value = state.filters.sort || "recommended";
}

function hydrateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  URL_FILTER_KEYS.forEach((key) => {
    state.filters[key] = key === "sort" ? "recommended" : "";
    if (params.has(key)) state.filters[key] = params.get(key) || "";
  });
  const requestedView = params.get("view") || window.location.hash.replace(/^#/, "");
  state.currentView = VALID_VIEWS.includes(requestedView) ? requestedView : "home";
  const videoId = params.get("video");
  state.activeVideoId = videoId && state.videosById.has(videoId) ? videoId : null;
  const pathId = params.get("path") || browserStorage.getSelectedPath();
  state.selectedPathId = state.paths.some((path) => path.id === pathId) ? pathId : "";
  syncControlsFromFilters();
}

function updateUrl({ push = false, includeVideo = true } = {}) {
  const url = new URL(window.location.href);
  URL_FILTER_KEYS.forEach((key) => {
    const value = state.filters[key];
    if (value && !(key === "sort" && value === "recommended")) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  });
  if (state.currentView !== "home") url.searchParams.set("view", state.currentView);
  else url.searchParams.delete("view");
  if (includeVideo && state.activeVideoId) url.searchParams.set("video", state.activeVideoId);
  else url.searchParams.delete("video");
  if (state.currentView === "paths" && state.selectedPathId) url.searchParams.set("path", state.selectedPathId);
  else url.searchParams.delete("path");
  url.hash = "";
  try {
    window.history[push ? "pushState" : "replaceState"]({}, "", url);
  } catch {
    // Some standalone viewers (notably file://, embedded preview panes and
    // locked-down mobile browsers) disallow History API URL mutations. The
    // guide remains fully usable; only shareable filter state in the address
    // bar is omitted in that environment.
  }
}

function reflectMenuState(open) {
  const button = $("#mobile-menu-toggle");
  if (button) {
    button.setAttribute("aria-expanded", String(open));
    button.setAttribute("aria-label", open
      ? ui("סגירת תפריט הניווט", "Close navigation menu")
      : ui("פתיחת תפריט הניווט", "Open navigation menu"));
  }
  $("#primary-nav")?.classList.toggle("is-open", open);
  if ($("#site-header")) $("#site-header").dataset.menuOpen = String(open);
}

function setMenuOpen(open, { restoreFocus = true } = {}) {
  if (!open) {
    const closed = overlayManager.close("menu", { restoreFocus });
    if (!closed) reflectMenuState(false);
    return;
  }
  if (!overlayManager.mobileMedia.matches) return;
  reflectMenuState(true);
  overlayManager.open("menu", {
    root: $("#primary-nav"),
    opener: $("#mobile-menu-toggle"),
    firstFocus: () => $("#primary-nav a"),
    inertBackground: true,
    onClose: () => reflectMenuState(false),
  });
}

function reflectFilterState(open) {
  $("#filter-panel")?.setAttribute("data-open", String(open));
  $("#mobile-filter-toggle")?.setAttribute("aria-expanded", String(open));
}

function setFiltersOpen(open, { restoreFocus = true } = {}) {
  if (!open) {
    const closed = overlayManager.close("filters", { restoreFocus });
    if (!closed) reflectFilterState(false);
    return;
  }
  if (!overlayManager.mobileMedia.matches) return;
  reflectFilterState(true);
  overlayManager.open("filters", {
    root: $("#filter-panel"),
    opener: $("#mobile-filter-toggle"),
    firstFocus: () => $(".filter-close", $("#filter-panel")) || $("#filter-domain"),
    inertBackground: true,
    onClose: () => reflectFilterState(false),
  });
}

function closeTransientOverlays({ restoreFocus = false } = {}) {
  setFiltersOpen(false, { restoreFocus });
  setMenuOpen(false, { restoreFocus });
}

function navigate(view, { updateHistory = true, focus = false } = {}) {
  if (!VALID_VIEWS.includes(view)) view = "home";
  closeTransientOverlays({ restoreFocus: false });
  if ($("#video-dialog")?.open) closeVideo({ updateHistory: false, restoreFocus: false });
  if ($("#rights-dialog")?.open) closeRights({ restoreFocus: false });
  if ($("#feedback-dialog")?.open) closeFeedback({ restoreFocus: false });
  state.currentView = view;
  $$('[id$="-view"]').forEach((section) => {
    const active = section.id === `${view}-view` || (view === "shorts" && section.id === "library-view");
    section.hidden = !active;
    section.setAttribute("aria-hidden", String(!active));
  });
  $$('a[data-view], button[data-view], a[data-route], button[data-route]').forEach((item) => {
    const active = (item.dataset.view || item.dataset.route) === view;
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  if (view === "library" || view === "shorts") renderLibrary({ syncUrl: false });
  if (view === "paths") renderPaths();
  if (view === "trips") renderTrips();
  if (view === "smart") renderSmartResults(state.smartQuery);
  if (view === "home") renderContinue();
  if (updateHistory) updateUrl({ push: true });
  if (focus) {
    const targetView = view === "shorts" ? "library" : view;
    const heading = $(`#${targetView}-view h1, #${targetView}-view h2`);
    if (heading) {
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderDomainCards() {
  const container = $("#domain-grid");
  if (!container) return;
  const accents = ["earth", "road", "mixed", "practice", "safety", "touring"];
  const cards = (state.taxonomy.domains || []).map((domain, index) => {
    const count = state.videos.filter((video) => video.domain === domain.id).length;
    const button = createElement("button", {
      className: `domain-card domain-card--${accents[index] || "earth"}`,
      attrs: { type: "button", "data-domain": domain.id, "aria-label": englishMode() ? `${domain.name_en || domain.name_he}, ${count} videos` : `${domain.name_he}, ${count} סרטונים` },
    });
    button.append(
      createElement("span", { className: "domain-card__eyebrow", text: englishMode() ? `${count} videos` : `${count} סרטונים` }),
      createElement("strong", { className: "domain-card__title", text: localField(domain, "name") }),
      createElement("span", { className: "domain-card__description", text: localField(domain, "description") }),
      createElement("span", { className: "domain-card__link", text: ui("לספרייה ←", "Open library →") }),
    );
    return button;
  });
  container.replaceChildren(...cards);

  $$('[data-stat="videos"]').forEach((node) => { node.textContent = String(state.videos.length); });
  $$('[data-stat="shorts"]').forEach((node) => { node.textContent = String(state.shorts.length); });
  $$('[data-stat="all-videos"]').forEach((node) => { node.textContent = String(state.allVideos.length); });
  $$('[data-stat="domains"]').forEach((node) => { node.textContent = String((state.taxonomy.domains || []).length); });
  $$('[data-stat="paths"]').forEach((node) => { node.textContent = String(state.paths.length); });
  $$('[data-stat="channels"]').forEach((node) => {
    node.textContent = String(new Set(state.videos.map((video) => video.channel_name)).size);
  });
}

function renderFeatured() {
  const container = $("#featured-grid");
  if (!container) return;
  const featured = [...state.videos]
    .sort((a, b) => (b.quality_score - a.quality_score) || (a._sourceIndex - b._sourceIndex))
    .slice(0, 3);
  container.replaceChildren(...featured.map((video) => createVideoCard(video, { compact: true })));
}

function createBadge(text, kind = "neutral") {
  return createElement("span", { className: `badge badge--${kind}`, text });
}

function createImageFallback(message) {
  return createElement("span", {
    className: "image-fallback",
    text: message,
    attrs: { role: "status", hidden: "" },
  });
}

function connectImageFallback(image, fallback) {
  image.addEventListener("error", () => {
    image.hidden = true;
    fallback.hidden = false;
  }, { once: true });
}

function createVideoCard(video, { compact = false, matchReason = "" } = {}) {
  const article = createElement("article", {
    className: `video-card${compact ? " video-card--compact" : ""}${video.media_format === "short" ? " video-card--short" : ""}`,
    attrs: { "data-video-id": video.id },
  });
  const media = createElement("div", { className: "video-card__media" });
  const image = createElement("img", {
    attrs: {
      src: video.thumbnail_url,
      alt: ui(`תמונת תצוגה של ${videoTitle(video)}`, `Thumbnail for ${videoTitle(video)}`),
      loading: "lazy",
      decoding: "async",
      width: "480",
      height: "360",
    },
  });
  const play = createButton(ui("צפייה", "Watch"), "play-video", {
    className: "video-card__play",
    "data-video-id": video.id,
    "aria-label": ui(`צפייה בסרטון: ${videoTitle(video)}`, `Watch video: ${videoTitle(video)}`),
  });
  const imageFallback = createImageFallback(ui("תמונת התצוגה אינה זמינה. אפשר לפתוח את הסרטון או לעבור ל־YouTube.", "The thumbnail is unavailable. You can still open the video or view it on YouTube."));
  connectImageFallback(image, imageFallback);
  media.append(image, imageFallback, play);

  const body = createElement("div", { className: "video-card__body" });
  const badges = createElement("div", { className: "badge-row" });
  badges.append(
    createBadge(label(video.domain), "domain"),
    createBadge(label(video.skill_level), "level"),
    createBadge(video.language === "he" ? ui("עברית", "Hebrew") : ui("אנגלית", "English"), "language"),
  );
  if (video.media_format === "short") badges.prepend(createBadge(ui("קצר", "Short"), "short"));
  if (video.contains_marketing) badges.append(createBadge(ui("כולל רכיב שיווקי", "Includes marketing"), "warning"));
  if (state.watched.has(video.id)) badges.append(createBadge(ui("נצפה", "Watched"), "success"));

  const title = createElement("h3", { className: "video-card__title", text: videoTitle(video) });
  const originalText = englishMode() ? (video.language === "he" ? video.title_original : "") : video.title_original;
  const original = createElement("p", { className: "video-card__original", text: originalText, attrs: { dir: "auto" } });
  original.hidden = !originalText;
  const meta = createVideoMeta(video, { includeCategory: true, className: "video-card__meta" });
  const summary = createElement("p", { className: "video-card__summary", text: videoSummary(video) });
  const learning = createElement("p", { className: "video-card__learning" });
  learning.append(
    createElement("strong", { text: ui("מה נלמד: ", "What you will learn: ") }),
    document.createTextNode(videoArray(video, "learning_points").slice(0, compact ? 1 : 2).join(" · ")),
  );
  const tags = createElement("div", { className: "tag-list", attrs: { "aria-label": ui("תגיות", "Tags") } });
  uniqueDisplayTaxonomyIds([...(video.subtopics || []), ...video.tags], state.labels, currentLanguage())
    .slice(0, compact ? 2 : 4)
    .forEach((tag) => tags.append(createElement("span", { className: "tag", text: label(tag) })));
  const sourceNote = createElement("p", {
    className: "video-card__source",
    text: ui("סוג מקור", "Source") + ": " + label(video.source_type) + " · " + ui("עומק אימות", "Verification depth") + " " + video.quality_score + "/5",
  });
  const reason = matchReason ? createElement("p", { className: "smart-match-reason", text: matchReason }) : null;
  const likeNote = createElement("p", {
    className: compact ? "creator-like-note creator-like-note--compact" : "creator-like-note",
    text: ui("עזר לכם? תנו לייק ביוטיוב — כך מעודדים את היוצרים להמשיך.", "Helpful? Give it a like on YouTube — it helps creators keep making useful videos."),
  });

  const actions = createElement("div", { className: "video-card__actions" });
  const favorite = createButton(state.favorites.has(video.id) ? ui("במועדפים", "In favourites") : ui("מועדף", "Favourite"), "toggle-favorite", {
    className: `icon-button${state.favorites.has(video.id) ? " is-active" : ""}`,
    "data-video-id": video.id,
    "aria-pressed": String(state.favorites.has(video.id)),
    "aria-label": ui(
      `${state.favorites.has(video.id) ? "הסרה מהמועדפים" : "הוספה למועדפים"}: ${videoTitle(video)}`,
      `${state.favorites.has(video.id) ? "Remove from favourites" : "Add to favourites"}: ${videoTitle(video)}`,
    ),
  });
  const watched = createButton(state.watched.has(video.id) ? ui("נצפה", "Watched") : ui("סימון נצפה", "Mark watched"), "toggle-watched", {
    className: `icon-button${state.watched.has(video.id) ? " is-active" : ""}`,
    "data-video-id": video.id,
    "aria-pressed": String(state.watched.has(video.id)),
  });
  const details = createButton(ui("פרטים", "Details"), "open-video", {
    className: "button button--secondary",
    "data-video-id": video.id,
  });
  const youtube = createElement("a", {
    className: "button button--text",
    text: "YouTube",
    attrs: { href: video.youtube_url, target: "_blank", rel: "noopener noreferrer", "aria-label": ui(`פתיחה ב-YouTube: ${videoTitle(video)}`, `Open on YouTube: ${videoTitle(video)}`) },
  });
  actions.append(favorite, watched, details, youtube);
  body.append(badges, title, original, meta, summary, learning, tags, sourceNote);
  if (reason) body.append(reason);
  body.append(likeNote, actions);
  article.append(media, body);
  return article;
}

function activeFilterEntries() {
  const names = englishMode() ? {
    q: "Search", domain: "Area", category: "Topic", subcategory: "Focus", format: "Format", language: "Language", skill: "Level",
    risk: "Risk", motorcycle: "Motorcycle", weight: "Weight", terrain: "Terrain", road: "Road condition",
    duration: "Duration", subtitles: "Subtitles", professional: "Professional source", marketing: "No marketing",
    favorite: "Favourites", watched: "Watch status", practical: "Practical drill", warnings: "Warnings", beginner: "Beginner",
  } : {
    q: "חיפוש", domain: "תחום", category: "נושא", subcategory: "מיקוד", format: "סוג הדרכה", language: "שפה", skill: "רמה",
    risk: "סיכון", motorcycle: "אופנוע", weight: "משקל", terrain: "קרקע", road: "דרך",
    duration: "משך", subtitles: "כתוביות", professional: "מקור מקצועי", marketing: "ללא שיווק",
    favorite: "מועדפים", watched: "מצב צפייה", practical: "תרגול", warnings: "אזהרות", beginner: "מתחילים",
  };
  return Object.entries(state.filters)
    .filter(([key, value]) => value && key !== "sort")
    .map(([key, value]) => ({ key, name: names[key] || key, value: state.labels.has(value) ? label(value) : value }));
}

function renderActiveFilters() {
  const container = $("#active-filters");
  if (!container) return;
  const entries = activeFilterEntries();
  container.hidden = entries.length === 0;
  container.replaceChildren(...entries.map(({ key, name, value }) => {
    const button = createButton(`${name}: ${value} ×`, "remove-filter", {
      className: "filter-chip",
      "data-filter-key": key,
      "aria-label": `הסרת מסנן ${name}: ${value}`,
    });
    return button;
  }));
}

function renderLibraryNavigator() {
  const tabs = $("#library-domain-tabs");
  const chips = $("#topic-quick-chips");
  const title = $("#topic-context-title");
  const description = $("#topic-context-description");
  if (!tabs || !chips || !title || !description) return;

  const allButton = createButton(ui("הכול", "All"), "quick-domain", {
    className: `domain-tab${state.filters.domain ? "" : " is-active"}`,
    "data-filter-value": "",
    "aria-pressed": String(!state.filters.domain),
  });
  const collection = currentCollectionVideos();
  const domainButtons = (state.taxonomy.domains || []).map((domain) => {
    const count = collection.filter((video) => video.domain === domain.id).length;
    return createButton(`${label(domain.id)} · ${count}`, "quick-domain", {
      className: `domain-tab${state.filters.domain === domain.id ? " is-active" : ""}`,
      "data-filter-value": domain.id,
      "aria-pressed": String(state.filters.domain === domain.id),
    });
  });
  tabs.replaceChildren(allButton, ...domainButtons);

  const domain = state.labels.get(state.filters.domain);
  const category = state.labels.get(state.filters.category);
  const focus = state.labels.get(state.filters.subcategory);
  const contextParts = [domain && label(domain.id), category && label(category.id), focus && label(focus.id)].filter(Boolean);
  if (contextParts.length) {
    const nodes = [];
    contextParts.forEach((text, index) => {
      if (index) nodes.push(createElement("span", { className: "topic-context__separator", text: "/", attrs: { "aria-hidden": "true" } }));
      nodes.push(createElement("bdi", { className: "topic-context__segment", text, attrs: { dir: "auto" } }));
    });
    title.replaceChildren(...nodes);
  } else {
    title.textContent = ui("כל תחומי הרכיבה", "All riding areas");
  }
  description.textContent = focus ? localField(focus, "description") : category ? localField(category, "description") : domain ? localField(domain, "description") : ui("בחרו תחום כדי לראות נושאים ומיקודים רלוונטיים בלבד.", "Choose an area to see only relevant topics and focus areas.");

  let candidates = [];
  if (state.filters.category) {
    const base = contextualVideos({ includeCategory: true });
    const counts = CounterLike(base.flatMap((video) => video.subtopics || []));
    candidates = [...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8).map(([id,count]) => ({ id, count, action:"quick-focus" }));
  } else {
    const base = contextualVideos({ includeCategory: false });
    const counts = CounterLike(base.map((video) => video.primary_category));
    candidates = [...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,10).map(([id,count]) => ({ id, count, action:"quick-category" }));
  }
  chips.replaceChildren(...candidates.map(({id,count,action}) => createButton(`${label(id)} · ${count}`, action, {
    className: `topic-chip${state.filters.category === id || state.filters.subcategory === id ? " is-active" : ""}`,
    "data-filter-value": id,
  })));
}

function CounterLike(values) {
  const map = new Map();
  values.filter(Boolean).forEach((value) => map.set(value, (map.get(value) || 0) + 1));
  return map;
}

function applyQuickFacet(kind, value) {
  if (kind === "domain") {
    state.filters.domain = value;
    state.filters.category = "";
    state.filters.subcategory = "";
    state.filters.terrain = "";
    state.filters.road = "";
  } else if (kind === "category") {
    state.filters.category = value;
    state.filters.subcategory = "";
    state.filters.terrain = "";
    state.filters.road = "";
  } else if (kind === "focus") {
    state.filters.subcategory = value;
  }
  syncControlsFromFilters();
  state.visibleLimit = INITIAL_VISIBLE_LIMIT;
  renderLibrary();
}

function renderLibrary({ syncUrl = true } = {}) {
  if (!state.ready) return;
  const collection = currentCollectionVideos();
  const shortMode = state.currentView === "shorts";
  const title = $("#library-title");
  const eyebrow = $("#library-view .page-hero .eyebrow");
  const intro = $("#library-title + p");
  if (title) title.textContent = shortMode ? ui("ספריית הקצרים", "Shorts library") : ui("ספריית הסרטונים", "Video library");
  if (eyebrow) eyebrow.textContent = shortMode
    ? ui(`${state.shorts.length} קצרים מאומתים · רעיון אחד בכל צפייה`, `${state.shorts.length} verified Shorts · one idea per watch`)
    : ui(`${state.videos.length} סרטונים · מידע מאומת · חיפוש אחד`, `${state.videos.length} videos · verified information · one search`);
  if (intro) intro.textContent = shortMode
    ? ui("חפשו וסננו קטעי YouTube Shorts לפי תחום, נושא, רמה ושפה. קצר הוא נקודת כניסה מהירה — לא תחליף להדרכה מלאה.", "Search and filter YouTube Shorts by area, topic, level and language. A Short is a quick entry point, not a replacement for full instruction.")
    : ui("בחרו תחום, עברו לנושא מרכזי וצמצמו למיקוד מדויק. רק אפשרויות שרלוונטיות לבחירה שלכם יוצגו.", "Choose an area, move to a main topic and narrow to a precise focus. Only relevant options are shown.");
  state.filters = { ...state.filters, ...getFiltersFromControls() };
  const results = applySearchAndFilters(collection, state.filters, {
    favorites: state.favorites,
    watched: state.watched,
    synonymIndex: state.synonymIndex,
  });
  const count = $("#result-count");
  if (count) count.textContent = englishMode() ? `${results.length} videos found` : `${results.length} סרטונים נמצאו`;
  $$('[data-filter-result-count]').forEach((node) => { node.textContent = String(results.length); });
  renderActiveFilters();
  renderLibraryNavigator();

  const grid = $("#video-grid");
  const empty = $("#empty-state");
  const loadMore = $("#load-more");
  if (!grid) return;
  const limit = clampVisibleLimit(results.length, state.visibleLimit);
  grid.replaceChildren(...results.slice(0, limit).map((video) => createVideoCard(video)));
  grid.setAttribute("aria-busy", "false");
  if (empty) empty.hidden = results.length !== 0;
  if (loadMore) {
    loadMore.hidden = limit >= results.length;
    loadMore.textContent = englishMode() ? `Show more (${results.length - limit})` : `הצגת עוד (${results.length - limit})`;
    const wrap = $("#load-more-wrap");
    if (wrap) wrap.hidden = limit >= results.length;
  }
  const progress = $("#load-progress");
  if (progress) progress.textContent = englishMode() ? `Showing ${limit} of ${results.length} videos` : `מוצגים ${limit} מתוך ${results.length} סרטונים`;
  announce(englishMode() ? `${results.length} videos found` : `${results.length} סרטונים נמצאו`);
  if (syncUrl) updateUrl();
}

function renderContinue() {
  const section = $("#continue-section");
  const container = $("#continue-content");
  if (!section || !container) return;
  const last = browserStorage.getLastVideo();
  const lastVideo = last ? state.videosById.get(last.id) : null;
  const pathEntry = state.paths.find((path) => {
    const completed = state.pathProgress[path.id]?.length || 0;
    return completed > 0 && completed < path.steps.length;
  });
  const blocks = [];
  if (lastVideo) {
    const block = createElement("article", { className: "continue-card" });
    block.append(
      createElement("span", { className: "eyebrow", text: ui("הסרטון האחרון", "Last video") }),
      createElement("h3", { text: videoTitle(lastVideo) }),
      createElement("p", { text: lastVideo.channel_name, attrs: { dir: "auto" } }),
      createButton(ui("המשך לפרטים", "Continue to details"), "open-video", { "data-video-id": lastVideo.id, className: "button button--primary" }),
    );
    blocks.push(block);
  }
  if (pathEntry) {
    const complete = state.pathProgress[pathEntry.id].length;
    const block = createElement("article", { className: "continue-card" });
    block.append(
      createElement("span", { className: "eyebrow", text: ui("מסלול בתהליך", "Path in progress") }),
      createElement("h3", { text: localField(pathEntry, "name") }),
      createElement("p", { text: englishMode()
        ? `${complete} of ${pathEntry.steps.length} steps completed`
        : `${complete} מתוך ${pathEntry.steps.length} שלבים הושלמו` }),
      createButton(ui("המשך במסלול", "Continue path"), "open-paths", { className: "button button--primary" }),
    );
    blocks.push(block);
  }
  section.hidden = blocks.length === 0;
  container.replaceChildren(...blocks);
}

function videoLink(videoId, text, kind = "primary") {
  const video = state.videosById.get(videoId);
  if (!video) return null;
  return createButton(text || videoTitle(video), "open-video", {
    className: `path-video path-video--${kind}`,
    "data-video-id": video.id,
    title: video.title_original,
  });
}

function selectLearningPath(pathId, { focus = true, updateHistory = true } = {}) {
  if (!state.paths.some((path) => path.id === pathId)) return;
  state.selectedPathId = pathId;
  browserStorage.setSelectedPath(pathId);
  renderPaths();
  if (updateHistory) updateUrl();
  const pathNode = $(`#path-${CSS.escape(pathId)}`);
  if (focus) {
    const heading = $("h2", pathNode);
    if (heading) {
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }
  pathNode?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPaths() {
  const container = $("#paths-container");
  if (!container) return;
  if (!state.paths.some((path) => path.id === state.selectedPathId)) {
    const firstIncomplete = state.paths.find((path) => (state.pathProgress[path.id] || []).length < path.steps.length);
    state.selectedPathId = firstIncomplete?.id || state.paths[0]?.id || "";
    browserStorage.setSelectedPath(state.selectedPathId);
  }
  const pathCards = state.paths.filter((path) => path.id === state.selectedPathId).map((path) => {
    const completed = new Set(state.pathProgress[path.id] || []);
    const card = createElement("article", { className: "learning-path", attrs: { id: `path-${path.id}` } });
    const header = createElement("header", { className: "learning-path__header" });
    const titleBlock = createElement("div");
    titleBlock.append(
      createElement("span", { className: "eyebrow", text: label(path.skill_level) }),
      createElement("h2", { text: localField(path, "name") }),
      createElement("p", { text: localField(path, "description") }),
    );
    const nextStep = path.steps.find((step) => !completed.has(step.order));
    titleBlock.append(createElement("p", {
      className: "path-next-step",
      text: nextStep
        ? ui(`השלב הבא: ${localField(nextStep, "goal")}`, `Next: ${localField(nextStep, "goal")}`)
        : ui("המסלול הושלם — אפשר לבחור מסלול נוסף או לחזור לרענון.", "Path complete — choose another path or revisit it for practice."),
    }));
    const progress = createElement("div", { className: "path-progress" });
    progress.append(
      createElement("span", { text: ui(`${completed.size} מתוך ${path.steps.length} שלבים`, `${completed.size} of ${path.steps.length} steps`) }),
      createElement("progress", { attrs: { value: completed.size, max: path.steps.length, "aria-label": ui(`התקדמות במסלול ${localField(path, "name")}`, `Progress in ${localField(path, "name")}`) } }),
    );
    header.append(titleBlock, progress);

    const steps = createElement("ol", { className: "path-steps" });
    path.steps.forEach((step) => {
      const item = createElement("li", { className: `path-step${completed.has(step.order) ? " is-complete" : ""}` });
      const top = createElement("div", { className: "path-step__top" });
      const checkbox = createElement("input", {
        attrs: {
          type: "checkbox",
          id: `path-${path.id}-step-${step.order}`,
          "data-path-id": path.id,
          "data-step-order": step.order,
          "data-action": "toggle-path-step",
          "aria-label": ui(`סימון השלב ${step.order} כהושלם`, `Mark step ${step.order} complete`),
        },
      });
      checkbox.checked = completed.has(step.order);
      const labelNode = createElement("label", { attrs: { for: checkbox.id } });
      labelNode.append(
        createElement("span", { className: "path-step__number", text: step.order }),
        createElement("strong", { text: localField(step, "goal") }),
      );
      top.append(checkbox, labelNode);
      const explanation = createElement("p", { text: localField(step, "explanation") });
      const guardrails = createElement("dl", { className: "path-step__guardrails" });
      guardrails.append(
        createElement("dt", { text: ui("ציוד", "Equipment") }),
        createElement("dd", { text: (englishMode() ? step.equipment_en : step.equipment_he).join(" · ") }),
        createElement("dt", { text: ui("רמת סיכון", "Risk level") }),
        createElement("dd", { text: label(step.risk_level) }),
        createElement("dt", { text: ui("אזהרה", "Warning") }),
        createElement("dd", { text: localField(step, "warning") }),
      );
      const primary = createElement("div", { className: "path-step__videos" });
      primary.append(createElement("span", { className: "path-step__label", text: ui("סרטונים מרכזיים", "Core videos") }));
      step.primary_video_ids.forEach((id) => {
        const link = videoLink(id, null, "primary");
        if (link) primary.append(link);
      });
      const alternatives = createElement("div", { className: "path-step__videos path-step__videos--alternatives" });
      alternatives.append(createElement("span", { className: "path-step__label", text: ui("חלופות", "Alternatives") }));
      step.alternative_video_ids.forEach((id) => {
        const link = videoLink(id, null, "alternative");
        if (link) alternatives.append(link);
      });
      const shorts = createElement("div", { className: "path-step__videos path-step__videos--shorts" });
      shorts.append(createElement("span", { className: "path-step__label", text: ui("קצרים לחזרה מהירה", "Shorts for a quick recap") }));
      (step.short_video_ids || []).forEach((id) => {
        const link = videoLink(id, null, "short");
        if (link) shorts.append(link);
      });
      item.append(top, explanation, guardrails, primary, alternatives, shorts);
      steps.append(item);
    });
    card.append(header, steps);
    return card;
  });
  container.replaceChildren(...pathCards);
  container.setAttribute("aria-busy", "false");

  const totalSteps = state.paths.reduce((sum, path) => sum + path.steps.length, 0);
  const completedSteps = state.paths.reduce((sum, path) => {
    const validOrders = new Set(path.steps.map((step) => step.order));
    return sum + (state.pathProgress[path.id] || []).filter((order) => validOrders.has(order)).length;
  }, 0);
  const percent = totalSteps ? Math.round((completedSteps / totalSteps) * 100) : 0;
  $$('[data-completed-steps]').forEach((node) => { node.textContent = String(completedSteps); });
  $$('[data-total-steps]').forEach((node) => { node.textContent = String(totalSteps); });
  const ring = $("#overall-progress .overall-progress__ring");
  if (ring) {
    ring.style.setProperty("--progress", String(percent));
    ring.dataset.progress = String(percent);
    const text = $("span", ring);
    if (text) text.textContent = `${percent}%`;
  }
  const switcher = $("#path-switcher");
  if (switcher) {
    switcher.replaceChildren(...state.paths.map((path) => {
      const completed = (state.pathProgress[path.id] || []).length;
      const percent = path.steps.length ? Math.round((completed / path.steps.length) * 100) : 0;
      const button = createButton("", "select-path", {
        className: `path-catalog__card${path.id === state.selectedPathId ? " is-active" : ""}`,
        "data-path-id": path.id,
        "aria-pressed": String(path.id === state.selectedPathId),
        "aria-label": ui(`בחירת מסלול ${localField(path, "name")}`, `Select ${localField(path, "name")}`),
        role: "listitem",
      });
      button.append(
        createElement("span", { className: "eyebrow", text: label(path.skill_level) }),
        createElement("strong", { text: localField(path, "name") }),
        createElement("small", { text: ui(`${path.steps.length} שלבים · ${percent}% הושלמו`, `${path.steps.length} steps · ${percent}% complete`) }),
      );
      return button;
    }));
  }
}


function renderTrips() {
  const travel = state.travel || {};
  const typeGrid = $("#trip-type-grid");
  if (typeGrid) {
    const cards = (travel.trip_types || []).map((trip) => {
      const selected = state.selectedTripType === trip.id;
      const card = createElement("article", { className: `trip-type-card${selected ? " is-selected" : ""}` });
      card.append(
        createElement("p", { className: "eyebrow", text: selected ? ui("נבחר", "Selected") : ui("סוג טיול", "Trip type") }),
        createElement("h3", { text: localField(trip, "name") }),
        createElement("p", { text: localField(trip, "description") }),
      );
      const actions = createElement("div", { className: "trip-type-card__actions" });
      actions.append(createButton(selected ? ui("נבחר", "Selected") : ui("בחירת סוג הטיול", "Select trip type"), "select-trip-type", {
        className: selected ? "button button--secondary is-active" : "button button--secondary",
        "data-trip-type": trip.id,
        "aria-pressed": String(selected),
      }));
      if (trip.recommended_path_id) {
        actions.append(createButton(ui("למסלול המומלץ", "Open recommended path"), "open-trip-path", {
          className: "button button--text",
          "data-path-id": trip.recommended_path_id,
        }));
      }
      card.append(actions);
      return card;
    });
    typeGrid.replaceChildren(...cards);
  }

  $$('[data-mindfulness-note]').forEach((node) => {
    node.textContent = englishMode() ? (travel.mindfulness_note_en || "Pause briefly and check attention, fatigue, pace and your ability to stop before continuing.") : (travel.mindfulness_note_he || "עוצרים לרגע, בודקים קשב, עייפות, קצב ויכולת לעצור — ורק אז ממשיכים.");
  });

  const checklistGrid = $("#trip-checklist-grid");
  if (checklistGrid) {
    const groups = (travel.checklists || []).map((checklist) => {
      const card = createElement("section", { className: "checklist-card" });
      const items = createElement("ul", { className: "checklist-card__items" });
      (englishMode() ? checklist.items_en : checklist.items_he).forEach((item, index) => {
        const key = `${checklist.id}:${index}`;
        const checkbox = createElement("input", {
          attrs: {
            type: "checkbox",
            id: `trip-check-${checklist.id}-${index}`,
            "data-action": "toggle-trip-checklist",
            "data-checklist-key": key,
          },
        });
        checkbox.checked = state.tripChecklist.has(key);
        const labelNode = createElement("label", { attrs: { for: checkbox.id } });
        labelNode.append(checkbox, createElement("span", { text: item }));
        items.append(createElement("li", { className: checkbox.checked ? "is-complete" : "" }));
        items.lastElementChild.append(labelNode);
      });
      const completed = (englishMode() ? checklist.items_en : checklist.items_he).filter((_, index) => state.tripChecklist.has(`${checklist.id}:${index}`)).length;
      card.append(
        createElement("div", { className: "checklist-card__header" }),
        items,
      );
      card.firstElementChild.append(
        createElement("h3", { text: localField(checklist, "title") }),
        createElement("span", { text: `${completed}/${(englishMode() ? checklist.items_en : checklist.items_he).length}`, attrs: { dir: "ltr" } }),
      );
      return card;
    });
    checklistGrid.replaceChildren(...groups);
  }

  const appGrid = $("#navigation-app-grid");
  if (appGrid) {
    appGrid.replaceChildren(...(travel.navigation_apps || []).map((app) => {
      const card = createElement("article", { className: "navigation-app-card" });
      const capabilities = createElement("ul", { className: "feature-chip-list", attrs: { "aria-label": ui("יכולות מרכזיות", "Key capabilities") } });
      localArray(app, "capabilities").forEach((item) => capabilities.append(createElement("li", { text: item })));
      card.append(
        createElement("p", { className: "eyebrow", text: localField(app, "type") || ui("כלי ניווט", "Navigation tool") }),
        createElement("h3", { text: app.name, attrs: { dir: "auto" } }),
        createElement("p", { text: localField(app, "best_for") }),
      );
      if (capabilities.childElementCount) card.append(capabilities);
      const compare = createElement("div", { className: "navigation-app-card__compare" });
      [
        [ui("יתרונות", "Strengths"), localArray(app, "advantages")],
        [ui("מגבלות", "Limitations"), localArray(app, "limitations")],
      ].forEach(([title, items]) => {
        if (!items.length) return;
        const section = createElement("section");
        const list = createElement("ul");
        items.forEach((item) => list.append(createElement("li", { text: item })));
        section.append(createElement("h4", { text: title }), list);
        compare.append(section);
      });
      if (compare.childElementCount) card.append(compare);
      if (localField(app, "setup")) card.append(createElement("p", { className: "navigation-app-card__setup", text: `${ui("לפני הרכיבה", "Before the ride")}: ${localField(app, "setup")}` }));
      card.append(createElement("p", { className: "navigation-app-card__caution", text: `${ui("חשוב לדעת", "Keep in mind")}: ${localField(app, "caution")}` }));
      const videos = createElement("div", { className: "knowledge-video-links" });
      (app.video_ids || []).forEach((id) => {
        const link = videoLink(id, null, "guide");
        if (link) videos.append(link);
      });
      if (videos.childElementCount) {
        videos.prepend(createElement("h4", { text: ui("לימוד ויישום", "Learn and apply") }));
        card.append(videos);
      }
      return card;
    }));
  }

  const guideGrid = $("#knowledge-guide-grid");
  if (guideGrid) {
    guideGrid.replaceChildren(...(travel.knowledge_guides || []).map((guide) => {
      const card = createElement("article", { className: "knowledge-guide-card" });
      card.append(
        createElement("p", { className: "eyebrow", text: localField(guide, "eyebrow") }),
        createElement("h3", { text: localField(guide, "title") }),
        createElement("p", { className: "knowledge-guide-card__lead", text: localField(guide, "summary") }),
      );
      const columns = createElement("div", { className: "knowledge-guide-card__columns" });
      [
        [ui("מתאים כאשר", "Choose it when"), localArray(guide, "best_when")],
        [ui("פשרות ומגבלות", "Trade-offs and limits"), localArray(guide, "tradeoffs")],
        [ui("לפני שימוש", "Before use"), localArray(guide, "setup_checks")],
      ].forEach(([title, items]) => {
        if (!items.length) return;
        const section = createElement("section");
        const list = createElement("ul");
        items.forEach((item) => list.append(createElement("li", { text: item })));
        section.append(createElement("h4", { text: title }), list);
        columns.append(section);
      });
      card.append(columns);
      const videos = createElement("div", { className: "knowledge-video-links" });
      (guide.video_ids || []).forEach((id) => {
        const link = videoLink(id, null, "guide");
        if (link) videos.append(link);
      });
      if (videos.childElementCount) {
        videos.prepend(createElement("h4", { text: ui("סרטונים נבחרים", "Selected videos") }));
        card.append(videos);
      }
      return card;
    }));
  }

  const tripGrid = $("#trip-video-grid");
  if (tripGrid) {
    const results = applySearchAndFilters(state.videos, { domain: "touring_travel", sort: "recommended" }, {
      favorites: state.favorites,
      watched: state.watched,
      synonymIndex: state.synonymIndex,
    }).slice(0, 8);
    tripGrid.replaceChildren(...results.map((video) => createVideoCard(video, { compact: true })));
  }
}

function updateLocalAiUi(stage, detail = "", percent = null) {
  const button = $("#local-ai-toggle");
  const status = $("#local-ai-status");
  const progress = $("#local-ai-progress");
  const standalone = document.documentElement.dataset.standalone === "true";
  if (button) {
    button.disabled = standalone || stage === "loading";
    button.textContent = standalone
      ? ui("AI מקומי באתר המלא", "Local AI on full site")
      : state.semantic.enabled
      ? ui("השבתת AI מקומי", "Disable local AI")
      : ui("הפעלת AI מקומי", "Enable local AI");
  }
  if (status) {
    const title = $("strong", status);
    const copy = $("p", status);
    if (title) title.textContent = standalone
      ? ui("AI מקומי זמין באתר המלא", "Local AI is available on the full site")
      : stage === "ready"
      ? ui("AI מקומי פעיל", "Local AI is active")
      : stage === "loading"
        ? ui("טוען מודל מקומי…", "Loading the local model…")
        : stage === "error"
          ? ui("AI מקומי אינו זמין כרגע", "Local AI is currently unavailable")
          : ui("חיפוש חכם זמין תמיד", "Smart search is always available");
    if (copy) copy.textContent = standalone
      ? ui("קובץ HTML העצמאי ממשיך להשתמש בחיפוש החכם הרגיל ואינו מוריד את המודל.", "The standalone HTML continues to use regular smart search and does not download the model.")
      : detail || (stage === "ready"
      ? ui("השאלה מדורגת מול אינדקס הסרטונים במכשיר. אין שליחה לשרת AI.", "Your question is ranked against the video index on this device. Nothing is sent to an AI server.")
      : ui("בהפעלה הראשונה יורד מודל של כ־140MB. החיפוש הרגיל נשאר זמין גם בלי המודל.", "The first activation downloads a model of about 140MB. Regular search remains available without it."));
  }
  if (progress) {
    progress.hidden = stage !== "loading" || percent == null;
    if (percent != null) progress.value = percent;
  }
}

async function ensureSemanticReady() {
  if (state.semantic.ready) return true;
  if (state.semantic.loading) {
    while (state.semantic.loading) await new Promise((resolve) => window.setTimeout(resolve, 100));
    return state.semantic.ready;
  }
  if (document.documentElement.dataset.standalone === "true") {
    throw new Error(ui("AI מקומי זמין באתר המלא; קובץ HTML עצמאי ממשיך להשתמש בחיפוש החכם הרגיל.", "Local AI is available on the full site; the standalone HTML continues to use regular smart search."));
  }
  if (!("Worker" in window) || !("WebAssembly" in window)) {
    throw new Error(ui("הדפדפן אינו תומך בהרצת המודל המקומי.", "This browser cannot run the local model."));
  }
  state.semantic.loading = true;
  updateLocalAiUi("loading");
  try {
    const meta = await fetchJson(SEMANTIC_META_URL);
    if (!meta || meta.count !== state.videos.length || !Number.isInteger(meta.dimensions) || meta.ids?.length !== state.videos.length
      || meta.ids.some((id) => !state.videosById.has(id))) {
      throw new Error(ui("מטא־דאטה של האינדקס הסמנטי אינה תואמת לספריית הסרטונים.", "Semantic index metadata does not match the video library."));
    }
    const indexUrl = new URL(`data/${meta.binary}`, document.baseURI);
    indexUrl.searchParams.set("v", DATA_CACHE_REVISION);
    const response = await fetch(indexUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(ui(`בקשת האינדקס הסמנטי נכשלה (${response.status}).`, `Semantic index request failed (${response.status}).`));
    const buffer = await response.arrayBuffer();
    if (buffer.byteLength !== meta.count * meta.dimensions * Float32Array.BYTES_PER_ELEMENT) {
      throw new Error(ui("גודל האינדקס הסמנטי אינו תקין.", "Semantic index size is invalid."));
    }
    state.semantic.meta = meta;
    state.semantic.matrix = new Float32Array(buffer);
    const worker = new Worker(new URL(SEMANTIC_WORKER_URL, document.baseURI), { type: "module" });
    state.semantic.worker = worker;
    await new Promise((resolve, reject) => {
      const timeout = window.setTimeout(() => reject(new Error("Local model loading timed out.")), 240000);
      worker.addEventListener("message", (event) => {
        const message = event.data || {};
        if (message.type === "progress") updateLocalAiUi("loading", "", message.percent);
        if (message.type === "status" && message.stage === "ready") {
          window.clearTimeout(timeout);
          resolve();
        }
        if (message.type === "embedding") {
          const pending = state.semantic.pending.get(message.requestId);
          if (pending) {
            state.semantic.pending.delete(message.requestId);
            pending.resolve(message.vector);
          }
        }
        if (message.type === "error") {
          const pending = state.semantic.pending.get(message.requestId);
          if (pending) {
            state.semantic.pending.delete(message.requestId);
            pending.reject(new Error(message.message));
          } else {
            window.clearTimeout(timeout);
            reject(new Error(message.message));
          }
        }
      });
      worker.addEventListener("error", (event) => reject(new Error(event.message || "Local AI worker failed.")), { once: true });
      worker.postMessage({ type: "load" });
    });
    state.semantic.ready = true;
    updateLocalAiUi("ready");
    return true;
  } finally {
    state.semantic.loading = false;
  }
}

function requestSemanticEmbedding(query) {
  return new Promise((resolve, reject) => {
    if (!state.semantic.worker || !state.semantic.ready) {
      reject(new Error("Local AI is not ready."));
      return;
    }
    const requestId = ++state.semantic.requestSequence;
    const timeout = window.setTimeout(() => {
      state.semantic.pending.delete(requestId);
      reject(new Error("Local semantic query timed out."));
    }, 30000);
    state.semantic.pending.set(requestId, {
      resolve: (vector) => { window.clearTimeout(timeout); resolve(vector); },
      reject: (error) => { window.clearTimeout(timeout); reject(error); },
    });
    state.semantic.worker.postMessage({ type: "embed", requestId, query });
  });
}

async function toggleLocalAi() {
  if (state.semantic.enabled) {
    state.semantic.enabled = false;
    browserStorage.setSemanticEnabled(false);
    updateLocalAiUi("idle");
    renderSmartResults(state.smartQuery);
    return;
  }
  state.semantic.enabled = true;
  browserStorage.setSemanticEnabled(true);
  try {
    await ensureSemanticReady();
    updateLocalAiUi("ready");
    renderSmartResults(state.smartQuery);
  } catch (error) {
    state.semantic.enabled = false;
    browserStorage.setSemanticEnabled(false);
    updateLocalAiUi("error", error instanceof Error ? error.message : String(error));
    renderSmartResults(state.smartQuery);
  }
}

const SMART_STOP_WORDS = new Set([
  "אני", "רוצה", "איך", "אפשר", "צריך", "כדאי", "מה", "עם", "של", "על", "את", "זה", "לי", "יש", "שלי",
  "לפני", "אחרי", "עבור", "תנו", "תן", "תמצאו", "ללמוד", "לראות", "קודם", "קצת", "מאוד", "יותר", "פחות",
  "the", "a", "an", "to", "for", "with", "and", "or", "how", "what", "should", "i", "my", "me", "video", "videos",
].map(normalizeText));

function inferSmartIntent(query) {
  const normalized = normalizeText(query);
  const hasAny = (terms) => terms.some((term) => (` ${normalized} `).includes(` ${normalizeText(term)} `));
  let domain = "";
  let category = "";
  let topic = "";
  if (hasAny(["ניווט", "gpx", "osmand", "rever", "gaia", "dmd2", "garmin", "gps", "calimoto", "kurviger", "locus", "מפה אופליין", "טלפון או", "שיקוף", "navigation", "offline map", "smart display"])) {
    domain = "touring_travel";
    category = "route_navigation";
    topic = "navigation";
  } else if (hasAny(["דיבורית", "דיבוריות", "אינטרקום", "בלוטות", "bluetooth", "mesh", "intercom", "cardo", "sena", "lexin"])) {
    domain = "touring_travel";
    category = "intercoms_communications";
    topic = "communications";
  } else if (hasAny(["מיגון", "קסדה", "מגפיים", "מגן ברכ", "כרית אוויר", "helmet", "protective gear", "motorcycle gear", "airbag", "boots"])) {
    domain = "safety_recovery";
    category = "protective_gear";
    topic = "protection";
  } else if (hasAny(["טיול", "מסע", "זיווד", "מטען", "קבוצה", "מוביל", "מאסף", "touring", "trip", "packing", "luggage", "route"])) domain = "touring_travel";
  else if (hasAny(["שטח", "אדוונצר", "חול", "בוץ", "חריץ", "שביל", "עליה", "ירידה", "מכשול", "off road", "offroad", "dirt", "sand", "mud", "hill", "trail"])) domain = "offroad_adventure";
  else if (hasAny(["כביש", "פניה", "פניות", "גשם", "עירוני", "כביש מהיר", "corner", "road", "rain", "traffic", "highway"])) domain = "road";
  else if (hasAny(["חילוץ", "הרמת", "נפילה", "עייפות", "חירום", "recovery", "rescue", "lift", "fatigue", "emergency"])) domain = "safety_recovery";
  else if (hasAny(["תרגיל", "תרגול", "אימון", "שמיניות", "מגרש", "drill", "practice", "training lot"])) domain = "practice";

  let skill = "";
  if (hasAny(["מתחיל", "מתחילה", "beginner", "חדש ברכיבה"])) skill = "beginner";
  else if (hasAny(["מתקדם", "advanced"])) skill = "advanced";
  else if (hasAny(["בינוני", "intermediate"])) skill = "intermediate";

  let weight = "";
  if (hasAny(["כבד", "אופנוע גדול", "heavy", "big bike"])) weight = "heavy";
  else if (hasAny(["קל", "light bike"])) weight = "light";

  const tokens = normalized.split(" ")
    .filter((token) => token.length >= 2 && !SMART_STOP_WORDS.has(token))
    .slice(0, 18);
  return { normalized, tokens, domain, category, topic, skill, weight };
}

function smartRankVideos(query) {
  const intent = inferSmartIntent(query);
  if (!intent.normalized) return { intent, results: [], matches: [] };
  const candidates = intent.category
    ? state.allVideos.filter((video) => video.primary_category === intent.category || video.secondary_categories.includes(intent.category))
    : intent.domain ? state.allVideos.filter((video) => video.domain === intent.domain) : state.allVideos;
  const scored = candidates.map((video) => {
    let score = 0;
    intent.tokens.forEach((token) => { score += scoreSearchMatch(video, token, state.synonymIndex); });
    if (intent.domain && video.domain === intent.domain) score += 180;
    if (intent.category && video.primary_category === intent.category) score += 260;
    if (intent.skill && video.skill_level === intent.skill) score += 35;
    if (intent.weight && video.motorcycle_weight_classes.includes(intent.weight)) score += 30;
    if (intent.tokens.some((token) => normalizeText(video.title_he).includes(token) || normalizeText(video.title_original).includes(token))) score += 55;
    score += Number(video.quality_score || 0) * 5;
    return { video, score, reason: smartMatchReason(video, intent, false) };
  }).filter((entry) => entry.score > 20);
  scored.sort((a, b) => b.score - a.score || b.video.quality_score - a.video.quality_score || a.video._sourceIndex - b.video._sourceIndex);
  const matches = scored.slice(0, 12);
  return { intent, matches, results: matches.map((entry) => entry.video) };
}

function smartMatchReason(video, intent, semantic = false) {
  const reasons = [];
  if (semantic) reasons.push(ui("התאמה סמנטית מקומית", "Local semantic match"));
  if (intent.category && video.primary_category === intent.category) reasons.push(label(intent.category));
  else if (intent.domain && video.domain === intent.domain) reasons.push(label(intent.domain));
  if (intent.skill && video.skill_level === intent.skill) reasons.push(label(intent.skill));
  if (intent.weight && video.motorcycle_weight_classes.includes(intent.weight)) reasons.push(label(intent.weight));
  if (!reasons.length) reasons.push(ui("התאמה למונחים ולנושאים שבשאלה", "Matches terms and topics in the question"));
  return `${ui("למה התאים", "Why it matched")}: ${reasons.join(" · ")}`;
}

async function semanticRankVideos(query, intent) {
  const vector = await requestSemanticEmbedding(query);
  const meta = state.semantic.meta;
  const matrix = state.semantic.matrix;
  const scored = meta.ids.map((id, index) => {
    const video = state.videosById.get(id);
    if (!video) return null;
    let cosine = 0;
    const offset = index * meta.dimensions;
    for (let dimension = 0; dimension < meta.dimensions; dimension += 1) cosine += vector[dimension] * matrix[offset + dimension];
    let score = cosine * 1000;
    if (intent.domain && video.domain === intent.domain) score += 80;
    if (intent.category && video.primary_category === intent.category) score += 130;
    if (intent.skill && video.skill_level === intent.skill) score += 22;
    if (intent.weight && video.motorcycle_weight_classes.includes(intent.weight)) score += 18;
    if (video.contains_marketing) score -= 12;
    score += Number(video.quality_score || 0) * 3;
    return { video, score, reason: smartMatchReason(video, intent, true) };
  }).filter(Boolean);
  scored.sort((left, right) => right.score - left.score || right.video.quality_score - left.video.quality_score);
  return scored.slice(0, 12);
}

async function renderSmartResults(query = "") {
  const grid = $("#smart-video-grid");
  const note = $("#smart-result-note");
  if (!grid || !note) return;
  const clean = String(query || "").trim();
  if (!clean) {
    grid.replaceChildren();
    note.textContent = ui("כתבו שאלה כדי לקבל המלצות.", "Ask a question to get recommendations.");
    return;
  }
  const { intent, results, matches } = smartRankVideos(clean);
  state.smartQuery = clean;
  state.smartResults = results;
  state.smartMatches = matches;
  const intentParts = [intent.domain ? label(intent.domain) : ui("כל התחומים", "All areas")];
  if (intent.category) intentParts.push(label(intent.category));
  if (intent.skill) intentParts.push(label(intent.skill));
  if (intent.weight) intentParts.push(label(intent.weight));
  note.textContent = results.length
    ? ui(`${results.length} התאמות מובילות · ${intentParts.join(" · ")}. חיפוש מקומי, לא ייעוץ רכיבה.`, `${results.length} leading matches · ${intentParts.join(" · ")}. Local search, not riding advice.`)
    : ui("לא נמצאה התאמה חזקה. נסו לציין תחום, תנאי דרך, רמה או סוג אופנוע.", "No strong match was found. Try adding an area, road condition, level or motorcycle type.");
  grid.replaceChildren(...matches.map(({ video, reason }) => createVideoCard(video, { compact: true, matchReason: reason })));
  announce(ui(`${results.length} המלצות חכמות נמצאו`, `${results.length} smart recommendations found`));

  if (!state.semantic.enabled) return;
  try {
    await ensureSemanticReady();
    if (state.smartQuery !== clean) return;
    note.textContent = ui("AI מקומי מדרג כעת את הרשומות לפי משמעות…", "Local AI is ranking the records by meaning…");
    const semanticMatches = await semanticRankVideos(clean, intent);
    if (state.smartQuery !== clean || !state.semantic.enabled) return;
    const quickMatches = matches
      .filter(({ video }) => video.media_format === "short")
      .slice(0, 4)
      .map(({ video }) => ({ video, score: 0, reason: smartMatchReason(video, intent, false) }));
    const combinedMatches = [...quickMatches, ...semanticMatches]
      .filter((entry, index, collection) => collection.findIndex((candidate) => candidate.video.id === entry.video.id) === index)
      .slice(0, 12);
    state.smartMatches = combinedMatches;
    state.smartResults = combinedMatches.map((entry) => entry.video);
    note.textContent = ui(
      `${combinedMatches.length} התאמות מקומיות — סרטונים מלאים וקצרים · ${intentParts.join(" · ")}. כל התוצאות מגיעות מן המאגר המאומת.`,
      `${combinedMatches.length} local matches — full videos and Shorts · ${intentParts.join(" · ")}. Every result comes from the curated library.`,
    );
    grid.replaceChildren(...combinedMatches.map(({ video, reason }) => createVideoCard(video, { compact: true, matchReason: reason })));
  } catch (error) {
    updateLocalAiUi("error", ui("החיפוש הרגיל ממשיך לעבוד. טעינת המודל המקומי נכשלה.", "Regular search remains available. The local model could not be loaded."));
  }
}

function buildAiPrompt() {
  const question = $("#smart-query")?.value.trim() || state.smartQuery || "";
  return englishMode()
    ? `I am using a non-profit community guide for adventure motorcycle riding.\n\nMy question: ${question || "[Write the question here]"}\n\nHelp me build a safe, progressive learning plan. Separate: knowledge to study, practice in a controlled environment, topics that require a professional instructor, equipment, stopping conditions and risks. Do not invent motorcycle specifications. Suggest Hebrew and English search terms for finding relevant videos in the guide. Watching video does not replace a course or advanced practical training.`
    : `אני משתמש/ת במדריך קהילתי ללא כוונת רווח לרכיבת אופנועי אדוונצ'ר.\n\nהשאלה שלי: ${question || "[כתבו כאן את השאלה]"}\n\nעזור לי לנסח תוכנית למידה בטוחה ומדורגת. הפרד בין: ידע לצפייה, תרגול בסביבה מבוקרת, נושאים שמחייבים מדריך מקצועי, ציוד נדרש, תנאי עצירה וסיכונים. אל תמציא נתונים טכניים של אופנוע. המלץ על מילות חיפוש בעברית ובאנגלית כדי לאתר סרטונים במאגר. צפייה בווידאו אינה תחליף לקורס או לאימון מתקדם.`;
}

function detailSection(title, content) {
  if (content == null || (Array.isArray(content) && content.length === 0) || content === "") return null;
  const section = createElement("section", { className: "detail-section" });
  section.append(createElement("h3", { text: title }));
  if (Array.isArray(content)) {
    const list = createElement("ul");
    content.forEach((item) => list.append(createElement("li", { text: item })));
    section.append(list);
  } else {
    section.append(createElement("p", { text: content }));
  }
  return section;
}

function isPlaceholderChapter(chapter) {
  return /^<untitled chapter \d+>$/i.test(String(chapter?.title || "").trim());
}

function createDialogVideoContent(video) {
  const wrapper = createElement("div", { className: "video-detail", attrs: { "data-current-video": video.id } });
  const header = createElement("header", { className: "video-detail__header" });
  const badges = createElement("div", { className: "badge-row" });
  badges.append(
    createBadge(label(video.domain), "domain"),
    createBadge(label(video.skill_level), "level"),
    createBadge(`${ui("רמת סיכון", "Risk level")} ${label(video.risk_level)}`, video.risk_level === "high" ? "warning" : "neutral"),
  );
  header.append(
    badges,
    createElement("p", { className: "video-detail__original", text: englishMode() && video.language === "en" ? "" : video.title_original, attrs: { dir: "auto" } }),
    createVideoMeta(video, { includeDate: true, className: "video-detail__meta" }),
  );

  const player = createElement("div", { className: "video-player-slot", attrs: { id: "video-player-slot", "data-video-id": video.id } });
  const poster = createElement("img", {
    attrs: { src: video.thumbnail_url, alt: ui(`תמונת תצוגה של ${videoTitle(video)}`, `Thumbnail for ${videoTitle(video)}`), width: 960, height: 720 },
  });
  const loadPlayer = createButton(ui("טעינת נגן YouTube", "Load YouTube player"), "load-player", {
    className: "button button--primary video-player-slot__button",
    "data-video-id": video.id,
  });
  const posterFallback = createImageFallback(ui("תמונת התצוגה אינה זמינה. ניתן עדיין לטעון את הנגן או לפתוח את המקור ב־YouTube.", "The thumbnail is unavailable. You can still load the player or open the source on YouTube."));
  connectImageFallback(poster, posterFallback);
  player.append(poster, posterFallback, loadPlayer);

  const actions = createElement("div", { className: "video-detail__actions" });
  actions.append(
    createButton(state.favorites.has(video.id) ? ui("הסרה מהמועדפים", "Remove from favourites") : ui("הוספה למועדפים", "Add to favourites"), "toggle-favorite", {
      className: `button button--secondary${state.favorites.has(video.id) ? " is-active" : ""}`,
      "data-video-id": video.id,
      "aria-pressed": String(state.favorites.has(video.id)),
    }),
    createButton(state.watched.has(video.id) ? ui("סומן כנצפה", "Marked watched") : ui("סימון כנצפה", "Mark watched"), "toggle-watched", {
      className: `button button--secondary${state.watched.has(video.id) ? " is-active" : ""}`,
      "data-video-id": video.id,
      "aria-pressed": String(state.watched.has(video.id)),
    }),
    createButton(ui("שיתוף", "Share"), "share-video", { className: "button button--secondary", "data-video-id": video.id }),
    createElement("a", {
      className: "button button--text",
      text: ui("פתיחה ב־YouTube", "Open on YouTube"),
      attrs: { href: video.youtube_url, target: "_blank", rel: "noopener noreferrer" },
    }),
  );

  const summaryGrid = createElement("div", { className: "video-detail__summary-grid" });
  [
    detailSection(ui("תקציר", "Summary"), videoSummary(video)),
    detailSection(ui("מה בדיוק לומדים", "What you will learn"), videoArray(video, "learning_points")),
    detailSection(ui("למי מתאים", "Who it suits"), videoText(video, "fit_for")),
    detailSection(ui("למה כדאי לצפות", "Why watch it"), videoText(video, "why_watch")),
    detailSection(ui("תרגילים", "Drills"), videoArray(video, "exercises")),
    detailSection(ui("ציוד נדרש", "Required equipment"), videoArray(video, "equipment")),
    detailSection(ui("טעויות נפוצות", "Common mistakes"), videoArray(video, "common_mistakes")),
    detailSection(
      ui("מתי הסרטון לא מספיק", "When this video is not enough"),
      ui(
        "הסרטון הוא מקור לימוד בלבד. לתרגול עם סיכון, להתאמה לאופנוע או לציוד שלכם, ולכל ספק בטיחותי — עוצרים ופונים למדריך מוסמך, למדריך היצרן או לבעל מקצוע מתאים.",
        "This video is a learning resource only. For risk-bearing practice, motorcycle- or equipment-specific setup, or any safety doubt, stop and consult a qualified instructor, the manufacturer manual or an appropriate professional.",
      ),
    ),
  ].filter(Boolean).forEach((section) => summaryGrid.append(section));

  const warnings = detailSection(ui("אזהרות בטיחות", "Safety warnings"), videoArray(video, "safety_warnings"));
  if (warnings) warnings.classList.add("detail-section--warning");

  const filteredChapters = video.chapters.filter((chapter) => !isPlaceholderChapter(chapter));
  const chaptersSection = filteredChapters.length ? createElement("section", { className: "detail-section" }) : null;
  if (chaptersSection) {
    chaptersSection.append(createElement("h3", { text: ui("פרקים / נקודות זמן מתועדות", "Documented chapters / timestamps") }));
    const list = createElement("ol", { className: "chapters" });
    filteredChapters.forEach((chapter) => {
      const item = createElement("li");
      item.append(
        createElement("time", { text: formatDuration(chapter.start_seconds), attrs: { dir: "ltr", datetime: `PT${chapter.start_seconds}S` } }),
        createElement("bdi", { text: chapter.title, attrs: { dir: "auto" } }),
      );
      list.append(item);
    });
    chaptersSection.append(list);
  }

  const facts = createElement("dl", { className: "video-facts" });
  const qualityScore = createElement("span", { text: ui(`${video.quality_score} מתוך 5`, `${video.quality_score} of 5`), attrs: { dir: "ltr" } });
  const lastChecked = video.last_checked
    ? createElement("time", { text: formatDate(video.last_checked), attrs: { dir: "ltr", datetime: video.last_checked } })
    : createElement("span", { text: ui("תאריך לא זמין", "Date unavailable") });
  [
    [ui("קטגוריה", "Category"), label(video.primary_category)],
    [ui("מיקוד", "Focus"), (video.subtopics || []).map(label).join(", ")],
    [ui("סוג הדרכה", "Guidance format"), label(video.content_type)],
    [ui("שפה", "Language"), video.language === "he" ? ui("עברית", "Hebrew") : ui("אנגלית", "English")],
    [ui("כתוביות", "Subtitles"), video.subtitle_languages.length ? video.subtitle_languages.map(label).join(", ") : ui("לא תועדו", "Not documented")],
    [ui("סוגי אופנוע", "Motorcycle types"), video.motorcycle_types.map(label).join(", ")],
    [ui("משקל אופנוע", "Motorcycle weight"), video.motorcycle_weight_classes.map(label).join(", ")],
    [ui("קרקע", "Terrain"), video.terrain_types.length ? video.terrain_types.map(label).join(", ") : ui("לא רלוונטי", "Not applicable")],
    [ui("תנאי דרך", "Road conditions"), video.road_conditions.length ? video.road_conditions.map(label).join(", ") : ui("לא רלוונטי", "Not applicable")],
    [ui("סוג מקור", "Source type"), label(video.source_type)],
    [ui("תוכן שיווקי", "Marketing content"), video.contains_marketing ? ui("כן — מסומן בשקיפות", "Yes — marked transparently") : ui("לא תועד", "Not documented")],
    [ui("עומק אימות ותיעוד", "Verification and documentation depth"), qualityScore],
    [ui("נבדק לאחרונה", "Last checked"), lastChecked],
  ].forEach(([term, description]) => {
    const value = createElement("dd");
    if (description instanceof Node) value.append(description);
    else value.textContent = description;
    facts.append(createElement("dt", { text: term }), value);
  });

  const verification = createElement("section", { className: "detail-section detail-section--verification" });
  const verificationMeta = createElement("p", { className: "mixed-inline" });
  verificationMeta.append(
    document.createTextNode(ui("בסיס הסיווג: ", "Classification basis: ")),
    createElement("bdi", { text: video.verification.content_evidence_types.join(", "), attrs: { dir: "ltr" } }),
    createElement("span", { text: "·", attrs: { "aria-hidden": "true" } }),
    document.createTextNode(ui("ביטחון: ", "Confidence: ")),
    createElement("bdi", { text: video.verification.classification_confidence, attrs: { dir: "ltr" } }),
  );
  verification.append(
    createElement("h3", { text: ui("תיעוד אימות", "Verification record") }),
    createElement("p", { text: englishMode() ? video.verification.notes_en : video.verification.notes_he }),
    verificationMeta,
    createElement("p", { text: videoText(video, "quality_reason") }),
  );

  const related = createElement("section", { className: "related-videos" });
  related.append(createElement("h3", { text: ui("סרטונים קשורים", "Related videos") }));
  const relatedGrid = createElement("div", { className: "related-videos__grid" });
  video.related_video_ids.forEach((id) => {
    const relatedVideo = state.videosById.get(id);
    if (relatedVideo) relatedGrid.append(createVideoCard(relatedVideo, { compact: true }));
  });
  related.append(relatedGrid);

  const source = createElement("section", { className: "source-credit" });
  const channelLink = createElement("a", { attrs: { href: video.channel_url, target: "_blank", rel: "noopener noreferrer" } });
  channelLink.append(document.createTextNode(ui("לערוץ ", "Visit channel ")), createElement("bdi", { text: video.channel_name, attrs: { dir: "auto" } }));
  source.append(
    createElement("p", { text: ui("הסרטון, הסימנים המסחריים וכל זכויותיו שייכים ליוצר ולערוץ המקורי. המדריך הוא אוצר קישורים קהילתי בלבד; הוא אינו נותן חסות, בעלות, אחריות או אישור לתוכן.", "The video, trademarks and all associated rights belong to its creator and original channel. This guide is a community link curator only; it does not claim sponsorship, ownership, warranty or endorsement.") }),
    createElement("p", { className: "creator-like-note creator-like-note--detail", text: ui("הסרטון עזר לכם? פתחו אותו ב־YouTube ותנו לייק — זו דרך פשוטה להודות ליוצרים ולעודד המשך השקעה בתוכן איכותי.", "Did it help? Open it on YouTube and leave a like — a simple way to thank creators and encourage more useful work.") }),
    channelLink,
    createButton(ui("דיווח על קישור שבור או בקשת הסרה", "Report a broken link or request removal"), "copy-report", {
      className: "button button--text",
      "data-video-id": video.id,
    }),
  );

  wrapper.append(header, player, actions, summaryGrid);
  if (warnings) wrapper.append(warnings);
  wrapper.append(facts);
  if (chaptersSection) wrapper.append(chaptersSection);
  wrapper.append(verification, related, source);
  return wrapper;
}

function openVideo(videoId, { play = false, updateHistory = true } = {}) {
  const video = state.videosById.get(videoId);
  const dialog = $("#video-dialog");
  const content = $("#video-dialog-content");
  if (!video || !dialog || !content) return;
  const wasOpen = dialog.open;
  const opener = document.activeElement;
  if (!wasOpen) closeTransientOverlays({ restoreFocus: false });
  state.activeVideoId = videoId;
  browserStorage.setLastVideo(videoId);
  content.replaceChildren(createDialogVideoContent(video));
  content.scrollTop = 0;
  const dialogTitle = $("#video-dialog-shell-title");
  if (dialogTitle) dialogTitle.textContent = videoTitle(video);
  if (!wasOpen) dialog.showModal();
  overlayManager.open("video", {
    root: dialog,
    opener,
    firstFocus: () => $("[data-action='close-video']", dialog),
  });
  if (play) loadPlayer(videoId);
  if (updateHistory) updateUrl({ push: !wasOpen });
  renderContinue();
}

function clearVideoDialogContent() {
  const content = $("#video-dialog-content");
  content?.querySelectorAll("iframe").forEach((iframe) => {
    iframe.src = "about:blank";
    iframe.remove();
  });
  content?.replaceChildren();
}

function finalizeVideoClose({ updateHistory = true, restoreFocus = true } = {}) {
  const hadActiveVideo = Boolean(state.activeVideoId);
  clearVideoDialogContent();
  state.activeVideoId = null;
  overlayManager.close("video", { restoreFocus });
  if (updateHistory && hadActiveVideo) updateUrl({ includeVideo: false });
}

function closeVideo({ updateHistory = true, restoreFocus = true } = {}) {
  const dialog = $("#video-dialog");
  const hadActiveVideo = Boolean(state.activeVideoId);
  state.activeVideoId = null;
  clearVideoDialogContent();
  if (updateHistory && hadActiveVideo) updateUrl({ includeVideo: false });
  if (dialog?.open) dialog.close();
  overlayManager.close("video", { restoreFocus });
}

function loadPlayer(videoId) {
  const video = state.videosById.get(videoId);
  const slot = $("#video-player-slot");
  if (!video || !slot || slot.querySelector("iframe")) return;
  if (!navigator.onLine) {
    const message = createElement("div", {
      className: "video-player-slot__offline",
      text: englishMode()
        ? "You are offline. The guide remains available, but playing YouTube videos requires an internet connection."
        : "אין כרגע חיבור לאינטרנט. המדריך נשאר זמין, אך הפעלת סרטוני YouTube דורשת חיבור לרשת.",
    });
    slot.replaceChildren(message);
    announce(message.textContent);
    return;
  }
  const iframe = createElement("iframe", {
    attrs: {
      src: `https://www.youtube-nocookie.com/embed/${video.youtube_video_id}?rel=0`,
      title: ui(`נגן YouTube: ${videoTitle(video)}`, `YouTube player: ${videoTitle(video)}`),
      allow: "accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
      allowfullscreen: "",
      referrerpolicy: "strict-origin-when-cross-origin",
      loading: "lazy",
    },
  });
  slot.replaceChildren(iframe);
  announce(ui("נגן YouTube נטען לאחר בקשת המשתמש", "YouTube player loaded after the user's request"));
}

function restoreControlFocus(action, videoId, inDialog) {
  const scope = inDialog ? $("#video-dialog") : document;
  const selector = `[data-action="${action}"][data-video-id="${videoId}"]`;
  const replacement = $(selector, scope || document);
  replacement?.focus();
}

function toggleFavorite(videoId, origin) {
  const inDialog = Boolean(origin?.closest("#video-dialog"));
  const active = browserStorage.toggleFavorite(videoId);
  state.favorites = browserStorage.getFavorites();
  showToast(active ? ui("נוסף למועדפים", "Added to favourites") : ui("הוסר מהמועדפים", "Removed from favourites"));
  renderLibrary();
  if (state.activeVideoId === videoId) {
    const content = $("#video-dialog-content");
    content?.replaceChildren(createDialogVideoContent(state.videosById.get(videoId)));
  }
  renderContinue();
  restoreControlFocus("toggle-favorite", videoId, inDialog);
}

function toggleWatched(videoId, origin) {
  const inDialog = Boolean(origin?.closest("#video-dialog"));
  const active = browserStorage.toggleWatched(videoId);
  state.watched = browserStorage.getWatched();
  showToast(active ? ui("סומן כנצפה", "Marked as watched") : ui("סימון נצפה הוסר", "Watch mark removed"));
  renderLibrary();
  if (state.activeVideoId === videoId) {
    const content = $("#video-dialog-content");
    content?.replaceChildren(createDialogVideoContent(state.videosById.get(videoId)));
  }
  restoreControlFocus("toggle-watched", videoId, inDialog);
}

function togglePathStep(control) {
  const pathId = control.dataset.pathId;
  const stepOrder = Number(control.dataset.stepOrder);
  browserStorage.setPathStep(pathId, stepOrder, control.checked);
  state.pathProgress = browserStorage.getPathProgress();
  renderPaths();
  renderContinue();
  $(`[data-action="toggle-path-step"][data-path-id="${pathId}"][data-step-order="${stepOrder}"]`)?.focus();
  showToast(control.checked
    ? ui("השלב סומן כהושלם", "Step marked complete")
    : ui("סימון השלב הוסר", "Step completion removed"));
}

async function copyText(text, successMessage = ui("הקישור הועתק", "Link copied")) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const textarea = createElement("textarea", { attrs: { readonly: "" } });
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.append(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  showToast(successMessage);
}

async function shareVideo(videoId) {
  const video = state.videosById.get(videoId);
  if (!video) return;
  const url = new URL(window.location.href);
  url.searchParams.set("video", videoId);
  url.searchParams.set("view", "library");
  const shareData = { title: videoTitle(video), text: videoSummary(video), url: url.toString() };
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return;
    } catch (error) {
      if (error.name === "AbortError") return;
    }
  }
  await copyText(url.toString());
}

function openRights() {
  const dialog = $("#rights-dialog");
  if (!dialog || dialog.open) return;
  const opener = document.activeElement;
  closeTransientOverlays({ restoreFocus: false });
  dialog.showModal();
  overlayManager.open("rights", {
    root: dialog,
    opener,
    firstFocus: () => $(".modal__close", dialog),
  });
}

function closeRights({ restoreFocus = true } = {}) {
  const dialog = $("#rights-dialog");
  if (dialog?.open) dialog.close();
  overlayManager.close("rights", { restoreFocus });
}


function openFeedback() {
  const dialog = $("#feedback-dialog");
  if (!dialog || dialog.open) return;
  const opener = document.activeElement;
  closeTransientOverlays({ restoreFocus: false });
  if ($("#rights-dialog")?.open) closeRights({ restoreFocus: false });
  dialog.showModal();
  overlayManager.open("feedback", {
    root: dialog,
    opener,
    firstFocus: () => $("#feedback-message", dialog) || $(".modal__close", dialog),
  });
}

function closeFeedback({ restoreFocus = true } = {}) {
  const dialog = $("#feedback-dialog");
  if (dialog?.open) dialog.close();
  overlayManager.close("feedback", { restoreFocus });
}

function buildFeedbackText() {
  const missing = ui("לא צוין", "Not provided");
  const name = $("#feedback-name")?.value.trim() || missing;
  const email = $("#feedback-email")?.value.trim() || missing;
  const type = $("#feedback-type")?.value || ui("שיפור או רעיון", "Improvement or idea");
  const message = $("#feedback-message")?.value.trim() || "";
  const page = window.location.href;
  const active = state.activeVideoId ? state.videosById.get(state.activeVideoId) : null;
  return englishMode() ? [
    `Adventure Guide feedback — ${translateExact(type)}`,
    `Name: ${name}`,
    `Reply email: ${email}`,
    active ? `Active video: ${videoTitle(active)} (${active.id})` : "Active video: none",
    `Page: ${page}`,
    "",
    message,
  ].join("\n") : [
    `משוב למדריך האדוונצ'ר — ${type}`,
    `שם: ${name}`,
    `אימייל לחזרה: ${email}`,
    active ? `סרטון פעיל: ${active.title_he} (${active.id})` : "סרטון פעיל: אין",
    `עמוד: ${page}`,
    "",
    message,
  ].join("\n");
}

function sendFeedback() {
  const message = $("#feedback-message")?.value.trim() || "";
  if (!message) {
    $("#feedback-message")?.focus();
    showToast(ui("כתבו הודעה לפני פתיחת GitHub", "Write a message before opening GitHub"));
    return;
  }
  const type = $("#feedback-type")?.value || "שיפור או רעיון";
  const subject = englishMode() ? `Adventure Guide feedback: ${translateExact(type)}` : `משוב למדריך האדוונצ'ר: ${type}`;
  const target = new URL(state.config.feedback_url || FEEDBACK_URL);
  target.searchParams.set("title", subject);
  target.searchParams.set("body", buildFeedbackText());
  window.location.href = target.toString();
  showToast(ui("נפתח דיווח מוכן ב־GitHub", "A prepared GitHub report was opened"));
}

function saveBlob(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = createElement("a", { attrs: { href: url, download: filename } });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}

async function downloadStandaloneHtml() {
  const standalone = document.documentElement.dataset.standalone === "true";
  const filename = state.config.standalone_filename || "Adventure-Riding-Video-Guide-v3.0.0-Standalone.html";
  if (standalone) {
    const source = `<!DOCTYPE html>\n${document.documentElement.outerHTML}`;
    saveBlob(filename, source, "text/html;charset=utf-8");
    showToast(ui("קובץ ה־HTML נשמר", "The HTML file was saved"));
    return;
  }
  const target = document.body.dataset.downloadFile;
  if (!target) {
    showToast(ui("קובץ ההורדה אינו זמין בחבילה זו", "The download is unavailable in this package"));
    return;
  }
  const anchor = createElement("a", { attrs: { href: target, download: filename } });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  showToast(ui("הורדת קובץ ה־HTML החלה", "The HTML download started"));
}

function copyReport(videoId) {
  const video = state.videosById.get(videoId);
  if (!video) return;
  const text = englishMode()
    ? `Broken-link report / removal request\nID: ${video.id}\nTitle: ${video.title_original}\nSource: ${video.youtube_url}`
    : `דיווח על קישור שבור / בקשת הסרה\nמזהה: ${video.id}\nכותרת: ${video.title_original}\nמקור: ${video.youtube_url}`;
  copyText(text, ui("נוסח הדיווח הועתק", "Report text copied"));
}

function clearFilter(key) {
  state.filters[key] = "";
  if (key === "domain") {
    state.filters.category = "";
    state.filters.subcategory = "";
    state.filters.terrain = "";
    state.filters.road = "";
  } else if (key === "category") {
    state.filters.subcategory = "";
  }
  syncControlsFromFilters();
  state.visibleLimit = INITIAL_VISIBLE_LIMIT;
  renderLibrary();
}

function resetFilters() {
  state.filters = { sort: "recommended" };
  $("#filter-form")?.reset();
  syncControlsFromFilters();
  state.visibleLimit = INITIAL_VISIBLE_LIMIT;
  renderLibrary();
  $("#library-search")?.focus();
  showToast(ui("כל המסננים אופסו", "All filters were reset"));
}

function handleDomainSelection(domain) {
  state.filters.domain = domain;
  state.filters.category = "";
  state.filters.subcategory = "";
  state.filters.terrain = "";
  state.filters.road = "";
  syncControlsFromFilters();
  navigate("library", { focus: true });
}

function bindEvents() {
  let debounceTimer;
  $("#library-search")?.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      state.filters = { ...state.filters, ...getFiltersFromControls() };
      state.visibleLimit = INITIAL_VISIBLE_LIMIT;
      renderLibrary();
    }, 180);
  });
  $("#filter-form")?.addEventListener("change", (event) => {
    if (event.target.id === "filter-watched" && event.target.checked && $("#filter-unwatched")) $("#filter-unwatched").checked = false;
    if (event.target.id === "filter-unwatched" && event.target.checked && $("#filter-watched")) $("#filter-watched").checked = false;
    state.filters = { ...state.filters, ...getFiltersFromControls() };
    if (event.target.id === FILTER_IDS.domain) {
      state.filters.category = "";
      state.filters.subcategory = "";
      state.filters.terrain = "";
      state.filters.road = "";
      refreshContextualFilters();
    } else if (event.target.id === FILTER_IDS.category) {
      state.filters.subcategory = "";
      state.filters.terrain = "";
      state.filters.road = "";
      refreshContextualFilters();
    }
    syncControlsFromFilters();
    state.filters = { ...state.filters, ...getFiltersFromControls() };
    state.visibleLimit = INITIAL_VISIBLE_LIMIT;
    renderLibrary();
  });
  $("#sort-select")?.addEventListener("change", () => renderLibrary());

  document.addEventListener("click", (event) => {
    const viewControl = event.target.closest("a[data-view], button[data-view], a[data-route], button[data-route]");
    if (viewControl) {
      event.preventDefault();
      const href = viewControl.getAttribute("href") || "";
      const queryIndex = href.indexOf("?");
      if (queryIndex >= 0) {
        const params = new URLSearchParams(href.slice(queryIndex + 1));
        URL_FILTER_KEYS.forEach((key) => {
          if (params.has(key)) state.filters[key] = params.get(key) || "";
        });
        syncControlsFromFilters();
      }
      navigate(viewControl.dataset.view || viewControl.dataset.route, { focus: true });
      return;
    }
    const domainControl = event.target.closest("[data-domain]");
    if (domainControl) {
      handleDomainSelection(domainControl.dataset.domain);
      return;
    }
    const sample = event.target.closest("[data-smart-example]");
    if (sample) {
      const query = sample.dataset.smartExample || "";
      if ($("#smart-query")) $("#smart-query").value = query;
      renderSmartResults(query);
      return;
    }
    const control = event.target.closest("[data-action]");
    if (!control) return;
    const action = control.dataset.action;
    const videoId = control.dataset.videoId;
    if (action === "open-video") openVideo(videoId);
    else if (action === "play-video") openVideo(videoId, { play: true });
    else if (action === "load-player") loadPlayer(videoId);
    else if (action === "toggle-favorite") toggleFavorite(videoId, control);
    else if (action === "toggle-watched") toggleWatched(videoId, control);
    else if (action === "share-video") shareVideo(videoId);
    else if (action === "share-filters") copyText(window.location.href, ui("קישור החיפוש הועתק", "Search link copied"));
    else if (action === "copy-report") copyReport(videoId);
    else if (action === "remove-filter") clearFilter(control.dataset.filterKey);
    else if (action === "quick-domain") applyQuickFacet("domain", control.dataset.filterValue || "");
    else if (action === "quick-category") applyQuickFacet("category", control.dataset.filterValue || "");
    else if (action === "quick-focus") applyQuickFacet("focus", control.dataset.filterValue || "");
    else if (action === "reset-filters") resetFilters();
    else if (action === "clear-search") {
      if ($("#library-search")) $("#library-search").value = "";
      state.filters.q = "";
      renderLibrary();
      $("#library-search")?.focus();
    }
    else if (action === "reload-app") window.location.reload();
    else if (action === "apply-filters" || action === "close-filters") {
      setFiltersOpen(false, { restoreFocus: true });
      if (action === "apply-filters") renderLibrary();
    }
    else if (action === "open-rights") openRights();
    else if (action === "open-feedback") openFeedback();
    else if (action === "close-feedback") closeFeedback();
    else if (action === "copy-feedback") copyText(buildFeedbackText(), ui("נוסח המשוב הועתק", "Feedback text copied"));
    else if (action === "download-html") downloadStandaloneHtml();
    else if (action === "copy-ai-prompt") copyText(buildAiPrompt(), ui("נוסח מפורט לכלי AI הועתק", "Detailed AI prompt copied"));
    else if (action === "reset-trip-checklists") {
      state.tripChecklist = browserStorage.resetTripChecklist();
      renderTrips();
      showToast(ui("סימוני הצ׳קליסט אופסו", "Checklist marks were reset"));
    }
    else if (action === "select-trip-type") {
      state.selectedTripType = control.dataset.tripType || "day";
      browserStorage.setSelectedTripType(state.selectedTripType);
      renderTrips();
      showToast(ui("סוג הטיול נשמר במכשיר", "Trip type saved on this device"));
    }
    else if (action === "open-trip-path") {
      state.selectedPathId = control.dataset.pathId || state.selectedPathId;
      browserStorage.setSelectedPath(state.selectedPathId);
      navigate("paths", { focus: true });
      window.setTimeout(() => {
        selectLearningPath(state.selectedPathId, { focus: true, updateHistory: true });
      }, 50);
    }
    else if (action === "open-paths") navigate("paths", { focus: true });
    else if (action === "select-path" || action === "jump-path") selectLearningPath(control.dataset.pathId, { focus: true });
    else if (action === "toggle-local-ai") toggleLocalAi();
    else if (action === "back-to-top") window.scrollTo({ top: 0, behavior: "smooth" });
    else if (action === "close-video" || action === "close-video-dialog") closeVideo();
    else if (action === "close-rights") closeRights();
  });

  document.addEventListener("change", (event) => {
    if (event.target.matches('[data-action="toggle-path-step"]')) togglePathStep(event.target);
    if (event.target.matches('[data-action="toggle-trip-checklist"]')) {
      const key = event.target.dataset.checklistKey;
      browserStorage.toggleTripChecklist(key, event.target.checked);
      state.tripChecklist = browserStorage.getTripChecklist();
      renderTrips();
      $(`[data-checklist-key="${CSS.escape(key)}"]`)?.focus();
    }
  });

  $("#theme-toggle")?.addEventListener("click", toggleTheme);
  $("#language-toggle")?.addEventListener("click", () => saveLanguage(englishMode() ? "he" : "en"));
  $("#mobile-menu-toggle")?.addEventListener("click", () => setMenuOpen(!overlayManager.active("menu")));
  $("#mobile-filter-toggle")?.addEventListener("click", () => setFiltersOpen(!overlayManager.active("filters")));
  $("#hero-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = $("#hero-search")?.value.trim() || "";
    state.filters.q = query;
    syncControlsFromFilters();
    navigate("library", { focus: true });
  });
  $("#library-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    state.filters = { ...state.filters, ...getFiltersFromControls() };
    renderLibrary();
  });
  $("#smart-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    renderSmartResults($("#smart-query")?.value || "");
  });
  $("#feedback-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    sendFeedback();
  });
  $("#reset-filters")?.addEventListener("click", resetFilters);
  $("#load-more")?.addEventListener("click", () => {
    const total = applySearchAndFilters(currentCollectionVideos(), state.filters, {
      favorites: state.favorites,
      watched: state.watched,
      synonymIndex: state.synonymIndex,
    }).length;
    state.visibleLimit = nextVisibleLimit(state.visibleLimit, total, LOAD_MORE_BATCH_SIZE);
    renderLibrary();
  });

  $("#video-dialog")?.addEventListener("close", () => finalizeVideoClose());
  $("#video-dialog")?.addEventListener("cancel", (event) => { event.preventDefault(); closeVideo(); });
  $("#video-dialog")?.addEventListener("click", (event) => { if (event.target === event.currentTarget) closeVideo(); });
  $("#rights-dialog")?.addEventListener("close", () => overlayManager.close("rights"));
  $("#rights-dialog")?.addEventListener("cancel", (event) => { event.preventDefault(); closeRights(); });
  $("#rights-dialog")?.addEventListener("click", (event) => { if (event.target === event.currentTarget) closeRights(); });
  $("#feedback-dialog")?.addEventListener("close", () => overlayManager.close("feedback"));
  $("#feedback-dialog")?.addEventListener("cancel", (event) => { event.preventDefault(); closeFeedback(); });
  $("#feedback-dialog")?.addEventListener("click", (event) => { if (event.target === event.currentTarget) closeFeedback(); });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if ($("#video-dialog")?.open) { event.preventDefault(); closeVideo(); }
    else if ($("#feedback-dialog")?.open) { event.preventDefault(); closeFeedback(); }
    else if ($("#rights-dialog")?.open) { event.preventDefault(); closeRights(); }
    else if (overlayManager.active("filters")) { event.preventDefault(); setFiltersOpen(false, { restoreFocus: true }); }
    else if (overlayManager.active("menu")) { event.preventDefault(); setMenuOpen(false, { restoreFocus: true }); }
  });
  window.addEventListener("popstate", () => {
    hydrateFromUrl();
    navigate(state.currentView, { updateHistory: false });
    const params = new URLSearchParams(window.location.search);
    const videoId = params.get("video");
    if (videoId && state.videosById.has(videoId)) openVideo(videoId, { updateHistory: false });
    else if ($("#video-dialog")?.open) closeVideo({ updateHistory: false });
  });
  window.addEventListener("scroll", () => {
    const backToTop = $("#back-to-top");
    if (backToTop) backToTop.hidden = window.scrollY < 640;
  }, { passive: true });
}

function renderSafety() {
  applySiteConfig(state.config);
}

async function initialize() {
  applyLanguageShell();
  applyTheme();
  bindEvents();
  overlayManager.syncBody();
  try {
    const [videos, shorts, taxonomy, paths, synonyms, config, travel] = await Promise.all([
      fetchJson(DATA_FILES.videos),
      fetchJson(DATA_FILES.shorts),
      fetchJson(DATA_FILES.taxonomy),
      fetchJson(DATA_FILES.paths),
      fetchJson(DATA_FILES.synonyms),
      fetchJson(DATA_FILES.config),
      fetchJson(DATA_FILES.travel),
    ]);
    validateRuntimeVideos(videos);
    validateRuntimeVideos(shorts);
    state.config = normalizeSiteConfig(config);
    state.taxonomy = taxonomy;
    state.paths = paths;
    state.travel = travel || {};
    state.synonyms = synonyms || {};
    setLabels();
    const prepared = prepareVideos(videos, taxonomy, synonyms);
    const preparedShorts = prepareVideos(shorts, taxonomy, synonyms);
    state.videos = prepared.videos;
    state.shorts = preparedShorts.videos;
    state.allVideos = [...state.videos, ...state.shorts];
    state.synonymIndex = prepared.synonymIndex;
    state.videosById = new Map(state.allVideos.map((video) => [video.id, video]));
    state.favorites = browserStorage.getFavorites();
    state.watched = browserStorage.getWatched();
    state.pathProgress = browserStorage.getPathProgress();
    state.tripChecklist = browserStorage.getTripChecklist();
    state.selectedTripType = browserStorage.getSelectedTripType();
    state.selectedPathId = browserStorage.getSelectedPath();
    state.semantic.enabled = browserStorage.getSemanticEnabled();
    state.ready = true;

    hydrateFromUrl();
    populateFilters();
    syncControlsFromFilters();
    renderSafety();
    initializeVisitCounter();
    renderDomainCards();
    renderFeatured();
    renderContinue();
    renderLibrary();
    renderPaths();
    renderTrips();
    renderSmartResults(state.smartQuery);
    updateLocalAiUi(state.semantic.enabled ? "loading" : "idle");
    if (state.semantic.enabled) {
      ensureSemanticReady()
        .then(() => renderSmartResults(state.smartQuery))
        .catch((error) => {
          state.semantic.enabled = false;
          browserStorage.setSemanticEnabled(false);
          updateLocalAiUi("error", error instanceof Error ? error.message : String(error));
        });
    }
    navigate(state.currentView, { updateHistory: false });
    $("#loading-state")?.remove();
    if ($("#app")) $("#app").hidden = false;
    if ($("#app-status")) $("#app-status").hidden = true;
    document.documentElement.dataset.appReady = "true";
    window.__ADV_GUIDE__ = {
      getState: () => ({
        ready: state.ready,
        videoCount: state.videos.length,
        resultCount: applySearchAndFilters(state.videos, state.filters, {
          favorites: state.favorites, watched: state.watched, synonymIndex: state.synonymIndex,
        }).length,
        pathCount: state.paths.length,
        currentView: state.currentView,
        activeVideoId: state.activeVideoId,
        selectedPathId: state.selectedPathId,
        semanticEnabled: state.semantic.enabled,
        semanticReady: state.semantic.ready,
      }),
      getSmartResults: (query) => smartRankVideos(query).results.map((video) => video.id),
      openVideo,
      navigate,
      refreshContextualFilters,
    };
    window.dispatchEvent(new CustomEvent("adv-guide:ready", { detail: { videoCount: state.videos.length } }));
    if (englishMode()) translateDocument(document);
    announce(englishMode() ? `The guide loaded with ${state.allVideos.length} videos and Shorts` : `המדריך נטען עם ${state.allVideos.length} סרטונים וקצרים`);

    if (state.activeVideoId) openVideo(state.activeVideoId, { updateHistory: false });
  } catch (error) {
    showFatalError(error);
  }
}

initialize();
