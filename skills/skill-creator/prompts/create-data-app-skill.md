# Create a New Data-App Skill — Example Prompts

For a brand-new pipeline/hybrid skill that should have a live mosaic
dashboard from day one, not just a report file. Load skill-creator first —
it reads `references/data-app-skills.md` when this applies.

- "Create a new skill that tracks `<X>` and shows it on mosaic."
- "Scaffold a data-app skill called `<name>` — kind pipeline, with a webapp."
- "I want a live mosaic dashboard for `<idea>`, not just a report file."
- "Add a webapp/ to the existing `<skill-name>` skill so it shows up on mosaic."

Scaffold command (generates `webapp/app.json` + `webapp/static/{index.html,
js/app.js,css/style.css}`; refuses with `--kind guidance`):

```bash
~/dotfiles/workspace/aistuff/skills/skill-creator/scripts/scaffold.sh <name> --kind pipeline --webapp
```

Then follow `references/data-app-skills.md`'s "How to build one": the
generation script writes straight to `~/.local/share/mosaic/data/<name>/`,
`webapp/` renders it (any way the skill wants — no shared renderer, no
enforced layout), onboard with `mkdir -p ~/.local/share/mosaic/apps && ln -sfn
<skill-path>/webapp ~/.local/share/mosaic/apps/<name>`.

The scaffold already appends a "Steady state, once onboarded to mosaic"
section to the new skill's own `SKILL.md` — leave it in place. It's what
tells a future agent invoking this skill that routine runs are data-producing
only, and that touching `webapp/` or the generation script's logic is a
separate, explicitly-requested action.
