/* IFT Web Push service worker. Receives push events and shows notifications. */
self.addEventListener('push', function (event) {
    let data = {};
    try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }
    const title = data.title || "India's Future Tycoons";
    const options = {
        body: data.body || '',
        icon: data.icon || '/static/images/email_logo.png',
        badge: '/static/images/email_logo.png',
        data: { url: data.url || '/' },
        tag: data.tag || undefined,
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
            for (const client of list) {
                if ('focus' in client) { client.navigate(url); return client.focus(); }
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});
