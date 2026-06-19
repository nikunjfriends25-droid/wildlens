/* WildLens Service Worker
   Strategy:
   - news.json       → network-first  (always fresh data)
   - app shell       → stale-while-revalidate
   - CDN assets      → cache-first
   - navigation miss → offline.html
*/
const CACHE = 'wildlens-v3';

const PRECACHE = [
  '/',
  '/index.html',
  '/style.css',
  '/map.js',
  '/regional/',
  '/regional/index.html',
  '/regional/style.css',
  '/regional/map.js',
  '/app/',
  '/app/index.html',
  '/app/style.css',
  '/app/map.js',
  '/app/regional/',
  '/app/regional/index.html',
  '/app/regional/map.js',
  '/offline.html',
  '/manifest.json',
  '/india_boundary.geojson',
];

// ── Install ───────────────────────────────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache =>
      cache.addAll(PRECACHE).catch(err => console.warn('[SW] Precache partial:', err))
    )
  );
  self.skipWaiting();
});

// ── Activate: delete old caches ───────────────────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  const { request } = e;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (!url.protocol.startsWith('http')) return;

  // news.json → network-first, cache as fallback
  if (url.pathname.endsWith('news.json')) {
    e.respondWith(
      fetch(request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then(c => c.put(request, clone));
          }
          return res;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // External CDN (Leaflet, fonts, tiles) → cache-first
  if (url.hostname !== self.location.hostname) {
    e.respondWith(
      caches.match(request).then(cached =>
        cached || fetch(request).then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then(c => c.put(request, clone));
          }
          return res;
        })
      )
    );
    return;
  }

  // App shell → stale-while-revalidate with offline fallback
  e.respondWith(
    caches.match(request).then(cached => {
      const fetchFresh = fetch(request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(request, clone));
        }
        return res;
      }).catch(() => null);

      if (cached) {
        fetchFresh.catch(() => {});
        return cached;
      }

      return fetchFresh.then(res => {
        if (res) return res;
        if (request.mode === 'navigate') return caches.match('/offline.html');
      });
    })
  );
});
