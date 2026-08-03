import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  applySearchAndFilters,
  prepareVideos,
  sortVideos,
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
const context = { synonymIndex: prepared.synonymIndex };


test("three simultaneous filters return only matching real records", () => {
  const filters = {
    domain: "offroad_adventure",
    terrain: "sand",
    language: "en",
  };
  const results = applySearchAndFilters(prepared.videos, filters, context);

  assert.ok(results.length > 0, "the documented three-filter combination must have results");
  results.forEach((video) => {
    assert.equal(video.domain, filters.domain);
    assert.equal(video.language, filters.language);
    assert.ok(video.terrain_types.includes(filters.terrain));
  });
});


test("logical reset to empty filters restores the complete dataset", () => {
  const filtered = applySearchAndFilters(
    prepared.videos,
    { domain: "road", category: "emergency_braking", professional: "yes" },
    context,
  );
  assert.ok(filtered.length > 0 && filtered.length < prepared.videos.length);

  const reset = applySearchAndFilters(prepared.videos, { sort: "recommended" }, context);
  assert.equal(reset.length, prepared.videos.length);
  assert.deepEqual(new Set(reset.map((video) => video.id)), new Set(prepared.videos.map((video) => video.id)));
});


test("quality sorting is descending, deterministic, and does not mutate input", () => {
  const input = prepared.videos.slice(0, 15);
  const originalOrder = input.map((video) => video.id);
  const sorted = sortVideos(input, "quality");

  assert.deepEqual(input.map((video) => video.id), originalOrder);
  assert.notStrictEqual(sorted, input);
  for (let index = 1; index < sorted.length; index += 1) {
    assert.ok(sorted[index - 1].quality_score >= sorted[index].quality_score);
  }
  assert.deepEqual(
    sortVideos(input, "quality").map((video) => video.id),
    sorted.map((video) => video.id),
  );
});


test("duration filters follow the labels shown in the UI", () => {
  const short = applySearchAndFilters(prepared.videos, { duration: "short" }, context);
  const medium = applySearchAndFilters(prepared.videos, { duration: "medium" }, context);
  const long = applySearchAndFilters(prepared.videos, { duration: "long" }, context);

  assert.ok(short.every((video) => video.duration_seconds <= 300));
  assert.ok(medium.every((video) => video.duration_seconds > 300 && video.duration_seconds <= 900));
  assert.ok(long.every((video) => video.duration_seconds > 900));
  const knownDurations = prepared.videos.filter((video) => video.duration_seconds != null);
  assert.equal(short.length + medium.length + long.length, knownDurations.length);
  assert.equal(
    new Set([...short, ...medium, ...long].map((video) => video.id)).size,
    knownDurations.length,
  );
});
