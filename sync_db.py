"""Sync epux.sqlite3 between a Modal volume and this machine.

Uses the `modal volume get/put` CLI (safe file copy, no live sqlite3
connection into a running container) instead of writing to the DB directly.

Usage:
    python sync_db.py down [--profile modal_5] [--volume epux-data-volume]
    python sync_db.py up   <backup_file> [--profile modal_5] [--volume epux-data-volume] [--force]

Examples:
    # Pull the current remote DB into db_backups/ (old account, before it dies)
    python sync_db.py down --profile modal_5

    # Push a local backup into a freshly created volume on the new account
    python sync_db.py up db_backups/epux_20260709.sqlite3 --profile modal_8 --force
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP_DIR = ROOT / "db_backups"
REMOTE_FILENAME = "epux.sqlite3"


def run_modal(args: list[str], profile: str | None) -> None:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if profile:
        env["MODAL_PROFILE"] = profile
    subprocess.run(["modal", *args], check=True, env=env)


def sync_down(volume: str, profile: str | None) -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"epux_{stamp}.sqlite3"
    run_modal(["volume", "get", volume, REMOTE_FILENAME, str(dest)], profile)
    print(f"Saved to {dest}")


def sync_up(backup_file: str, volume: str, profile: str | None, force: bool) -> None:
    src = Path(backup_file)
    if not src.is_file():
        sys.exit(f"No such file: {src}")
    args = ["volume", "put", volume, str(src), REMOTE_FILENAME]
    if force:
        args.append("--force")
    run_modal(args, profile)
    print(f"Uploaded {src} -> {volume}:/{REMOTE_FILENAME}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_down = sub.add_parser("down", help="Download the remote DB into db_backups/")
    p_down.add_argument("--volume", default="epux-data-volume")
    p_down.add_argument("--profile", default=None, help="Modal CLI profile, e.g. modal_5")

    p_up = sub.add_parser("up", help="Upload a local backup file to a volume")
    p_up.add_argument("backup_file")
    p_up.add_argument("--volume", default="epux-data-volume")
    p_up.add_argument("--profile", default=None, help="Modal CLI profile, e.g. modal_8")
    p_up.add_argument("--force", action="store_true", help="Overwrite the existing remote file")

    args = parser.parse_args()
    if args.cmd == "down":
        sync_down(args.volume, args.profile)
    else:
        sync_up(args.backup_file, args.volume, args.profile, args.force)


if __name__ == "__main__":
    main()
