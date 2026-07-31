/* Super admin dashboard — small conveniences only. */
(function () {
  "use strict";

  // Mobile sidebar
  var side = document.querySelector("[data-side]");
  var toggle = document.querySelector("[data-side-toggle]");
  if (side && toggle) {
    toggle.addEventListener("click", function () {
      side.classList.toggle("open");
    });
    document.addEventListener("click", function (e) {
      if (!side.classList.contains("open")) return;
      if (side.contains(e.target) || toggle.contains(e.target)) return;
      side.classList.remove("open");
    });
  }

  // Confirm destructive actions
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });

  // Live preview for image uploads
  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      if (!file || !/^image\//.test(file.type)) return;
      var field = input.closest(".field");
      if (!field) return;
      var preview = field.querySelector("[data-preview]");
      if (!preview) {
        preview = document.createElement("img");
        preview.className = "thumb";
        preview.setAttribute("data-preview", "");
        preview.style.marginTop = "10px";
        input.parentNode.appendChild(preview);
      }
      preview.src = URL.createObjectURL(file);
    });
  });

  // Add another inline row (metrics / gallery)
  document.querySelectorAll("[data-add-row]").forEach(function (button) {
    button.addEventListener("click", function () {
      var prefix = button.getAttribute("data-add-row");
      var container = document.querySelector('[data-rows="' + prefix + '"]');
      var totalInput = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
      var template = document.getElementById("empty-" + prefix);
      if (!container || !totalInput || !template) return;
      var index = parseInt(totalInput.value, 10);
      var html = template.innerHTML.replace(/__prefix__/g, index);
      var wrapper = document.createElement("div");
      wrapper.innerHTML = html;
      while (wrapper.firstChild) container.appendChild(wrapper.firstChild);
      totalInput.value = index + 1;
    });
  });
})();
