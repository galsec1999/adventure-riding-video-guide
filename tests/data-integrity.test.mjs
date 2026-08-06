import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";


async function loadJson(relativeUrl) {
  return JSON.parse(await readFile(new URL(relativeUrl, import.meta.url), "utf8"));
}


const [videos, taxonomy, learningPaths, travelGuides] = await Promise.all([
  loadJson("../data/videos.json"),
  loadJson("../data/categories.json"),
  loadJson("../data/learning-paths.json"),
  loadJson("../data/travel-guides.json"),
]);
const videoIds = new Set(videos.map((video) => video.id));


function ids(collection) {
  return new Set(collection.map((item) => item.id));
}


function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}


function assertBilingualText(record, stems, context) {
  stems.forEach((stem) => {
    const he = record[`${stem}_he`];
    const en = record[`${stem}_en`];
    assert.ok(isNonEmptyString(he) && /[\u0590-\u05ff]/u.test(he), `${context}.${stem}_he lacks Hebrew text`);
    assert.ok(isNonEmptyString(en) && /[A-Za-z]/u.test(en), `${context}.${stem}_en lacks English text`);
  });
}


function assertBilingualLists(record, stems, context, expectedLength = null, everyHebrewItem = false) {
  stems.forEach((stem) => {
    const he = record[`${stem}_he`];
    const en = record[`${stem}_en`];
    assert.ok(Array.isArray(he) && he.length > 0, `${context}.${stem}_he must be a non-empty array`);
    assert.ok(Array.isArray(en) && en.length > 0, `${context}.${stem}_en must be a non-empty array`);
    assert.equal(he.length, en.length, `${context}.${stem} translations must have matching lengths`);
    if (expectedLength !== null) {
      assert.equal(he.length, expectedLength, `${context}.${stem}_he must contain ${expectedLength} entries`);
      assert.equal(en.length, expectedLength, `${context}.${stem}_en must contain ${expectedLength} entries`);
    }
    assert.ok(he.every(isNonEmptyString), `${context}.${stem}_he contains an empty entry`);
    assert.ok(en.every((item) => isNonEmptyString(item) && /[A-Za-z]/u.test(item)), `${context}.${stem}_en contains invalid English text`);
    const hasExpectedHebrew = everyHebrewItem
      ? he.every((item) => /[\u0590-\u05ff]/u.test(item))
      : /[\u0590-\u05ff]/u.test(he.join(" "));
    assert.ok(hasExpectedHebrew, `${context}.${stem}_he lacks Hebrew content`);
  });
}


function assertValidVideoReferences(videoReferences, context) {
  assert.ok(Array.isArray(videoReferences) && videoReferences.length > 0, `${context}.video_ids must be non-empty`);
  assert.equal(new Set(videoReferences).size, videoReferences.length, `${context}.video_ids contains duplicates`);
  videoReferences.forEach((videoId) => {
    assert.ok(videoIds.has(videoId), `${context} refers to missing ${videoId}`);
  });
}


test("non-empty dataset has unique records with matching YouTube URLs", () => {
  assert.equal(videos.length, 411, "the canonical root dataset must contain release 3.0.0's 411 active records");
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
    content_type: ids(taxonomy.content_types),
    skill_level: ids(taxonomy.skill_levels),
    risk_level: ids(taxonomy.risk_levels),
    source_type: ids(taxonomy.source_types),
    language: ids(taxonomy.languages),
  };
  const arrayFields = {
    secondary_categories: ids(taxonomy.categories),
    subtopics: ids(taxonomy.subcategories),
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


test("every primary category is permitted by its video's domain", () => {
  const domainIds = ids(taxonomy.domains);
  const categoryIds = ids(taxonomy.categories);
  assert.deepEqual(
    new Set(Object.keys(taxonomy.domain_category_map)),
    domainIds,
    "domain_category_map must define every and only controlled domain",
  );

  Object.entries(taxonomy.domain_category_map).forEach(([domainId, categoryList]) => {
    assert.ok(Array.isArray(categoryList) && categoryList.length > 0, `${domainId} must map to categories`);
    assert.equal(new Set(categoryList).size, categoryList.length, `${domainId} repeats a mapped category`);
    categoryList.forEach((categoryId) => {
      assert.ok(categoryIds.has(categoryId), `${domainId} maps unknown category ${categoryId}`);
    });
  });

  videos.forEach((video) => {
    const allowedCategories = taxonomy.domain_category_map[video.domain] || [];
    assert.ok(
      allowedCategories.includes(video.primary_category),
      `${video.id} maps ${video.domain} to disallowed primary category ${video.primary_category}`,
    );
  });
});


test("all related-video references resolve to existing records", () => {
  videos.forEach((video) => {
    video.related_video_ids.forEach((relatedId) => {
      assert.ok(videoIds.has(relatedId), `${video.id} refers to missing ${relatedId}`);
    });
  });
});


test("all 17 learning paths have ordered stages, safety fields, and valid video choices", () => {
  assert.equal(learningPaths.length, 17);
  assert.equal(ids(learningPaths).size, 17);

  learningPaths.forEach((path) => {
    assert.ok(path.steps.length >= 8 && path.steps.length <= 12, `${path.id} must have 8-12 steps`);
    assert.deepEqual(path.steps.map((step) => step.order), path.steps.map((_, index) => index + 1));
    path.steps.forEach((step) => {
      assert.ok(step.primary_video_ids.length >= 1, `${path.id}/${step.order} must have a primary video`);
      assert.ok(step.alternative_video_ids.length >= 1, `${path.id}/${step.order} must have an alternative`);
      assert.ok(Array.isArray(step.equipment_he) && step.equipment_he.length > 0, `${path.id}/${step.order} lacks equipment`);
      assert.ok(["low", "medium", "high"].includes(step.risk_level), `${path.id}/${step.order} has invalid risk`);
      assert.ok(typeof step.warning_he === "string" && step.warning_he.trim(), `${path.id}/${step.order} lacks warning`);
      const choices = [...step.primary_video_ids, ...step.alternative_video_ids];
      assert.ok(choices.length >= 2 && choices.length <= 5, `${path.id}/${step.order} must offer 2-5 choices`);
      assert.equal(new Set(choices).size, choices.length, `${path.id}/${step.order} repeats a video`);
      choices.forEach((videoId) => {
        assert.ok(videoIds.has(videoId), `${path.id}/${step.order} refers to missing ${videoId}`);
      });
    });
  });
});


test("travel guide has three bilingual trip types and seven six-item bilingual checklists", () => {
  assert.match(travelGuides.version, /^\d+\.\d+\.\d+(?:[-+].+)?$/u);
  assert.ok(!Number.isNaN(Date.parse(travelGuides.updated)), "travel guide must have a valid updated date");
  assertBilingualText(travelGuides, ["mindfulness_note"], "travel guide");

  assert.equal(travelGuides.trip_types.length, 3);
  assert.deepEqual(ids(travelGuides.trip_types), new Set(["day", "multi_day", "abroad"]));
  const learningPathIds = ids(learningPaths);
  travelGuides.trip_types.forEach((tripType) => {
    const context = `trip type ${tripType.id}`;
    assertBilingualText(tripType, ["name", "description"], context);
    assert.ok(learningPathIds.has(tripType.recommended_path_id), `${context} refers to a missing learning path`);
  });

  assert.equal(travelGuides.checklists.length, 7);
  assert.equal(ids(travelGuides.checklists).size, 7);
  travelGuides.checklists.forEach((checklist) => {
    const context = `checklist ${checklist.id}`;
    assertBilingualText(checklist, ["title"], context);
    assertBilingualLists(checklist, ["items"], context, 6, true);
  });
});


test("travel guide has ten bilingual navigation comparisons with valid HTTPS sources and videos", () => {
  assert.equal(travelGuides.navigation_apps.length, 10);
  assert.equal(new Set(travelGuides.navigation_apps.map((item) => item.name)).size, 10);
  const sourceUrls = new Set();

  travelGuides.navigation_apps.forEach((comparison) => {
    const context = `navigation comparison ${comparison.name}`;
    assert.ok(isNonEmptyString(comparison.name), `${context} lacks a name`);
    assertBilingualText(comparison, ["type", "best_for", "setup", "caution"], context);
    assertBilingualLists(comparison, ["capabilities", "advantages", "limitations"], context);

    const source = new URL(comparison.source_url);
    assert.equal(source.protocol, "https:", `${context} source must use HTTPS`);
    assert.ok(source.hostname, `${context} source must have a hostname`);
    assert.equal(source.username, "", `${context} source must not contain credentials`);
    assert.equal(source.password, "", `${context} source must not contain credentials`);
    assert.ok(!/\s/u.test(comparison.source_url), `${context} source contains whitespace`);
    assert.ok(!sourceUrls.has(comparison.source_url), `${context} repeats a source URL`);
    sourceUrls.add(comparison.source_url);
    assertValidVideoReferences(comparison.video_ids, context);
  });

  const offRoad = travelGuides.navigation_apps.find((item) => item.name === "אופרוד / Off-Road");
  assert.ok(offRoad, "the verified אופרוד / Off-Road comparison is missing");
  assert.deepEqual(offRoad.video_ids, ["yt-uJwRnbm74E4"]);
  assert.ok(videoIds.has(offRoad.video_ids[0]), "the אופרוד / Off-Road video reference is missing from videos.json");
});


test("travel guide has six bilingual knowledge guides with valid video references", () => {
  assert.equal(travelGuides.knowledge_guides.length, 6);
  assert.equal(ids(travelGuides.knowledge_guides).size, 6);

  travelGuides.knowledge_guides.forEach((guide) => {
    const context = `knowledge guide ${guide.id}`;
    assertBilingualText(guide, ["eyebrow", "title", "summary"], context);
    assertBilingualLists(guide, ["best_when", "tradeoffs", "setup_checks"], context);
    assertValidVideoReferences(guide.video_ids, context);
  });
});
