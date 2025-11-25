"""Save benchmark results to benchmarks/ directory with version suffix."""

import glob
import shutil
from pathlib import Path

from jsonpath import __version__


def main(suffix=None):
    """Save benchmark files to benchmarks/ with version suffix.

    Args:
        suffix: Custom suffix (default: version number without 'v' prefix)

    Usage:
        python scripts/save_benchmark.py              # Uses version (e.g., 1.1.1)
        python scripts/save_benchmark.py baseline     # Uses custom suffix
        python scripts/save_benchmark.py v1.1.1-opt   # Uses custom suffix with 'v'
    """
    version = __version__

    # Use custom suffix or version number (without 'v')
    file_suffix = suffix or version

    benchmarks_dir = Path("benchmarks")
    benchmarks_dir.mkdir(exist_ok=True)

    # Move and rename JSON files
    for json_file in glob.glob(".benchmarks/**/*.json", recursive=True):
        json_path = Path(json_file)
        if json_path.is_file():
            new_name = f"jsonpath-python-{file_suffix}.json"
            target = benchmarks_dir / new_name
            shutil.copy2(json_path, target)
            print(f"Copied {json_file} -> {target}")

    # Move and rename SVG files
    for svg in glob.glob("benchmark_*.svg"):
        svg_path = Path(svg)
        new_name = f"jsonpath-python-{file_suffix}.svg"
        target = benchmarks_dir / new_name
        shutil.move(svg_path, target)
        print(f"Moved {svg} -> {target}")


if __name__ == "__main__":
    import sys

    # Get custom suffix from command line argument
    custom_suffix = sys.argv[1] if len(sys.argv) > 1 else None
    main(custom_suffix)
