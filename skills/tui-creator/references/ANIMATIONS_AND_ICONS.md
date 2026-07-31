# TUI Animations, Data Visualizations & Icon Fonts

## 1. Cross-Platform Braille Spinners (Loading States)
When a task command takes time to initialize or execute, render a **Braille Spinner**.

Braille patterns (`U+2800` to `U+28FF`: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`) are part of standard Unicode and work **natively across Linux, macOS, WSL, and Windows Terminal** without installing extra font packages.

```python
BRAILLE_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
```

## 2. Smooth Sub-block Progress Bars
For operations reporting numerical completion percentage, use Unicode 1/8th sub-blocks (` `, `▏`, `▎`, `▍`, `▌`, `▋`, `▊`, `▉`, `█`) to render high-resolution sub-pixel progress bars:

```
  [████████████████▌               ] 53.4%
```

## 3. Data Patterns & Distribution Histograms (Sparklines)
To display metric distributions, CPU loads, request rates, or memory trends in a single inline line, use 1/8th height block characters (` `, `▂`, `▃`, `▄`, `▅`, `▆`, `▇`, `█`):

```
  Memory Trend:  ▂▃▄▅▆▇█▇▅▃ 
```

## 4. Terminal Icon Fonts (Nerd Fonts vs. Universal Unicode)

The terminal equivalent of **Font Awesome** is **Nerd Fonts** ([nerdfonts.com](https://www.nerdfonts.com/)). Nerd Fonts patch popular monospace fonts (JetBrains Mono, Fira Code, Hack) with 10,000+ developer icons (Docker `󰡨`, Git `󰊢`, Linux `󰌽`, Python `󰌠`).

* **Best Practice**: Use standard Unicode emoji/symbols (`📁`, `⚙️`, `🎨`, `✓`, `✗`, `📦`) as safe defaults so TUIs render cleanly on any terminal without requiring users to install Nerd Fonts, while keeping provision for Nerd Font icons when available.
