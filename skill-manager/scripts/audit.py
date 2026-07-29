#!/usr/bin/env python3
"""Audit skills against the authoring contract.

stdout: findings, one per line (data only)   stderr: diagnostics
exit 0 = clean · 1 = errors found · 2 = cannot run
"""
import os
import re
import sys

HOME = os.path.expanduser("~")
SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(HOME, "dotfiles", "skills"))
TEMPLATE = os.path.join(SKILLS_DIR, "AGENTS-TEMPLATE.md")

REQUIRED = ["name", "description", "version", "kind", "triggers", "intent",
            "created_at", "updated_at"]
KINDS = {"guidance", "pipeline", "hybrid"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
ISODATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BUDGET = 150

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

    fm, _ = parse_frontmatter(text)
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
    if kind == "pipeline":
        if not scripts:
            add("ERR", name, "kind", "pipeline skill has no scripts/")
        else:
            blob = text + "".join(
                open(s, encoding="utf-8", errors="ignore").read()
                for s in scripts if os.path.isfile(s))
            if "summary" not in blob.lower():
                add("ERR", name, "contract",
                    "no summary projection — agent must read the full artifact")

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
    if not fm.get("config_dir") and "skill-config/" in text:
        add("WARN", name, "config",
            "references a skill-config path but declares no config_dir")

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
