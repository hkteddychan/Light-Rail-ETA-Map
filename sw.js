/* LRT ETA service worker — shell cache-first, data network-first w/ offline fallback */
const SHELL = "lrt-v1";
const SHELL_FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (e) => {
  const url = e.request.url;
  // Data files (ETA + geojson): network-first, fall back to cache when offline
  if (url.includes("lrt_eta_data.json") || url.includes("stations.geojson")) {
    e.respondWith(
      fetch(e.request).then((res) => {
        const clone = res.clone();
        caches.open(SHELL).then((c) => c.put(e.request, clone));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  // Everything else (shell): cache-first
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});