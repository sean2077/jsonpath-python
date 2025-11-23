"""Rename benchmark SVG files with version and timestamp suffix."""

import glob
import re
import shutil
from pathlib import Path


def main():
    """Rename benchmark_*.svg to benchmark_v{version}_{timestamp}.svg."""
    # Read version from pyproject.toml
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("pyproject.toml not found")
        return

    version = None
    for line in pyproject.read_text().splitlines():
        if line.startswith("version = "):
            version = line.split('"')[1]
            break

    if not version:
        print("Version not found in pyproject.toml")
        return

    # Rename SVG files
    for svg in glob.glob("benchmark_*.svg"):
        if not svg.startswith("benchmark_v"):
            # Extract timestamp from filename (e.g., benchmark_20251123_154214.svg)
            match = re.search(r"benchmark_(\d{8}_\d{6})\.svg", svg)
            if match:
                timestamp = match.group(1)
                new_name = f"benchmark_v{version}_{timestamp}.svg"
            else:
                new_name = f"benchmark_v{version}.svg"
            shutil.move(svg, new_name)
            print(f"Renamed {svg} -> {new_name}")


if __name__ == "__main__":
    main()
