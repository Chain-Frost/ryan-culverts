"""Install the newest locally built ryan-culverts wheel."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

WHEEL_PATTERN: str = "ryan_culverts-*.whl"


def _latest_wheel(dist_dir: Path) -> Path:
    """Return the most recently modified matching wheel."""
    wheels = list(dist_dir.glob(WHEEL_PATTERN))
    if not wheels:
        raise FileNotFoundError(f"No {WHEEL_PATTERN} wheel found in {dist_dir}")
    return max(wheels, key=lambda path: (path.stat().st_mtime_ns, path.name))


def _pip_command(wheel: Path, target: Path | None, force_reinstall: bool) -> list[str]:
    """Build the user or isolated-target installation command."""
    command = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if target is None:
        command.append("--user")
    else:
        command.extend(("--target", str(target)))
    if force_reinstall:
        command.extend(("--force-reinstall", "--no-deps"))
    return [*command, str(wheel)]


def main(argv: list[str] | None = None) -> int:
    """Select the latest wheel, install it, and preserve the pip exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        help="Install into this isolated directory instead of the user site-packages.",
    )
    parser.add_argument(
        "--force-reinstall",
        action="store_true",
        help="Reinstall the wheel without resolving dependencies.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected wheel and pip command without installing.",
    )
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    try:
        wheel = _latest_wheel(project_root / "dist")
    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    target = args.target.resolve() if args.target is not None else None
    command = _pip_command(wheel, target, args.force_reinstall)
    print(f"Using Python: {sys.executable}")
    print(f"Installing:   {wheel}")
    print(f"Command:      {subprocess.list2cmdline(command)}")
    if args.dry_run:
        print("Dry run completed successfully.")
        return 0

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"ERROR: pip exited with status {result.returncode}", file=sys.stderr)
        return result.returncode
    print("Installation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
