{% load static %}
const CACHE_VERSION = "rotina-conecta-v9";
const STATIC_CACHE = `${CACHE_VERSION}-static`;

const APP_SHELL = [
    "{% url 'offline' %}",
    "{% static 'css/app.css' %}?v=20260924-delivery",
    "{% static 'js/app.js' %}",
    "{% static 'manifest.webmanifest' %}",
    "{% static 'img/icons/app-icon-180.png' %}",
    "{% static 'img/icons/app-icon-192.png' %}",
    "{% static 'img/icons/app-icon-512.png' %}",
    "{% static 'img/icons/app-icon-maskable-192.png' %}",
    "{% static 'img/icons/app-icon-maskable-512.png' %}"
];


self.addEventListener("install", function (event) {
    event.waitUntil(
        caches
            .open(STATIC_CACHE)
            .then(function (cache) {
                return cache.addAll(APP_SHELL);
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});


self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches
            .keys()
            .then(function (keys) {
                return Promise.all(
                    keys
                        .filter(function (key) {
                            return (
                                (
                                    key.startsWith("rotina-conecta-")
                                    || key.startsWith("minha-rotina-")
                                )
                                && key !== STATIC_CACHE
                            );
                        })
                        .map(function (key) {
                            return caches.delete(key);
                        })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});


self.addEventListener("fetch", function (event) {
    const request = event.request;

    if (request.method !== "GET") {
        return;
    }

    const url = new URL(request.url);

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request).catch(function () {
                return caches.match("{% url 'offline' %}");
            })
        );
        return;
    }

    if (url.origin === self.location.origin) {
        const isStaticAsset = (
            url.pathname.startsWith("/static/")
            || url.pathname === "/manifest.webmanifest"
        );

        if (isStaticAsset) {
            event.respondWith(
                fetch(request)
                    .then(function (response) {
                        const copy = response.clone();

                        caches
                            .open(STATIC_CACHE)
                            .then(function (cache) {
                                cache.put(request, copy);
                            });

                        return response;
                    })
                    .catch(function () {
                        return caches.match(request);
                    })
            );
        }
    }
});
