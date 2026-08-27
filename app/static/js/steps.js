// Record Steps page: calendar day selection + AJAX save
document.addEventListener("DOMContentLoaded", () => {
  const calendarCard = document.getElementById("calendarCard");
  if (!calendarCard) return;

  const entryPanel = document.getElementById("entryPanel");
  const entryDate = document.getElementById("entryDate");
  const stepsInput = document.getElementById("stepsInput");
  const stepsError = document.getElementById("stepsError");
  const saveBtn = document.getElementById("saveStepsBtn");
  const confirmationBox = document.getElementById("saveConfirmation");
  const noSelectionHint = document.getElementById("noSelectionHint");

  let selectedDay = null;

  function formatDateLabel(iso) {
    const d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  }

  function selectDay(dayEl) {
    document.querySelectorAll(".calendar-day.selected").forEach((el) => el.classList.remove("selected"));
    dayEl.classList.add("selected");
    selectedDay = dayEl;

    entryPanel.hidden = false;
    noSelectionHint.hidden = true;
    entryDate.textContent = formatDateLabel(dayEl.dataset.date);
    stepsInput.value = dayEl.dataset.steps || "";
    stepsError.hidden = true;
    confirmationBox.style.display = "none";
    stepsInput.focus();
  }

  calendarCard.querySelectorAll(".calendar-day").forEach((dayEl) => {
    dayEl.addEventListener("click", () => {
      if (dayEl.dataset.editable !== "true") return;
      selectDay(dayEl);
    });
  });

  saveBtn.addEventListener("click", async () => {
    if (!selectedDay) return;
    const rawValue = stepsInput.value.trim();
    stepsError.hidden = true;

    if (rawValue === "" || !/^\d+$/.test(rawValue)) {
      stepsError.textContent = "Please enter a whole, non-negative number.";
      stepsError.hidden = false;
      return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
      const resp = await fetch("/api/steps", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ date: selectedDay.dataset.date, steps: rawValue }),
      });
      const data = await resp.json();

      if (!resp.ok || !data.success) {
        stepsError.textContent = data.error || "Something went wrong. Please try again.";
        stepsError.hidden = false;
        return;
      }

      // Update the calendar cell immediately.
      selectedDay.dataset.steps = String(data.steps);
      selectedDay.classList.add("recorded");
      let stepsLabel = selectedDay.querySelector(".day-steps");
      if (!stepsLabel) {
        stepsLabel = document.createElement("span");
        stepsLabel.className = "day-steps";
        selectedDay.appendChild(stepsLabel);
      }
      stepsLabel.textContent = Number(data.steps).toLocaleString();

      // Update headline stats immediately.
      const totals = data.totals || {};
      const totalEl = document.getElementById("statTotalSteps");
      const avgEl = document.getElementById("statAvgActiveDay");
      const activeEl = document.getElementById("statActiveDays");
      if (totalEl) totalEl.textContent = Number(totals.total_steps || 0).toLocaleString();
      if (avgEl) avgEl.textContent = Number(totals.avg_per_active_day || 0).toLocaleString();
      if (activeEl) activeEl.textContent = totals.active_days || 0;

      confirmationBox.textContent = data.message || "Saved!";
      confirmationBox.style.display = "block";
    } catch (err) {
      stepsError.textContent = "Network error - please try again.";
      stepsError.hidden = false;
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save";
    }
  });
});
