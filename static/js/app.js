document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (event) => {
      if (!window.confirm(el.dataset.confirm || "Are you sure?")) event.preventDefault();
    });
  });
  document.querySelectorAll("input, textarea, select").forEach((el) => {
    if (!el.classList.contains("no-style")) el.classList.add("control");
  });
});
