(function () {
    "use strict";

    // زیردستهٔ فرم محصول فقط از دستهٔ انتخاب‌شده پر می‌شود
    var mapEl = document.getElementById("subcategory-map");
    var category = document.getElementById("id_category");
    var sub = document.getElementById("id_subcategory");
    if (mapEl && category && sub) {
        var map = JSON.parse(mapEl.textContent);
        var emptyLabel = sub.options.length ? sub.options[0].text : "بدون زیردسته";
        var fill = function (selected) {
            sub.innerHTML = "";
            var blank = document.createElement("option");
            blank.value = "";
            blank.textContent = emptyLabel;
            sub.appendChild(blank);
            (map[category.value] || []).forEach(function (item) {
                var option = document.createElement("option");
                option.value = item.id;
                option.textContent = item.name;
                if (String(item.id) === String(selected)) { option.selected = true; }
                sub.appendChild(option);
            });
        };
        category.addEventListener("change", function () { fill(""); });
        fill(sub.value);
    }

    // پیش‌نمایش آدرس (اسلاگ) هنگام ساخت محصول جدید
    var source = document.getElementById("id_name");
    var out = document.querySelector("[data-slug-out]");
    if (source && out) {
        var timer;
        source.addEventListener("input", function () {
            clearTimeout(timer);
            timer = setTimeout(function () {
                fetch(out.dataset.url + "?text=" + encodeURIComponent(source.value), { credentials: "same-origin" })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        out.textContent = data.slug ? out.dataset.prefix + data.slug + "/" : "—";
                    })
                    .catch(function () {});
            }, 250);
        });
    }
})();
