(function () {
    "use strict";

    const INSTALL_DISMISSED_KEY = "minhaRotinaInstallDismissed";

    function isStandalone() {
        return (
            window.matchMedia("(display-mode: standalone)").matches
            || window.navigator.standalone === true
        );
    }


    function isIOS() {
        return (
            /iphone|ipad|ipod/i.test(window.navigator.userAgent)
            && !window.MSStream
        );
    }


    function registerServiceWorker() {
        if (!("serviceWorker" in navigator)) {
            return;
        }

        window.addEventListener("load", function () {
            navigator.serviceWorker
                .register("/service-worker.js", {
                    scope: "/"
                })
                .catch(function (error) {
                    console.error(
                        "Falha ao registrar o Service Worker:",
                        error
                    );
                });
        });
    }


    function setupInstallExperience() {
        let deferredPrompt = null;

        const banner = document.getElementById(
            "pwa-install-banner"
        );

        const installButton = document.getElementById(
            "pwa-install-button"
        );

        const closeButton = document.getElementById(
            "pwa-install-close"
        );

        const iosHelp = document.getElementById(
            "pwa-ios-help"
        );

        const iosClose = document.getElementById(
            "pwa-ios-close"
        );

        if (isStandalone()) {
            return;
        }

        const wasDismissed = (
            window.sessionStorage.getItem(
                INSTALL_DISMISSED_KEY
            ) === "1"
        );

        if (isIOS() && iosHelp && !wasDismissed) {
            setTimeout(function () {
                iosHelp.classList.remove("d-none");
            }, 1400);
        }

        window.addEventListener(
            "beforeinstallprompt",
            function (event) {
                event.preventDefault();
                deferredPrompt = event;

                if (
                    banner
                    && !wasDismissed
                ) {
                    setTimeout(function () {
                        banner.classList.remove("d-none");
                    }, 900);
                }
            }
        );


        if (installButton) {
            installButton.addEventListener(
                "click",
                async function () {
                    if (!deferredPrompt) {
                        return;
                    }

                    deferredPrompt.prompt();

                    try {
                        await deferredPrompt.userChoice;
                    } finally {
                        deferredPrompt = null;
                        banner.classList.add("d-none");
                    }
                }
            );
        }


        if (closeButton) {
            closeButton.addEventListener(
                "click",
                function () {
                    window.sessionStorage.setItem(
                        INSTALL_DISMISSED_KEY,
                        "1"
                    );

                    banner.classList.add("d-none");
                }
            );
        }


        if (iosClose) {
            iosClose.addEventListener(
                "click",
                function () {
                    window.sessionStorage.setItem(
                        INSTALL_DISMISSED_KEY,
                        "1"
                    );

                    iosHelp.classList.add("d-none");
                }
            );
        }


        window.addEventListener(
            "appinstalled",
            function () {
                deferredPrompt = null;

                if (banner) {
                    banner.classList.add("d-none");
                }

                if (iosHelp) {
                    iosHelp.classList.add("d-none");
                }
            }
        );
    }


    function setupPasswordToggles() {
        document
            .querySelectorAll("[data-password-toggle]")
            .forEach(function (button) {
                const inputId = button.getAttribute(
                    "data-password-toggle"
                );

                const input = document.getElementById(
                    inputId
                );

                const icon = button.querySelector("i");

                if (!input || !icon) {
                    return;
                }

                button.addEventListener(
                    "click",
                    function () {
                        const showing = (
                            input.type === "text"
                        );

                        input.type = (
                            showing
                            ? "password"
                            : "text"
                        );

                        icon.classList.toggle(
                            "bi-eye",
                            showing
                        );

                        icon.classList.toggle(
                            "bi-eye-slash",
                            !showing
                        );

                        const label = (
                            showing
                            ? "Mostrar senha"
                            : "Ocultar senha"
                        );

                        button.setAttribute(
                            "aria-label",
                            label
                        );

                        button.setAttribute(
                            "title",
                            label
                        );

                        button.setAttribute(
                            "aria-pressed",
                            String(!showing)
                        );

                        input.focus();
                    }
                );
            });
    }


    registerServiceWorker();

    document.addEventListener(
        "DOMContentLoaded",
        function () {
            setupInstallExperience();
            setupPasswordToggles();
        }
    );
})();
