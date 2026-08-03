import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  applySearchAndFilters,
  normalizeText,
  prepareVideos,
} from "../assets/js/search.js";


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


const acceptanceQueries = [
  ["חול", (video) => video.primary_category === "sand" || video.tags.includes("sand")],
  ["בוץ", (video) => video.primary_category === "mud_wet" || video.tags.includes("mud")],
  ["פניות בכביש", (video) => video.domain === "road" && video.tags.includes("cornering")],
  ["בלימת חירום", (video) => video.primary_category === "emergency_braking" || video.tags.includes("emergency_braking")],
  ["הרמת אופנוע", (video) => video.domain === "safety_recovery" && video.tags.includes("lifting")],
  ["גשם", (video) => video.primary_category === "wet_weather" || video.tags.includes("rain")],
  ["עלייה תלולה", (video) => video.primary_category === "hills" || video.tags.includes("hill_climb")],
  ["רכיבה איטית", (video) => video.tags.includes("slow_speed") || video.primary_category === "balance_slow_control"],
];


for (const [query, isRelevant] of acceptanceQueries) {
  test(`acceptance search ranks a relevant result first: ${query}`, () => {
    const results = search(query);
    assert.ok(results.length > 0, `no results for ${query}`);
    assert.ok(isRelevant(results[0]), `top result ${results[0].id} is not relevant to ${query}`);
  });
}
