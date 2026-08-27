// Renders the "My Progress" daily steps chart using Chart.js
function initProgressChart(data) {
  const canvas = document.getElementById("dailyChart");
  if (!canvas || !window.Chart) return;

  const labels = data.daily.map((d) => d.date);
  const values = data.daily.map((d) => (d.steps === null ? null : d.steps));

  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Steps",
          data: values,
          borderColor: "#ff6b35",
          backgroundColor: "rgba(255, 107, 53, 0.15)",
          spanGaps: false,
          fill: true,
          tension: 0.25,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { maxTicksLimit: 8 },
        },
        y: {
          beginAtZero: true,
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => (ctx.parsed.y === null ? "No record" : `${ctx.parsed.y.toLocaleString()} steps`),
          },
        },
      },
    },
  });
}

// Renders the "My Team" daily total steps chart using Chart.js
function initTeamChart(data) {
  const canvas = document.getElementById("teamDailyChart");
  if (!canvas || !window.Chart) return;

  new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels: data.daily.map((d) => d.date),
      datasets: [
        {
          label: "Team steps",
          data: data.daily.map((d) => d.steps),
          backgroundColor: "#2ec4b6",
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: true },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y.toLocaleString()} steps`,
          },
        },
      },
    },
  });
}

// Auto-initialise from embedded JSON <script> tags - avoids any inline
// script execution so a strict Content-Security-Policy (script-src 'self')
// can be enforced.
document.addEventListener("DOMContentLoaded", () => {
  const progressEl = document.getElementById("chartData");
  if (progressEl) {
    initProgressChart(JSON.parse(progressEl.textContent));
  }
  const teamEl = document.getElementById("teamChartData");
  if (teamEl) {
    initTeamChart(JSON.parse(teamEl.textContent));
  }
});
