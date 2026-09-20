/* Mindily 서비스 워커
 * 목적: 홈 화면에 설치해 앱처럼 열고, 화면 껍데기는 오프라인에서도 뜨게 한다.
 * 원칙:
 *  - /api/* 응답은 절대 캐시하지 않는다. 감정 분석 결과와 일기 관련 응답은 항상 서버에서 받는다.
 *  - 캐시에는 화면 자원(HTML·CSS·JS·아이콘)만 담는다.
 *  - 버전을 올리면 이전 캐시는 즉시 삭제된다.
 */
const VERSION = 'mindily-r20260920events2';
const SHELL = [
  './',
  'index.html',
  'manifest.webmanifest',
  'icon-192.png',
  'icon-512.png',
  'icon-maskable-512.png',
  'apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(VERSION)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;      // 폰트 등 외부 자원은 그대로 통과
  if (url.pathname.startsWith('/api/')) return;         // 분석·일기 관련 응답은 캐시 금지

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put('index.html', copy)).catch(() => {});
          return response;
        })
        .catch(() => caches.match('index.html').then((hit) => hit || caches.match('./')))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((hit) => {
      if (hit) {
        fetch(request)
          .then((fresh) => caches.open(VERSION).then((cache) => cache.put(request, fresh)))
          .catch(() => {});
        return hit;
      }
      return fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copy)).catch(() => {});
          return response;
        })
        .catch(() => hit);
    })
  );
});
