# Reusable list-view component (optional)

Two independently-built data-app skills — `repo-reliability` and
`pr-review` — converged on the identical shape for their top-level view:
fetch `data/manifest.json`, render one clickable card per entry, click
navigates into a detail view, with checkbox selection and single/bulk deletion.
If a new data-app skill's primary view is "a list of records with drill-down,"
start here instead of designing the list from scratch.

This is a starting point to copy and adapt, not a shared runtime — per the
`webapp/` contract, mosaic has no opinion on rendering and there is no
shared JS file to import. Paste the pattern into the new skill's own
`app.js`/`style.css` and rename/restyle for its domain.

## Shared theme & controls (CSS)

The variable *names* are what's shared (a 4-band severity scale plus accent
color); the hex values are each skill's own choice.

```css
:root {
  --bg: #f5f4f0; --card: #ffffff; --ink: #1c1c1a; --muted: #6b6a64;
  --line: #e2e0d8; --accent: #4f5d95;
  --healthy: #2e8f63; --healthy-bg: #e2f2ea;
  --warning: #b07c1e; --warning-bg: #f8eed7;
  --critical: #bb4444; --critical-bg: #f9e4e4;
  --unknown: #8a8880; --unknown-bg: #eceae3;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #191917; --card: #232320; --ink: #e8e6df; --muted: #a09e95;
    --line: #3a3934; --accent: #93a1d8;
    --healthy: #5cc498; --healthy-bg: #1e3a2d;
    --warning: #ddaf54; --warning-bg: #3d3321;
    --critical: #e07a7a; --critical-bg: #422323;
    --unknown: #94928a; --unknown-bg: #2e2d29;
  }
}
* { box-sizing: border-box; margin: 0; }
body { background: var(--bg); color: var(--ink); font: 15px/1.55 system-ui, sans-serif; padding: 24px; }
.wrap { max-width: 1100px; margin: 0 auto; }
header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
h1 { font-size: 21px; font-weight: 600; }
h1 span { color: var(--muted); font-weight: 400; }
.crumb { color: var(--muted); font-size: 14px; cursor: pointer; }
.crumb:hover { color: var(--accent); }
.home-link { color: var(--muted); font-size: 13px; text-decoration: none; }
.home-link:hover { color: var(--accent); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; margin-bottom: 14px; }
.badge { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px; margin-right: 4px; }
.b-healthy  { color: var(--healthy);  background: var(--healthy-bg); }
.b-warning  { color: var(--warning);  background: var(--warning-bg); }
.b-critical { color: var(--critical); background: var(--critical-bg); }
.b-unknown  { color: var(--unknown);  background: var(--unknown-bg); }
.empty { text-align: center; color: var(--muted); padding: 60px 0; }
.listrow { cursor: pointer; transition: border-color .15s; position: relative; padding-left: 40px; padding-right: 42px; }
.listrow:hover { border-color: var(--accent); }

/* ── delete & selection UI: single (corner button) and bulk (checkbox + toolbar) ── */
.sel-box {
  appearance: none; -webkit-appearance: none; margin: 0;
  position: absolute; top: 14px; left: 14px; width: 17px; height: 17px;
  border: 1.5px solid var(--line); border-radius: 5px; background: var(--card);
  cursor: pointer; transition: background .15s, border-color .15s;
}
.sel-box:hover { border-color: var(--accent); }
.sel-box:checked { background: var(--accent); border-color: var(--accent); }
.sel-box:checked::after {
  content: ""; position: absolute; left: 5px; top: 1px; width: 4px; height: 8px;
  border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg);
}
.sel-box:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.del-btn {
  position: absolute; top: 10px; right: 10px;
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; border: 1px solid var(--line); background: var(--card);
  color: var(--muted); font-size: 14px; line-height: 1; cursor: pointer;
}
.del-btn:hover { color: var(--critical); border-color: var(--critical); }
.bulk-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 8px 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }
.bulk-bar .count { font-size: 13px; color: var(--muted); }
.bulk-bar button { font: inherit; font-size: 13px; padding: 5px 12px; border-radius: 6px; cursor: pointer; }
.bulk-delete-btn { border: 1px solid var(--critical); background: var(--critical-bg); color: var(--critical); }
.bulk-delete-btn:hover { opacity: .85; }
.bulk-clear-btn { border: 1px solid var(--line); background: var(--bg); color: var(--ink); }
```

## List-view JS pattern (with selection & deletion)

```js
let MANIFEST = { datasets: [] };
let SELECTED = new Set(); // dataset ids currently checked for bulk delete
const app = document.getElementById("app");

async function fetchJSON(path) {
  try { const r = await fetch(path); return r.ok ? await r.json() : null; }
  catch (e) { return null; }
}

async function deleteDataset(id) {
  const res = await fetch(`data/${id}.json`, { method: "DELETE" });
  if (!res.ok) throw new Error(`delete failed (${res.status})`);
}

async function bulkDelete(ids) {
  const results = await Promise.allSettled(ids.map(deleteDataset));
  const succeeded = ids.filter((_, i) => results[i].status === "fulfilled");
  MANIFEST.datasets = MANIFEST.datasets.filter(d => !succeeded.includes(d.id));
  succeeded.forEach(id => SELECTED.delete(id));
  renderList();
  const failed = ids.length - succeeded.length;
  if (failed) alert(`${failed} of ${ids.length} item(s) could not be deleted.`);
}

function renderList() {
  if (!MANIFEST.datasets.length) {
    app.innerHTML = `<div class="empty">No data yet. Run the skill to populate this dashboard.</div>`;
    return;
  }
  app.innerHTML = "";

  // Bulk action toolbar (renders when at least one item is checked)
  if (SELECTED.size) {
    const bar = document.createElement("div");
    bar.className = "bulk-bar";
    bar.innerHTML = `<span class="count">${SELECTED.size} selected</span>
      <button class="bulk-delete-btn">Delete selected</button>
      <button class="bulk-clear-btn">Clear</button>`;
    bar.querySelector(".bulk-clear-btn").onclick = () => { SELECTED.clear(); renderList(); };
    bar.querySelector(".bulk-delete-btn").onclick = () => {
      const ids = [...SELECTED];
      if (!confirm(`Delete ${ids.length} item(s)? This cannot be undone.`)) return;
      bulkDelete(ids);
    };
    app.appendChild(bar);
  }

  // Render dataset cards
  MANIFEST.datasets.forEach(d => {
    const row = document.createElement("div");
    row.className = "card listrow";
    row.innerHTML = `
      <input type="checkbox" class="sel-box" title="Select for bulk delete" ${SELECTED.has(d.id) ? "checked" : ""}>
      <!-- title / meta / badges built from d, the skill's own fields -->
      <button class="del-btn" title="Delete this item">&times;</button>`;
    
    // Main card click navigates to detail view
    row.onclick = () => openDetail(d.id);

    // CRITICAL: Stop event propagation on controls so clicking checkbox/delete button doesn't trigger openDetail()
    row.querySelector(".sel-box").onclick = e => {
      e.stopPropagation();
      if (e.target.checked) SELECTED.add(d.id); else SELECTED.delete(d.id);
      renderList();
    };
    row.querySelector(".del-btn").onclick = async e => {
      e.stopPropagation();
      if (!confirm(`Delete item "${d.id}"? This cannot be undone.`)) return;
      try {
        await deleteDataset(d.id);
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

async function loadData() {
  MANIFEST = (await fetchJSON("data/manifest.json")) || { datasets: [] };
  renderList();
}
loadData();
```

## Key Card Design Rules

1. **Card Layout Padding**: Cards (`.listrow`) use `position: relative` with `padding-left: 40px` and `padding-right: 42px` to make dedicated space for the selection checkbox on the left and the delete button on the top-right.
2. **Event Propagation (`e.stopPropagation()`)**: Always invoke `e.stopPropagation()` in click handlers for `.sel-box` and `.del-btn`. Without this, clicking a checkbox or delete button will bubble up and trigger `row.onclick` (navigating into the detail view).
3. **Single Delete Button**: Positioned absolutely at `top: 10px; right: 10px;` as a circular icon button (`&times;` or trash icon), matching mosaic's standard placement.
4. **Bulk Action Toolbar**: Renders dynamically above the card list whenever `SELECTED.size > 0`, providing a count of selected items, a clear action, and a confirmation prompt for bulk deletion via mosaic's `DELETE` API.

