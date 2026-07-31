#!/usr/bin/env python3
"""Audit skills against the authoring contract.

stdout: findings, one per line (data only)   stderr: diagnostics
exit 0 = clean · 1 = errors found · 2 = cannot run
"""
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(HOME, "dotfiles", "skills"))
TEMPLATE = os.path.join(SKILLS_DIR, "AGENTS-TEMPLATE.md")

REQUIRED = ["name", "description", "version", "kind", "triggers", "intent",
            "created_at", "updated_at"]
# House convention: `tools:` names real executables, because skills deploy to five
# agents. Agent primitives (write_to_file, view_file, read_file) differ per agent.
AGENT_PRIMITIVES = {"write_to_file", "view_file", "read_file", "edit_file",
                    "run_command", "list_directory", "search_files",
                    "activate_skill", "web_search"}
# Env vars whose literal expansion must not be hardcoded in skill prose.
ENV_LITERALS = {
    "~/workspace/scripts": "$SCRIPTS_PATH",
    "~/workspace/tools": "$TOOLS_PATH",
    "~/workspace/services": "$SERVICES_PATH",
    "~/workspace/install": "$INSTALL_PATH",
    "~/workspace/sdk": "$SDK_PATH",
}
KINDS = {"guidance", "pipeline", "hybrid"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
ISODATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BUDGET = 200

findings = []   # (severity, skill, check, message)


def add(sev, skill, check, msg):
    findings.append((sev, skill, check, msg))


def parse_frontmatter(text):
    """Minimal YAML subset: scalars and '- ' lists. Avoids a PyYAML dependency."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, 0
    # '...' is a YAML document-end marker: a real parser stops there, silently
    # dropping every field below it. Surface it rather than parsing through.
    for i in range(1, end):
        if lines[i].strip() == "...":
            return "DOCEND", i + 1
    data, key = {}, None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", raw):
            if key:
                data.setdefault(key, []).append(re.sub(r"^\s+-\s+", "", raw).strip())
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", raw)
        if m:
            key, val = m.group(1), m.group(2).strip()
            data[key] = val if val else []
    return data, end + 1


def strip_comment(s):
    return re.sub(r"\s+#.*$", "", s).strip()


def prose_only(text):
    """Drop fenced code blocks — examples and templates are not assertions."""
    return re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)


def resolve(res, skill_dir):
    """Return (abs_path, error, style_hint) for a resources: entry.

    './x' is the legacy convention and means skill-relative — resolved, not
    rejected, so that only genuinely missing paths surface as errors.
    """
    p = strip_comment(res)
    if not p:
        return None, None, None
    if p.startswith("./"):
        return os.path.join(skill_dir, p[2:]), None, "prefer <SKILL_PATH>/ over ./"
    if p.startswith("../"):
        return None, "escapes the skill directory", None
    if p.startswith("<SKILL_PATH>/"):
        return os.path.join(skill_dir, p[len("<SKILL_PATH>/"):]), None, None
    if p.startswith("$"):
        m = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)(/.*)?$", p)
        if not m:
            return None, f"unparseable variable path: {p}", None
        base = os.environ.get(m.group(1))
        if not base:
            return None, f"${m.group(1)} not set in this environment", None
        return base + (m.group(2) or ""), None, None
    if p.startswith("~"):
        return os.path.expanduser(p), None, None
    return os.path.join(skill_dir, p), None, None


def table_rows():
    """Map skill name -> Enabled cell from the AGENTS-TEMPLATE.md table."""
    rows = {}
    if not os.path.isfile(TEMPLATE):
        return rows
    with open(TEMPLATE, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            name = cells[0].strip("`").strip()
            if not name or name.startswith("---") or name == "Skill":
                continue
            rows[name] = cells[-1]
    return rows


def audit(skill_dir, name, disabled, table):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md):
        add("ERR", name, "structure", "no SKILL.md")
        return
    text = open(md, encoding="utf-8").read()
    total_lines = len(text.splitlines())

    fm, where = parse_frontmatter(text)
    if fm == "DOCEND":
        add("ERR", name, "frontmatter",
            f"bare '...' at line {where} ends the YAML document — "
            "every field below it is silently dropped")
        return
    if fm is None:
        add("ERR", name, "frontmatter", "missing or unterminated YAML frontmatter")
        return

    for field in REQUIRED:
        if field not in fm or fm[field] in ("", []):
            add("ERR", name, "frontmatter", f"missing required field: {field}")

    if fm.get("name") and fm["name"] != name:
        add("ERR", name, "frontmatter", f"name '{fm['name']}' != directory '{name}'")
    if fm.get("version") and not SEMVER.match(str(fm["version"])):
        add("ERR", name, "frontmatter", f"version not SemVer: {fm['version']}")
    for d in ("created_at", "updated_at"):
        if fm.get(d) and not ISODATE.match(str(fm[d])):
            add("ERR", name, "frontmatter", f"{d} not ISO 8601: {fm[d]}")

    kind = fm.get("kind")
    if kind and kind not in KINDS:
        add("ERR", name, "kind", f"invalid kind '{kind}' (guidance|pipeline|hybrid)")

    # ── budget & progressive disclosure ──────────────────────────────────────
    has_refs = os.path.isdir(os.path.join(skill_dir, "references"))
    if total_lines > BUDGET:
        if has_refs:
            add("WARN", name, "budget", f"SKILL.md {total_lines} lines (budget {BUDGET})")
        else:
            add("ERR", name, "budget",
                f"SKILL.md {total_lines} lines with no references/ — split it")

    # ── kind-specific shape ──────────────────────────────────────────────────
    scripts_dir = os.path.join(skill_dir, "scripts")
    scripts = []
    if os.path.isdir(scripts_dir):
        for root, _, files in os.walk(scripts_dir):
            scripts += [os.path.join(root, f) for f in files]

    if kind == "guidance" and scripts:
        add("ERR", name, "kind",
            f"guidance skill has {len(scripts)} script(s) — reclassify or remove")
    if kind == "pipeline" and not scripts:
        add("ERR", name, "kind", "pipeline skill has no scripts/")
    # A hybrid has a pipeline half, so its script->agent boundary matters too.
    if kind in ("pipeline", "hybrid"):
        if scripts:
            # The script->agent boundary must be designed: either a summary
            # projection over an artifact, or a documented compact output for
            # skills that stream results directly and have no artifact.
            blob = (text + "".join(
                open(s, encoding="utf-8", errors="ignore").read()
                for s in scripts if os.path.isfile(s))).lower()
            documented = re.search(r"^#{2,}\s+output\b", text, re.I | re.M)
            if not documented and "summary" not in blob and "projection" not in blob:
                add("ERR", name, "contract",
                    "script->agent boundary undocumented — add a summary "
                    "projection or an ## Output section")

    for s in scripts:
        if s.endswith(".sh") and not os.access(s, os.X_OK):
            add("WARN", name, "scripts",
                f"not executable: {os.path.relpath(s, skill_dir)}")

    # ── resources resolve ────────────────────────────────────────────────────
    for res in fm.get("resources", []) or []:
        path, err, hint = resolve(res, skill_dir)
        if err:
            add("ERR", name, "resources", f"{strip_comment(res)} — {err}")
        elif path and not os.path.exists(path):
            add("ERR", name, "resources", f"{strip_comment(res)} — does not exist")
        elif hint:
            add("WARN", name, "resources", f"{strip_comment(res)} — {hint}")

    # ── config ceremony without state ────────────────────────────────────────
    # A real config user references the concrete path, not just the filename —
    # this avoids flagging docs that merely mention skill.properties.
    cfg = fm.get("config_dir")
    if not cfg and "skill-config/" in prose_only(text):
        add("WARN", name, "config",
            "references a skill-config path but declares no config_dir")
    # config_dir is derivable from name; a hand-typed mismatch is silent drift.
    expected = f"~/.config/skill-config/{name}"
    if cfg and str(cfg).rstrip("/") != expected:
        add("ERR", name, "config",
            f"config_dir '{cfg}' != conventional '{expected}'")

    # ── house conventions ────────────────────────────────────────────────────
    for t in fm.get("tools", []) or []:
        tool = strip_comment(t)
        if tool in AGENT_PRIMITIVES:
            add("ERR", name, "conventions",
                f"tools: '{tool}' is an agent primitive, not a binary — "
                "skills deploy to five agents")
    body = prose_only(text)
    if re.search(r"/home/[a-z][a-z0-9_-]*/", body):
        add("ERR", name, "conventions",
            "hardcoded absolute home path in prose — use an env var or <SKILL_PATH>")
    for literal, var in ENV_LITERALS.items():
        if literal in body:
            add("WARN", name, "conventions", f"'{literal}' in prose — use {var}")

    # ── data-app skills (mosaic) ─────────────────────────────────────────────
    webapp_dir = os.path.join(skill_dir, "webapp")
    app_json = os.path.join(webapp_dir, "app.json")
    if os.path.isfile(app_json):
        try:
            meta = json.loads(open(app_json, encoding="utf-8").read())
        except (OSError, ValueError) as e:
            add("ERR", name, "data-app", f"webapp/app.json invalid JSON: {e}")
            meta = {}
        for field in ("id", "name", "version", "entry"):
            if not meta.get(field):
                add("ERR", name, "data-app", f"webapp/app.json missing field: {field}")
        app_id = meta.get("id")
        if app_id and not re.match(r"^[a-z0-9][a-z0-9-]*$", app_id):
            add("ERR", name, "data-app", f"webapp/app.json id '{app_id}' must be kebab-case")
        if app_id and app_id != name:
            add("ERR", name, "data-app",
                f"webapp/app.json id '{app_id}' != skill name '{name}' — the mosaic "
                "symlink name is derived from id, so this chain must match exactly")
        entry = meta.get("entry", "index.html")
        if not os.path.isfile(os.path.join(webapp_dir, "static", entry)):
            add("ERR", name, "data-app", f"entry '{entry}' not found under webapp/static/")

        data_dir = os.path.join(webapp_dir, "data")
        if os.path.isdir(data_dir) and not os.path.islink(data_dir) and os.listdir(data_dir):
            add("ERR", name, "data-app",
                "webapp/data is a populated real directory — data belongs in mosaic's "
                "centralized ~/.local/share/mosaic/data/<id>, not committed here")

        scripts_blob = "".join(
            open(s, encoding="utf-8", errors="ignore").read()
            for s in scripts if os.path.isfile(s)
        )
        if ".local/share/mosaic" not in scripts_blob:
            add("WARN", name, "data-app",
                "no script references ~/.local/share/mosaic/data — confirm the "
                "generation script writes there directly (skill-creator/references/data-app-skills.md)")

        if re.search(r"do-(un)?stow", body):
            add("ERR", name, "data-app",
                "do-stow/do-unstow must never be involved in onboarding a data-app "
                "skill — use mosaic's own scripts/onboard.sh")

    # ── registration & enabled-state ─────────────────────────────────────────
    if name not in table:
        add("ERR", name, "registration", "not listed in AGENTS-TEMPLATE.md")
    else:
        cell = table[name].lower()
        if disabled and cell != "no":
            add("ERR", name, "enabled", f"dir is .disabled but table says '{table[name]}'")
        if not disabled and cell == "no":
            add("ERR", name, "enabled", "table says No but dir is deployed")


def main():
    argv = sys.argv[1:]
    show_all = "--all" in argv
    targets = [a for a in argv if not a.startswith("-")]

    if not os.path.isdir(SKILLS_DIR):
        print(f"error: skills dir not found: {SKILLS_DIR}", file=sys.stderr)
        return 2

    table = table_rows()
    if not table:
        print(f"warning: no skills table parsed from {TEMPLATE}", file=sys.stderr)

    audited = 0
    for entry in sorted(os.listdir(SKILLS_DIR)):
        path = os.path.join(SKILLS_DIR, entry)
        if not os.path.isdir(path) or entry.startswith("."):
            continue
        disabled = entry.endswith(".disabled")
        name = entry[:-len(".disabled")] if disabled else entry
        if targets and name not in targets:
            continue
        audit(path, name, disabled, table)
        audited += 1

    if targets and audited == 0:
        print(f"error: no such skill: {', '.join(targets)}", file=sys.stderr)
        return 2

    errs = [f for f in findings if f[0] == "ERR"]
    warns = [f for f in findings if f[0] == "WARN"]
    shown = findings if show_all else (errs + warns)

    width = max((len(f[1]) for f in shown), default=0)
    for sev, skill, check, msg in sorted(shown, key=lambda f: (f[0] != "ERR", f[1])):
        print(f"{sev:4} {skill:<{width}}  {check:<12}  {msg}")

    print(f"— {audited} skills audited · {len(errs)} errors · {len(warns)} warnings",
          file=sys.stderr)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
