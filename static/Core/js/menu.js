// منوی همبرگری موبایل: باز/بسته شدن با دکمه، بستن با کلیک بیرون، Escape و کلیک روی لینک
(function () {
    var btn = document.querySelector(".menu-toggle");
    var menu = document.querySelector(".site-menu");
    if (!btn || !menu) return;

    var header = document.querySelector(".site-header");
    function setOpen(open) {
        if (open && header) {
            menu.style.setProperty("--header-h", header.getBoundingClientRect().bottom + 5 + "px");
        }
        menu.classList.toggle("is-open", open);
        btn.setAttribute("aria-expanded", open ? "true" : "false");
    }

    btn.addEventListener("click", function (e) {
        e.stopPropagation();
        setOpen(!menu.classList.contains("is-open"));
    });
    document.addEventListener("click", function (e) {
        if (!menu.contains(e.target)) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { setOpen(false); btn.focus(); }
    });
    menu.addEventListener("click", function (e) {
        if (e.target.closest("a") || e.target.classList.contains("menu-backdrop")) setOpen(false);
    });
    window.addEventListener("resize", function () {
        if (window.innerWidth > 640) setOpen(false);
    });
})();
