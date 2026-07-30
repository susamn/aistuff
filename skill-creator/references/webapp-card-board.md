# Reusable single-page card board component (optional)

For data-app skills whose UI shape is a **single-page card board** (like Google Keep or Trello cards) rather than a list-with-detail-drill-down. All cards live on a single responsive board canvas without sub-page navigation, and individual cards can toggle content between collapsed (hidden) and expanded (plain) views.

This pattern shares mosaic's exact design language, CSS custom properties, header navigation (`← mosaic`), card styling, selection checkboxes, and single/bulk deletion.

---

## Data Model & Generation Contract

The skill's generation script writes to a single board dataset:

```
~/.local/share/mosaic/data/<id>/board.json
```

```json
{
  "title": "Project Notes & Tasks",
  "updated_at": "2026-07-30 15:14",
  "cards": [
    {
      "id": "card-101",
      "title": "Database Migration Plan",
      "category": "architecture",
      "status": "warning",
      "tags": ["db", "v2"],
      "collapsible": true,
      "default_collapsed": false,
      "preview": "Summary of steps for upgrading PostgreSQL schema...",
      "content": "Detailed step-by-step migration instructions:\n1. Backup DB\n2. Run DDL scripts\n3. Verify indices",
      "created_at": "2026-07-30"
    }
  ]
}
```

Skills can append new cards to `board.json` or update card states directly via their generation scripts.

---

## Shared CSS Design Tokens & Board Layout

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
.wrap { max-width: 1200px; margin: 0 auto; }

/* ── Mandatory Header & Home Link ───────────────────────────────────── */
header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
h1 { font-size: 21px; font-weight: 600; }
h1 span { color: var(--muted); font-weight: 400; }
.home-link { color: var(--muted); font-size: 13px; text-decoration: none; }
.home-link:hover { color: var(--accent); }

/* ── Card Board Grid Layout ─────────────────────────────────────────── */
.board-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  align-items: start;
}

/* ── Board Card Component ───────────────────────────────────────────── */
.board-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 16px 18px;
  position: relative;
  padding-left: 40px;
  padding-right: 42px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color .15s, box-shadow .15s;
}
.board-card:hover { border-color: var(--accent); }

.card-title { font-weight: 650; font-size: 16px; word-break: break-word; }
.card-meta { color: var(--muted); font-size: 12.5px; display: flex; gap: 8px; flex-wrap: wrap; }

.badge { display: inline-block; font-size: 11.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.b-healthy  { color: var(--healthy);  background: var(--healthy-bg); }
.b-warning  { color: var(--warning);  background: var(--warning-bg); }
.b-critical { color: var(--critical); background: var(--critical-bg); }
.b-unknown  { color: var(--unknown);  background: var(--unknown-bg); }

.chip { font-size: 11px; color: var(--muted); background: var(--bg); border: 1px solid var(--line); border-radius: 999px; padding: 1px 8px; }

/* ── Collapsible Info Section (Hidden vs Plain) ─────────────────────── */
.card-body { font-size: 13.5px; color: var(--ink); white-space: pre-wrap; line-height: 1.5; }
.card-body.collapsed { display: none; }
.toggle-btn {
  background: none; border: none; color: var(--accent); font-size: 12.5px;
  cursor: pointer; padding: 0; text-align: left; font-weight: 500;
  display: inline-flex; align-items: center; gap: 4px; width: fit-content;
}
.toggle-btn:hover { text-decoration: underline; }

/* ── Checkbox Selection & Single Delete Corner Control ──────────────── */
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
.del-btn {
  position: absolute; top: 10px; right: 10px;
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; border: 1px solid var(--line); background: var(--card);
  color: var(--muted); font-size: 14px; line-height: 1; cursor: pointer;
}
.del-btn:hover { color: var(--critical); border-color: var(--critical); }

/* ── Floating Bulk Action Toolbar ───────────────────────────────────── */
.bulk-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding: 8px 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }
.bulk-bar .count { font-size: 13px; color: var(--muted); }
.bulk-bar button { font: inherit; font-size: 13px; padding: 5px 12px; border-radius: 6px; cursor: pointer; }
.bulk-delete-btn { border: 1px solid var(--critical); background: var(--critical-bg); color: var(--critical); }
.bulk-delete-btn:hover { opacity: .85; }
.bulk-clear-btn { border: 1px solid var(--line); background: var(--bg); color: var(--ink); }
.empty { text-align: center; color: var(--muted); padding: 60px 0; }
```

---

## Single-Page Board JS Implementation

```js
"use strict";
let BOARD = { title: "Board", cards: [] };
let SELECTED = new Set();
let COLLAPSED = new Set(); // tracks collapsed card ids
const app = document.getElementById("app");

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function statusBadge(status) { return status ? `<span class="badge b-${esc(status)}">${esc(status)}</span>` : ""; }

async function fetchJSON(path) {
  try { const r = await fetch(path); return r.ok ? await r.json() : null; }
  catch (e) { return null; }
}

async function deleteCard(cardId) {
  // Option A: Single card delete via mosaic generic DELETE route if stored as data/<cardId>.json
  // Option B: Remove card locally and save updated board structure
  BOARD.cards = BOARD.cards.filter(c => c.id !== cardId);
  SELECTED.delete(cardId);
  renderBoard();
}

async function bulkDelete(ids) {
  BOARD.cards = BOARD.cards.filter(c => !ids.includes(c.id));
  ids.forEach(id => SELECTED.delete(id));
  renderBoard();
}

function renderBoard() {
  if (!BOARD.cards.length) {
    app.innerHTML = `<div class="empty">No cards on this board yet.</div>`;
    return;
  }
  app.innerHTML = "";

  // Render floating bulk selection toolbar
  if (SELECTED.size) {
    const bar = document.createElement("div");
    bar.className = "bulk-bar";
    bar.innerHTML = `<span class="count">${SELECTED.size} selected</span>
      <button class="bulk-delete-btn">Delete selected</button>
      <button class="bulk-clear-btn">Clear</button>`;
    bar.querySelector(".bulk-clear-btn").onclick = () => { SELECTED.clear(); renderBoard(); };
    bar.querySelector(".bulk-delete-btn").onclick = () => {
      const ids = [...SELECTED];
      if (!confirm(`Delete ${ids.length} card(s)? This cannot be undone.`)) return;
      bulkDelete(ids);
    };
    app.appendChild(bar);
  }

  // Render Card Grid
  const grid = document.createElement("div");
  grid.className = "board-grid";

  BOARD.cards.forEach(c => {
    const card = document.createElement("div");
    card.className = "board-card";
    const isCollapsed = COLLAPSED.has(c.id) || (c.collapsible && c.default_collapsed && !COLLAPSED.has(`expanded-${c.id}`));

    card.innerHTML = `
      <input type="checkbox" class="sel-box" title="Select card" ${SELECTED.has(c.id) ? "checked" : ""}>
      <button class="del-btn" title="Delete card">&times;</button>
      
      <div class="card-title">${esc(c.title)}</div>
      <div class="card-meta">
        ${statusBadge(c.status)}
        ${(c.tags || []).map(t => `<span class="chip">${esc(t)}</span>`).join("")}
        <span>${esc(c.created_at || "")}</span>
      </div>

      ${c.preview ? `<div class="card-preview">${esc(c.preview)}</div>` : ""}

      ${c.content ? `
        <button class="toggle-btn">${isCollapsed ? "▶ Show details" : "▼ Hide details"}</button>
        <div class="card-body ${isCollapsed ? "collapsed" : ""}">${esc(c.content)}</div>
      ` : ""}
    `;

    // Toggle hidden vs plain info
    const toggleBtn = card.querySelector(".toggle-btn");
    if (toggleBtn) {
      toggleBtn.onclick = () => {
        if (isCollapsed) {
          COLLAPSED.delete(c.id);
          COLLAPSED.add(`expanded-${c.id}`);
        } else {
          COLLAPSED.add(c.id);
          COLLAPSED.delete(`expanded-${c.id}`);
        }
        renderBoard();
      };
    }

    // Checkbox selection
    card.querySelector(".sel-box").onclick = e => {
      e.stopPropagation();
      if (e.target.checked) SELECTED.add(c.id); else SELECTED.delete(c.id);
      renderBoard();
    };

    // Delete single card
    card.querySelector(".del-btn").onclick = async e => {
      e.stopPropagation();
      if (!confirm(`Delete card "${c.title}"?`)) return;
      await deleteCard(c.id);
    };

    grid.appendChild(card);
  });

  app.appendChild(grid);
}

async function loadData() {
  BOARD = (await fetchJSON("data/board.json")) || { title: "Board", cards: [] };
  renderBoard();
}
loadData();
```

---

## Key Design & Architecture Rules

1. **Single Canvas (No Sub-Pages)**: The entire dataset is presented directly on one responsive card grid. Do not build a list-to-detail router for single-document apps.
2. **Hidden vs Plain Info Toggle**: Use inline state (`COLLAPSED` set) and `.card-body.collapsed { display: none; }` to toggle content visibility per card directly on the board.
3. **Mosaic Language Consistency**: Use standard CSS variables (`--bg`, `--card`, `--accent`, `--line`), `--healthy`/`--warning`/`--critical` badges, circular `.del-btn`, `.sel-box` checkboxes, and dynamic `.bulk-bar` toolbar.
4. **Mandatory Header Link**: Header must include `<a href="/mosaic/" class="home-link">← mosaic</a>` to return to mosaic's root app dashboard.
