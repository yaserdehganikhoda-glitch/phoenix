// نام و نسخه‌ی کش — با هر تغییر مهم در فایل‌ها این عدد را افزایش دهید
// تا Service Worker کش قدیمی را کنار بگذارد و نسخه‌ی جدید را نصب کند
const CACHE_VERSION = 'v1';
const CACHE_NAME = 'naghavi-shift-calc-' + CACHE_VERSION;

// فایل‌های اصلی برنامه که باید برای اجرای کامل آفلاین کش شوند
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg'
];

// نصب: کش کردن فایل‌های اصلی برنامه
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// فعال‌سازی: پاک کردن نسخه‌های قدیمی کش
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith('naghavi-shift-calc-') && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// دریافت درخواست‌ها: استراتژی "ابتدا کش، سپس شبکه" برای پایداری کامل آفلاین
self.addEventListener('fetch', (event) => {
  // فقط درخواست‌های GET همین دامنه را مدیریت کن
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request)
        .then((networkResponse) => {
          // پاسخ معتبر را برای استفاده‌ی آفلاین بعدی هم کش کن
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return networkResponse;
        })
        .catch(() => {
          // اگر هم شبکه و هم کش برای این درخواست در دسترس نبود
          // و درخواست برای یک صفحه‌ی HTML بود، صفحه‌ی اصلی را برگردان
          if (event.request.mode === 'navigate') {
            return caches.match('./index.html');
          }
        });
    })
  );
});
