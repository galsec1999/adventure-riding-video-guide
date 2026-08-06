// PWA release 3.1.0 — app shell, Shorts and local semantic runtime.
const CACHE_PREFIX = "adventure-guide-";
const CACHE_NAME = "adventure-guide-v3.1.0-20260806d";
const BASE_URL = new URL("./", self.registration.scope);
const APP_SHELL = [
  "./",
  "./index.html",
  "./offline.html",
  "./manifest.webmanifest",
  "./assets/css/styles.css?v=3.1.0-20260806d",
  "./assets/js/app.js?v=3.1.0-20260806d",
  "./assets/js/i18n.js",
  "./assets/js/pagination.js",
  "./assets/js/pwa.js",
  "./assets/js/search.js",
  "./assets/js/semantic-worker.js?v=3.1.0-20260806d",
  "./assets/js/storage.js",
  "./assets/vendor/transformers.min.js",
  "./assets/vendor/ort-wasm-simd-threaded.mjs",
  "./assets/vendor/ort-wasm-simd-threaded.wasm",
  "./assets/img/adventure-guide-mark.svg",
  "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png",
  "./assets/icons/icon-maskable-512.png",
  "./assets/icons/apple-touch-icon.png",
  "./assets/icons/favicon-32.png",
  "./data/categories.json?v=3.1.0-20260806c",
  "./data/learning-paths.json?v=3.1.0-20260806c",
  "./data/semantic-index.f32?v=3.1.0-20260806c",
  "./data/semantic-index.json?v=3.1.0-20260806c",
  "./data/shorts.json?v=3.1.0-20260806c",
  "./data/site-config.json?v=3.1.0-20260806c",
  "./data/synonyms.json?v=3.1.0-20260806c",
  "./data/travel-guides.json?v=3.1.0-20260806c",
  "./data/videos.json?v=3.1.0-20260806c"
].map((path) => new URL(path, BASE_URL).href);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

async function networkFirst(request, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackUrl) return (await caches.match(fallbackUrl)) || new Response("Offline", { status: 503, statusText: "Offline" });
    return new Response("Offline", { status: 503, statusText: "Offline" });
  }
}

async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const refresh = fetch(request).then(async (response) => {
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, response.clone());
    }
    return response;
  }).catch(() => null);
  if (cached) {
    refresh.catch(() => null);
    return cached;
  }
  return (await refresh) || new Response("Offline", { status: 503, statusText: "Offline" });
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.includes("/downloads/")) return;
  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, new URL("./index.html", BASE_URL).href));
    return;
  }
  if (url.pathname.endsWith(".json") || url.pathname.endsWith(".webmanifest")) {
    event.respondWith(networkFirst(event.request));
    return;
  }
  event.respondWith(cacheFirst(event.request));
});
