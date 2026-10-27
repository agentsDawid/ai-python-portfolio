#!/usr/bin/env python3
"""Regenerate project listings before starting a Zensical serve/build command."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_project_lists.py"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate project cards/navigation, then run Zensical."
    )
    parser.add_argument("command", choices=("serve", "build"), help="Zensical command")
    args, passthrough = parser.parse_known_args()

    if not GENERATOR.is_file():
        print(f"ERROR: generator not found: {GENERATOR}", file=sys.stderr)
        return 2

    zensical = shutil.which("zensical")
    if not zensical:
        print(
            "ERROR: zensical command not found. Activate the correct Python environment "
            "and install project requirements.",
            file=sys.stderr,
        )
        return 127

    print(f"[site.py] Regenerating project listings with: {GENERATOR}", flush=True)
    try:
        generated = subprocess.run(
            [sys.executable, str(GENERATOR)], cwd=ROOT, check=False
        )
        if generated.returncode != 0:
            print(
                f"[site.py] Generator failed with exit code {generated.returncode}; "
                "Zensical was not started.",
                file=sys.stderr,
                flush=True,
            )
            return generated.returncode

        command = [zensical, args.command, *passthrough]
        print(f"[site.py] Running: {' '.join(command)}", flush=True)
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    except KeyboardInterrupt:
        print("\n[site.py] Interrupted by user (Ctrl+C).", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
