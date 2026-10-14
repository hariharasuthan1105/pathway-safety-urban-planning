```javascript
(() => {
  "use strict";

  const sampleIncidents = [
    {
      id: 1,
      title: "Poor lighting near pedestrian crossing",
      location: "North bus stop",
      severity: 4,
      likelihood: 4,
      people: 3
    },
    {
      id: 2,
      title: "Damaged pavement on school route",
      location: "West residential lane",
      severity: 3,
      likelihood: 4,
      people: 4
    },
    {
      id: 3,
      title: "Blocked storm drain",
      location: "Market street",
      severity: 2,
      likelihood: 3,
      people: 2
    },
    {
      id: 4,
      title: "Missing guardrail beside road",
      location: "Riverside curve",
      severity: 5,
      likelihood: 3,
      people: 2
    }
  ];

  let incidents = sampleIncidents.map(item => ({ ...item }));
  let nextId = Math.max(...incidents.map(item => item.id)) + 1;

  const $ = id => document.getElementById(id);

  const impactLabels = {
    1: "1–5 people",
    2: "6–20 people",
    3: "21–50 people",
    4: "51–100 people",
    5: "More than 100 people"
  };

  // Educational model: score ranges from 1 to 125.
  function calculateScore(incident) {
    return incident.severity *
      incident.likelihood *
      incident.people;
  }

  function getPriority(score) {
    if (score >= 60) return "high";
    if (score >= 25) return "medium";
    return "low";
  }

  function titleCase(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  // Escape user-entered text before inserting it into HTML.
  function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[character]);
  }

  function render() {
    const filter = $("priority-filter").value;

    const ranked = incidents
      .map(item => ({
        ...item,
        score: calculateScore(item)
      }))
      .sort((a, b) => b.score - a.score || a.id - b.id);

    const visible = ranked.filter(item => {
      return filter === "all" ||
        getPriority(item.score) === filter;
    });

    // Update dashboard statistics.
    $("total-count").textContent = incidents.length;

    $("high-count").textContent = ranked.filter(item =>
      getPriority(item.score) === "high"
    ).length;

    const average = incidents.length
      ? Math.round(
          ranked.reduce((sum, item) => sum + item.score, 0) /
          incidents.length
        )
      : 0;

    $("average-score").textContent = average;

    // Render the ranked incident queue.
    $("incident-list").innerHTML = visible.map(item => {
      const priority = getPriority(item.score);
      const barWidth = (item.score / 125) * 100;

      return `
        <article class="incident-card">
          <div class="incident-top">
            <div class="incident-info">
              <h3>${escapeHTML(item.title)}</h3>
              <p>Location: ${escapeHTML(item.location)}</p>
            </div>

            <span class="priority-tag priority-${priority}">
              ${titleCase(priority)}
            </span>
          </div>

          <div class="score-row">
            <span class="score-number">
              ${item.score} <small>/ 125</small>
            </span>

            <div
              class="score-track"
              role="img"
              aria-label="Illustrative score ${item.score} out of 125"
            >
              <div
                class="score-fill ${priority}"
                style="width: ${barWidth}%"
              ></div>
            </div>

            <button
              class="remove-button"
              type="button"
              data-remove="${item.id}"
              aria-label="Remove ${escapeHTML(item.title)}"
            >
              Remove
            </button>
          </div>

          <div class="incident-meta">
            Severity: ${item.severity}/5 ·
            Likelihood: ${item.likelihood}/5 ·
            Impact: ${impactLabels[item.people]}
          </div>
        </article>
      `;
    }).join("");

    $("empty-state").hidden = visible.length > 0;
    $("incident-list").hidden = visible.length === 0;
  }

  // Add a new incident.
  $("incident-form").addEventListener("submit", event => {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    const title = String(form.get("title")).trim();
    const location = String(form.get("location")).trim();

    if (!title || !location) return;

    incidents.push({
      id: nextId++,
      title,
      location,
      severity: Number(form.get("severity")),
      likelihood: Number(form.get("likelihood")),
      people: Number(form.get("people"))
    });

    event.currentTarget.reset();

    // Restore the default form values.
    $("severity").value = "3";
    $("likelihood").value = "3";
    $("people").value = "3";
    $("priority-filter").value = "all";

    render();
    $("incident-title").focus();
  });

  // Filter the queue by priority.
  $("priority-filter").addEventListener("change", render);

  // Remove an incident using event delegation.
  $("incident-list").addEventListener("click", event => {
    const button = event.target.closest("[data-remove]");

    if (!button) return;

    const id = Number(button.dataset.remove);

    incidents = incidents.filter(item => item.id !== id);
    render();
  });

  // Restore the original example incidents.
  $("reset-button").addEventListener("click", () => {
    incidents = sampleIncidents.map(item => ({ ...item }));
    nextId = Math.max(...incidents.map(item => item.id)) + 1;
    $("priority-filter").value = "all";

    render();
  });

  // Export all current incidents as a CSV file.
  $("export-button").addEventListener("click", () => {
    const rows = [
      [
        "Title",
        "Location",
        "Severity",
        "Likelihood",
        "Impact Band",
        "Illustrative Score",
        "Priority"
      ]
    ];

    const ranked = incidents
      .map(item => ({
        ...item,
        score: calculateScore(item)
      }))
      .sort((a, b) => b.score - a.score);

    ranked.forEach(item => {
      rows.push([
        item.title,
        item.location,
        item.severity,
        item.likelihood,
        impactLabels[item.people],
        item.score,
        titleCase(getPriority(item.score))
      ]);
    });

    const csv = rows.map(row =>
      row.map(value =>
        `"${String(value).replace(/"/g, '""')}"`
      ).join(",")
    ).join("\r\n");

    const blob = new Blob(
      ["\uFEFF", csv],
      { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = "incident-triage-demo.csv";

    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(url);
  });

  // Display the sample queue when the page opens.
  render();
})();
```
