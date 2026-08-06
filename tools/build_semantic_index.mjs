import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { env, pipeline } from "@huggingface/transformers";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MODEL_ID = "Xenova/multilingual-e5-small";
const MODEL_REVISION = "761b726dd34fb83930e26aab4e9ac3899aa1fa78";
const DIMENSIONS = 384;
const BATCH_SIZE = 12;
const OUTPUT_BINARY = resolve(ROOT, "data", "semantic-index.f32");
const OUTPUT_META = resolve(ROOT, "data", "semantic-index.json");

env.cacheDir = process.env.ADV_GUIDE_MODEL_CACHE || resolve(ROOT, ".model-cache");
env.allowRemoteModels = true;
env.allowLocalModels = true;

function passageFor(video) {
  const fields = [
    video.title_he,
    video.title_en,
    video.title_original,
    video.summary_he,
    video.summary_en,
    ...(video.learning_points_he || []),
    ...(video.learning_points_en || []),
    video.primary_category,
    ...(video.secondary_categories || []),
    ...(video.subtopics || []),
    ...(video.tags || []),
  ].filter(Boolean);
  return `passage: ${[...new Set(fields)].join(" · ")}`;
}

async function main() {
  const videos = JSON.parse(await readFile(resolve(ROOT, "data", "videos.json"), "utf8"));
  const extractor = await pipeline("feature-extraction", MODEL_ID, {
    revision: MODEL_REVISION,
    dtype: "q8",
  });
  const matrix = new Float32Array(videos.length * DIMENSIONS);

  for (let offset = 0; offset < videos.length; offset += BATCH_SIZE) {
    const batch = videos.slice(offset, offset + BATCH_SIZE);
    const output = await extractor(batch.map(passageFor), { pooling: "mean", normalize: true });
    const values = output.data instanceof Float32Array ? output.data : Float32Array.from(output.data);
    if (values.length !== batch.length * DIMENSIONS) {
      throw new Error(`Unexpected embedding shape at offset ${offset}: ${values.length}`);
    }
    matrix.set(values, offset * DIMENSIONS);
    process.stdout.write(`\rEmbedded ${Math.min(offset + batch.length, videos.length)}/${videos.length}`);
  }

  await mkdir(dirname(OUTPUT_META), { recursive: true });
  await writeFile(OUTPUT_BINARY, Buffer.from(matrix.buffer));
  await writeFile(OUTPUT_META, `${JSON.stringify({
    version: "1.0.0",
    generated: new Date().toISOString(),
    model: MODEL_ID,
    revision: MODEL_REVISION,
    dtype: "q8",
    dimensions: DIMENSIONS,
    count: videos.length,
    ids: videos.map((video) => video.id),
    binary: "semantic-index.f32",
    query_prefix: "query: ",
    passage_prefix: "passage: ",
  }, null, 2)}\n`, "utf8");
  process.stdout.write(`\nWrote ${OUTPUT_META} and ${OUTPUT_BINARY}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
