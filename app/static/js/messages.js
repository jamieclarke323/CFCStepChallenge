// Confirm-before-submit for delete forms on the message board
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".confirm-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const message = form.dataset.confirm || "Are you sure?";
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
