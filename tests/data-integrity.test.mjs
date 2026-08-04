import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";


async function loadJson(relativeUrl) {
  return JSON.parse(await readFile(new URL(relativeUrl, import.meta.url), "utf8"));
}


const [videos, taxonomy, learningPaths] = await Promise.all([
  loadJson("../data/videos.json"),
  loadJson("../data/categories.json"),
  loadJson("../data/learning-paths.json"),
]);
const videoIds = new Set(videos.map((video) => video.id));


function ids(collection) {
  return new Set(collection.map((item) => item.id));
}


test("non-empty dataset has unique records with matching YouTube URLs", () => {
  assert.ok(videos.length > 0);
  assert.equal(videoIds.size, videos.length);
  assert.equal(new Set(videos.map((video) => video.youtube_video_id)).size, videos.length);
  assert.equal(new Set(videos.map((video) => video.youtube_url)).size, videos.length);

  videos.forEach((video) => {
    assert.equal(video.id, `yt-${video.youtube_video_id}`);
    assert.equal(video.youtube_url, `https://www.youtube.com/watch?v=${video.youtube_video_id}`);
  });
});


test("all taxonomy fields reference controlled IDs", () => {
  const scalarFields = {
    domain: ids(taxonomy.domains),
    primary_category: ids(taxonomy.categories),
    skill_level: ids(taxonomy.skill_levels),
    risk_level: ids(taxonomy.risk_levels),
    source_type: ids(taxonomy.source_types),
    language: ids(taxonomy.languages),
  };
  const arrayFields = {
    secondary_categories: ids(taxonomy.categories),
    tags: ids(taxonomy.controlled_tags),
    motorcycle_types: ids(taxonomy.motorcycle_types),
    motorcycle_weight_classes: ids(taxonomy.motorcycle_weight_classes),
    terrain_types: ids(taxonomy.terrain_types),
    road_conditions: ids(taxonomy.road_conditions),
    subtitle_languages: ids(taxonomy.languages),
  };

  videos.forEach((video) => {
    Object.entries(scalarFields).forEach(([field, allowed]) => {
      assert.ok(allowed.has(video[field]), `${video.id} has unknown ${field}: ${video[field]}`);
    });
    Object.entries(arrayFields).forEach(([field, allowed]) => {
      video[field].forEach((value) => {
        assert.ok(allowed.has(value), `${video.id} has unknown ${field}: ${value}`);
      });
    });
  });
});


test("all related-video references resolve to existing records", () => {
  videos.forEach((video) => {
    video.related_video_ids.forEach((relatedId) => {
      assert.ok(videoIds.has(relatedId), `${video.id} refers to missing ${relatedId}`);
    });
  });
});


test("all eight learning paths have ordered stages, safety fields, and valid video choices", () => {
  assert.equal(learningPaths.length, 8);
  assert.equal(ids(learningPaths).size, 8);

  learningPaths.forEach((path) => {
    assert.ok(path.steps.length >= 8 && path.steps.length <= 12, `${path.id} must have 8-12 steps`);
    assert.deepEqual(path.steps.map((step) => step.order), path.steps.map((_, index) => index + 1));
    path.steps.forEach((step) => {
      assert.equal(step.primary_video_ids.length, 2, `${path.id}/${step.order} must have two primary videos`);
      assert.equal(step.alternative_video_ids.length, 1, `${path.id}/${step.order} must have one alternative`);
      assert.ok(Array.isArray(step.equipment_he) && step.equipment_he.length > 0, `${path.id}/${step.order} lacks equipment`);
      assert.ok(["low", "medium", "high"].includes(step.risk_level), `${path.id}/${step.order} has invalid risk`);
      assert.ok(typeof step.warning_he === "string" && step.warning_he.trim(), `${path.id}/${step.order} lacks warning`);
      const choices = [...step.primary_video_ids, ...step.alternative_video_ids];
      assert.ok(choices.length >= 2, `${path.id}/${step.order} must offer at least two choices`);
      assert.equal(new Set(choices).size, choices.length, `${path.id}/${step.order} repeats a video`);
      choices.forEach((videoId) => {
        assert.ok(videoIds.has(videoId), `${path.id}/${step.order} refers to missing ${videoId}`);
      });
    });
  });
});
