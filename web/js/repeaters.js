(() => {
  const CSV_URL = "data/persistence_by_year_pct.csv";

  const svg = d3.select("#streamgraph");
  const container = svg.node().parentNode;

  const margin = { top: 30, right: 20, bottom: 30, left: 50 };

  let width = 0;
  let height = 0;
  let innerWidth = 0;
  let innerHeight = 0;

  const g = svg.append("g");

  const COLORS = [
    "#CFF2E6",
    "#6FD3B0",
    "#2FA37A",
    "#1E7F5D",
    "#0E4F3A"
  ];

  let rawData = [];
  let currentInstitution = null;


  /* ---------- LOAD CSV ---------- */

  function loadCSV() {
    return fetch(CSV_URL)
      .then(r => r.text())
      .then(
        text =>
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

  function resize() {
    const rect = container.getBoundingClientRect();

    width = rect.width;
    height = rect.height;

    innerWidth = width - margin.left - margin.right;
    innerHeight = height - margin.top - margin.bottom;

    svg
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "none");

    g.attr("transform", `translate(${margin.left},${margin.top})`);

    if (currentInstitution) {
      draw(currentInstitution);
    }
  }


  function getInstitutions(data) {
    return [...new Set(data.map(d => d.institution))];
  }

  function getYears(data) {
    return [...new Set(data.map(d => d.year))]
      .filter(y => y != null)
      .sort((a, b) => a - b);
  }

  function getStreaks(data) {
    return [...new Set(data.map(d => d.streak))]
      .filter(s => s != null)
      .sort((a, b) => a - b);
  }

  /* ---------- BUILD STREAM DATA ---------- */

  function buildStreamData(data) {
    const years = getYears(data);
    const streaks = getStreaks(data);

    return years.map(year => {
      const row = { year };
      streaks.forEach(streak => {
        const r = data.find(
          d => d.year === year && d.streak === streak
        );
        row[`streak_${streak}`] = r ? r.pct : 0;
      });
      return row;
    });
  }

  /* ---------- DRAW ---------- */

  function draw(institution) {
    g.selectAll("*").remove();

    const filtered = rawData.filter(
      d => d.institution === institution
    );

    const years = getYears(filtered);
    const streaks = getStreaks(filtered);
    const data = buildStreamData(filtered);

    const keys = streaks.map(s => `streak_${s}`);

    const stack = d3
      .stack()
      .keys(keys)
  .offset(d3.stackOffsetNone)

    const series = stack(data);

    const x = d3
      .scaleLinear()
      .domain(d3.extent(years))
      .range([0, innerWidth]);
const xGrid = d3
  .axisBottom(x)
  .ticks(years.length)
  .tickSize(-innerHeight)
  .tickFormat("");
    const y = d3
      .scaleLinear()
      .domain([
        d3.min(series, s => d3.min(s, d => d[0])),
        d3.max(series, s => d3.max(s, d => d[1]))
      ])
      .range([innerHeight, 0]);

    const color = d3
      .scaleOrdinal()
      .domain(keys)
      .range(COLORS);

    const area = d3
      .area()
      .x(d => x(d.data.year))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveCatmullRom.alpha(0.5));

    g.selectAll("path")
      .data(series)
      .join("path")
      .attr("d", area)
      .attr("fill", d => color(d.key))
      .attr("opacity", 0.9);

    /* ---------- AXES ---------- */
g.append("g")
  .attr("class", "x-grid")
  .attr("transform", `translate(0,${innerHeight})`)
  .call(xGrid)
  .call(g =>
    g.selectAll("line")
      .attr("stroke", "#000")
      .attr("stroke-opacity", 0.2)
      .attr("stroke-dasharray", "2,4")
  )
  .call(g => g.select(".domain").remove());
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(years.length)
          .tickFormat(d3.format("d"))
      );
g.append("text")
  .attr("class", "y-label")
  .attr("transform", "rotate(-90)")
  .attr("x", -innerHeight / 2)
  .attr("y", -margin.left-6 + 15)
  .attr("text-anchor", "middle")
  .attr("fill", "#444")
  .style("font-size", "12px")
  .text("Porcentaje de participantes");
  
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d}%`));
  }


  /* ---------- INIT ---------- */

  async function init() {
    rawData = (await loadCSV()).filter(
      d =>
        d.year != null &&
        d.institution != null &&
        d.streak != null
    );

    const select = document.getElementById("institutionFilter");
    const institutions = getInstitutions(rawData);

    institutions.forEach(inst => {
      const opt = document.createElement("option");
      opt.value = inst;
      opt.textContent = inst;
      select.appendChild(opt);
    });

    currentInstitution = institutions.includes("Total")
      ? "Total"
      : institutions[0];

    select.value = currentInstitution;

    resize();               // 👈 first layout
    draw(currentInstitution);

    select.addEventListener("change", e => {
      currentInstitution = e.target.value;
      draw(currentInstitution);
    });

    window.addEventListener("resize", resize);
  }

  init();
})();


