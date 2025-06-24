// Service Worker for Running Heatmap Mobile App
// Provides offline functionality and caching

const CACHE_NAME = 'running-heatmap-v1';
const STATIC_CACHE_NAME = 'running-heatmap-static-v1';
const DATA_CACHE_NAME = 'running-heatmap-data-v1';

// Files to cache for offline use
const STATIC_FILES = [
  './',
  './index.html',
  './js/spatial.js',
  'https://unpkg.com/maplibre-gl/dist/maplibre-gl.js',
  'https://unpkg.com/maplibre-gl/dist/maplibre-gl.css'
];

// Data files to cache
const DATA_FILES = [
  './data/runs.json',
  './data/spatial_index.json'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      }),
      // Cache data files
      caches.open(DATA_CACHE_NAME).then((cache) => {
        console.log('Service Worker: Caching data files');
        return cache.addAll(DATA_FILES);
      })
    ]).then(() => {
      console.log('Service Worker: Installation complete');
      self.skipWaiting();
    }).catch((error) => {
      console.error('Service Worker: Installation failed', error);
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE_NAME && 
              cacheName !== DATA_CACHE_NAME &&
              cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Activation complete');
      self.clients.claim();
    })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);
  
  // Handle data files (runs.json, spatial_index.json)
  if (requestUrl.pathname.includes('/data/')) {
    event.respondWith(
      caches.open(DATA_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            console.log('Service Worker: Serving data from cache', requestUrl.pathname);
            return response;
          }
          
          // Try to fetch and cache
          return fetch(event.request).then((response) => {
            if (response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          }).catch(() => {
            console.log('Service Worker: Failed to fetch data, offline mode');
            return new Response('Offline - data not available', { status: 503 });
          });
        });
      })
    );
    return;
  }
  
  // Handle static files
  if (STATIC_FILES.some(file => requestUrl.pathname.endsWith(file.replace('./', '')))) {
    event.respondWith(
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            console.log('Service Worker: Serving static file from cache', requestUrl.pathname);
            return response;
          }
          
          return fetch(event.request).then((response) => {
            if (response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          });
        });
      })
    );
    return;
  }
  
  // Handle map tiles - cache them for offline use
  if (requestUrl.hostname.includes('tile.openstreetmap.org') || 
      requestUrl.hostname.includes('tiles.')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            return response;
          }
          
          return fetch(event.request).then((response) => {
            if (response.status === 200) {
              // Cache map tiles for offline use
              cache.put(event.request, response.clone());
            }
            return response;
          }).catch(() => {
            // Return a placeholder tile when offline
            return new Response('', { status: 503 });
          });
        });
      })
    );
    return;
  }
  
  // Handle external CDN resources (MapLibre GL)
  if (requestUrl.hostname.includes('unpkg.com')) {
    event.respondWith(
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            return response;
          }
          
          return fetch(event.request).then((response) => {
            if (response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          });
        });
      })
    );
    return;
  }
  
  // Default: try network first, fall back to cache
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// Background sync for future data updates
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('Service Worker: Background sync triggered');
    // Could implement data sync logic here if needed
  }
});

// Push notifications (for future use)
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push message received');
  
  const options = {
    body: event.data ? event.data.text() : 'New run data available',
    icon: './icon-192.png',
    badge: './badge-72.png',
    tag: 'running-heatmap-notification'
  };
  
  event.waitUntil(
    self.registration.showNotification('Running Heatmap', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('./')
  );
});

// Message handler for communication with main app
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_STATUS') {
    // Return cache status
    Promise.all([
      caches.has(STATIC_CACHE_NAME),
      caches.has(DATA_CACHE_NAME)
    ]).then(([hasStatic, hasData]) => {
      event.ports[0].postMessage({
        type: 'CACHE_STATUS_RESPONSE',
        hasStatic,
        hasData,
        offline: !navigator.onLine
      });
    });
  }
});

// Error handler
self.addEventListener('error', (event) => {
  console.error('Service Worker: Error occurred', event.error);
});

console.log('Service Worker: Script loaded');