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


test("dataset has exactly 60 unique records with matching YouTube URLs", () => {
  assert.equal(videos.length, 60);
  assert.equal(videoIds.size, 60);
  assert.equal(new Set(videos.map((video) => video.youtube_video_id)).size, 60);
  assert.equal(new Set(videos.map((video) => video.youtube_url)).size, 60);

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


test("both learning paths have ordered stages and valid video choices", () => {
  assert.equal(learningPaths.length, 2);
  assert.equal(ids(learningPaths).size, 2);

  learningPaths.forEach((path) => {
    assert.ok(path.steps.length > 0, `${path.id} has no steps`);
    assert.deepEqual(path.steps.map((step) => step.order), path.steps.map((_, index) => index + 1));
    path.steps.forEach((step) => {
      assert.ok(step.primary_video_ids.length > 0, `${path.id}/${step.order} has no primary video`);
      const choices = [...step.primary_video_ids, ...step.alternative_video_ids];
      assert.ok(choices.length >= 2, `${path.id}/${step.order} must offer at least two choices`);
      assert.equal(new Set(choices).size, choices.length, `${path.id}/${step.order} repeats a video`);
      choices.forEach((videoId) => {
        assert.ok(videoIds.has(videoId), `${path.id}/${step.order} refers to missing ${videoId}`);
      });
    });
  });
});
