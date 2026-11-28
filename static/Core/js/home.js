// صفحهٔ اصلی: «مشاهده محصولات» محصولات را همین‌جا زیر بنر باز می‌کند و تا آنجا اسکرول می‌کند.
(function () {
    var section = document.getElementById("catalog");
    if (!section) return;

    function reveal(scroll) {
        if (section.hidden) {
            section.hidden = false;
            section.classList.add("is-revealed");
        }
        if (scroll) {
            var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            section.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
        }
    }

    // دکمهٔ بنر و لینک «مشاهده کاتالوگ» منو (وقتی از قبل در صفحهٔ اصلی هستیم)
    document.addEventListener("click", function (e) {
        var link = e.target.closest("a");
        if (!link) return;
        var url;
        try { url = new URL(link.href, location.href); } catch (err) { return; }
        if (url.origin === location.origin && url.pathname === location.pathname && url.hash === "#catalog") {
            e.preventDefault();
            reveal(true);
            history.replaceState(null, "", "#catalog");
        }
    });

    // دکمه‌های دسته: کلیک = باز شدن زیردسته‌ها/محصولات همان دسته (فقط یکی باز است)؛ کلیک دوباره = بستن
    var cards = section.querySelectorAll(".cat-card");
    function setPanel(card, open, scroll) {
        var panel = document.getElementById(card.getAttribute("aria-controls"));
        card.setAttribute("aria-expanded", open ? "true" : "false");
        card.classList.toggle("is-active", open);
        if (panel) {
            panel.hidden = !open;
            if (open) {
                panel.classList.remove("is-revealed"); void panel.offsetWidth; panel.classList.add("is-revealed");
                if (scroll) {
                    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
                    panel.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
                }
            }
        }
    }
    Array.prototype.forEach.call(cards, function (card) {
        card.addEventListener("click", function () {
            var willOpen = card.getAttribute("aria-expanded") !== "true";
            Array.prototype.forEach.call(cards, function (other) { if (other !== card) setPanel(other, false); });
            setPanel(card, willOpen, willOpen);
        });
    });

    // ورود مستقیم با آدرس …/#catalog (مثلاً از صفحهٔ محصول)
    if (location.hash === "#catalog") reveal(true);
    window.addEventListener("hashchange", function () {
        if (location.hash === "#catalog") reveal(true);
    });
})();
