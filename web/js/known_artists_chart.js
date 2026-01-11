(() => {

const institutions = [
  {
    id: "Barcelona Crea",
    canvas: "known-barcelona",
    url: "data/known_artists_barcelona_crea.csv",
    color: "#ff6b6b"
  },
  {
    id: "CLT019",
    canvas: "known-clt019",
    url: "data/known_artists_CLT019.csv",
    color: "#4dabf7"
  },
  {
    id: "Moniques",
    canvas: "known-moniques",
    url: "data/known_artists_moniques.csv",
    color: "#51cf66"
  }
];

/* ---------- LOAD CSV ---------- */

async function loadCSV(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.warn(`[known_artists] Failed to load ${url}`);
      return [];
    }

    const text = await res.text();

    return await new Promise(resolve => {
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        complete: res => {
          if (!Array.isArray(res.data)) {
            console.warn(`[known_artists] Invalid CSV structure: ${url}`);
            resolve([]);
            return;
          }
          resolve(res.data.filter(d => d && d.year != null));
        },
        error: err => {
          console.warn(`[known_artists] Parse error in ${url}`, err);
          resolve([]);
        }
      });
    });
  } catch (err) {
    console.warn(`[known_artists] Error loading ${url}`, err);
    return [];
  }
}

/* ---------- CHART ---------- */

function createChart(inst, rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    console.warn(`[known_artists] No data for ${inst.id}`);
    return;
  }

  const canvas = document.getElementById(inst.canvas);
  if (!canvas) {
    console.warn(`[known_artists] Canvas #${inst.canvas} not found`);
    return;
  }

  const years = rows.map(r => r.year);

  const known = rows.map(r =>
    r.total_winners > 0
      ? (r.known_artists / r.total_winners) * 100
      : 0
  );

  const emerging = rows.map(r =>
    r.total_winners > 0
      ? 100 - (r.known_artists / r.total_winners) * 100
      : 0
  );

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: years,
      datasets: [
        {
          label: "Artistas emergentes",
          data: emerging,
          backgroundColor: inst.color + "55",
          stack: "share"
        },
        {
          label: "Artistas con trayectoria",
          data: known,
          backgroundColor: inst.color,
          stack: "share"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label(ctx) {
              const i = ctx.dataIndex;
              const total = known[i] + emerging[i];
              const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : "0.0";
              return `${ctx.dataset.label}: ${pct}%`;
            }
          }
        }
      },
      scales: {
        x: { stacked: true },
        y: {
          stacked: true,
          max: 100,
          ticks: { callback: v => v + "%" },
          title: {
            display: true,
            text: "Share of winners (%)"
          }
        }
      }
    }
  });
}

/* ---------- INIT ---------- */

(async function init() {
  for (const inst of institutions) {
    const rows = await loadCSV(inst.url);
    createChart(inst, rows);
  }
})();
})();
