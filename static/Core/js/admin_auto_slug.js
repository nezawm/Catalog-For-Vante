/* پر شدن زندهٔ «اسلاگ» (انگلیسی) هنگام تایپ «نام» در ادمین.
   ترجمه سمت سرور انجام می‌شود (Core/slugs.py)، پس همیشه با اسلاگ ذخیره‌شده یکی است.
   - اگر ادمین خودش اسلاگ را دست بزند، دیگر خودکار عوض نمی‌شود (خالی کردنش دوباره خودکارش می‌کند).
   - در صفحهٔ ویرایش، اسلاگ موجود دست‌نخورده می‌ماند.
   - ردیف‌های زیردسته داخل صفحهٔ دسته‌بندی هم کار می‌کنند. */
(function () {
    "use strict";
    var endpoint = location.pathname.split("/admin/")[0] + "/admin/slugify/";
    var timers = {};

    function isName(el) { return el && el.tagName === "INPUT" && /(^|-)name$/.test(el.name || ""); }
    function isSlug(el) { return el && el.tagName === "INPUT" && /(^|-)slug$/.test(el.name || ""); }
    function slugFor(nameInput) { return document.getElementById(nameInput.id.replace(/name$/, "slug")); }

    // اسلاگی که از قبل مقدار دارد (صفحهٔ ویرایش) دستی حساب می‌شود
    function markExisting() {
        document.querySelectorAll("input[name$='slug']").forEach(function (el) {
            if (el.value && !el.closest(".empty-form")) { el.dataset.manual = "1"; }
        });
    }
    document.addEventListener("DOMContentLoaded", markExisting);

    document.addEventListener("input", function (e) {
        var el = e.target;
        if (isSlug(el)) {
            if (el.value === "") { delete el.dataset.manual; } else { el.dataset.manual = "1"; }
            return;
        }
        if (!isName(el)) { return; }
        var slug = slugFor(el);
        if (!slug || slug.dataset.manual === "1") { return; }
        clearTimeout(timers[el.id]);
        timers[el.id] = setTimeout(function () {
            var text = el.value;
            fetch(endpoint + "?text=" + encodeURIComponent(text), { credentials: "same-origin" })
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (data) {
                    if (data && el.value === text && slug.dataset.manual !== "1") { slug.value = data.slug; }
                })
                .catch(function () { /* بی‌صدا؛ اسلاگ هنگام ذخیره ساخته می‌شود */ });
        }, 200);
    });
})();
