#!/usr/bin/env python3
"""Report disk usage and safely preview or remove old log files."""

import argparse
import shutil
import time
from pathlib import Path


def check_disk(mount=None, warn_pct=80):
    """Return disk usage details for one mount point."""
    if mount is None:
        mount = Path.cwd().anchor or "/"

    total, used, free = shutil.disk_usage(mount)
    used_pct = used / total * 100

    return {
        "mount": str(mount),
        "used_pct": round(used_pct, 1),
        "free_gib": free // (2 ** 30),
        "status": "WARN" if used_pct > warn_pct else "OK",
    }


def clean_logs(directory, days=7, dry_run=True):
    """Find top-level .log files older than days; preview unless applying."""
    cutoff = time.time() - days * 86400
    matched = []

    for log_file in Path(directory).glob("*.log"):
        try:
            if log_file.is_file() and log_file.stat().st_mtime < cutoff:
                if not dry_run:
                    log_file.unlink()
                matched.append(str(log_file))
        except OSError as error:
            print(f"skip {log_file}: {error}")

    return matched


def main():
    parser = argparse.ArgumentParser(
        description="Report disk usage and clean up old .log files."
    )
    parser.add_argument(
        "--mount",
        default=None,
        help="filesystem to check (defaults to the current drive/root)",
    )
    parser.add_argument("--logs", default="logs", help="directory containing logs")
    parser.add_argument("--days", type=int, default=7, help="minimum log age in days")
    parser.add_argument("--warn", type=int, default=80, help="disk warning threshold")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="preview matching files (the default)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="actually delete matching files",
    )

    args = parser.parse_args()
    if args.days < 0:
        parser.error("--days cannot be negative")
    if not 0 <= args.warn <= 100:
        parser.error("--warn must be between 0 and 100")

    print("disk:", check_disk(args.mount, args.warn))
    removed = clean_logs(args.logs, args.days, dry_run=not args.apply)
    action = "deleted" if args.apply else "would delete"
    print(f"{action}: {removed}")


if __name__ == "__main__":
    main()
