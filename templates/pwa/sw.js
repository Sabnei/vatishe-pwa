{% load static %}
// Service Worker de VATISHE (PWA). Cambia la versión para invalidar la caché.
const CACHE = "vatishe-v1";
const OFFLINE_URL = "/offline/";
const PRECACHE = [
  OFFLINE_URL,
  "{% static 'css/vatishe.css' %}",
  "{% static 'pwa/icon-192.png' %}",
  "{% static 'pwa/icon-512.png' %}",
  "{% static 'pwa/manifest.webmanifest' %}",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((claves) =>
      Promise.all(claves.filter((c) => c !== CACHE).map((c) => caches.delete(c)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Navegaciones: primero la red; si falla, la página offline.
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Estáticos: primero la caché; si no está, red y se cachea.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((hit) =>
        hit ||
        fetch(req).then((resp) => {
          const copia = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, copia));
          return resp;
        })
      )
    );
    return;
  }

  // Resto: red con respaldo en caché.
  event.respondWith(fetch(req).catch(() => caches.match(req)));
});
