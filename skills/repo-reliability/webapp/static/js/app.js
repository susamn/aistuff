"use strict";
let DATA = [];
let SELECTED = new Set(); // dataset ids currently checked for bulk delete
const PALETTE = ["#6b7fd7","#5dbb8f","#e0a35c","#d76b6b","#9a6bd7","#5cc2e0","#8a8880"];
const app = document.getElementById("app");
const crumb = document.getElementById("crumb");
let view = { name: "projects", proj: null };

function bandBadge(b) { return `<span class="badge b-${b}">${b}</span>`; }
function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function fmt(v) { return typeof v === "number" ? v.toLocaleString() : esc(v); }

function svg(w, h) {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", `0 0 ${w} ${h}`); s.setAttribute("width", w);
  return s;
}
function el(s, tag, attrs, text) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  s.appendChild(e); return e;
}
const AXIS = "var(--muted)", GRID = "var(--line)";

function barChart(data, color) {
  const W = 780, H = 220, L = 46, B = 40, max = Math.max(1, ...data.map(d => d.value));
  const s = svg(W, H), bw = (W - L - 10) / data.length;
  [0, .5, 1].forEach(f => {
    const y = H - B - f * (H - B - 14);
    el(s, "line", { x1: L, y1: y, x2: W - 4, y2: y, stroke: GRID, "stroke-width": 1 });
    el(s, "text", { x: L - 6, y: y + 4, "text-anchor": "end", "font-size": 11, fill: AXIS }, Math.round(max * f).toLocaleString());
  });
  data.forEach((d, i) => {
    const h = (d.value / max) * (H - B - 14);
    el(s, "rect", { x: L + i * bw + 2, y: H - B - h, width: Math.max(2, bw - 4), height: Math.max(1, h), rx: 2, fill: color || PALETTE[0] });
    if (data.length <= 16 || i % Math.ceil(data.length / 12) === 0)
      el(s, "text", { x: L + i * bw + bw / 2, y: H - B + 14, "text-anchor": "middle", "font-size": 10, fill: AXIS }, String(d.label).slice(0, 8));
  });
  return s;
}

function lineChart(series) {
  const labels = [...new Set(series.flatMap(sr => sr.points.map(p => p.label)))].sort();
  const W = 780, H = 240, L = 46, B = 40;
  const max = Math.max(1, ...series.flatMap(sr => sr.points.map(p => p.value)));
  const s = svg(W, H);
  const x = i => L + (labels.length < 2 ? 0 : i * (W - L - 12) / (labels.length - 1));
  const y = v => H - B - (v / max) * (H - B - 16);
  [0, .5, 1].forEach(f => {
    el(s, "line", { x1: L, y1: y(max * f), x2: W - 4, y2: y(max * f), stroke: GRID });
    el(s, "text", { x: L - 6, y: y(max * f) + 4, "text-anchor": "end", "font-size": 11, fill: AXIS }, Math.round(max * f).toLocaleString());
  });
  labels.forEach((lb, i) => {
    if (labels.length <= 14 || i % Math.ceil(labels.length / 10) === 0)
      el(s, "text", { x: x(i), y: H - B + 14, "text-anchor": "middle", "font-size": 10, fill: AXIS }, lb);
  });
  series.forEach((sr, si) => {
    const m = new Map(sr.points.map(p => [p.label, p.value]));
    const pts = labels.map((lb, i) => m.has(lb) ? `${x(i)},${y(m.get(lb))}` : null).filter(Boolean);
    el(s, "polyline", { points: pts.join(" "), fill: "none", stroke: PALETTE[si % PALETTE.length], "stroke-width": 2 });
  });
  const wrap = document.createElement("div");
  wrap.appendChild(s);
  wrap.insertAdjacentHTML("beforeend", `<div class="legend">${series.map((sr, i) =>
    `<span><i style="background:${PALETTE[i % PALETTE.length]}"></i>${esc(sr.name)}</span>`).join("")}</div>`);
  return wrap;
}

function scatterChart(v) {
  const W = 780, H = 260, L = 52, B = 44;
  const xs = v.data.map(p => p.x), ys = v.data.map(p => p.y);
  const mx = Math.max(1, ...xs), my = Math.max(1, ...ys);
  const s = svg(W, H);
  const X = x => L + Math.sqrt(x / mx) * (W - L - 14);
  const Y = y => H - B - (y / my) * (H - B - 16);
  [0, .5, 1].forEach(f => {
    el(s, "line", { x1: L, y1: Y(my * f), x2: W - 4, y2: Y(my * f), stroke: GRID });
    el(s, "text", { x: L - 6, y: Y(my * f) + 4, "text-anchor": "end", "font-size": 11, fill: AXIS }, Math.round(my * f));
  });
  [.25, 1].forEach(f => el(s, "text", { x: X(mx * f), y: H - B + 16, "text-anchor": "middle", "font-size": 10, fill: AXIS }, Math.round(mx * f).toLocaleString()));
  v.data.forEach(p => {
    const c = el(s, "circle", { cx: X(p.x), cy: Y(p.y), r: 4, fill: PALETTE[0], "fill-opacity": .55 });
    el(c, "title", {}, `${p.label || ""} (${p.x.toLocaleString()}, ${p.y})`);
  });
  if (v.axes) el(s, "text", { x: W / 2, y: H - 6, "text-anchor": "middle", "font-size": 11, fill: AXIS }, `${v.axes.x} (sqrt scale) vs ${v.axes.y}`);
  return s;
}

function stackedBar(v) {
  const W = 780, H = 250, L = 46, B = 44, labels = v.labels, series = v.series;
  const totals = labels.map((_, i) => series.reduce((a, sr) => a + (sr.values[i] || 0), 0));
  const max = Math.max(1, ...totals);
  const s = svg(W, H), bw = (W - L - 10) / labels.length;
  [0, .5, 1].forEach(f => {
    const y = H - B - f * (H - B - 14);
    el(s, "line", { x1: L, y1: y, x2: W - 4, y2: y, stroke: GRID });
    el(s, "text", { x: L - 6, y: y + 4, "text-anchor": "end", "font-size": 11, fill: AXIS }, Math.round(max * f).toLocaleString());
  });
  labels.forEach((lb, i) => {
    let acc = 0;
    series.forEach((sr, si) => {
      const val = sr.values[i] || 0;
      if (!val) return;
      const h = (val / max) * (H - B - 14);
      const yAcc = (acc / max) * (H - B - 14);
      el(s, "rect", { x: L + i * bw + 2, y: H - B - yAcc - h, width: Math.max(2, bw - 4), height: Math.max(1, h), fill: PALETTE[si % PALETTE.length] });
      acc += val;
    });
    if (labels.length <= 14 || i % Math.ceil(labels.length / 10) === 0)
      el(s, "text", { x: L + i * bw + bw / 2, y: H - B + 14, "text-anchor": "middle", "font-size": 10, fill: AXIS }, lb);
  });
  const wrap = document.createElement("div");
  wrap.appendChild(s);
  wrap.insertAdjacentHTML("beforeend", `<div class="legend">${series.map((sr, i) =>
    `<span><i style="background:${PALETTE[i % PALETTE.length]}"></i>${esc(sr.name)}</span>`).join("")}</div>`);
  return wrap;
}

function tableVis(v) {
  const t = document.createElement("table");
  t.innerHTML = `<thead><tr>${v.columns.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead>` +
    `<tbody>${v.rows.map(r => `<tr>${r.map(c =>
      `<td class="${typeof c === "number" ? "num" : ""}">${fmt(c)}</td>`).join("")}</tr>`).join("")}</tbody>`;
  return t;
}

function checklistVis(v) {
  const d = document.createElement("div");
  d.innerHTML = v.items.map(it =>
    `<div style="padding:4px 0"><span style="color:${it.ok ? "var(--healthy)" : "var(--critical)"}">${it.ok ? "✓" : "✗"}</span>
     ${esc(it.label)} ${it.note ? `<span class="conf">— ${esc(it.note)}</span>` : ""}</div>`).join("");
  return d;
}

function renderVisual(v) {
  switch (v.type) {
    case "histogram": return barChart(v.data);
    case "line": return lineChart(v.series);
    case "scatter": return scatterChart(v);
    case "stacked-bar": return stackedBar(v);
    case "table": return tableVis(v);
    case "checklist": return checklistVis(v);
    default: return document.createTextNode("");
  }
}

function bandColor(b) { return `var(--${b === "unknown" ? "unknown" : b})`; }

// Deletes go straight through mosaic's generic per-item route — one file per
// project (data/<id>.json), matching manifest.json's dataset ids. No write-back
// to manifest.json (mosaic has no write endpoint, by design); loadData()
// already skips any manifest entry whose file 404s, so a stale reference left
// behind by a delete is harmless and self-heals on next full reload.
async function deleteDataset(id) {
  const res = await fetch(`data/${id}.json`, { method: "DELETE" });
  if (!res.ok) throw new Error(`delete failed (${res.status})`);
}

async function bulkDelete(ids) {
  const results = await Promise.allSettled(ids.map(deleteDataset));
  const succeeded = ids.filter((_, i) => results[i].status === "fulfilled");
  DATA = DATA.filter(b => !succeeded.includes(b._datasetId));
  succeeded.forEach(id => SELECTED.delete(id));
  renderProjects();
  const failed = ids.length - succeeded.length;
  if (failed) alert(`${failed} of ${ids.length} report(s) could not be deleted.`);
}

function renderProjects() {
  crumb.textContent = "";
  if (!DATA.length) { app.innerHTML = `<div class="empty">No projects analyzed yet. Run the skill against a repo to populate this report.</div>`; return; }
  app.innerHTML = "";

  if (SELECTED.size) {
    const bar = document.createElement("div");
    bar.className = "bulk-bar";
    bar.innerHTML = `<span class="count">${SELECTED.size} selected</span>
      <button class="bulk-delete-btn">Delete selected</button>
      <button class="bulk-clear-btn">Clear</button>`;
    bar.querySelector(".bulk-clear-btn").onclick = () => { SELECTED.clear(); renderProjects(); };
    bar.querySelector(".bulk-delete-btn").onclick = () => {
      const ids = [...SELECTED];
      if (!confirm(`Delete ${ids.length} project report(s)? This cannot be undone.`)) return;
      bulkDelete(ids);
    };
    app.appendChild(bar);
  }

  DATA.forEach((b, i) => {
    const p = b.project;
    const row = document.createElement("div");
    row.className = "card projrow";
    row.innerHTML = `<input type="checkbox" class="sel-box" title="Select for bulk delete" ${SELECTED.has(b._datasetId) ? "checked" : ""}>
      <div class="pname">${esc(p.name)}</div>
      <div class="pmeta">${p.commits.toLocaleString()} commits · ${p.contributors} contributors · ${p.age_years} yrs</div>
      <div class="pmeta">analyzed ${esc(p.analyzed_at)}</div>${bandBadge(b.overall_band)}
      <button class="del-btn" title="Delete this report">&times;</button>`;
    row.onclick = () => { view = { name: "dash", proj: i }; render(); };
    row.querySelector(".sel-box").onclick = e => {
      e.stopPropagation();
      if (e.target.checked) SELECTED.add(b._datasetId); else SELECTED.delete(b._datasetId);
      renderProjects();
    };
    row.querySelector(".del-btn").onclick = async e => {
      e.stopPropagation();
      if (!confirm(`Delete the report for "${p.name}"? This cannot be undone.`)) return;
      try {
        await deleteDataset(b._datasetId);
        DATA = DATA.filter(x => x !== b);
        SELECTED.delete(b._datasetId);
        renderProjects();
      } catch (err) {
        alert(`Could not delete: ${err.message}`);
      }
    };
    app.appendChild(row);
  });
}

function renderDash() {
  const b = DATA[view.proj], p = b.project;
  crumb.innerHTML = `← all projects`;
  crumb.onclick = () => { view = { name: "projects" }; render(); };
  app.innerHTML = "";
  const head = document.createElement("div");
  head.className = "card phead";
  head.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap">
      <div><div style="font-size:18px;font-weight:650">${esc(p.name)}</div>
      <div class="remote">${esc(p.remote || "(local repository)")}</div></div>
      <div>${bandBadge(b.overall_band)}</div></div>
    <div class="chips">
      <span class="chip">age ${p.age_years} yrs</span>
      <span class="chip">${p.commits.toLocaleString()} commits</span>
      <span class="chip">${p.contributors} contributors</span>
      <span class="chip">branch ${esc(p.branch)}</span>
      <span class="chip">analyzed ${esc(p.analyzed_at)}</span></div>`;
  app.appendChild(head);
  const grid = document.createElement("div");
  grid.className = "grid";
  b.pointers.forEach(pt => {
    const c = document.createElement("div");
    c.className = "card pcard";
    const s = pt.summary;
    const max = Math.max(1, ...(s.series || []).map(d => d.value));
    c.innerHTML = `<div class="top"><div class="pname">${esc(pt.name)}</div>${bandBadge(s.band)}</div>
      <div class="val">${s.value === null ? "—" : fmt(s.value)}<small>${esc(s.unit)}</small></div>
      <div class="mini">${(s.series || []).slice(0, 24).map(d =>
        `<div style="height:${Math.max(4, 100 * d.value / max)}%;background:${bandColor(s.band)};opacity:.75" title="${esc(d.label)}: ${d.value}"></div>`).join("")}</div>
      <div class="ev">${esc(s.evidence)} <span class="conf">· confidence: ${esc(pt.confidence)}</span></div>`;
    c.onclick = () => openDetail(pt);
    grid.appendChild(c);
  });
  app.appendChild(grid);
}

function openDetail(pt) {
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.onclick = e => { if (e.target === ov) ov.remove(); };
  const panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML = `<span class="close" title="close">×</span>
    <h2>${esc(pt.name)} ${bandBadge(pt.summary.band)}</h2>
    <div class="sub">${esc(pt.category)} · source: ${esc(pt.source)} · window ${esc(pt.window.from)} → ${esc(pt.window.to)} · confidence ${esc(pt.confidence)}</div>
    <div class="narrative">${esc(pt.detail.narrative)}</div>`;
  panel.querySelector(".close").onclick = () => ov.remove();
  pt.detail.visuals.forEach(v => {
    const d = document.createElement("div");
    d.className = "vis";
    d.innerHTML = `<h3>${esc(v.title)}</h3>`;
    d.appendChild(renderVisual(v));
    panel.appendChild(d);
  });
  ov.appendChild(panel);
  document.body.appendChild(ov);
}

function render() { view.name === "projects" ? renderProjects() : renderDash(); }
document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelector(".overlay")?.remove(); });

async function loadData() {
  let manifest = { datasets: [] };
  try {
    const r = await fetch("data/manifest.json");
    if (r.ok) manifest = await r.json();
  } catch (e) { /* no data yet — render the empty state */ }
  const bundles = await Promise.all((manifest.datasets || []).map(async d => {
    try {
      const r = await fetch(`data/${d.id}.json`);
      if (!r.ok) return null;
      const bundle = await r.json();
      bundle._datasetId = d.id;
      return bundle;
    } catch (e) { return null; }
  }));
  DATA = bundles.filter(Boolean).sort((a, b) => a.project.name.toLowerCase().localeCompare(b.project.name.toLowerCase()));
  render();
}
loadData();
