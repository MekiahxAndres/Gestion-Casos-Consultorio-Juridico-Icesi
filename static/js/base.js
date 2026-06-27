function toggleDropdown() {
    const menu = document.getElementById("userDropdown");
    if (!menu) return;
    menu.classList.toggle("open");
}

document.addEventListener("click", function (event) {
    const trigger = document.querySelector(".user-trigger");
    const menu = document.getElementById("userDropdown");

    if (!menu || !trigger) return;

    if (!trigger.contains(event.target) && !menu.contains(event.target)) {
        menu.classList.remove("open");
    }
});

(function () {
    let loadingTimer = null;
    let activeRequests = 0;

    function getOverlay() {
        return document.getElementById("globalLoadingOverlay");
    }

    window.showGlobalLoading = function () {
        const overlay = getOverlay();
        if (!overlay) return;

        window.clearTimeout(loadingTimer);
        loadingTimer = window.setTimeout(function () {
            overlay.classList.add("is-visible");
            overlay.setAttribute("aria-hidden", "false");
        }, 120);
    };

    window.hideGlobalLoading = function () {
        const overlay = getOverlay();
        if (!overlay) return;

        window.clearTimeout(loadingTimer);
        overlay.classList.remove("is-visible");
        overlay.setAttribute("aria-hidden", "true");
    };

    function shouldShowForLink(link, event) {
        if (!link || !link.href) return false;
        if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
        if (link.target && link.target !== "_self") return false;
        if (link.hasAttribute("download")) return false;
        if (link.getAttribute("href").startsWith("#")) return false;
        if (link.dataset.noLoading === "true") return false;

        const url = new URL(link.href, window.location.href);
        return url.origin === window.location.origin && url.href !== window.location.href + "#";
    }

    document.addEventListener("click", function (event) {
        const link = event.target.closest("a");
        if (shouldShowForLink(link, event)) {
            window.showGlobalLoading();
        }
    });

    document.addEventListener("submit", function (event) {
        const form = event.target;
        if (form && form.dataset.noLoading !== "true") {
            window.showGlobalLoading();
        }
    });

    if (window.fetch) {
        const originalFetch = window.fetch.bind(window);
        window.fetch = function (input, init) {
            const options = init || {};
            const skipGlobalLoading = options.skipGlobalLoading === true;
            if (skipGlobalLoading) {
                delete options.skipGlobalLoading;
            }

            if (!skipGlobalLoading) {
                activeRequests += 1;
                window.showGlobalLoading();
            }

            return originalFetch.call(window, input, options).finally(function () {
                if (skipGlobalLoading) return;
                activeRequests = Math.max(0, activeRequests - 1);
                if (activeRequests === 0) {
                    window.hideGlobalLoading();
                }
            });
        };
    }

    window.addEventListener("pageshow", function () {
        activeRequests = 0;
        window.hideGlobalLoading();
    });
})();
