import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  applySearchAndFilters,
  normalizeText,
  prepareVideos,
  uniqueDisplayTaxonomyIds,
} from "../assets/js/search.js";
import { searchAcceptanceCases } from "../tools/search_acceptance.mjs";


async function loadJson(relativeUrl) {
  return JSON.parse(await readFile(new URL(relativeUrl, import.meta.url), "utf8"));
}


const [sourceVideos, taxonomy, synonyms] = await Promise.all([
  loadJson("../data/videos.json"),
  loadJson("../data/categories.json"),
  loadJson("../data/synonyms.json"),
]);
const prepared = prepareVideos(sourceVideos, taxonomy, synonyms);


function search(query) {
  return applySearchAndFilters(
    prepared.videos,
    { q: query, sort: "recommended" },
    { synonymIndex: prepared.synonymIndex },
  );
}


test("normalizeText normalizes English case and punctuation", () => {
  assert.equal(normalizeText("  SAND/Ruts!  "), "sand ruts");
  assert.equal(normalizeText("Trail-Braking"), "trail-braking");
});


test("normalizeText folds Hebrew final letters", () => {
  assert.equal(normalizeText("מלך"), normalizeText("מלכ"));
  assert.equal(normalizeText("גשם"), normalizeText("גשמ"));
  assert.equal(normalizeText("חריץ"), normalizeText("חריצ"));
});


test("display taxonomy IDs are deduplicated by localized label, not only by ID", () => {
  const labels = new Map([
    ["lifting-focus", { name_he: "הרמת אופנוע", name_en: "Motorcycle lifting" }],
    ["lifting-tag", { name_he: "הרמת אופנוע", name_en: "Motorcycle lifting" }],
    ["recovery-tag", { name_he: "חילוץ", name_en: "Recovery" }],
  ]);
  const ids = ["lifting-focus", "lifting-tag", "recovery-tag", "lifting-focus"];

  assert.deepEqual(
    uniqueDisplayTaxonomyIds(ids, labels, "he"),
    ["lifting-focus", "recovery-tag"],
  );
  assert.deepEqual(
    uniqueDisplayTaxonomyIds(ids, labels, "en"),
    ["lifting-focus", "recovery-tag"],
  );
});


test("every real card's combined focus and tag labels are unique in Hebrew and English", () => {
  const labelLookup = new Map();
  for (const section of [taxonomy.subcategories, taxonomy.controlled_tags]) {
    for (const item of section) {
      if (!labelLookup.has(item.id)) labelLookup.set(item.id, item);
    }
  }

  for (const video of sourceVideos) {
    const ids = [...(video.subtopics || []), ...(video.tags || [])];
    for (const language of ["he", "en"]) {
      const displayed = uniqueDisplayTaxonomyIds(ids, labelLookup, language);
      const normalizedLabels = displayed.map((id) => {
        const item = labelLookup.get(id);
        return normalizeText(language === "en" ? item?.name_en : item?.name_he);
      });
      assert.equal(
        new Set(normalizedLabels).size,
        normalizedLabels.length,
        `${video.id} repeats a displayed ${language} taxonomy label`,
      );
    }
  }
});


test("Hebrew and English synonyms reach the same relevant sand records", () => {
  const hebrewIds = new Set(search("חול").slice(0, 5).map((video) => video.id));
  const englishIds = search("sand").slice(0, 5).map((video) => video.id);
  assert.ok(englishIds.some((id) => hebrewIds.has(id)), "expected an overlapping sand result");
  assert.ok(search("sand")[0].tags.includes("sand"));
});


test("one-character English typo still finds emergency braking", () => {
  const results = search("emergency brakin");
  assert.ok(results.length > 0);
  assert.equal(results[0].primary_category, "emergency_braking");
});


test("English search matches whole words instead of unrelated substrings", () => {
  const results = search("rain");
  assert.ok(results.length > 0);
  assert.equal(results[0].primary_category, "wet_weather");

  const trainingOnly = prepareVideos(
    [{ id: "training-only", title_original: "Advanced training drills" }],
    {},
    {},
  );
  const falsePositives = applySearchAndFilters(
    trainingOnly.videos,
    { q: "rain", sort: "recommended" },
    { synonymIndex: trainingOnly.synonymIndex },
  );
  assert.deepEqual(falsePositives, [], "rain must not match the substring in training");
});


test("English-only summaries, learning points and taxonomy descriptions are searchable", () => {
  const englishOnlyVideo = {
    id: "english-only-fields",
    title_he: "כותרת בדיקה",
    title_original: "Unrelated source title",
    channel_name: "Fixture channel",
    summary_he: "תקציר בדיקה שאינו כולל את מילות החיפוש.",
    summary_en: "Contour breadcrumb workflow for a long route.",
    learning_points_he: [],
    learning_points_en: ["Visor fogging mitigation"],
    fit_for_he: "לבדיקה",
    fit_for_en: "Riders testing bilingual retrieval",
    why_watch_he: "לבדיקה",
    why_watch_en: "Explains an English-only retrieval concept",
    exercises_he: [],
    exercises_en: ["Practise waypoint reconciliation"],
    equipment_he: [],
    equipment_en: ["Offline map"],
    safety_warnings_he: [],
    safety_warnings_en: ["Stop before changing settings"],
    common_mistakes_he: [],
    common_mistakes_en: ["Skipping topology checks"],
    domain: "fixture_domain",
    primary_category: "fixture_category",
    secondary_categories: [],
    subtopics: [],
    content_type: "fixture_format",
    tags: [],
    skill_level: "beginner",
    risk_level: "low",
    motorcycle_types: [],
    motorcycle_weight_classes: [],
    terrain_types: [],
    road_conditions: [],
    source_type: "experienced_rider",
    language: "en",
    chapters: [],
    quality_score: 5,
  };
  const englishOnlyTaxonomy = {
    categories: [{
      id: "fixture_category",
      name_he: "קטגוריית בדיקה",
      name_en: "Fixture category",
      description_he: "תיאור בדיקה",
      description_en: "Route sculpting and topology reconciliation",
    }],
  };
  const fixture = prepareVideos([englishOnlyVideo], englishOnlyTaxonomy, {});
  const fixtureSearch = (query) => applySearchAndFilters(
    fixture.videos,
    { q: query, sort: "recommended" },
    { synonymIndex: fixture.synonymIndex },
  );

  for (const query of ["contour breadcrumb", "visor fogging", "route sculpting"]) {
    assert.deepEqual(
      fixtureSearch(query).map((video) => video.id),
      [englishOnlyVideo.id],
      `English-only field was not indexed for query: ${query}`,
    );
  }
});


test("release search acceptance defines all 25 required queries", () => {
  assert.equal(searchAcceptanceCases.length, 25);
});


for (const [query, isRelevant] of searchAcceptanceCases) {
  test(`acceptance search ranks three relevant results first: ${query}`, () => {
    const results = search(query);
    assert.ok(results.length >= 3, `fewer than three results for ${query}`);
    results.slice(0, 3).forEach((video, index) => {
      assert.ok(isRelevant(video), `result ${index + 1} (${video.id}) is not relevant to ${query}`);
    });
  });
}
