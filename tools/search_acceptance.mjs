import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { applySearchAndFilters, prepareVideos } from "../assets/js/search.js";

// Test document version: 1.2.0 — product 3.4.0.

const root = path.resolve(fileURLToPath(new URL("..", import.meta.url)));

async function loadJson(relativePath) {
  return JSON.parse(await readFile(path.join(root, relativePath), "utf8"));
}

const hasTag = (video, tag) => Array.isArray(video.tags) && video.tags.includes(tag);
const categoryIs = (video, category) => video.primary_category === category
  || (Array.isArray(video.secondary_categories) && video.secondary_categories.includes(category));
const offroad = (video) => video.domain === "offroad_adventure" || video.domain === "mixed";

export const searchAcceptanceCases = [
  ["חול", (video) => categoryIs(video, "sand") || hasTag(video, "sand")],
  ["בוץ", (video) => categoryIs(video, "mud_wet") || hasTag(video, "mud")],
  ["פניות בכביש", (video) => video.domain === "road" && (hasTag(video, "cornering") || categoryIs(video, "road_cornering"))],
  ["בלימת חירום", (video) => categoryIs(video, "emergency_braking") || hasTag(video, "emergency_braking")],
  ["הרמת אופנוע", (video) => categoryIs(video, "lifting") || hasTag(video, "lifting")],
  ["גשם", (video) => categoryIs(video, "wet_weather") || hasTag(video, "rain")],
  ["עלייה תלולה", (video) => categoryIs(video, "hills") || hasTag(video, "hill_climb")],
  ["רכיבה איטית", (video) => categoryIs(video, "balance_slow_control") || hasTag(video, "slow_speed")],
  ["רוח צד", (video) => hasTag(video, "crosswind")],
  ["רכיבת לילה", (video) => hasTag(video, "night")],
  ["לחץ אוויר", (video) => hasTag(video, "tire_pressure")],
  ["מתלים", (video) => hasTag(video, "suspension") || categoryIs(video, "suspension_setup")],
  ["ABS בשטח", (video) => hasTag(video, "abs") && offroad(video)],
  ["רכיבה עם מורכב", (video) => hasTag(video, "pillion")],
  ["מטען", (video) => hasTag(video, "luggage")],
  ["עייפות", (video) => hasTag(video, "fatigue")],
  ["Countersteering", (video) => hasTag(video, "countersteering")],
  ["Trail Braking", (video) => hasTag(video, "trail_braking")],
  ["Sand", (video) => categoryIs(video, "sand") || hasTag(video, "sand")],
  ["Mud", (video) => categoryIs(video, "mud_wet") || hasTag(video, "mud")],
  ["Emergency braking", (video) => categoryIs(video, "emergency_braking") || hasTag(video, "emergency_braking")],
  ["Cornering", (video) => hasTag(video, "cornering") || categoryIs(video, "road_cornering")],
  ["Crosswind", (video) => hasTag(video, "crosswind")],
  ["Suspension", (video) => hasTag(video, "suspension") || categoryIs(video, "suspension_setup")],
  ["Tire pressure", (video) => hasTag(video, "tire_pressure")],
];

export async function evaluateSearchAcceptance() {
  const [videos, taxonomy, synonyms] = await Promise.all([
    loadJson("data/videos.json"),
    loadJson("data/categories.json"),
    loadJson("data/synonyms.json"),
  ]);
  const prepared = prepareVideos(videos, taxonomy, synonyms);
  const checks = searchAcceptanceCases.map(([query, isRelevant]) => {
    const results = applySearchAndFilters(
      prepared.videos,
      { q: query, sort: "recommended" },
      { synonymIndex: prepared.synonymIndex },
    );
    const topThree = results.slice(0, 3).map((video) => ({
      id: video.id,
      title_he: video.title_he,
      channel_name: video.channel_name,
      score: video._searchScore,
      relevant: isRelevant(video),
    }));
    return {
      query,
      result_count: results.length,
      top_three: topThree,
      pass: topThree.length === 3 && topThree.every((item) => item.relevant),
    };
  });
  return {
    document_title: "Search acceptance report",
    document_version: "1.2.0",
    product_version: "3.4.0",
    generated_at_utc: new Date().toISOString(),
    required_query_count: searchAcceptanceCases.length,
    passed: checks.filter((check) => check.pass).length,
    failed: checks.filter((check) => !check.pass).length,
    status: checks.every((check) => check.pass) ? "PASS" : "FAIL",
    checks,
  };
}

async function main() {
  const reportArgIndex = process.argv.indexOf("--report");
  const reportPath = reportArgIndex >= 0
    ? path.resolve(root, process.argv[reportArgIndex + 1])
    : path.join(root, "reports", "final-one-shot", "search-acceptance.json");
  const report = await evaluateSearchAcceptance();
  await mkdir(path.dirname(reportPath), { recursive: true });
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  for (const check of report.checks) {
    const ids = check.top_three.map((item) => `${item.id}:${item.relevant ? "ok" : "bad"}`).join(", ");
    console.log(`${check.pass ? "PASS" : "FAIL"} ${check.query}: ${ids}`);
  }
  console.log(`Search acceptance: ${report.passed}/${report.required_query_count} passed`);
  if (report.status !== "PASS") process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  await main();
}
