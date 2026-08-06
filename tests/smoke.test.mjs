import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { access, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";


const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));


async function fileExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}


function startLocalServer() {
  const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const child = spawn(
    python,
    ["-u", "-B", "tools/serve_local.py", "--host", "127.0.0.1", "--port", "0"],
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    },
  );

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timeout = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill();
      reject(new Error(`local server did not become ready; stdout=${stdout}; stderr=${stderr}`));
    }, 7_000);

    const finish = (callback) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      callback();
    };

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
      const match = stdout.match(/Open (http:\/\/[^\s]+)/);
      if (match) finish(() => resolve({ child, url: match[1] }));
    });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString("utf8"); });
    child.once("error", (error) => finish(() => reject(error)));
    child.once("exit", (code) => {
      finish(() => reject(new Error(`local server exited with ${code}; stderr=${stderr}`)));
    });
  });
}


async function stopLocalServer(child) {
  if (child.exitCode !== null || child.signalCode !== null) return;
  await new Promise((resolve) => {
    const timeout = setTimeout(() => {
      if (child.exitCode === null && child.signalCode === null) child.kill("SIGKILL");
      resolve();
    }, 3_000);
    child.once("exit", () => {
      clearTimeout(timeout);
      resolve();
    });
    child.kill();
  });
}


test("index is Hebrew RTL and all declared local assets exist", async () => {
  const indexPath = join(projectRoot, "index.html");
  const html = await readFile(indexPath, "utf8");
  assert.match(html, /<html\b[^>]*\blang=["']he["'][^>]*\bdir=["']rtl["']/i);
  assert.match(html, /<script\b(?=[^>]*\btype=["']module["'])(?=[^>]*\bsrc=["'](?:\.\/)?assets\/js\/app\.js(?:\?[^"']*)?["'])[^>]*>/i);

  const localAssets = [...html.matchAll(/\b(?:href|src)=["']((?:\.\/)?assets\/[^"'#?]+)["']/gi)]
    .map((match) => match[1].replace(/^\.\//, ""));
  assert.ok(localAssets.length >= 2, "expected stylesheet and module references");
  for (const relativePath of new Set(localAssets)) {
    assert.ok(await fileExists(join(projectRoot, relativePath)), `missing declared asset: ${relativePath}`);
  }
});


test("initial HTML has no iframe and app defers a privacy-enhanced player", async () => {
  const [html, appSource] = await Promise.all([
    readFile(join(projectRoot, "index.html"), "utf8"),
    readFile(join(projectRoot, "assets/js/app.js"), "utf8"),
  ]);
  assert.doesNotMatch(html, /<iframe\b/i);
  assert.match(html, /loading=["']lazy["']/i);
  assert.match(appSource, /youtube-nocookie\.com\/embed\//);
  assert.match(appSource, /function\s+loadPlayer\s*\(/);
});


test("local server returns the site and a non-empty video JSON array without directory listings", { timeout: 15_000 }, async () => {
  const { child, url } = await startLocalServer();
  try {
    const [indexResponse, dataResponse, directoryResponse] = await Promise.all([
      fetch(url, { signal: AbortSignal.timeout(5_000) }),
      fetch(new URL("data/videos.json", url), { signal: AbortSignal.timeout(5_000) }),
      fetch(new URL("data/", url), { signal: AbortSignal.timeout(5_000) }),
    ]);
    assert.equal(indexResponse.status, 200);
    assert.match(indexResponse.headers.get("content-type") || "", /text\/html/);
    assert.match(indexResponse.headers.get("cache-control") || "", /no-store/);
    assert.match(await indexResponse.text(), /מדריך הווידאו לרכיבת אדוונצ'ר/);

    assert.equal(dataResponse.status, 200);
    const videos = await dataResponse.json();
    assert.ok(Array.isArray(videos));
    assert.ok(videos.length > 0);
    assert.equal(new Set(videos.map((video) => video.id)).size, videos.length);
    assert.equal(directoryResponse.status, 404);
  } finally {
    await stopLocalServer(child);
  }
});
