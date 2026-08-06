import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const MIRRORED_DIRECTORIES = ["assets", "data", "downloads"];
const MIRRORED_FILES = ["index.html", "404.html", "offline.html", "manifest.webmanifest", "service-worker.js"];

async function listMirroredFiles(prefix = "") {
  const files = [...MIRRORED_FILES];
  async function walk(relativeDirectory) {
    const directory = new URL(`../${prefix}${relativeDirectory}/`, import.meta.url);
    const entries = await readdir(directory, { withFileTypes: true });
    for (const entry of entries) {
      const relative = `${relativeDirectory}/${entry.name}`;
      if (entry.isDirectory()) await walk(relative);
      else if (entry.isFile() && entry.name !== ".gitkeep") files.push(relative);
    }
  }
  for (const directory of MIRRORED_DIRECTORIES) await walk(directory);
  return files.sort();
}

async function sha256(path) {
  const content = await readFile(new URL(`../${path}`, import.meta.url));
  return createHash("sha256").update(content).digest("hex");
}

test("published code and data are an exact SHA-256 mirror of the canonical root", async () => {
  const sourceFiles = await listMirroredFiles();
  const publishedFiles = await listMirroredFiles("site/");
  assert.deepEqual(publishedFiles, sourceFiles, "site mirror file set differs from the canonical root");

  const mismatches = [];
  for (const path of sourceFiles) {
    const [sourceHash, publishedHash] = await Promise.all([
      sha256(path),
      sha256(`site/${path}`),
    ]);
    if (sourceHash !== publishedHash) mismatches.push({ path, sourceHash, publishedHash });
  }
  assert.deepEqual(mismatches, [], "site contains stale code or data");
});

test("manifest defines a stable relative standalone identity", async () => {
  const manifest = JSON.parse(await read("site/manifest.webmanifest"));
  assert.equal(manifest.id, "./");
  assert.equal(manifest.scope, "./");
  assert.equal(manifest.start_url, "./#home");
  assert.equal(manifest.display, "standalone");
  assert.deepEqual(manifest.display_override, ["standalone", "minimal-ui"]);
});

test("manifest exposes required icons, screenshots and five shortcuts", async () => {
  const manifest = JSON.parse(await read("site/manifest.webmanifest"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "192x192"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "512x512" && icon.purpose === "any"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "512x512" && icon.purpose === "maskable"));
  assert.equal(manifest.screenshots.length, 2);
  assert.equal(manifest.shortcuts.length, 5);
  assert.ok(manifest.shortcuts.every((shortcut) => shortcut.url.startsWith("./#")));
});

test("semantic index exactly matches the published catalogue", async () => {
  const [videos, semantic, binary] = await Promise.all([
    read("site/data/videos.json").then(JSON.parse),
    read("site/data/semantic-index.json").then(JSON.parse),
    readFile(new URL("../site/data/semantic-index.f32", import.meta.url)),
  ]);
  assert.equal(semantic.count, videos.length);
  assert.deepEqual(semantic.ids, videos.map((video) => video.id));
  assert.equal(binary.byteLength, videos.length * semantic.dimensions * Float32Array.BYTES_PER_ELEMENT);
  assert.equal(semantic.model, "Xenova/multilingual-e5-small");
  assert.equal(semantic.revision, "761b726dd34fb83930e26aab4e9ac3899aa1fa78");
});

test("HTML links the PWA surface with relative paths", async () => {
  const html = await read("site/index.html");
  assert.match(html, /rel="manifest"/);
  assert.match(html, /href="\.\/manifest\.webmanifest"/);
  assert.match(html, /navigator|pwa\.js/);
  assert.match(html, /id="install-app-button"/);
  assert.match(html, /id="install-help-dialog"/);
  assert.match(html, /apple-mobile-web-app-capable/);
});

test("public author credit uses a first name without a personal copyright claim", async () => {
  const siteConfig = JSON.parse(await read("site/data/site-config.json"));
  const [html, config, translations, standalone, license, packagedLicense, contentLicense] = await Promise.all([
    read("site/index.html"),
    read("site/data/site-config.json"),
    read("site/assets/js/i18n.js"),
    read(`site/downloads/${siteConfig.standalone_filename}`),
    read("LICENSE"),
    read("documentation/LICENSE.md"),
    read("documentation/COMMUNITY_CONTENT_LICENSE.md"),
  ]);
  for (const source of [html, config, translations, standalone, license, packagedLicense, contentLicense]) {
    assert.doesNotMatch(source, /אילן נחמן|Ilan Nachman/);
  }
  for (const source of [html, config, translations, standalone]) {
    assert.doesNotMatch(source, /nachman/i);
    assert.doesNotMatch(source, /mailto:/i);
  }
  assert.equal(siteConfig.contact, "");
  assert.equal(siteConfig.feedback_url, "https://github.com/galsec1999/adventure-riding-video-guide/issues/new");
  assert.match(html, /data-author-name="">אילן<\/span>\. התקצירים והסיווגים/);
  assert.doesNotMatch(html, /data-author-block="">©/);
  assert.match(html, /פרויקט קהילתי — קוד ורכיבים מקוריים בלבד/);
});

test("visit counter is canonical-only, transparent and has a visible failure fallback", async () => {
  const [html, app] = await Promise.all([
    read("site/index.html"),
    read("site/assets/js/app.js"),
  ]);
  assert.match(html, /מונה חיצוני סופר טעינות של האתר החי, לא אנשים ייחודיים/);
  assert.match(app, /galsec1999\.github\.io\/adventure-riding-video-guide\.svg/);
  assert.match(app, /image\.addEventListener\("error"/);
  assert.match(app, /Counter currently unavailable/);
});

test("install button only appears after beforeinstallprompt and success waits for appinstalled", async () => {
  const pwa = await read("site/assets/js/pwa.js");
  assert.match(pwa, /beforeinstallprompt/);
  assert.match(pwa, /event\.preventDefault\(\)/);
  assert.match(pwa, /appinstalled/);
  assert.match(pwa, /choice\.outcome !== "accepted"/);
  assert.doesNotMatch(pwa, /choice\.outcome === "accepted"[\s\S]{0,100}(success|הותקנה)/i);
});

test("service worker activates updates only after an explicit message", async () => {
  const [worker, config, manifest] = await Promise.all([
    read("site/service-worker.js"),
    read("site/data/site-config.json").then(JSON.parse),
    read("site/manifest.webmanifest").then(JSON.parse),
  ]);
  assert.equal(manifest.version, config.release_version);
  assert.ok(worker.includes(`adventure-guide-v${config.release_version}`));
  assert.match(worker, /event\.data\?\.type === "SKIP_WAITING"/);
  assert.doesNotMatch(worker, /addEventListener\("install"[\s\S]{0,180}skipWaiting/);
  assert.match(worker, /clients\.claim/);
});

test("service worker keeps external YouTube traffic out of its cache", async () => {
  const worker = await read("site/service-worker.js");
  assert.match(worker, /url\.origin !== self\.location\.origin/);
  assert.doesNotMatch(worker, /youtube(?:-nocookie)?\.com|googlevideo\.com/);
});

test("offline video playback renders a friendly message instead of an iframe", async () => {
  const app = await read("site/assets/js/app.js");
  assert.match(app, /if \(!navigator\.onLine\)/);
  assert.match(app, /video-player-slot__offline/);
  assert.match(app, /requires an internet connection/);
});
