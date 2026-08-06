import { env, pipeline } from "../vendor/transformers.min.js";

const MODEL_ID = "Xenova/multilingual-e5-small";
const MODEL_REVISION = "761b726dd34fb83930e26aab4e9ac3899aa1fa78";
const WASM_MODULE_URL = new URL("../vendor/ort-wasm-simd-threaded.mjs", import.meta.url).href;
const WASM_BINARY_URL = new URL("../vendor/ort-wasm-simd-threaded.wasm", import.meta.url).href;

env.allowRemoteModels = true;
env.allowLocalModels = false;
env.useBrowserCache = true;
env.backends.onnx.wasm.wasmPaths = {
  mjs: WASM_MODULE_URL,
  wasm: WASM_BINARY_URL,
};
// GitHub Pages cannot set cross-origin-isolation headers. One WASM thread keeps
// the model compatible with regular browsers and phones without SharedArrayBuffer.
env.backends.onnx.wasm.numThreads = 1;

let extractorPromise = null;

function post(type, payload = {}) {
  self.postMessage({ type, ...payload });
}

async function getExtractor() {
  if (!extractorPromise) {
    post("status", { stage: "loading" });
    extractorPromise = pipeline("feature-extraction", MODEL_ID, {
      revision: MODEL_REVISION,
      dtype: "q8",
      device: "wasm",
      progress_callback(progress) {
        const loaded = Number(progress?.loaded || 0);
        const total = Number(progress?.total || 0);
        post("progress", {
          file: progress?.file || "",
          percent: total > 0 ? Math.min(100, Math.round((loaded / total) * 100)) : null,
        });
      },
    }).then((extractor) => {
      post("status", { stage: "ready" });
      return extractor;
    }).catch((error) => {
      extractorPromise = null;
      throw error;
    });
  }
  return extractorPromise;
}

self.addEventListener("message", async (event) => {
  const message = event.data || {};
  try {
    if (message.type === "load") {
      await getExtractor();
      return;
    }
    if (message.type === "embed") {
      const extractor = await getExtractor();
      const output = await extractor(`query: ${String(message.query || "").trim()}`, {
        pooling: "mean",
        normalize: true,
      });
      const vector = output.data instanceof Float32Array ? output.data : Float32Array.from(output.data);
      self.postMessage({ type: "embedding", requestId: message.requestId, vector }, [vector.buffer]);
    }
  } catch (error) {
    post("error", {
      requestId: message.requestId || null,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});
