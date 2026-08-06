const HEBREW_FINAL_LETTERS = new Map([
  ["ך", "כ"],
  ["ם", "מ"],
  ["ן", "נ"],
  ["ף", "פ"],
  ["ץ", "צ"],
]);

const PROFESSIONAL_SOURCE_TYPES = new Set([
  "riding_school",
  "professional_instructor",
  "training_channel",
  "official_safety_program",
]);

const SKILL_ORDER = new Map([
  ["beginner", 0],
  ["advanced_beginner", 1],
  ["intermediate", 2],
  ["advanced", 3],
]);

function asArray(value) {
  return Array.isArray(value) ? value : value == null ? [] : [value];
}

function flattenText(value, target = []) {
  if (typeof value === "string" || typeof value === "number") {
    target.push(String(value));
  } else if (Array.isArray(value)) {
    value.forEach((item) => flattenText(item, target));
  } else if (value && typeof value === "object") {
    Object.values(value).forEach((item) => flattenText(item, target));
  }
  return target;
}

/**
 * Normalizes Hebrew and English search text without changing the source data.
 * Hebrew final letters are folded to their common forms and punctuation is
 * treated as whitespace so URLs and titles remain searchable by words.
 */
export function normalizeText(value = "") {
  return String(value)
    .normalize("NFKD")
    .toLocaleLowerCase("he")
    .replace(/[\u0591-\u05c7]/g, "")
    .replace(/[ךםןףץ]/g, (letter) => HEBREW_FINAL_LETTERS.get(letter) || letter)
    .replace(/[’'״“”„`´]/g, "")
    .replace(/[\u2010-\u2015־_/\\|+&:;,.!?()[\]{}<>@#$%^*=~]+/g, " ")
    .replace(/[^\p{L}\p{N}\s-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function searchTokenForms(token) {
  const forms = new Set([token]);
  if (/^[בלמהוכש]/u.test(token) && token.length >= 4) {
    forms.add(token.slice(1));
  }
  if (/^וה/u.test(token) && token.length >= 6) {
    forms.add(token.slice(2));
  }
  return [...forms].filter((item) => item.length >= 2);
}

function boundedLevenshteinOne(left, right) {
  if (left === right) return true;
  if (Math.abs(left.length - right.length) > 1) return false;
  if (Math.min(left.length, right.length) < 5) return false;

  let leftIndex = 0;
  let rightIndex = 0;
  let edits = 0;
  while (leftIndex < left.length && rightIndex < right.length) {
    if (left[leftIndex] === right[rightIndex]) {
      leftIndex += 1;
      rightIndex += 1;
      continue;
    }
    edits += 1;
    if (edits > 1) return false;
    if (left.length > right.length) leftIndex += 1;
    else if (right.length > left.length) rightIndex += 1;
    else {
      leftIndex += 1;
      rightIndex += 1;
    }
  }
  if (leftIndex < left.length || rightIndex < right.length) edits += 1;
  return edits <= 1;
}

function containsPhrase(text, phrase) {
  return (` ${text} `).includes(` ${phrase} `);
}

export function createTaxonomyLookup(taxonomy = {}) {
  const lookup = new Map();
  Object.values(taxonomy).forEach((collection) => {
    if (!Array.isArray(collection)) return;
    collection.forEach((item) => {
      if (!item?.id) return;
      lookup.set(item.id, [item.id, item.name_he, item.name_en, item.description_he, item.description_en].filter(Boolean));
    });
  });
  return lookup;
}

export function uniqueDisplayTaxonomyIds(ids = [], labels = new Map(), language = "he") {
  const seen = new Set();
  return asArray(ids).filter((id) => {
    const entry = labels instanceof Map ? labels.get(id) : labels?.[id];
    const value = entry && typeof entry === "object"
      ? (language === "en" ? entry.name_en : entry.name_he) || entry.name_he || entry.name_en || id
      : entry || id;
    const normalized = normalizeText(value);
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

export function createSynonymIndex(synonyms = {}) {
  const aliasGroups = new Map();
  const concepts = new Map();
  asArray(synonyms.terms).forEach((term) => {
    const aliases = [term.concept_id, term.preferred_he, term.preferred_en, ...asArray(term.variants)]
      .map(normalizeText)
      .filter(Boolean);
    const group = new Set(aliases);
    concepts.set(term.concept_id, group);
    aliases.forEach((alias) => aliasGroups.set(alias, group));
  });
  return { aliasGroups, concepts };
}

export function expandQuery(query, synonymIndex) {
  const normalized = normalizeText(query);
  if (!normalized) return [];
  const expansions = new Set([normalized]);
  const queryTokens = normalized.split(" ").flatMap(searchTokenForms);
  queryTokens.forEach((token) => expansions.add(token));

  const groups = synonymIndex?.aliasGroups || new Map();
  groups.forEach((group, alias) => {
    const overlaps = containsPhrase(normalized, alias)
      || containsPhrase(alias, normalized)
      || normalized.split(" ").includes(alias)
      || alias.split(" ").includes(normalized);
    if (overlaps) group.forEach((variant) => expansions.add(variant));
  });
  return [...expansions].filter(Boolean);
}

export function buildSearchText(video, taxonomyLookup = new Map()) {
  const taxonomyValues = [
    video.domain,
    video.primary_category,
    ...asArray(video.secondary_categories),
    ...asArray(video.subtopics),
    video.content_type,
    ...asArray(video.tags),
    video.skill_level,
    video.risk_level,
    ...asArray(video.motorcycle_types),
    ...asArray(video.motorcycle_weight_classes),
    ...asArray(video.terrain_types),
    ...asArray(video.road_conditions),
    video.source_type,
    video.language,
  ].flatMap((id) => taxonomyLookup.get(id) || [id]);

  const searchable = [
    video.id,
    video.youtube_video_id,
    video.title_he,
    video.title_en,
    video.title_original,
    video.channel_name,
    video.summary_he,
    video.summary_en,
    video.learning_points_he,
    video.learning_points_en,
    video.fit_for_he,
    video.fit_for_en,
    video.why_watch_he,
    video.why_watch_en,
    video.exercises_he,
    video.exercises_en,
    video.equipment_he,
    video.equipment_en,
    video.safety_warnings_he,
    video.safety_warnings_en,
    video.common_mistakes_he,
    video.common_mistakes_en,
    video.quality_reason_he,
    video.quality_reason_en,
    video.chapters?.map((chapter) => chapter.title),
    taxonomyValues,
  ];
  return normalizeText(flattenText(searchable).join(" "));
}

function buildSearchFacetText(video, taxonomyLookup = new Map()) {
  const taxonomyValues = [
    video.domain,
    video.primary_category,
    ...asArray(video.secondary_categories),
    ...asArray(video.subtopics),
    video.content_type,
    ...asArray(video.tags),
    video.skill_level,
    video.risk_level,
    ...asArray(video.motorcycle_types),
    ...asArray(video.motorcycle_weight_classes),
    ...asArray(video.terrain_types),
    ...asArray(video.road_conditions),
  ].flatMap((id) => taxonomyLookup.get(id) || [id]);

  return normalizeText(flattenText([
    video.title_he,
    video.title_en,
    video.title_original,
    taxonomyValues,
  ]).join(" "));
}

export function prepareVideos(videos, taxonomy, synonyms) {
  const taxonomyLookup = createTaxonomyLookup(taxonomy);
  const synonymIndex = createSynonymIndex(synonyms);
  return {
    synonymIndex,
    videos: videos.map((video, sourceIndex) => {
      const searchText = buildSearchText(video, taxonomyLookup);
      const searchFacetText = buildSearchFacetText(video, taxonomyLookup);
      const titleText = normalizeText([video.title_he, video.title_en, video.title_original].filter(Boolean).join(" "));
      const primaryText = normalizeText([video.primary_category, ...(taxonomyLookup.get(video.primary_category) || [])].join(" "));
      const subtopicText = normalizeText(asArray(video.subtopics).flatMap((id) => taxonomyLookup.get(id) || [id]).join(" "));
      const tagText = normalizeText(asArray(video.tags).flatMap((id) => taxonomyLookup.get(id) || [id]).join(" "));
      const technicalText = normalizeText([
        video.title_he,
        video.title_en,
        video.title_original,
        video.primary_category,
        ...asArray(video.secondary_categories),
        ...asArray(video.subtopics),
        ...asArray(video.tags),
      ].filter(Boolean).join(" "));
      return {
        ...video,
        _sourceIndex: sourceIndex,
        _searchText: searchText,
        _searchWords: new Set(searchText.split(" ").filter(Boolean)),
        _searchFacetText: searchFacetText,
        _titleText: titleText,
        _primaryText: primaryText,
        _subtopicText: subtopicText,
        _tagText: tagText,
        _technicalText: technicalText,
      };
    }),
  };
}

export function scoreSearchMatch(video, query, synonymIndex) {
  const normalized = normalizeText(query);
  if (!normalized) return 0;
  const text = video._searchText || normalizeText(flattenText(video).join(" "));
  const words = video._searchWords || new Set(text.split(" ").filter(Boolean));
  const facetText = video._searchFacetText || text;
  const expansions = expandQuery(normalized, synonymIndex);
  const titleText = video._titleText || normalizeText([video.title_he, video.title_en, video.title_original].filter(Boolean).join(" "));
  const primaryText = video._primaryText || normalizeText(video.primary_category || "");
  const subtopicText = video._subtopicText || normalizeText(asArray(video.subtopics).join(" "));
  const tagText = video._tagText || normalizeText(asArray(video.tags).join(" "));
  let score = 0;

  if (containsPhrase(text, normalized)) score += 120;
  if (containsPhrase(facetText, normalized)) score += 80;
  if (containsPhrase(titleText, normalized)) score += 260;
  if (containsPhrase(primaryText, normalized)) score += 210;
  if (containsPhrase(subtopicText, normalized)) score += 75;
  if (containsPhrase(tagText, normalized)) score += 40;
  expansions.forEach((phrase) => {
    if (phrase !== normalized && phrase.length >= 3 && containsPhrase(text, phrase)) score += 30;
    if (phrase.length >= 3 && containsPhrase(facetText, phrase)) score += 24;
    if (phrase.length >= 3 && containsPhrase(titleText, phrase)) score += 105;
    if (phrase.length >= 3 && containsPhrase(primaryText, phrase)) score += 90;
    if (phrase.length >= 3 && containsPhrase(subtopicText, phrase)) score += 34;
    if (phrase.length >= 3 && containsPhrase(tagText, phrase)) score += 18;
  });

  const queryTokens = normalized.split(" ").flatMap(searchTokenForms);
  let matchedTokens = 0;
  queryTokens.forEach((token) => {
    if (words.has(token)) {
      matchedTokens += 1;
      score += 16;
      if (titleText.split(" ").includes(token)) score += 32;
      if (primaryText.split(" ").includes(token)) score += 46;
      if (subtopicText.split(" ").includes(token)) score += 12;
      if (tagText.split(" ").includes(token)) score += 6;
      return;
    }
    const fuzzy = [...words].some((word) => boundedLevenshteinOne(token, word));
    if (fuzzy) {
      matchedTokens += 1;
      score += 5;
    }
    if (titleText.split(" ").some((word) => boundedLevenshteinOne(token, word))) score += 32;
    if (primaryText.split(" ").some((word) => boundedLevenshteinOne(token, word))) score += 46;
    if (subtopicText.split(" ").some((word) => boundedLevenshteinOne(token, word))) score += 12;
    if (tagText.split(" ").some((word) => boundedLevenshteinOne(token, word))) score += 6;
  });

  const directPhraseMatch = containsPhrase(text, normalized);
  const synonymVariantMatch = expansions
    .filter((phrase) => phrase !== normalized && !queryTokens.includes(phrase) && phrase.length >= 3)
    .some((phrase) => containsPhrase(text, phrase));
  // Preserve explicit technical acronyms and English terms in mixed-language
  // queries. For example, "ABS בשטח" must not rank a generic off-road braking
  // video merely because "שטח" matched a synonym group.
  const explicitLatinTokens = String(query).split(/\s+/)
    .map((token) => normalizeText(token))
    .filter((token, index) => /^[a-z0-9-]{2,}$/i.test(token)
      && /[A-Z]/.test(String(query).split(/\s+/)[index] || ""));
  const technicalWords = new Set((video._technicalText || titleText).split(" ").filter(Boolean));
  if (explicitLatinTokens.some((token) => !technicalWords.has(token)
    && ![...technicalWords].some((word) => boundedLevenshteinOne(token, word)))) return 0;
  const requiredTokenMatches = queryTokens.length <= 1 ? 1 : queryTokens.length;
  if (!directPhraseMatch && !synonymVariantMatch && matchedTokens < requiredTokenMatches) return 0;
  if (matchedTokens === queryTokens.length && queryTokens.length > 1) score += 24;
  return score;
}

function matchesDuration(video, duration) {
  if (!duration) return true;
  if (video.duration_seconds == null) return duration === "unknown";
  if (duration === "short") return video.duration_seconds <= 300;
  if (duration === "medium") return video.duration_seconds > 300 && video.duration_seconds <= 900;
  if (duration === "long") return video.duration_seconds > 900;
  return true;
}

function matchesArrayFilter(video, field, expected) {
  return !expected || asArray(video[field]).includes(expected);
}

export function filterVideos(videos, filters = {}, context = {}) {
  const favorites = context.favorites || new Set();
  const watched = context.watched || new Set();
  const synonymIndex = context.synonymIndex;

  return videos
    .map((video) => ({ ...video, _searchScore: scoreSearchMatch(video, filters.q, synonymIndex) }))
    .filter((video) => {
      if (filters.q && video._searchScore <= 0) return false;
      if (filters.domain && video.domain !== filters.domain) return false;
      if (filters.category && video.primary_category !== filters.category) return false;
      if (filters.subcategory && !asArray(video.subtopics).includes(filters.subcategory)) return false;
      if (filters.format && video.content_type !== filters.format) return false;
      if (filters.language && video.language !== filters.language) return false;
      if (filters.skill && video.skill_level !== filters.skill) return false;
      if (filters.risk && video.risk_level !== filters.risk) return false;
      if (!matchesArrayFilter(video, "motorcycle_types", filters.motorcycle)) return false;
      if (!matchesArrayFilter(video, "motorcycle_weight_classes", filters.weight)) return false;
      if (!matchesArrayFilter(video, "terrain_types", filters.terrain)) return false;
      if (!matchesArrayFilter(video, "road_conditions", filters.road)) return false;
      if (!matchesDuration(video, filters.duration)) return false;
      if (filters.subtitles === "yes" && asArray(video.subtitle_languages).length === 0) return false;
      if (filters.subtitles === "no" && asArray(video.subtitle_languages).length > 0) return false;
      if (filters.professional === "yes" && !PROFESSIONAL_SOURCE_TYPES.has(video.source_type)) return false;
      if (filters.professional === "no" && PROFESSIONAL_SOURCE_TYPES.has(video.source_type)) return false;
      if (filters.marketing === "yes" && !video.contains_marketing) return false;
      if (filters.marketing === "no" && video.contains_marketing) return false;
      if (filters.beginner === "yes" && !["beginner", "advanced_beginner"].includes(video.skill_level)) return false;
      if (filters.practical === "yes" && asArray(video.exercises_he).length === 0) return false;
      if (filters.warnings === "yes" && asArray(video.safety_warnings_he).length === 0) return false;
      if ((filters.favorite === "yes" || filters.userState === "favorite") && !favorites.has(video.id)) return false;
      if ((filters.watched === "yes" || filters.userState === "watched") && !watched.has(video.id)) return false;
      if ((filters.watched === "no" || filters.userState === "unwatched") && watched.has(video.id)) return false;
      return true;
    });
}

export function sortVideos(videos, sort = "recommended") {
  const prepared = [...videos];
  const byTitle = (a, b) => String(a.title_he).localeCompare(String(b.title_he), "he");
  const tieBreak = (a, b) => (b.quality_score - a.quality_score) || byTitle(a, b);

  prepared.sort((a, b) => {
    if (sort === "beginner") {
      return (SKILL_ORDER.get(a.skill_level) - SKILL_ORDER.get(b.skill_level)) || tieBreak(a, b);
    }
    if (sort === "skill") {
      return (SKILL_ORDER.get(a.skill_level) - SKILL_ORDER.get(b.skill_level)) || byTitle(a, b);
    }
    if (sort === "duration" || sort === "duration-asc" || sort === "duration-desc") {
      const delta = (a.duration_seconds ?? Number.MAX_SAFE_INTEGER) - (b.duration_seconds ?? Number.MAX_SAFE_INTEGER);
      return (sort === "duration-desc" ? -delta : delta) || byTitle(a, b);
    }
    if (["newest", "oldest", "date-desc", "date-asc"].includes(sort)) {
      const left = a.published_date ? Date.parse(a.published_date) : 0;
      const right = b.published_date ? Date.parse(b.published_date) : 0;
      return (["newest", "date-desc"].includes(sort) ? right - left : left - right) || byTitle(a, b);
    }
    if (sort === "channel") {
      return String(a.channel_name).localeCompare(String(b.channel_name), "he") || byTitle(a, b);
    }
    if (sort === "quality") return (b.quality_score - a.quality_score) || byTitle(a, b);

    return (b._searchScore - a._searchScore)
      || (Number(PROFESSIONAL_SOURCE_TYPES.has(b.source_type)) - Number(PROFESSIONAL_SOURCE_TYPES.has(a.source_type)))
      || tieBreak(a, b);
  });
  return prepared;
}

export function applySearchAndFilters(videos, filters = {}, context = {}) {
  return sortVideos(filterVideos(videos, filters, context), filters.sort || "recommended");
}

export const searchInternals = Object.freeze({
  PROFESSIONAL_SOURCE_TYPES,
  SKILL_ORDER,
  boundedLevenshteinOne,
  containsPhrase,
  searchTokenForms,
});
