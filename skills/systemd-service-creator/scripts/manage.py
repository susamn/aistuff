#!/usr/bin/env python3
"""systemd-service-creator manage.py — Scaffold, install, and audit personal systemd units.

Provides modes:
  scaffold: Generate hardened .service and/or .timer unit files with personal-services.target.
  install:  Copy unit files to systemd system path, enable personal-services.target, and reload daemon.
  list:     Audit all systemd units attached to personal-services.target.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SERVICES_PATH = Path(os.environ.get("SERVICES_PATH", Path.home() / "workspace" / "services"))
PERSONAL_TARGET = "personal-services.target"
SYSTEMD_SYSTEM_DIR = Path("/etc/systemd/system")
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(@)?$")


def die(msg: str, code: int = 1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def scaffold_service(name: str, exec_cmd: str, user: str = "@USER@", service_type: str = "oneshot", is_template: bool = False) -> str:
    display_name = name.replace("-", " ").title()
    spec = "%i" if is_template else ""
    unit_desc = f"{display_name} Personal Service {spec}".strip()

    content = f"""[Unit]
Description={unit_desc}
After=network-online.target
Wants=network-online.target

[Service]
Type={service_type}
ExecStart={exec_cmd}
User={user}
ProtectSystem=strict
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
PrivateDevices=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target {PERSONAL_TARGET}
"""
    return content


def scaffold_timer(name: str, schedule: str = "daily", is_template: bool = False) -> str:
    display_name = name.replace("-", " ").title()
    spec = "%i" if is_template else ""
    unit_desc = f"{display_name} Personal Timer {spec}".strip()
    target_unit = f"{name}@%i.service" if is_template else f"{name}.service"

    content = f"""[Unit]
Description={unit_desc}

[Timer]
OnCalendar={schedule}
Persistent=true
Unit={target_unit}

[Install]
WantedBy=timers.target {PERSONAL_TARGET}
"""
    return content


def cmd_scaffold(args):
    name = args.name.lower().strip()
    is_template = args.template or name.endswith("@")
    clean_name = name.rstrip("@")

    if not ID_RE.match(clean_name):
        die(f"invalid name '{name}'. Use kebab-case alphanumeric characters.")

    exec_cmd = args.exec
    if is_template and "%I" in exec_cmd:
        print("warning: standard specifier %I unescapes dashes; consider %i (lowercase) for profile names.", file=sys.stderr)

    out_dir = Path(args.output_dir) if args.output_dir else SERVICES_PATH / clean_name
    out_dir.mkdir(parents=True, exist_ok=True)

    files_created = []

    if args.unit_type in ["service", "both"]:
        svc_name = f"{clean_name}@.service" if is_template else f"{clean_name}.service"
        svc_path = out_dir / svc_name
        svc_content = scaffold_service(
            clean_name,
            exec_cmd=exec_cmd,
            user=args.user,
            service_type=args.service_type,
            is_template=is_template,
        )
        svc_path.write_text(svc_content)
        files_created.append(svc_path)

    if args.unit_type in ["timer", "both"]:
        tmr_name = f"{clean_name}@.timer" if is_template else f"{clean_name}.timer"
        tmr_path = out_dir / tmr_name
        tmr_content = scaffold_timer(
            clean_name,
            schedule=args.schedule,
            is_template=is_template,
        )
        tmr_path.write_text(tmr_content)
        files_created.append(tmr_path)

    print(f"Scaffolding complete in {out_dir}:")
    for f in files_created:
        print(f"  ✓ {f.name}")


def cmd_install(args):
    unit_path = Path(args.file).resolve()
    if not unit_path.exists():
        die(f"file not found: {unit_path}")

    dest_dir = SYSTEMD_SYSTEM_DIR
    real_user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))

    dest_path = dest_dir / unit_path.name
    content = unit_path.read_text()
    if "@USER@" in content:
        content = content.replace("@USER@", real_user)

    print(f"Installing {unit_path.name} -> {dest_path}...")
    if os.geteuid() != 0:
        print("Note: Root privileges required. Re-running with sudo...")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    dest_path.write_text(content)
    dest_path.chmod(0o644)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", PERSONAL_TARGET], check=False)
    subprocess.run(["systemctl", "enable", unit_path.name], check=False)
    print(f"✓ Installed and enabled {unit_path.name}")


def cmd_list(args):
    units = []
    try:
        res = subprocess.run(
            ["systemctl", "list-dependencies", PERSONAL_TARGET, "--plain", "--no-legend"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if line and line != PERSONAL_TARGET:
                    # Parse status
                    status_res = subprocess.run(
                        ["systemctl", "is-active", line],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    active_state = status_res.stdout.strip() or "unknown"
                    units.append({"unit": line, "state": active_state})
    except Exception as e:
        die(f"failed to query systemctl: {e}")

    artifact = {
        "schema": 1,
        "id": "personal-services-list",
        "count": len(units),
        "units": units,
    }

    if args.json:
        print(json.dumps(artifact, indent=2))
    else:
        print(f"Personal Services attached to {PERSONAL_TARGET} ({len(units)} total):")
        for u in units:
            state = u["state"]
            symbol = "●" if state == "active" else "○"
            print(f"  {symbol} {u['unit']} ({state})")


def main():
    parser = argparse.ArgumentParser(description="Manage personal systemd services and timers")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # scaffold
    p_scaffold = subparsers.add_parser("scaffold", help="Scaffold new systemd unit files")
    p_scaffold.add_argument("--name", required=True, help="Name of the service/timer (e.g. my-app)")
    p_scaffold.add_argument("--exec", required=True, help="ExecStart command or script path")
    p_scaffold.add_argument("--unit-type", choices=["service", "timer", "both"], default="both")
    p_scaffold.add_argument("--service-type", choices=["oneshot", "simple", "forking"], default="oneshot")
    p_scaffold.add_argument("--schedule", default="daily", help="OnCalendar schedule for timer (default: daily)")
    p_scaffold.add_argument("--user", default="@USER@", help="User to run as (default: @USER@)")
    p_scaffold.add_argument("--template", action="store_true", help="Generate template unit (app@.service)")
    p_scaffold.add_argument("--output-dir", help="Directory to save generated files")

    # install
    p_install = subparsers.add_parser("install", help="Install a unit file to systemd")
    p_install.add_argument("--file", required=True, help="Path to unit file")

    # list
    p_list = subparsers.add_parser("list", help="List personal services attached to personal-services.target")
    p_list.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    if args.mode == "scaffold":
        cmd_scaffold(args)
    elif args.mode == "install":
        cmd_install(args)
    elif args.mode == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
