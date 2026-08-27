// Account dropdown toggle + auto-dismiss flash messages
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("accountToggle");
  const dropdown = document.getElementById("accountDropdown");
  if (toggle && dropdown) {
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = !dropdown.hidden;
      dropdown.hidden = isOpen;
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });
    document.addEventListener("click", (e) => {
      if (!dropdown.hidden && !dropdown.contains(e.target)) {
        dropdown.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  const flashStack = document.getElementById("flashStack");
  if (flashStack) {
    setTimeout(() => {
      flashStack.style.transition = "opacity 0.4s ease";
      flashStack.style.opacity = "0";
      setTimeout(() => flashStack.remove(), 400);
    }, 4500);
  }
});

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}
