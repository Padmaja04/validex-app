const CACHE_NAME = 'attendance-pwa-v1.0.0';
const STATIC_CACHE_URLS = [
    '/',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static resources');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .catch((error) => {
                console.error('[SW] Cache failed:', error);
            })
    );
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    console.log('[SW] Serving from cache:', event.request.url);
                    return cachedResponse;
                }

                // Not in cache, fetch from network
                return fetch(event.request)
                    .then((response) => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone response (it can only be consumed once)
                        const responseToCache = response.clone();

                        // Cache successful responses
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // Network failed, try to serve offline page
                        if (event.request.destination === 'document') {
                            return caches.match('/') || new Response('Offline - Please check your connection');
                        }
                    });
            })
    );
});

// Background sync for offline attendance data
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);

    if (event.tag === 'attendance-sync') {
        event.waitUntil(syncAttendanceData());
    }
});

// Push notification handler
self.addEventListener('push', (event) => {
    console.log('[SW] Push received:', event);

    const options = {
        body: 'Don\'t forget to mark your attendance!',
        icon: '/static/icon-192.png',
        badge: '/static/icon-72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'check-in',
                title: 'Check In',
                icon: '/static/icon-72.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Attendance Reminder', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);

    event.notification.close();

    if (event.action === 'check-in') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Sync offline attendance data
async function syncAttendanceData() {
    try {
        console.log('[SW] Syncing offline attendance data...');

        // Get offline data from IndexedDB or localStorage
        const offlineData = await getOfflineAttendance();

        if (offlineData && offlineData.length > 0) {
            // Send to server
            const response = await fetch('/api/sync-attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(offlineData)
            });

            if (response.ok) {
                console.log('[SW] Attendance data synced successfully');
                await clearOfflineAttendance();
            }
        }
    } catch (error) {
        console.error('[SW] Sync failed:', error);
        throw error; // Let the browser retry
    }
}

async function getOfflineAttendance() {
    // Implementation to get offline data
    return [];
}

async function clearOfflineAttendance() {
    // Implementation to clear offline data after successful sync
    console.log('[SW] Offline attendance data cleared');
}