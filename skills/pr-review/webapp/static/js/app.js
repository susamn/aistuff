"use strict";
let MANIFEST = { datasets: [] };
let SELECTED = new Set(); // review ids currently checked for bulk delete
const app = document.getElementById("app");
const crumb = document.getElementById("crumb");
let view = { name: "list" };

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function badge(cls, text) { return `<span class="badge b-${esc(cls)}">${esc(text)}</span>`; }
function sevClass(s) { return s === "must-fix" ? "critical" : s === "should-fix" ? "warning" : "unknown"; }
function verdictClass(v) { return v === "APPROVE" ? "healthy" : v === "REQUEST_CHANGES" ? "critical" : v === "NEEDS_DISCUSSION" ? "warning" : "unknown"; }
function statusClass(s) { return s === "reviewed" ? "healthy" : (s === "in_progress" || s === "awaiting_verdict") ? "warning" : "unknown"; }

async function fetchJSON(path) {
  try { const r = await fetch(path); return r.ok ? await r.json() : null; }
  catch (e) { return null; }
}

// ── unified diff → per-file hunks/rows. Deterministic parsing only; no
//    inference happens here — the agent already picked side+line when it
//    wrote each finding, this just has to lay the same diff out visually. ──
function parseDiff(text) {
  const fileHeaderRe = /^diff --git a\/(.*) b\/(.*)$/;
  const hunkRe = /^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$/;
  const files = [];
  let cur = null, hunk = null, oldN = 0, newN = 0;
  for (const raw of text.split("\n")) {
    let m;
    if ((m = fileHeaderRe.exec(raw))) {
      cur = { oldPath: m[1], newPath: m[2], path: m[2] !== "/dev/null" ? m[2] : m[1], binary: false, hunks: [] };
      files.push(cur); hunk = null;
      continue;
    }
    if (!cur) continue;
    if (raw.startsWith("Binary files ")) { cur.binary = true; continue; }
    if ((m = hunkRe.exec(raw))) {
      oldN = parseInt(m[1], 10); newN = parseInt(m[3], 10);
      hunk = { header: m[5] || "", oldStart: oldN, newStart: newN, rows: [] };
      cur.hunks.push(hunk);
      continue;
    }
    if (!hunk) continue; // pre-hunk metadata: index/---/+++/mode lines
    if (raw.startsWith("\\")) continue; // "\ No newline at end of file"
    if (raw.startsWith("+")) {
      hunk.rows.push({ type: "add", newLine: newN++, content: raw.slice(1) });
    } else if (raw.startsWith("-")) {
      hunk.rows.push({ type: "del", oldLine: oldN++, content: raw.slice(1) });
    } else {
      hunk.rows.push({ type: "ctx", oldLine: oldN++, newLine: newN++, content: raw.startsWith(" ") ? raw.slice(1) : raw });
    }
  }
  return files;
}

function buildFindingsIndex(chunks) {
  const idx = {};
  chunks.forEach(c => (c.findings || []).forEach(f => {
    const key = `${f.file}|${f.side}|${f.line}`;
    (idx[key] = idx[key] || []).push(f);
  }));
  return idx;
}

// Findings render as a small inline marker on the line, not a full-width row
// — a row would push the opposite side of the diff down and break left/right
// alignment. Marker content (which findings it holds) lives in MARKER_STORE,
// looked up by id when the marker is clicked; see popup logic below.
let MARKER_STORE = {};
let MARKER_ID = 0;
function worstSeverity(hits) {
  if (hits.some(f => f.severity === "must-fix")) return "must-fix";
  if (hits.some(f => f.severity === "should-fix")) return "should-fix";
  return "suggestion";
}
function commentMarker(file, side, line, findingsIdx) {
  if (line == null) return "";
  const hits = findingsIdx[`${file.path}|${side}|${line}`];
  if (!hits) return "";
  const id = MARKER_ID++;
  MARKER_STORE[id] = hits;
  return `<span class="finding-marker sev-${sevClass(worstSeverity(hits))}" data-marker-id="${id}" title="${hits.length} finding(s) — click to view">${hits.length}</span>`;
}

function renderFileDiff(file, findingsIdx) {
  const wrap = document.createElement("div");
  wrap.className = "diff-file";

  let rowsHtml = "";
  let findingCount = 0;
  file.hunks.forEach(hunk => {
    rowsHtml += `<tr class="hunk-row"><td colspan="4">@@ -${hunk.oldStart} +${hunk.newStart} @@ ${esc(hunk.header)}</td></tr>`;
    hunk.rows.forEach(row => {
      const oldMarker = commentMarker(file, "LEFT", row.oldLine, findingsIdx);
      const newMarker = commentMarker(file, "RIGHT", row.newLine, findingsIdx);
      if (oldMarker) findingCount++;
      if (newMarker) findingCount++;
      if (row.type === "add") {
        rowsHtml += `<tr class="add-row">
          <td class="ln old"></td><td class="code old"></td>
          <td class="ln new">${row.newLine}</td><td class="code new">${esc(row.content)}${newMarker}</td>
        </tr>`;
      } else if (row.type === "del") {
        rowsHtml += `<tr class="del-row">
          <td class="ln old">${row.oldLine}</td><td class="code old">${esc(row.content)}${oldMarker}</td>
          <td class="ln new"></td><td class="code new"></td>
        </tr>`;
      } else {
        rowsHtml += `<tr class="ctx-row">
          <td class="ln old">${row.oldLine}</td><td class="code old">${esc(row.content)}${oldMarker}</td>
          <td class="ln new">${row.newLine}</td><td class="code new">${esc(row.content)}${newMarker}</td>
        </tr>`;
      }
    });
  });

  wrap.innerHTML = `<div class="diff-file-head">${esc(file.path)}${findingCount ? ` <span class="chip">${findingCount} finding(s)</span>` : ""}</div>`;

  if (file.binary) {
    wrap.insertAdjacentHTML("beforeend", `<div class="diff-binary">Binary file — no diff shown.</div>`);
    return wrap;
  }

  const table = document.createElement("table");
  table.className = "diff-table";
  table.innerHTML = `
    <colgroup><col class="ln"><col class="code"><col class="ln"><col class="code"></colgroup>
    <thead><tr><th colspan="2">Old</th><th colspan="2">New</th></tr></thead>
    <tbody>${rowsHtml}</tbody>`;
  wrap.appendChild(table);
  return wrap;
}

// ── finding popup: a single floating card, positioned next to whichever
//    marker was clicked, closed on outside click / Escape / re-click. ──────
const popup = document.createElement("div");
popup.className = "finding-popup";
popup.hidden = true;
document.body.appendChild(popup);

function closePopup() { popup.hidden = true; popup.dataset.markerId = ""; }
function openPopup(marker, hits) {
  popup.innerHTML = hits.map(f => `
    <div class="finding-popup-item">
      ${badge(sevClass(f.severity), f.severity)}${badge("cat", f.category)}
      <div class="comment-text">${esc(f.comment)}</div>
    </div>`).join("");
  popup.hidden = false;
  popup.dataset.markerId = marker.dataset.markerId;
  const r = marker.getBoundingClientRect();
  const top = r.bottom + window.scrollY + 6;
  const maxLeft = window.scrollX + document.documentElement.clientWidth - popup.offsetWidth - 12;
  const left = Math.max(window.scrollX + 8, Math.min(r.left + window.scrollX, maxLeft));
  popup.style.top = `${top}px`;
  popup.style.left = `${left}px`;
}
app.addEventListener("click", e => {
  const marker = e.target.closest(".finding-marker");
  if (!marker) return;
  e.stopPropagation();
  if (popup.dataset.markerId === marker.dataset.markerId && !popup.hidden) { closePopup(); return; }
  openPopup(marker, MARKER_STORE[marker.dataset.markerId]);
});
document.addEventListener("click", e => { if (!popup.contains(e.target)) closePopup(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closePopup(); });

// Deletes go straight through mosaic's generic per-item route — each review
// is a whole sub-directory (data/<id>/), deleted recursively in one call. No
// write-back to manifest.json (mosaic has no write endpoint, by design);
// renderDetail() already shows "Review not found" for a manifest entry whose
// data 404s, so a stale reference left behind by a delete is harmless and
// self-heals on next full reload.
async function deleteReview(id) {
  const res = await fetch(`data/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`delete failed (${res.status})`);
}

async function bulkDelete(ids) {
  const results = await Promise.allSettled(ids.map(deleteReview));
  const succeeded = ids.filter((_, i) => results[i].status === "fulfilled");
  MANIFEST.datasets = MANIFEST.datasets.filter(d => !succeeded.includes(d.id));
  succeeded.forEach(id => SELECTED.delete(id));
  renderList();
  const failed = ids.length - succeeded.length;
  if (failed) alert(`${failed} of ${ids.length} review(s) could not be deleted.`);
}

function renderList() {
  closePopup();
  crumb.textContent = "";
  if (!MANIFEST.datasets.length) {
    app.innerHTML = `<div class="empty">No PRs reviewed yet. Run the pr-review skill against a PR to populate this dashboard.</div>`;
    return;
  }
  app.innerHTML = "";

  if (SELECTED.size) {
    const bar = document.createElement("div");
    bar.className = "bulk-bar";
    bar.innerHTML = `<span class="count">${SELECTED.size} selected</span>
      <button class="bulk-delete-btn">Delete selected</button>
      <button class="bulk-clear-btn">Clear</button>`;
    bar.querySelector(".bulk-clear-btn").onclick = () => { SELECTED.clear(); renderList(); };
    bar.querySelector(".bulk-delete-btn").onclick = () => {
      const ids = [...SELECTED];
      if (!confirm(`Delete ${ids.length} review(s)? This cannot be undone.`)) return;
      bulkDelete(ids);
    };
    app.appendChild(bar);
  }

  const rows = [...MANIFEST.datasets].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
  rows.forEach(d => {
    const row = document.createElement("div");
    row.className = "card reviewrow";
    row.innerHTML = `
      <input type="checkbox" class="sel-box" title="Select for bulk delete" ${SELECTED.has(d.id) ? "checked" : ""}>
      <div class="rtitle">${esc(d.repo)}#${d.pr_number} <span class="rname">${esc(d.title)}</span></div>
      <div class="rmeta">by ${esc(d.author)} · updated ${esc(d.updated_at)}</div>
      <div class="rcounts">${d.must_fix} must-fix · ${d.should_fix} should-fix · ${d.suggestions} suggestion(s)</div>
      ${badge(statusClass(d.status), d.status)}${d.verdict ? badge(verdictClass(d.verdict), d.verdict) : ""}
      <button class="del-btn" title="Delete this review">&times;</button>`;
    row.onclick = () => renderDetail(d.id, 1);
    row.querySelector(".sel-box").onclick = e => {
      e.stopPropagation();
      if (e.target.checked) SELECTED.add(d.id); else SELECTED.delete(d.id);
      renderList();
    };
    row.querySelector(".del-btn").onclick = async e => {
      e.stopPropagation();
      if (!confirm(`Delete the review for ${d.repo}#${d.pr_number}? This cannot be undone.`)) return;
      try {
        await deleteReview(d.id);
        MANIFEST.datasets = MANIFEST.datasets.filter(x => x.id !== d.id);
        SELECTED.delete(d.id);
        renderList();
      } catch (err) {
        alert(`Could not delete: ${err.message}`);
      }
    };
    app.appendChild(row);
  });
}

// A review's chunks are exactly its pages: each chunk_N.json is fetched only
// when its page is viewed, never all at once — the point for a large PR is
// to keep any single view small, the same reason the agent reviews one
// chunk at a time instead of the whole diff in one shot.
async function renderDetail(id, page) {
  closePopup();
  crumb.innerHTML = "← all reviews";
  crumb.onclick = () => { view = { name: "list" }; render(); };
  app.innerHTML = `<div class="empty">Loading…</div>`;

  const meta = await fetchJSON(`data/${id}/meta.json`);
  if (!meta) { app.innerHTML = `<div class="empty">Review not found.</div>`; return; }
  page = Math.min(Math.max(1, page || 1), Math.max(1, meta.chunk_count));
  view = { name: "detail", id, page };

  app.innerHTML = "";
  const head = document.createElement("div");
  head.className = "card phead";
  head.innerHTML = `
    <div class="head-top">
      <div>
        <div class="rtitle-lg">${esc(meta.title)}</div>
        <div class="remote">${esc(meta.repo)}#${meta.pr_number} · ${esc(meta.head_branch)} → ${esc(meta.base_branch)} · by ${esc(meta.author)}</div>
      </div>
      <div>${badge(statusClass(meta.status), meta.status)}${meta.verdict ? badge(verdictClass(meta.verdict), meta.verdict) : ""}</div>
    </div>
    <div class="chips">
      <span class="chip">+${meta.additions} / -${meta.deletions}</span>
      <span class="chip">${meta.changed_files} file(s)</span>
      <span class="chip">${meta.chunks_reviewed}/${meta.chunk_count} chunks reviewed</span>
      ${(meta.labels || []).map(l => `<span class="chip">${esc(l)}</span>`).join("")}
    </div>
    ${meta.story ? `<div class="story"><strong>Story:</strong> ${esc(meta.story)}</div>` : ""}`;
  app.appendChild(head);

  if (!meta.chunk_count) {
    app.insertAdjacentHTML("beforeend", `<div class="empty">No diff to review.</div>`);
    return;
  }

  const nav = document.createElement("div");
  nav.className = "pager card";
  app.appendChild(nav);
  const pageMount = document.createElement("div");
  pageMount.className = "pager-page";
  app.appendChild(pageMount);

  await renderPagerControls(nav, id, meta, page);
  await renderChunkPage(pageMount, id, page);
}

async function renderPagerControls(nav, id, meta, page) {
  // Options are labeled from meta's counts alone — listing per-chunk reviewed
  // state would mean fetching every chunk just to build the dropdown, which
  // defeats the point of paginating a large PR in the first place.
  const opts = [];
  for (let n = 1; n <= meta.chunk_count; n++) {
    opts.push(`<option value="${n}" ${n === page ? "selected" : ""}>Chunk ${n}</option>`);
  }
  nav.innerHTML = `
    <button class="pager-btn" id="pager-prev" ${page <= 1 ? "disabled" : ""}>← Prev</button>
    <select class="pager-select" id="pager-select">${opts.join("")}</select>
    <span class="pager-count">of ${meta.chunk_count}</span>
    <button class="pager-btn" id="pager-next" ${page >= meta.chunk_count ? "disabled" : ""}>Next →</button>`;
  nav.querySelector("#pager-prev").onclick = () => renderDetail(id, page - 1);
  nav.querySelector("#pager-next").onclick = () => renderDetail(id, page + 1);
  nav.querySelector("#pager-select").onchange = e => renderDetail(id, parseInt(e.target.value, 10));
}

async function renderChunkPage(mount, id, page) {
  closePopup();
  MARKER_STORE = {}; MARKER_ID = 0;
  mount.innerHTML = `<div class="empty">Loading chunk ${page}…</div>`;
  const chunk = await fetchJSON(`data/${id}/chunk_${page}.json`);
  mount.innerHTML = "";
  if (!chunk) { mount.innerHTML = `<div class="empty">Chunk ${page} not available yet.</div>`; return; }
  if (!chunk.reviewed) {
    mount.insertAdjacentHTML("beforeend", `<div class="pending-banner">${badge("warning", "not yet reviewed")} findings will appear here once this chunk has been reviewed</div>`);
  }
  const findingsIdx = buildFindingsIndex([chunk]);
  parseDiff(chunk.diff).forEach(f => mount.appendChild(renderFileDiff(f, findingsIdx)));
}

function render() { view.name === "list" ? renderList() : renderDetail(view.id, view.page); }

async function loadData() {
  MANIFEST = (await fetchJSON("data/manifest.json")) || { datasets: [] };
  render();
}
loadData();
