#!/usr/bin/env python3
"""
Scaffold TUI Generator Script
Auto-discovers scripts in a directory and builds a valid menu.json specification.
Usage:
  python3 scaffold_tui.py --dir ~/workspace/scripts --out menu.json --title "My Scripts TUI"
"""
import os
import sys
import json
import argparse

def extract_description(filepath):
    """Reads top comment lines of a script to extract description."""
    desc = os.path.basename(filepath)
    try:
        with open(filepath, 'r', errors='ignore') as f:
            lines = [f.readline().strip() for _ in range(15)]
            for line in lines:
                if line.startswith("# Description:") or line.startswith("// Description:"):
                    return line.split(":", 1)[1].strip()
                elif line.startswith("#") and not line.startswith("#!") and len(line) > 3:
                    candidate = line.lstrip("#/ ").strip()
                    if candidate and not candidate.startswith("-*-"):
                        return candidate
    except Exception:
        pass
    return desc

def scaffold_directory(target_dir, title="Auto-Discovered TUI"):
    target_dir = os.path.abspath(os.path.expanduser(target_dir))
    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    items = []
    supported_exts = ('.sh', '.py', '.zsh', '.bash')
    
    files = sorted(os.listdir(target_dir))
    key_counter = 1
    
    for filename in files:
        filepath = os.path.join(target_dir, filename)
        if os.path.isfile(filepath) and (filename.endswith(supported_exts) or os.access(filepath, os.X_OK)):
            if filename.startswith(".") or filename.endswith(".json"):
                continue
                
            label = extract_description(filepath)
            key = str(key_counter) if key_counter <= 9 else chr(97 + (key_counter - 10))
            
            cmd = f"bash '{filepath}'" if filename.endswith(('.sh', '.zsh', '.bash')) else f"python3 '{filepath}'" if filename.endswith('.py') else f"'{filepath}'"
            
            items.append({
                "key": str(key),
                "label": label,
                "cmd": cmd
            })
            key_counter += 1

    menu_spec = {
        "title": title,
        "theme": "obsidian",
        "clamp_threshold": 10,
        "sections": [
            {
                "title": f"Discovered Tools ({len(items)})",
                "items": items
            }
        ]
    }
    return menu_spec

def main():
    parser = argparse.ArgumentParser(description="Auto-discover scripts and generate menu.json for TUI runner.")
    parser.add_argument("--dir", required=True, help="Target directory containing scripts")
    parser.add_argument("--out", default="menu.json", help="Output JSON path (default: menu.json)")
    parser.add_argument("--title", default="Auto-Discovered TUI", help="TUI Title")
    args = parser.parse_args()

    spec = scaffold_directory(args.dir, args.title)
    out_path = os.path.abspath(args.out)
    
    with open(out_path, 'w') as f:
        json.dump(spec, f, indent=2)
        
    print(f"✓ Generated TUI spec with {len(spec['sections'][0]['items'])} items at: {out_path}")

if __name__ == '__main__':
    main()
