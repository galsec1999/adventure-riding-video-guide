import { applySearchAndFilters, prepareVideos } from "./search.js";
import { browserStorage } from "./storage.js";
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

const DATA_FILES = Object.freeze({
  videos: "data/videos.json",
  taxonomy: "data/categories.json",
  paths: "data/learning-paths.json",
  synonyms: "data/synonyms.json",
  config: "data/site-config.json",
});

const FILTER_IDS = Object.freeze({
  domain: "filter-domain",
  category: "filter-category",
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
  "q", "domain", "category", "language", "skill", "risk", "motorcycle",
  "weight", "terrain", "road", "duration", "subtitles", "professional",
  "marketing", "favorite", "watched", "practical", "warnings", "beginner", "sort",
];

const state = {
  config: {},
  taxonomy: {},
  paths: [],
  videos: [],
  videosById: new Map(),
  labels: new Map(),
  synonymIndex: null,
  filters: { sort: "recommended" },
  favorites: new Set(),
  watched: new Set(),
  pathProgress: {},
  currentView: "home",
  visibleLimit: INITIAL_VISIBLE_LIMIT,
  activeVideoId: null,
  ready: false,
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
    return name === "video" || name === "rights" || mobileMedia.matches;
  }

  function syncBody() {
    const modalOpen = active.has("video") || active.has("rights");
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
    if (name === "video" || name === "rights") {
      close("menu", { restoreFocus: false });
      close("filters", { restoreFocus: false });
    }
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

function cleanConfigText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeSiteConfig(config) {
  if (!config || Array.isArray(config) || typeof config !== "object") {
    throw new Error("קובץ הגדרות האתר חייב להיות אובייקט JSON תקין.");
  }
  const language = cleanConfigText(config.default_language);
  const direction = cleanConfigText(config.direction);
  return {
    site_name_he: cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    author_name: cleanConfigText(config.author_name),
    community_name: cleanConfigText(config.community_name),
    contact: cleanConfigText(config.contact),
    logo_path: cleanConfigText(config.logo_path),
    safety_warning_he: cleanConfigText(config.safety_warning_he) || DEFAULT_SAFETY_WARNING,
    meta_title_he: cleanConfigText(config.meta_title_he) || cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    meta_description_he: cleanConfigText(config.meta_description_he || config.description_he),
    og_title_he: cleanConfigText(config.og_title_he || config.meta_title_he) || cleanConfigText(config.site_name_he) || DEFAULT_SITE_NAME,
    og_description_he: cleanConfigText(config.og_description_he || config.meta_description_he || config.description_he),
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
    image.alt = `לוגו ${config.site_name_he}`;
    fallback.hidden = true;
    image.hidden = false;
    image.src = logoUrl;
  });
}

function applySiteConfig(config) {
  document.documentElement.lang = config.default_language;
  document.documentElement.dir = config.direction;
  document.title = config.meta_title_he;
  const description = $('meta[name="description"]');
  const descriptionText = config.meta_description_he
    || `${config.site_name_he} — ספריית וידאו מקצועית בעברית ללימוד רכיבת אדוונצ'ר, שטח וכביש.`;
  if (description) description.setAttribute("content", descriptionText);
  const ogTitle = $('meta[property="og:title"]');
  const ogDescription = $('meta[property="og:description"]');
  const twitterTitle = $('meta[name="twitter:title"]');
  const twitterDescription = $('meta[name="twitter:description"]');
  if (ogTitle) ogTitle.setAttribute("content", config.og_title_he || config.meta_title_he);
  if (ogDescription) ogDescription.setAttribute("content", config.og_description_he || descriptionText);
  if (twitterTitle) twitterTitle.setAttribute("content", config.og_title_he || config.meta_title_he);
  if (twitterDescription) twitterDescription.setAttribute("content", config.og_description_he || descriptionText);
  $$('[data-site-name]').forEach((node) => { node.textContent = config.site_name_he; });
  $$('[data-site-home-link]').forEach((node) => {
    node.setAttribute("aria-label", `${config.site_name_he} — דף הבית`);
  });
  $$('[data-author-name]').forEach((node) => { node.textContent = config.author_name; });
  $$('[data-author-block]').forEach((node) => { node.hidden = !config.author_name; });
  $$('[data-community-name]').forEach((node) => {
    node.textContent = config.community_name;
    node.hidden = !config.community_name;
  });
  $$('[data-contact]').forEach((node) => {
    node.textContent = config.contact;
    node.dir = "auto";
  });
  $$('[data-contact-block]').forEach((node) => { node.hidden = !config.contact; });
  $$('[data-safety-warning]').forEach((node) => { node.textContent = config.safety_warning_he; });
  $$('[data-current-year]').forEach((node) => { node.textContent = String(new Date().getFullYear()); });
  applyLogoConfig(config);
}

function validateRuntimeVideos(videos) {
  if (!Array.isArray(videos)) throw new Error("נתוני הסרטונים חייבים להיות מערך JSON.");
  if (videos.length === 0) throw new Error("ספריית הסרטונים ריקה. נדרשת לפחות רשומה תקינה אחת.");
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
      throw new Error(`רשומת הסרטון ${index + 1} אינה אובייקט תקין.`);
    }
    requiredStrings.forEach((field) => {
      if (typeof video[field] !== "string" || !video[field].trim()) {
        throw new Error(`רשומת הסרטון ${index + 1} חסרה ערך טקסט תקין בשדה ${field}.`);
      }
    });
    requiredArrays.forEach((field) => {
      if (!Array.isArray(video[field])) throw new Error(`רשומת הסרטון ${video.id} חייבת לכלול מערך בשדה ${field}.`);
    });
    if (!video.verification || typeof video.verification !== "object"
      || typeof video.verification.notes_he !== "string"
      || typeof video.verification.classification_confidence !== "string"
      || !Array.isArray(video.verification.content_evidence_types)) {
      throw new Error(`רשומת הסרטון ${video.id} חסרה תיעוד אימות תקין.`);
    }
    if (!Number.isFinite(video.quality_score) || (video.duration_seconds != null && !Number.isFinite(video.duration_seconds))) {
      throw new Error(`רשומת הסרטון ${video.id} כוללת ערך מספרי לא תקין.`);
    }
    if (ids.has(video.id)) throw new Error(`מזהה הסרטון ${video.id} מופיע יותר מפעם אחת.`);
    if (youtubeIds.has(video.youtube_video_id)) throw new Error(`YouTube Video ID ${video.youtube_video_id} מופיע יותר מפעם אחת.`);
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
      : { text: "תאריך לא זמין", dir: "auto", attrs: { class: "mixed-meta__date" } });
  }
  return appendSeparatedParts(createElement("p", { className: `mixed-meta ${className}`.trim() }), parts);
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "משך לא זמין";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function formatDate(value) {
  if (!value) return "תאריך לא זמין";
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.valueOf())) return value;
  return `${String(date.getUTCDate()).padStart(2, "0")}.${String(date.getUTCMonth() + 1).padStart(2, "0")}.${date.getUTCFullYear()}`;
}

function label(id) {
  return state.labels.get(id)?.name_he || id || "לא צוין";
}

function setLabels() {
  state.labels.clear();
  Object.values(state.taxonomy).forEach((items) => {
    if (!Array.isArray(items)) return;
    items.forEach((item) => {
      if (item?.id) state.labels.set(item.id, item);
    });
  });
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`טעינת ${path} נכשלה (${response.status})`);
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
    createElement("h1", { text: "לא הצלחנו לטעון את המדריך", attrs: { id: "load-error-title" } }),
    createElement("p", { text: error.message || "אירעה שגיאה לא צפויה." }),
    createElement("p", { text: "יש לפתוח את האתר דרך השרת המקומי: run-local.bat או python tools/serve_local.py" }),
  );
  app.replaceChildren(panel);
  app.hidden = false;
  if ($("#app-status")) $("#app-status").hidden = true;
  announce("טעינת האתר נכשלה. מוצגות הוראות להפעלה מקומית.");
}

function applyTheme(theme) {
  const preferred = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const activeTheme = theme || browserStorage.getTheme() || preferred;
  document.documentElement.dataset.theme = activeTheme;
  document.documentElement.style.colorScheme = activeTheme;
  const toggle = $("#theme-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", String(activeTheme === "dark"));
    toggle.setAttribute("aria-label", activeTheme === "dark" ? "מעבר למצב בהיר" : "מעבר למצב כהה");
    const text = $("[data-theme-label], .theme-toggle__label", toggle);
    if (text) text.textContent = activeTheme === "dark" ? "מצב בהיר" : "מצב כהה";
  }
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  browserStorage.setTheme(next);
  applyTheme(next);
  showToast(next === "dark" ? "מצב כהה הופעל" : "מצב בהיר הופעל");
}

function populateSelect(id, items, emptyLabel) {
  const select = $(`#${id}`);
  if (!select) return;
  const current = select.value;
  const options = [createElement("option", { text: emptyLabel, attrs: { value: "" } })];
  items.forEach((item) => options.push(createElement("option", {
    text: item.name_he,
    attrs: { value: item.id },
  })));
  select.replaceChildren(...options);
  select.value = current;
}

function populateFilters() {
  populateSelect(FILTER_IDS.domain, state.taxonomy.domains || [], "כל התחומים");
  populateSelect(FILTER_IDS.category, state.taxonomy.categories || [], "כל הקטגוריות");
  populateSelect(FILTER_IDS.language, state.taxonomy.languages || [], "כל השפות");
  populateSelect(FILTER_IDS.skill, state.taxonomy.skill_levels || [], "כל הרמות");
  populateSelect(FILTER_IDS.risk, state.taxonomy.risk_levels || [], "כל רמות הסיכון");
  populateSelect(FILTER_IDS.motorcycle, state.taxonomy.motorcycle_types || [], "כל סוגי האופנוע");
  populateSelect(FILTER_IDS.weight, state.taxonomy.motorcycle_weight_classes || [], "כל המשקלים");
  populateSelect(FILTER_IDS.terrain, state.taxonomy.terrain_types || [], "כל סוגי הקרקע");
  populateSelect(FILTER_IDS.road, state.taxonomy.road_conditions || [], "כל תנאי הדרך");
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
  if ($("#library-search")) $("#library-search").value = state.filters.q || "";
  Object.entries(FILTER_IDS).forEach(([key, id]) => {
    const control = $(`#${id}`);
    if (control) control.value = state.filters[key] || "";
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
  state.currentView = ["home", "library", "paths", "safety"].includes(requestedView) ? requestedView : "home";
  const videoId = params.get("video");
  state.activeVideoId = videoId && state.videosById.has(videoId) ? videoId : null;
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
  url.hash = "";
  window.history[push ? "pushState" : "replaceState"]({}, "", url);
}

function reflectMenuState(open) {
  const button = $("#mobile-menu-toggle");
  if (button) {
    button.setAttribute("aria-expanded", String(open));
    button.setAttribute("aria-label", open ? "סגירת תפריט הניווט" : "פתיחת תפריט הניווט");
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
  if (!["home", "library", "paths", "safety"].includes(view)) view = "home";
  closeTransientOverlays({ restoreFocus: false });
  if ($("#video-dialog")?.open) closeVideo({ updateHistory: false, restoreFocus: false });
  if ($("#rights-dialog")?.open) closeRights({ restoreFocus: false });
  state.currentView = view;
  $$('[id$="-view"]').forEach((section) => {
    const active = section.id === `${view}-view`;
    section.hidden = !active;
    section.setAttribute("aria-hidden", String(!active));
  });
  $$('a[data-view], button[data-view], a[data-route], button[data-route]').forEach((item) => {
    const active = (item.dataset.view || item.dataset.route) === view;
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  if (view === "library") renderLibrary({ syncUrl: false });
  if (view === "paths") renderPaths();
  if (view === "home") renderContinue();
  if (updateHistory) updateUrl({ push: true });
  if (focus) {
    const heading = $(`#${view}-view h1, #${view}-view h2`);
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
  const accents = ["earth", "road", "mixed", "practice", "safety"];
  const cards = (state.taxonomy.domains || []).map((domain, index) => {
    const count = state.videos.filter((video) => video.domain === domain.id).length;
    const button = createElement("button", {
      className: `domain-card domain-card--${accents[index] || "earth"}`,
      attrs: { type: "button", "data-domain": domain.id, "aria-label": `${domain.name_he}, ${count} סרטונים` },
    });
    button.append(
      createElement("span", { className: "domain-card__eyebrow", text: `${count} סרטונים` }),
      createElement("strong", { className: "domain-card__title", text: domain.name_he }),
      createElement("span", { className: "domain-card__description", text: domain.description_he }),
      createElement("span", { className: "domain-card__link", text: "לספרייה ←" }),
    );
    return button;
  });
  container.replaceChildren(...cards);

  $$('[data-stat="videos"]').forEach((node) => { node.textContent = String(state.videos.length); });
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

function createVideoCard(video, { compact = false } = {}) {
  const article = createElement("article", {
    className: `video-card${compact ? " video-card--compact" : ""}`,
    attrs: { "data-video-id": video.id },
  });
  const media = createElement("div", { className: "video-card__media" });
  const image = createElement("img", {
    attrs: {
      src: video.thumbnail_url,
      alt: `תמונת תצוגה של ${video.title_he}`,
      loading: "lazy",
      decoding: "async",
      width: "480",
      height: "360",
    },
  });
  const play = createButton("צפייה", "play-video", {
    className: "video-card__play",
    "data-video-id": video.id,
    "aria-label": `צפייה בסרטון: ${video.title_he}`,
  });
  const imageFallback = createImageFallback("תמונת התצוגה אינה זמינה. אפשר לפתוח את הסרטון או לעבור ל־YouTube.");
  connectImageFallback(image, imageFallback);
  media.append(image, imageFallback, play);

  const body = createElement("div", { className: "video-card__body" });
  const badges = createElement("div", { className: "badge-row" });
  badges.append(
    createBadge(label(video.domain), "domain"),
    createBadge(label(video.skill_level), "level"),
    createBadge(video.language === "he" ? "עברית" : "אנגלית", "language"),
  );
  if (state.watched.has(video.id)) badges.append(createBadge("נצפה", "success"));

  const title = createElement("h3", { className: "video-card__title", text: video.title_he });
  const original = createElement("p", { className: "video-card__original", text: video.title_original, attrs: { dir: "auto" } });
  const meta = createVideoMeta(video, { includeCategory: true, className: "video-card__meta" });
  const summary = createElement("p", { className: "video-card__summary", text: video.summary_he });
  const learning = createElement("p", { className: "video-card__learning" });
  learning.append(
    createElement("strong", { text: "מה נלמד: " }),
    document.createTextNode(video.learning_points_he.slice(0, compact ? 1 : 2).join(" · ")),
  );
  const tags = createElement("div", { className: "tag-list", attrs: { "aria-label": "תגיות" } });
  video.tags.slice(0, compact ? 2 : 4).forEach((tag) => tags.append(createElement("span", { className: "tag", text: label(tag) })));

  const actions = createElement("div", { className: "video-card__actions" });
  const favorite = createButton(state.favorites.has(video.id) ? "במועדפים" : "מועדף", "toggle-favorite", {
    className: `icon-button${state.favorites.has(video.id) ? " is-active" : ""}`,
    "data-video-id": video.id,
    "aria-pressed": String(state.favorites.has(video.id)),
    "aria-label": `${state.favorites.has(video.id) ? "הסרה מהמועדפים" : "הוספה למועדפים"}: ${video.title_he}`,
  });
  const watched = createButton(state.watched.has(video.id) ? "נצפה" : "סימון נצפה", "toggle-watched", {
    className: `icon-button${state.watched.has(video.id) ? " is-active" : ""}`,
    "data-video-id": video.id,
    "aria-pressed": String(state.watched.has(video.id)),
  });
  const details = createButton("פרטים", "open-video", {
    className: "button button--secondary",
    "data-video-id": video.id,
  });
  const youtube = createElement("a", {
    className: "button button--text",
    text: "YouTube",
    attrs: { href: video.youtube_url, target: "_blank", rel: "noopener noreferrer", "aria-label": `פתיחה ב-YouTube: ${video.title_he}` },
  });
  actions.append(favorite, watched, details, youtube);
  body.append(badges, title, original, meta, summary, learning, tags, actions);
  article.append(media, body);
  return article;
}

function activeFilterEntries() {
  const names = {
    q: "חיפוש", domain: "תחום", category: "קטגוריה", language: "שפה", skill: "רמה",
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

function renderLibrary({ syncUrl = true } = {}) {
  if (!state.ready) return;
  state.filters = { ...state.filters, ...getFiltersFromControls() };
  const results = applySearchAndFilters(state.videos, state.filters, {
    favorites: state.favorites,
    watched: state.watched,
    synonymIndex: state.synonymIndex,
  });
  const count = $("#result-count");
  if (count) count.textContent = `${results.length} סרטונים נמצאו`;
  $$('[data-filter-result-count]').forEach((node) => { node.textContent = String(results.length); });
  renderActiveFilters();

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
    loadMore.textContent = `הצגת עוד (${results.length - limit})`;
    const wrap = $("#load-more-wrap");
    if (wrap) wrap.hidden = limit >= results.length;
  }
  const progress = $("#load-progress");
  if (progress) progress.textContent = `מוצגים ${limit} מתוך ${results.length} סרטונים`;
  announce(`${results.length} סרטונים נמצאו`);
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
      createElement("span", { className: "eyebrow", text: "הסרטון האחרון" }),
      createElement("h3", { text: lastVideo.title_he }),
      createElement("p", { text: lastVideo.channel_name, attrs: { dir: "auto" } }),
      createButton("המשך לפרטים", "open-video", { "data-video-id": lastVideo.id, className: "button button--primary" }),
    );
    blocks.push(block);
  }
  if (pathEntry) {
    const complete = state.pathProgress[pathEntry.id].length;
    const block = createElement("article", { className: "continue-card" });
    block.append(
      createElement("span", { className: "eyebrow", text: "מסלול בתהליך" }),
      createElement("h3", { text: pathEntry.name_he }),
      createElement("p", { text: `${complete} מתוך ${pathEntry.steps.length} שלבים הושלמו` }),
      createButton("המשך במסלול", "open-paths", { className: "button button--primary" }),
    );
    blocks.push(block);
  }
  section.hidden = blocks.length === 0;
  container.replaceChildren(...blocks);
}

function videoLink(videoId, text, kind = "primary") {
  const video = state.videosById.get(videoId);
  if (!video) return null;
  return createButton(text || video.title_he, "open-video", {
    className: `path-video path-video--${kind}`,
    "data-video-id": video.id,
    title: video.title_original,
  });
}

function renderPaths() {
  const container = $("#paths-container");
  if (!container) return;
  const pathCards = state.paths.map((path) => {
    const completed = new Set(state.pathProgress[path.id] || []);
    const card = createElement("article", { className: "learning-path", attrs: { id: `path-${path.id}` } });
    const header = createElement("header", { className: "learning-path__header" });
    const titleBlock = createElement("div");
    titleBlock.append(
      createElement("span", { className: "eyebrow", text: label(path.skill_level) }),
      createElement("h2", { text: path.name_he }),
      createElement("p", { text: path.description_he }),
    );
    const progress = createElement("div", { className: "path-progress" });
    progress.append(
      createElement("span", { text: `${completed.size} מתוך ${path.steps.length} שלבים` }),
      createElement("progress", { attrs: { value: completed.size, max: path.steps.length, "aria-label": `התקדמות במסלול ${path.name_he}` } }),
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
          "aria-label": `סימון השלב ${step.order} כהושלם`,
        },
      });
      checkbox.checked = completed.has(step.order);
      const labelNode = createElement("label", { attrs: { for: checkbox.id } });
      labelNode.append(
        createElement("span", { className: "path-step__number", text: step.order }),
        createElement("strong", { text: step.goal_he }),
      );
      top.append(checkbox, labelNode);
      const explanation = createElement("p", { text: step.explanation_he });
      const guardrails = createElement("dl", { className: "path-step__guardrails" });
      guardrails.append(
        createElement("dt", { text: "ציוד" }),
        createElement("dd", { text: step.equipment_he.join(" · ") }),
        createElement("dt", { text: "רמת סיכון" }),
        createElement("dd", { text: label(step.risk_level) }),
        createElement("dt", { text: "אזהרה" }),
        createElement("dd", { text: step.warning_he }),
      );
      const primary = createElement("div", { className: "path-step__videos" });
      primary.append(createElement("span", { className: "path-step__label", text: "סרטונים מרכזיים" }));
      step.primary_video_ids.forEach((id) => {
        const link = videoLink(id, null, "primary");
        if (link) primary.append(link);
      });
      const alternatives = createElement("div", { className: "path-step__videos path-step__videos--alternatives" });
      alternatives.append(createElement("span", { className: "path-step__label", text: "חלופות" }));
      step.alternative_video_ids.forEach((id) => {
        const link = videoLink(id, null, "alternative");
        if (link) alternatives.append(link);
      });
      item.append(top, explanation, guardrails, primary, alternatives);
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
    switcher.replaceChildren(...state.paths.map((path) => createButton(path.name_he, "jump-path", {
      className: "path-switcher__button",
      "data-path-id": path.id,
      "aria-label": `מעבר למסלול ${path.name_he}`,
    })));
  }
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
    createBadge(`סיכון ${label(video.risk_level)}`, video.risk_level === "high" ? "warning" : "neutral"),
  );
  header.append(
    badges,
    createElement("h2", { text: video.title_he, attrs: { id: "video-detail-title" } }),
    createElement("p", { className: "video-detail__original", text: video.title_original, attrs: { dir: "auto" } }),
    createVideoMeta(video, { includeDate: true, className: "video-detail__meta" }),
  );

  const player = createElement("div", { className: "video-player-slot", attrs: { id: "video-player-slot", "data-video-id": video.id } });
  const poster = createElement("img", {
    attrs: { src: video.thumbnail_url, alt: `תמונת תצוגה של ${video.title_he}`, width: 960, height: 720 },
  });
  const loadPlayer = createButton("טעינת נגן YouTube", "load-player", {
    className: "button button--primary video-player-slot__button",
    "data-video-id": video.id,
  });
  const posterFallback = createImageFallback("תמונת התצוגה אינה זמינה. ניתן עדיין לטעון את הנגן או לפתוח את המקור ב־YouTube.");
  connectImageFallback(poster, posterFallback);
  player.append(poster, posterFallback, loadPlayer);

  const actions = createElement("div", { className: "video-detail__actions" });
  actions.append(
    createButton(state.favorites.has(video.id) ? "הסרה מהמועדפים" : "הוספה למועדפים", "toggle-favorite", {
      className: `button button--secondary${state.favorites.has(video.id) ? " is-active" : ""}`,
      "data-video-id": video.id,
      "aria-pressed": String(state.favorites.has(video.id)),
    }),
    createButton(state.watched.has(video.id) ? "סומן כנצפה" : "סימון כנצפה", "toggle-watched", {
      className: `button button--secondary${state.watched.has(video.id) ? " is-active" : ""}`,
      "data-video-id": video.id,
      "aria-pressed": String(state.watched.has(video.id)),
    }),
    createButton("שיתוף", "share-video", { className: "button button--secondary", "data-video-id": video.id }),
    createElement("a", {
      className: "button button--text",
      text: "פתיחה ב־YouTube",
      attrs: { href: video.youtube_url, target: "_blank", rel: "noopener noreferrer" },
    }),
  );

  const summaryGrid = createElement("div", { className: "video-detail__summary-grid" });
  [
    detailSection("תקציר", video.summary_he),
    detailSection("מה בדיוק לומדים", video.learning_points_he),
    detailSection("למי מתאים", video.fit_for_he),
    detailSection("למה כדאי לצפות", video.why_watch_he),
    detailSection("תרגילים", video.exercises_he),
    detailSection("ציוד נדרש", video.equipment_he),
    detailSection("טעויות נפוצות", video.common_mistakes_he),
  ].filter(Boolean).forEach((section) => summaryGrid.append(section));

  const warnings = detailSection("אזהרות בטיחות", video.safety_warnings_he);
  if (warnings) warnings.classList.add("detail-section--warning");

  const filteredChapters = video.chapters.filter((chapter) => !isPlaceholderChapter(chapter));
  const chaptersSection = filteredChapters.length ? createElement("section", { className: "detail-section" }) : null;
  if (chaptersSection) {
    chaptersSection.append(createElement("h3", { text: "פרקים / נקודות זמן מתועדות" }));
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
  const qualityScore = createElement("span", { text: `${video.quality_score} מתוך 5`, attrs: { dir: "ltr" } });
  const lastChecked = video.last_checked
    ? createElement("time", { text: formatDate(video.last_checked), attrs: { dir: "ltr", datetime: video.last_checked } })
    : createElement("span", { text: "תאריך לא זמין" });
  [
    ["קטגוריה", label(video.primary_category)],
    ["שפה", video.language === "he" ? "עברית" : "אנגלית"],
    ["כתוביות", video.subtitle_languages.length ? video.subtitle_languages.map(label).join(", ") : "לא תועדו"],
    ["סוגי אופנוע", video.motorcycle_types.map(label).join(", ")],
    ["משקל אופנוע", video.motorcycle_weight_classes.map(label).join(", ")],
    ["קרקע", video.terrain_types.length ? video.terrain_types.map(label).join(", ") : "לא רלוונטי"],
    ["תנאי דרך", video.road_conditions.length ? video.road_conditions.map(label).join(", ") : "לא רלוונטי"],
    ["סוג מקור", label(video.source_type)],
    ["תוכן שיווקי", video.contains_marketing ? "כן — מסומן בשקיפות" : "לא"],
    ["דירוג פנימי", qualityScore],
    ["נבדק לאחרונה", lastChecked],
  ].forEach(([term, description]) => {
    const value = createElement("dd");
    if (description instanceof Node) value.append(description);
    else value.textContent = description;
    facts.append(createElement("dt", { text: term }), value);
  });

  const verification = createElement("section", { className: "detail-section detail-section--verification" });
  const verificationMeta = createElement("p", { className: "mixed-inline" });
  verificationMeta.append(
    document.createTextNode("בסיס הסיווג: "),
    createElement("bdi", { text: video.verification.content_evidence_types.join(", "), attrs: { dir: "ltr" } }),
    createElement("span", { text: "·", attrs: { "aria-hidden": "true" } }),
    document.createTextNode("ביטחון: "),
    createElement("bdi", { text: video.verification.classification_confidence, attrs: { dir: "ltr" } }),
  );
  verification.append(
    createElement("h3", { text: "תיעוד אימות" }),
    createElement("p", { text: video.verification.notes_he }),
    verificationMeta,
    createElement("p", { text: video.quality_reason_he }),
  );

  const related = createElement("section", { className: "related-videos" });
  related.append(createElement("h3", { text: "סרטונים קשורים" }));
  const relatedGrid = createElement("div", { className: "related-videos__grid" });
  video.related_video_ids.forEach((id) => {
    const relatedVideo = state.videosById.get(id);
    if (relatedVideo) relatedGrid.append(createVideoCard(relatedVideo, { compact: true }));
  });
  related.append(relatedGrid);

  const source = createElement("section", { className: "source-credit" });
  const channelLink = createElement("a", { attrs: { href: video.channel_url, target: "_blank", rel: "noopener noreferrer" } });
  channelLink.append(document.createTextNode("לערוץ "), createElement("bdi", { text: video.channel_name, attrs: { dir: "auto" } }));
  source.append(
    createElement("p", { text: "הסרטון שייך ליוצר ולערוץ המקורי. המדריך מרכז מידע וקישורים לצורכי למידה." }),
    channelLink,
    createButton("דיווח על קישור שבור או בקשת הסרה", "copy-report", {
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
  const dialogTitle = $("#video-dialog-shell-title");
  if (dialogTitle) dialogTitle.textContent = video.title_he;
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
  const iframe = createElement("iframe", {
    attrs: {
      src: `https://www.youtube-nocookie.com/embed/${video.youtube_video_id}?rel=0`,
      title: `נגן YouTube: ${video.title_he}`,
      allow: "accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
      allowfullscreen: "",
      referrerpolicy: "strict-origin-when-cross-origin",
      loading: "lazy",
    },
  });
  slot.replaceChildren(iframe);
  announce("נגן YouTube נטען לאחר בקשת המשתמש");
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
  showToast(active ? "נוסף למועדפים" : "הוסר מהמועדפים");
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
  showToast(active ? "סומן כנצפה" : "סימון נצפה הוסר");
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
  showToast(control.checked ? "השלב סומן כהושלם" : "סימון השלב הוסר");
}

async function copyText(text, successMessage = "הקישור הועתק") {
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
  const shareData = { title: video.title_he, text: video.summary_he, url: url.toString() };
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

function copyReport(videoId) {
  const video = state.videosById.get(videoId);
  if (!video) return;
  const text = `דיווח על קישור שבור / בקשת הסרה\nמזהה: ${video.id}\nכותרת: ${video.title_original}\nמקור: ${video.youtube_url}`;
  copyText(text, "נוסח הדיווח הועתק");
}

function clearFilter(key) {
  state.filters[key] = "";
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
  showToast("כל המסננים אופסו");
}

function handleDomainSelection(domain) {
  state.filters.domain = domain;
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
    state.visibleLimit = INITIAL_VISIBLE_LIMIT;
    renderLibrary();
  });
  $("#sort-select")?.addEventListener("change", () => renderLibrary());

  document.addEventListener("click", (event) => {
    const viewControl = event.target.closest("a[data-view], button[data-view], a[data-route], button[data-route]");
    if (viewControl) {
      event.preventDefault();
      navigate(viewControl.dataset.view || viewControl.dataset.route, { focus: true });
      return;
    }
    const domainControl = event.target.closest("[data-domain]");
    if (domainControl) {
      handleDomainSelection(domainControl.dataset.domain);
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
    else if (action === "share-filters") copyText(window.location.href, "קישור החיפוש הועתק");
    else if (action === "copy-report") copyReport(videoId);
    else if (action === "remove-filter") clearFilter(control.dataset.filterKey);
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
    else if (action === "open-paths") navigate("paths", { focus: true });
    else if (action === "jump-path") {
      const path = $(`#path-${control.dataset.pathId}`);
      path?.scrollIntoView({ behavior: "smooth", block: "start" });
      const heading = $("h2", path);
      if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    }
    else if (action === "back-to-top") window.scrollTo({ top: 0, behavior: "smooth" });
    else if (action === "close-video") closeVideo();
    else if (action === "close-video-dialog") closeVideo();
    else if (action === "close-rights") closeRights();
  });

  document.addEventListener("change", (event) => {
    if (event.target.matches('[data-action="toggle-path-step"]')) togglePathStep(event.target);
  });

  $("#theme-toggle")?.addEventListener("click", toggleTheme);
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
  $("#reset-filters")?.addEventListener("click", resetFilters);
  $("#load-more")?.addEventListener("click", () => {
    const total = applySearchAndFilters(state.videos, state.filters, {
      favorites: state.favorites,
      watched: state.watched,
      synonymIndex: state.synonymIndex,
    }).length;
    state.visibleLimit = nextVisibleLimit(state.visibleLimit, total, LOAD_MORE_BATCH_SIZE);
    renderLibrary();
  });

  $("#video-dialog")?.addEventListener("close", () => {
    finalizeVideoClose();
  });
  $("#video-dialog")?.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeVideo();
  });
  $("#video-dialog")?.addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeVideo();
  });
  $("#rights-dialog")?.addEventListener("close", () => overlayManager.close("rights"));
  $("#rights-dialog")?.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeRights();
  });
  $("#rights-dialog")?.addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeRights();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if ($("#video-dialog")?.open) {
      event.preventDefault();
      closeVideo();
    } else if ($("#rights-dialog")?.open) {
      event.preventDefault();
      closeRights();
    } else if (overlayManager.active("filters")) {
      event.preventDefault();
      setFiltersOpen(false, { restoreFocus: true });
    } else if (overlayManager.active("menu")) {
      event.preventDefault();
      setMenuOpen(false, { restoreFocus: true });
    }
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
  applyTheme();
  bindEvents();
  overlayManager.syncBody();
  try {
    const [videos, taxonomy, paths, synonyms, config] = await Promise.all([
      fetchJson(DATA_FILES.videos),
      fetchJson(DATA_FILES.taxonomy),
      fetchJson(DATA_FILES.paths),
      fetchJson(DATA_FILES.synonyms),
      fetchJson(DATA_FILES.config),
    ]);
    validateRuntimeVideos(videos);
    state.config = normalizeSiteConfig(config);
    state.taxonomy = taxonomy;
    state.paths = paths;
    setLabels();
    const prepared = prepareVideos(videos, taxonomy, synonyms);
    state.videos = prepared.videos;
    state.synonymIndex = prepared.synonymIndex;
    state.videosById = new Map(state.videos.map((video) => [video.id, video]));
    state.favorites = browserStorage.getFavorites();
    state.watched = browserStorage.getWatched();
    state.pathProgress = browserStorage.getPathProgress();
    state.ready = true;

    populateFilters();
    hydrateFromUrl();
    renderSafety();
    renderDomainCards();
    renderFeatured();
    renderContinue();
    renderLibrary();
    renderPaths();
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
        currentView: state.currentView,
        activeVideoId: state.activeVideoId,
      }),
      openVideo,
      navigate,
    };
    window.dispatchEvent(new CustomEvent("adv-guide:ready", { detail: { videoCount: state.videos.length } }));
    announce(`המדריך נטען עם ${state.videos.length} סרטונים`);

    if (state.activeVideoId) openVideo(state.activeVideoId, { updateHistory: false });
  } catch (error) {
    showFatalError(error);
  }
}

initialize();
