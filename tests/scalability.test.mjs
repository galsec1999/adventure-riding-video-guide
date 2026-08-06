import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

// Test document version: 1.2.0 — product 3.4.0.

import {
  getVisibleItems,
  INITIAL_VISIBLE_LIMIT,
  LOAD_MORE_BATCH_SIZE,
  nextVisibleLimit,
} from "../assets/js/pagination.js";
import {
  applySearchAndFilters,
  prepareVideos,
  sortVideos,
} from "../assets/js/search.js";
import { buildVideoFixture } from "./fixtures/video-fixture.mjs";


async function loadJson(relativeUrl) {
  return JSON.parse(await readFile(new URL(relativeUrl, import.meta.url), "utf8"));
}


const [sourceVideos, sourceShorts, taxonomy, synonyms] = await Promise.all([
  loadJson("../data/videos.json"),
  loadJson("../data/shorts.json"),
  loadJson("../data/categories.json"),
  loadJson("../data/synonyms.json"),
]);

test("the complete 578-record release prepares and searches without runtime errors", (t) => {
  const complete = [...sourceVideos, ...sourceShorts];
  const startedAt = performance.now();
  const prepared = prepareVideos(complete, taxonomy, synonyms);
  const results = applySearchAndFilters(prepared.videos, { q: "cornering", sort: "recommended" }, { synonymIndex: prepared.synonymIndex });
  const elapsedMs = performance.now() - startedAt;
  assert.equal(complete.length, 578);
  assert.equal(prepared.videos.length, 578);
  assert.equal(new Set(prepared.videos.map((video) => video.id)).size, 578);
  assert.ok(results.length > 0);
  t.diagnostic(`prepare/search 578: ${elapsedMs.toFixed(2)} ms (measurement only; no hardware threshold)`);
});


for (const fixtureSize of [425, 500]) {
  test(`${fixtureSize}-record fixture prepares and indexes without runtime errors`, (t) => {
    const fixture = buildVideoFixture(sourceVideos, fixtureSize);
    const startedAt = performance.now();
    const prepared = prepareVideos(fixture, taxonomy, synonyms);
    const elapsedMs = performance.now() - startedAt;

    assert.equal(fixture.length, fixtureSize);
    assert.equal(prepared.videos.length, fixtureSize);
    assert.equal(new Set(fixture.map((video) => video.id)).size, fixtureSize);
    assert.equal(new Set(fixture.map((video) => video.youtube_video_id)).size, fixtureSize);
    assert.equal(new Set(fixture.map((video) => video.youtube_url)).size, fixtureSize);
    assert.deepEqual(
      prepared.videos.map((video) => video._sourceIndex),
      Array.from({ length: fixtureSize }, (_, index) => index),
    );
    t.diagnostic(`prepare/index ${fixtureSize}: ${elapsedMs.toFixed(2)} ms (measurement only; no hardware threshold)`);
  });

  test(`${fixtureSize}-record fixture supports search, combined filters, sorting, and exact result counts`, (t) => {
    const fixture = buildVideoFixture(sourceVideos, fixtureSize);
    const prepared = prepareVideos(fixture, taxonomy, synonyms);
    const context = { synonymIndex: prepared.synonymIndex };
    const startedAt = performance.now();

    const searchResults = applySearchAndFilters(
      prepared.videos,
      { q: "חול", sort: "recommended" },
      context,
    );
    const filtered = applySearchAndFilters(
      prepared.videos,
      { domain: "offroad_adventure", terrain: "sand", language: "en" },
      context,
    );
    const sorted = sortVideos(prepared.videos, "quality");
    const elapsedMs = performance.now() - startedAt;

    assert.ok(searchResults.length > 0);
    assert.ok(searchResults.every((video) => video._searchScore > 0));
    assert.ok(filtered.length > 0 && filtered.length < fixtureSize);
    assert.equal(filtered.length, filtered.filter((video) => (
      video.domain === "offroad_adventure"
      && video.language === "en"
      && video.terrain_types.includes("sand")
    )).length);
    assert.equal(sorted.length, fixtureSize);
    for (let index = 1; index < sorted.length; index += 1) {
      assert.ok(sorted[index - 1].quality_score >= sorted[index].quality_score);
    }
    assert.equal(new Set(sorted.map((video) => video.id)).size, fixtureSize);
    t.diagnostic(`search/filter/sort ${fixtureSize}: ${elapsedMs.toFixed(2)} ms (measurement only; no hardware threshold)`);
  });

  test(`${fixtureSize}-record pagination loads every unique card identity without duplication`, () => {
    const fixture = buildVideoFixture(sourceVideos, fixtureSize);
    let visibleLimit = INITIAL_VISIBLE_LIMIT;
    const visibleCounts = [];

    while (true) {
      const visible = getVisibleItems(fixture, visibleLimit);
      visibleCounts.push(visible.length);
      assert.equal(new Set(visible.map((video) => video.id)).size, visible.length);
      assert.ok(visible.length <= fixtureSize);
      if (visible.length === fixtureSize) break;

      const nextLimit = nextVisibleLimit(visibleLimit, fixtureSize);
      assert.ok(nextLimit > visibleLimit);
      assert.ok(nextLimit - visibleLimit <= LOAD_MORE_BATCH_SIZE);
      visibleLimit = nextLimit;
    }

    assert.equal(visibleCounts[0], Math.min(INITIAL_VISIBLE_LIMIT, fixtureSize));
    assert.equal(visibleCounts.at(-1), fixtureSize);
    assert.ok(visibleCounts.length > 1);
  });
}
