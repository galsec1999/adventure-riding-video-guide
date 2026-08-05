import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("manifest defines a stable relative standalone identity", async () => {
  const manifest = JSON.parse(await read("site/manifest.webmanifest"));
  assert.equal(manifest.id, "./");
  assert.equal(manifest.scope, "./");
  assert.equal(manifest.start_url, "./#home");
  assert.equal(manifest.display, "standalone");
  assert.deepEqual(manifest.display_override, ["standalone", "minimal-ui"]);
});

test("manifest exposes required icons, screenshots and four shortcuts", async () => {
  const manifest = JSON.parse(await read("site/manifest.webmanifest"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "192x192"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "512x512" && icon.purpose === "any"));
  assert.ok(manifest.icons.some((icon) => icon.sizes === "512x512" && icon.purpose === "maskable"));
  assert.equal(manifest.screenshots.length, 2);
  assert.equal(manifest.shortcuts.length, 4);
  assert.ok(manifest.shortcuts.every((shortcut) => shortcut.url.startsWith("./#")));
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
  const [html, config, translations, standalone, license, packagedLicense, contentLicense] = await Promise.all([
    read("site/index.html"),
    read("site/data/site-config.json"),
    read("site/assets/js/i18n.js"),
    read("site/downloads/Adventure-Riding-Video-Guide-v2.3.1-Standalone.html"),
    read("LICENSE"),
    read("documentation/LICENSE.md"),
    read("documentation/COMMUNITY_CONTENT_LICENSE.md"),
  ]);
  for (const source of [html, config, translations, standalone, license, packagedLicense, contentLicense]) {
    assert.doesNotMatch(source, /אילן נחמן|Ilan Nachman/);
  }
  assert.match(html, /data-author-name="">אילן<\/span>\. התקצירים והסיווגים/);
  assert.doesNotMatch(html, /data-author-block="">©/);
  assert.match(html, /פרויקט קהילתי — קוד ורכיבים מקוריים בלבד/);
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
  const worker = await read("site/service-worker.js");
  assert.match(worker, /adventure-guide-v2\.3\.1/);
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
