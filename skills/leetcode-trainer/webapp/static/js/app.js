let MANIFEST = { problems: [] };
let SELECTED = new Set();
let ACTIVE_DIFFS = new Set();
let QUERY = "";
let CURRENT_SLUG = null;

const grid = document.getElementById("grid");
const emptyEl = document.getElementById("empty");
const listView = document.getElementById("list-view");
const detailView = document.getElementById("detail-view");

async function fetchJSON(path) {
  try {
    const r = await fetch(path);
    return r.ok ? await r.json() : null;
  } catch (e) {
    return null;
  }
}

async function deleteProblem(slug) {
  const res = await fetch(`data/problems/${slug}.json`, { method: "DELETE" });
  if (!res.ok) throw new Error(`delete failed (${res.status})`);
}

// ── list view ──────────────────────────────────────────────────────────
function matches(p) {
  if (ACTIVE_DIFFS.size && !ACTIVE_DIFFS.has(p.difficulty)) return false;
  if (!QUERY) return true;
  const hay = (p.title + " " + p.topics.join(" ")).toLowerCase();
  return hay.includes(QUERY);
}

function renderBulkBar() {
  const slot = document.getElementById("bulk-bar-slot");
  slot.innerHTML = "";
  if (!SELECTED.size) return;
  const bar = document.createElement("div");
  bar.className = "bulk-bar";
  bar.innerHTML = `<span class="count">${SELECTED.size} selected</span>
    <button class="bulk-delete-btn">Delete selected</button>
    <button class="bulk-clear-btn">Clear</button>`;
  bar.querySelector(".bulk-clear-btn").onclick = () => { SELECTED.clear(); renderList(); };
  bar.querySelector(".bulk-delete-btn").onclick = async () => {
    const ids = [...SELECTED];
    if (!confirm(`Delete ${ids.length} problem(s)? This cannot be undone.`)) return;
    const results = await Promise.allSettled(ids.map(deleteProblem));
    const succeeded = ids.filter((_, i) => results[i].status === "fulfilled");
    MANIFEST.problems = MANIFEST.problems.filter(p => !succeeded.includes(p.id));
    succeeded.forEach(id => SELECTED.delete(id));
    renderList();
    const failed = ids.length - succeeded.length;
    if (failed) alert(`${failed} of ${ids.length} could not be deleted.`);
  };
  slot.appendChild(bar);
}

function renderList() {
  document.getElementById("progress-badge").textContent =
    MANIFEST.problems.length ? `${MANIFEST.problems.length} problems` : "";
  renderBulkBar();
  const visible = MANIFEST.problems.filter(matches);
  grid.innerHTML = "";
  emptyEl.hidden = visible.length > 0;
  visible.forEach(p => {
    const card = document.createElement("div");
    card.className = "card pcard";
    card.innerHTML = `
      <div class="row1">
        <span class="lc-id">#${p.leetcode_id}</span>
        <span class="badge ${p.difficulty}">${p.difficulty}</span>
      </div>
      <h3>${escapeHtml(p.title)}</h3>
      <div class="topics">${p.topics.map(escapeHtml).join(" &middot; ")}</div>
      <button class="del-btn" title="Delete this problem">&times;</button>`;
    card.onclick = () => openDetail(p.id);
    card.querySelector(".del-btn").onclick = async (e) => {
      e.stopPropagation();
      if (!confirm(`Delete "${p.title}"? This cannot be undone.`)) return;
      try {
        await deleteProblem(p.id);
        MANIFEST.problems = MANIFEST.problems.filter(x => x.id !== p.id);
        SELECTED.delete(p.id);
        renderList();
      } catch (err) {
        alert(`Could not delete: ${err.message}`);
      }
    };
    grid.appendChild(card);
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

document.getElementById("search").addEventListener("input", (e) => {
  QUERY = e.target.value.trim().toLowerCase();
  renderList();
});
document.querySelectorAll(".diff-chip").forEach(btn => {
  btn.onclick = () => {
    const d = btn.dataset.diff;
    if (ACTIVE_DIFFS.has(d)) { ACTIVE_DIFFS.delete(d); btn.classList.remove("active"); }
    else { ACTIVE_DIFFS.add(d); btn.classList.add("active"); }
    renderList();
  };
});

// ── detail view ───────────────────────────────────────────────────────
async function openDetail(slug) {
  const p = await fetchJSON(`data/problems/${slug}.json`);
  if (!p) { alert("Could not load that problem."); return; }
  CURRENT_SLUG = slug;

  document.getElementById("d-title").textContent = `#${p.leetcode_id}. ${p.title}`;
  const diffEl = document.getElementById("d-difficulty");
  diffEl.textContent = p.difficulty;
  diffEl.className = `badge ${p.difficulty}`;
  document.getElementById("d-topics").textContent = p.topics.join(" · ");
  document.getElementById("d-source").href = p.source_url;

  document.getElementById("p-statement").textContent = p.problem.statement_md;
  const exWrap = document.getElementById("p-examples");
  exWrap.innerHTML = "";
  p.problem.examples.forEach((ex, i) => {
    const d = document.createElement("div");
    d.className = "example";
    d.innerHTML = `<div><strong>Example ${i + 1}</strong></div>
      <div><strong>Input:</strong> ${escapeHtml(ex.input)}</div>
      <div><strong>Output:</strong> ${escapeHtml(ex.output)}</div>
      ${ex.explanation ? `<div><strong>Explanation:</strong> ${escapeHtml(ex.explanation)}</div>` : ""}`;
    exWrap.appendChild(d);
  });
  const constraints = p.problem.constraints || [];
  document.getElementById("p-constraints-h").hidden = constraints.length === 0;
  const cList = document.getElementById("p-constraints");
  cList.innerHTML = constraints.map(c => `<li>${escapeHtml(c)}</li>`).join("");

  document.getElementById("i-summary").textContent = p.intuition.summary_md;
  document.getElementById("i-approach").textContent = p.intuition.approach_md;
  document.getElementById("i-time").textContent = p.intuition.time_complexity;
  document.getElementById("i-space").textContent = p.intuition.space_complexity;
  const diagWrap = document.getElementById("i-diagram");
  diagWrap.innerHTML = "";
  if (p.intuition.diagram && p.intuition.diagram.content) {
    if (p.intuition.diagram.type === "svg") {
      diagWrap.innerHTML = p.intuition.diagram.content;
    } else {
      const pre = document.createElement("pre");
      pre.textContent = p.intuition.diagram.content;
      diagWrap.appendChild(pre);
    }
  }

  document.getElementById("s-python-code").textContent = p.solutions.python.code;
  document.getElementById("s-python-notes").textContent = p.solutions.python.notes_md || "";
  document.getElementById("s-golang-code").textContent = p.solutions.golang.code;
  document.getElementById("s-golang-notes").textContent = p.solutions.golang.notes_md || "";

  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "problem"));
  document.querySelectorAll(".tab-panel").forEach(el => el.hidden = el.dataset.panel !== "problem");
  document.querySelectorAll(".lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === "python"));
  document.getElementById("lang-python").hidden = false;
  document.getElementById("lang-golang").hidden = true;

  listView.hidden = true;
  detailView.hidden = false;
  window.scrollTo(0, 0);
}

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
    document.querySelectorAll(".tab-panel").forEach(el => el.hidden = el.dataset.panel !== btn.dataset.tab);
  };
});
document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".lang-btn").forEach(b => b.classList.toggle("active", b === btn));
    document.getElementById("lang-python").hidden = btn.dataset.lang !== "python";
    document.getElementById("lang-golang").hidden = btn.dataset.lang !== "golang";
  };
});
document.getElementById("back-link").onclick = (e) => {
  e.preventDefault();
  detailView.hidden = true;
  listView.hidden = false;
  CURRENT_SLUG = null;
};

async function loadData() {
  MANIFEST = (await fetchJSON("data/manifest.json")) || { problems: [] };
  renderList();
}
loadData();
