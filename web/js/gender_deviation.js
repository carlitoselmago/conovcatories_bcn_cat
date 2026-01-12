(() => {
  // ---- CONFIG ----

  let genderMetric = "absolute"; // "absolute" | "fairness"
  const genderFiles = [
    { id: "Barcelona Crea", url: "data/desv_genero_barcelona_crea.csv", color: "#ff6b6b" },
    { id: "CLT019", url: "data/desv_genero_CLT019.csv", color: "#4dabf7" },
    { id: "Moniques", url: "data/desv_genero_moniques.csv", color: "#51cf66" }
  ];

  let genderRaw = {};
  let genderChart = null;
  let genderMode = "total"; // "total" or "mixed"

  // ---- LOAD CSVs ----
  async function loadGenderCSVs() {
    const results = await Promise.all(
      genderFiles.map(async f => {
        const text = await fetch(f.url).then(r => r.text());
        return new Promise(resolve => {
          Papa.parse(text, {
            header: true,
            dynamicTyping: true,
            complete: res => resolve({ id: f.id, data: res.data })
          });
        });
      })
    );

    results.forEach(r => {
      genderRaw[r.id] = (r.data || []).filter(d => d.year != null);
    });
  }

  // ---- HELPERS ----
  function getAllGenderYears() {
    const years = new Set();
    Object.values(genderRaw).forEach(rows =>
      rows.forEach(r => years.add(Number(r.year)))
    );
    return [...years].sort((a, b) => a - b);
  }

  function getRow(instId, year) {
    return (genderRaw[instId] || []).find(d => Number(d.year) === year) || null;
  }

  function getDeviationFromRow(r) {
    if (!r) return { devCand: 0, devWin: 0 };

    // ---- FAIRNESS MODE ----
    if (genderMetric === "fairness") {
      const maleCand = Number(r.male_cand || 0);
      const femaleCand = Number(r.female_cand || 0);
      const maleWin = Number(r.male_win || 0);
      const femaleWin = Number(r.female_win || 0);

      const maleRate = maleCand > 0 ? maleWin / maleCand : 0;
      const femaleRate = femaleCand > 0 ? femaleWin / femaleCand : 0;

      return {
        devCand: maleRate - femaleRate,
        devWin: maleRate - femaleRate
      };
    }

    // ---- ABSOLUTE MODE ----
    if (r.desviacion_cand != null && r.desviacion_win != null) {
      return {
        devCand: Number(r.desviacion_cand),
        devWin: Number(r.desviacion_win)
      };
    }

    return {
      devCand: Number(r.male_cand || 0) - Number(r.female_cand || 0),
      devWin: Number(r.male_win || 0) - Number(r.female_win || 0)
    };
  }

  function getYearDeviationTotal(year) {
    let devCand = 0;
    let devWin = 0;

    genderFiles.forEach(f => {
      const r = getRow(f.id, year);
      const d = getDeviationFromRow(r);
      devCand += d.devCand;
      devWin += d.devWin;
    });

    return { devCand, devWin };
  }

  // ---- DATASETS ----
  function buildGenderDatasets(years) {
    const datasets = [];

    function addInstitution(inst) {
      const devWin = years.map(y =>
        getDeviationFromRow(getRow(inst.id, y)).devWin
      );

      // ---- FAIRNESS MODE: ONE LINE ----
      if (genderMetric === "fairness") {
        datasets.push({
          label: [inst.id, "paridad ganadoras"],
          data: devWin,
          borderColor: inst.color,
          tension: 0.2,
          pointRadius: 0,
          borderWidth:12
        });
        return;
      }

      // ---- ABSOLUTE MODE: TWO LINES ----
      const devCand = years.map(y =>
        getDeviationFromRow(getRow(inst.id, y)).devCand
      );

      datasets.push({
        label: [inst.id, "Candidates"],
        data: devCand,
        borderColor: inst.color,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 12
      });

      datasets.push({
        label: [inst.id, "Ganadores"],
        data: devWin,
        borderColor: inst.color,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 4,
        borderDash: [6, 6]
      });
    }

    // ---- TOTAL MODE ----
    if (genderMode === "total") {
      const devWin = years.map(y => getYearDeviationTotal(y).devWin);

      if (genderMetric === "fairness") {
        datasets.push({
          label: ["Total", "paridad ganadoras"],
          data: devWin,
         borderColor: "#282828",
          tension: 0.2,
          pointRadius: 0,
          borderWidth: 12
        });
        return datasets;
      }

      datasets.push({
        label: ["Total", "Candidatas"],
        data: years.map(y => getYearDeviationTotal(y).devCand),
        borderColor: "#282828",
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 10
      });

      datasets.push({
        label: ["Total", "Ganadoras"],
        data: devWin,
        borderColor: "#999",
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 4,
        borderDash: [6, 6]
      });

      return datasets;
    }

    // ---- MIXED MODE ----
    genderFiles.forEach(addInstitution);
    return datasets;
  }

  // ---- 0 LINE PLUGIN ----
  const parityZeroLine = {
    id: "parityZeroLine",
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!chartArea) return;

      const y = scales.y.getPixelForValue(0);

      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([2, 2]);
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#343434ff";
      ctx.moveTo(chartArea.left, y);
      ctx.lineTo(chartArea.right, y);
      ctx.stroke();
      ctx.restore();
    }
  };

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
    ctx.fillText("Valores por encima de 0 = Sesgo masculino", x, y);
    y += 16;
    ctx.fillText("Valores por debajo de 0 = Sesgo femenino", x, y);
    ctx.restore();
  }
};

  // ---- CHART ----
  function createGenderChart(years) {
    const canvas = document.getElementById("genderChart");
    if (!canvas) return;

    genderChart = new Chart(canvas, {
      type: "line",
   
      data: {
        labels: years,
        datasets: buildGenderDatasets(years)
      },
options: {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "nearest", intersect: false },

  plugins: {
    legend: {
        align:'end',
      labels: {
      
        font: {
          size: 12,        // try 11–13
          lineHeight: 1  // important for multiline labels
        }
      }
    },

    tooltip: {
      displayColors: false,
      callbacks: {
        title(items) {
          return `Año ${items[0].label}`;
        }
      }
    }
  },

  scales: {
    x: { ticks: { color: "#aaa" } },
    y: {
      title: {
        display: true,
        text:
          genderMetric === "fairness"
            ? "Win-rate parity deviation (male − female)"
            : "Deviación de paridad (0 = paridad)"
      }
    }
  }
}
,
      plugins: [parityZeroLine,areaMeaningLegend]
    });
  }

  function updateGenderChart(years) {
    if (!genderChart) return;
    genderChart.data.labels = years;
    genderChart.data.datasets = buildGenderDatasets(years);
    genderChart.update();
  }

  // ---- INIT ----
  async function initGender() {
    await loadGenderCSVs();
    const years = getAllGenderYears();
    createGenderChart(years);

    const sel = document.getElementById("genderMode");
    if (sel) {
      sel.value = genderMode;
      sel.addEventListener("change", e => {
        genderMode = e.target.value;
        updateGenderChart(years);
      });
    }

    const metricSel = document.getElementById("genderMetric");
    if (metricSel) {
      metricSel.value = genderMetric;
      metricSel.addEventListener("change", e => {
        genderMetric = e.target.value;
        updateGenderChart(years);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGender);
  } else {
    initGender();
  }
})();
