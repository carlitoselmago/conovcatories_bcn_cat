const files = [
   { id: "Moniques", url: "data/vista_general_moniques.csv", color: "#51cf66" },
  { id: "CLT019", url: "data/vista_general_CLT019.csv", color: "#4dabf7" },

   { id: "Barcelona Crea", url: "data/vista_general_barcelona_crea.csv", color: "#ff6b6b" }
];

let rawData = {};
let chart = null;
let mode = "mixed";

/* ---------- COLOR UTILS ---------- */

function darkenColor(hex, factor = 0.55) {
  const c = hex.replace("#", "");
  const num = parseInt(c, 16);
  let r = (num >> 16) & 255;
  let g = (num >> 8) & 255;
  let b = num & 255;
  r = Math.round(r * factor);
  g = Math.round(g * factor);
  b = Math.round(b * factor);
  return `rgb(${r}, ${g}, ${b})`;
}

/* ---------- LOAD CSVs ---------- */

async function loadCSVs() {
  const results = await Promise.all(
    files.map(async f => {
      try {
        const res = await fetch(f.url);
        if (!res.ok) return { id: f.id, data: [] };
        const text = await res.text();
        return new Promise(resolve => {
          Papa.parse(text, {
            header: true,
            dynamicTyping: true,
            complete: res => resolve({ id: f.id, data: res.data || [] })
          });
        });
      } catch {
        return { id: f.id, data: [] };
      }
    })
  );

  results.forEach(r => {
    rawData[r.id] = (r.data || [])
      .filter(d => d && d.year != null)
      .map(d => ({
        year: Number(d.year),
        winners: Number(d.winners ?? 0),
        not_winners: Number(d.not_winners ?? d.notWinners ?? 0)
      }));
  });
}

/* ---------- HELPERS ---------- */

function getAllYears() {
  const years = new Set();
  Object.values(rawData).forEach(rows => rows.forEach(r => years.add(r.year)));
  return [...years].sort((a, b) => a - b);
}

/* ---------- DATASETS ---------- */

function buildDatasets(years) {
  const datasets = [];

  function addInstitution(label, color, rows) {
    const byYear = {};
    rows.forEach(r => (byYear[r.year] = r));

    const nonWinners = years.map(y => byYear[y]?.not_winners ?? 0);
    const total = years.map(y =>
      byYear[y] ? byYear[y].winners + byYear[y].not_winners : 0
    );

const lightColor =
  label === "Total" ? "rgba(120,120,120,0.35)" : color + "55";

const darkColor =
  label === "Total" ? "rgb(90,90,90)" : darkenColor(color, 0.55);

    datasets.push({
      label,
      group: label,
      data: nonWinners,
      fill: true,
      backgroundColor: color + "55",
      borderColor: color,
      tension: 0.2,
      pointRadius: 0,
      borderWidth:0
    });

    datasets.push({
      label,
      group: label,
      data: total,
      fill: "-1",
      backgroundColor: darkColor,
      borderColor: "rgba(0,0,0,0)",
      tension: 0.2,
      pointRadius: 0
    });
  }

  // -------- MODE LOGIC --------

  if (mode === "total") {
    const summedByYear = {};

    years.forEach(y => {
      summedByYear[y] = { year: y, winners: 0, not_winners: 0 };

      files.forEach(f => {
        const row = rawData[f.id]?.find(r => r.year === y);
        if (!row) return;
        summedByYear[y].winners += row.winners;
        summedByYear[y].not_winners += row.not_winners;
      });
    });

    addInstitution(
      "Total",
      "#777",
      Object.values(summedByYear)
    );

  } else {
    // mixed
    files.forEach(f => {
      if (rawData[f.id]) addInstitution(f.id, f.color, rawData[f.id]);
    });
  }

  return datasets;
}


/* ---------- PLUGIN: AREA MEANING ---------- */

const areaMeaningLegend = {
  id: "areaMeaningLegend",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    if (!chartArea) return;

    ctx.save();
    ctx.font = "12px sans-serif";
    ctx.fillStyle = "#282828";
    const x = chartArea.left + 10;
    let y = chartArea.top + 18;
    ctx.fillText("Color claro: total candidatos", x, y);
    y += 16;
    ctx.fillText("Color oscuro: propuestas ganadoras", x, y);
    ctx.restore();
  }
};

/* ---------- CHART ---------- */

function createChart(years) {
  const el = document.getElementById("chart");
  if (!el || !years.length) return;

  chart = new Chart(el, {
    type: "line",
    data: {
      labels: years,
      datasets: buildDatasets(years)
    },
    options: {
      responsive: true,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: {
          labels: {
            generateLabels(chart) {
              const groups = {};
              chart.data.datasets.forEach((ds, i) => {
                if (!groups[ds.group]) {
                  groups[ds.group] = {
                    text: ds.group,
                    fillStyle: ds.borderColor,
                    strokeStyle: "rgba(0,0,0,0)", // 👈 NO BORDER
            lineWidth: 0,                 // 👈 NO BORDER
                    hidden: chart.isDatasetVisible(i) === false,
                    group: ds.group
                  };
                }
              });
              return Object.values(groups);
            }
          },
          onClick(e, legendItem, legend) {
            const group = legendItem.group;
            legend.chart.data.datasets.forEach((ds, i) => {
              if (ds.group === group) {
                const visible = legend.chart.isDatasetVisible(i);
                legend.chart.setDatasetVisibility(i, !visible);
              }
            });
            legend.chart.update();
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: "Participants" }
        }
      }
    },
    plugins: [areaMeaningLegend]
  });
}

/* ---------- INIT ---------- */

(async function init() {
  await loadCSVs();
  const years = getAllYears();
  createChart(years);

  const modeSelect = document.getElementById("modeFilter");
  if (modeSelect) {
    modeSelect.value = mode;
    modeSelect.addEventListener("change", e => {
      mode = e.target.value;
      chart.data.datasets = buildDatasets(years);
      chart.update();
    });
  }
})();