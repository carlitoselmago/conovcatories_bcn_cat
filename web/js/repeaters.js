(() => {
  const CSV_URL = "data/persistence_by_year_pct.csv";

  let rawData = [];
  let chart = null;

  const COLORS = [
    "#FFFFA2", // new applicants
    "#FFB700",
    "#DD8100",
    "#DA6900",
    "#CE0700"
  ];

  /* ---------- LOAD DATA ---------- */

  function loadCSV() {
    return fetch(CSV_URL)
      .then(r => r.text())
      .then(text =>
        new Promise(resolve => {
          Papa.parse(text, {
            header: true,
            dynamicTyping: true,
            complete: res => resolve(res.data || [])
          });
        })
      );
  }

  /* ---------- HELPERS ---------- */

  function getInstitutions(data) {
    return [...new Set(data.map(d => d.institution))];
  }

  function getYears(data) {
    return [...new Set(data.map(d => d.year))]
      .filter(y => y != null)
      .sort((a, b) => a - b);
  }

  function buildDatasets(data, years) {
    const streaks = [...new Set(data.map(d => d.streak))]
      .filter(s => s != null)
      .sort((a, b) => a - b);

    return streaks.map((streak, i) => ({
      label: streak === 1 ? "New applicants" : `${streak} consecutive years`,
      data: years.map(year => {
        const r = data.find(d => d.year === year && d.streak === streak);
        return r ? r.pct : 0;
      }),
      backgroundColor: COLORS[i % COLORS.length],
      stack: "persistence"
    }));
  }

  function buildSankeyData(data) {
  const years = getYears(data);
  const links = [];

  for (let i = 0; i < years.length - 1; i++) {
    const y0 = years[i];
    const y1 = years[i + 1];

    const current = data.filter(d => d.year === y0);
    const next = data.filter(d => d.year === y1);

    current.forEach(d => {
      const from = `${y0} – streak ${d.streak}`;

      const target = next.find(
        n => n.streak === d.streak + 1
      );

      if (!target) return;

      const to = `${y1} – streak ${target.streak}`;

      links.push({
        from,
        to,
        flow: d.pct
      });
    });
  }

  return links;
}


  /* ---------- CHART ---------- */

  function createChart(data) {
    const years = getYears(data);
    const datasets = buildDatasets(data, years);

    const ctx = document.getElementById("persistenceChart");
    if (!ctx) {
      console.warn("[persistence_chart] canvas #persistenceChart not found");
      return;
    }

    chart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: years,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label(ctx) {
                return `${ctx.dataset.label}: ${ctx.raw.toFixed(1)}%`;
              }
            }
          },
          legend: {
            position: "right"
          }
        },
        scales: {
          x: {
            stacked: true,
            ticks: { color: "#aaa" }
          },
          y: {
            stacked: true,
            max: 100,
            ticks: {
              color: "#aaa",
              callback: v => v + "%"
            },
            title: {
              display: true,
              text: "Share of applicants (%)"
            }
          }
        }
      }
    });
  }

  function updateChart(institution) {
    if (!chart) return;

    const filtered = rawData.filter(d => d.institution === institution);
    const years = getYears(filtered);

    chart.data.labels = years;
    chart.data.datasets = buildDatasets(filtered, years);
    chart.update();
  }

  /* ---------- INIT ---------- */

  async function init() {
    rawData = (await loadCSV()).filter(
      d => d.year != null && d.institution != null
    );

    const select = document.getElementById("institutionFilter");
    if (!select) {
      console.warn("[persistence_chart] select #institutionFilter not found");
      return;
    }

    const institutions = getInstitutions(rawData);
    institutions.forEach(inst => {
      const opt = document.createElement("option");
      opt.value = inst;
      opt.textContent = inst;
      select.appendChild(opt);
    });

    const initial = institutions.includes("Total")
      ? "Total"
      : institutions[0];

    select.value = initial;
    createChart(rawData.filter(d => d.institution === initial));

    select.addEventListener("change", e => {
      updateChart(e.target.value);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
