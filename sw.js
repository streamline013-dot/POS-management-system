/* Print Shop POS — service worker (v39.2.0)
   - Installable and usable offline.
   - The page and app-config.js are network-first, so a new deploy or config shows up on the next open.
   - Icons, logo, and fonts are cache-first.
   - The Firebase SDK files (versioned URLs on www.gstatic.com) are cached so the login works offline
     after the first visit. Data, sign-in, Google Drive, and Gemini requests are never cached. */
const CACHE = 'printshop-pos-v39.2.0';
const SDK = 'printshop-sdk';
const CORE = [
  './',
  './app-config.js',
  './manifest.webmanifest',
  './favicon.ico',
  './favicon-32.png',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './apple-touch-icon.png',
  './logo.png',
  './fonts/inter-var-latin.woff2',
  './fonts/inter-var-latin-ext.woff2'
];

self.addEventListener('install', (event) => {
  // one by one, so a single missing file never stops the install
  event.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(CORE.map((u) => c.add(u).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== SDK).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const networkFirst = (req, key) =>
  fetch(req)
    .then((res) => {
      if (res && res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(key || req, copy));
      }
      return res;
    })
    .catch(() => caches.match(key || req).then((r) => r || caches.match(req)));

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Firebase SDK modules: immutable per version → cache first
  if (url.origin === 'https://www.gstatic.com' && url.pathname.startsWith('/firebasejs/')) {
    event.respondWith(
      caches.open(SDK).then((c) =>
        c.match(req).then((hit) =>
          hit ||
          fetch(req).then((res) => {
            if (res && res.ok) c.put(req, res.clone());
            return res;
          })
        )
      )
    );
    return;
  }
  if (url.origin !== self.location.origin) return; // sign-in, database, Drive, Gemini: straight to the network

  const isPage = req.mode === 'navigate' || url.pathname === '/' || url.pathname.endsWith('.html');
  if (isPage) {
    event.respondWith(networkFirst(req, './'));
    return;
  }
  if (url.pathname.endsWith('/app-config.js')) {
    event.respondWith(networkFirst(req, './app-config.js'));
    return;
  }

  // static files: cache first, then network (and keep it for next time). The optional
  // Appearance fonts are not pre-cached; each is kept here the first time it is used.
  event.respondWith(
    caches.match(req).then((hit) =>
      hit ||
      fetch(req).then((res) => {
        if (res && res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      })
    )
  );
});
