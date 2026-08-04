import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  applySearchAndFilters,
  normalizeText,
  prepareVideos,
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
