"""Compare two benchmark JSON files and generate report with visualization.

Usage:
    python scripts/compare_benchmarks.py benchmark-1.json benchmark-2.json
    python scripts/compare_benchmarks.py benchmark-1.json benchmark-2.json --output comparison.svg
"""

import argparse
import json
import sys
from pathlib import Path


def load_benchmark(file_path):
    """Load benchmark JSON file."""
    with open(file_path) as f:
        return json.load(f)


def compare_benchmarks(baseline, current):
    """Compare two benchmark results and return comparison data."""
    baseline_map = {b["name"]: b for b in baseline["benchmarks"]}
    current_map = {b["name"]: b for b in current["benchmarks"]}

    comparisons = []
    for name in sorted(set(baseline_map.keys()) | set(current_map.keys())):
        baseline_bench = baseline_map.get(name)
        current_bench = current_map.get(name)

        if not baseline_bench or not current_bench:
            continue

        baseline_mean = baseline_bench["stats"]["mean"]
        current_mean = current_bench["stats"]["mean"]
        diff_pct = ((current_mean - baseline_mean) / baseline_mean) * 100

        comparisons.append(
            {
                "name": name.replace("tests/test_performance.py::TestPerformance::", "").replace(
                    "tests/test_performance.py::TestScalability::", ""
                ),
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
                "diff_pct": diff_pct,
                "baseline_ops": baseline_bench["stats"]["ops"],
                "current_ops": current_bench["stats"]["ops"],
            }
        )

    return comparisons


def format_time(seconds):
    """Format time in appropriate unit."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f}ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.2f}μs"
    if seconds < 1:
        return f"{seconds * 1e3:.2f}ms"
    return f"{seconds:.2f}s"


def generate_text_report(comparisons, baseline_info, current_info):
    """Generate text comparison report."""
    print("=" * 100)
    print("BENCHMARK COMPARISON REPORT")
    print("=" * 100)
    print()
    print(f"Baseline: {baseline_info['commit_info'].get('id', 'unknown')[:8]} - {baseline_info['datetime']}")
    print(f"Current:  {current_info['commit_info'].get('id', 'unknown')[:8]} - {current_info['datetime']}")
    print()
    print(f"{'Test Name':<50} {'Baseline':<12} {'Current':<12} {'Change':>10}")
    print("-" * 100)

    regressions = []
    improvements = []

    for comp in comparisons:
        name = comp["name"]
        baseline_str = format_time(comp["baseline_mean"])
        current_str = format_time(comp["current_mean"])
        diff_pct = comp["diff_pct"]

        if diff_pct > 5:
            marker = "⚠️ "
            regressions.append(comp)
        elif diff_pct < -5:
            marker = "✅ "
            improvements.append(comp)
        else:
            marker = "   "

        change_str = f"{marker}{diff_pct:+.1f}%"
        print(f"{name:<50} {baseline_str:<12} {current_str:<12} {change_str:>10}")

    print("=" * 100)
    print()

    if regressions:
        print(f"⚠️  {len(regressions)} REGRESSIONS (>5% slower):")
        for comp in sorted(regressions, key=lambda x: x["diff_pct"], reverse=True)[:5]:
            print(f"  - {comp['name']}: {comp['diff_pct']:+.1f}%")
        print()

    if improvements:
        print(f"✅ {len(improvements)} IMPROVEMENTS (>5% faster):")
        for comp in sorted(improvements, key=lambda x: x["diff_pct"])[:5]:
            print(f"  - {comp['name']}: {comp['diff_pct']:+.1f}%")
        print()

    avg_change = sum(c["diff_pct"] for c in comparisons) / len(comparisons) if comparisons else 0
    print(f"Average change: {avg_change:+.1f}%")
    print()


def generate_svg_chart(comparisons, output_path, baseline_name="Baseline", current_name="Current"):
    """Generate SVG comparison chart."""
    width = 1400
    height = max(600, len(comparisons) * 35 + 100)
    bar_height = 25
    margin_left = 400
    margin_right = 150
    margin_top = 80

    svg_lines = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        "  <style>",
        '    text { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; }',
        "    .title { font-size: 18px; font-weight: bold; }",
        "    .test-name { font-size: 14px; fill: #222; font-weight: 600; }",
        "    .improvement { fill: #28a745; }",
        "    .regression { fill: #dc3545; }",
        "    .neutral { fill: #6c757d; }",
        "    .axis-label { font-size: 11px; fill: #666; }",
        "    .side-label { font-size: 13px; fill: #444; font-weight: 600; }",
        "  </style>",
        f'  <rect width="{width}" height="{height}" fill="white"/>',
        f'  <text x="{width / 2}" y="30" text-anchor="middle" class="title">Benchmark Comparison</text>',
    ]

    # Sort by diff percentage
    sorted_comps = sorted(comparisons, key=lambda x: x["diff_pct"])

    max_abs_diff = max(abs(c["diff_pct"]) for c in sorted_comps) if sorted_comps else 1
    scale = (width - margin_left - margin_right) / (max_abs_diff * 2) if max_abs_diff > 0 else 1

    for i, comp in enumerate(sorted_comps):
        y = margin_top + i * (bar_height + 10)
        diff_pct = comp["diff_pct"]

        # Determine color
        if diff_pct > 5:
            color_class = "regression"
        elif diff_pct < -5:
            color_class = "improvement"
        else:
            color_class = "neutral"

        # Draw test name (left-aligned, at the left margin)
        test_name = comp["name"]
        if len(test_name) > 50:
            test_name = test_name[:47] + "..."
        svg_lines.append(
            f'  <text x="20" y="{y + bar_height / 2 + 5}" text-anchor="start" class="test-name">{test_name}</text>'
        )

        # Draw bar
        center_x = margin_left + (width - margin_left - margin_right) / 2

        # Draw bar (from center line)
        bar_width = abs(diff_pct) * scale
        bar_x = center_x if diff_pct >= 0 else center_x - bar_width

        svg_lines.append(
            f'  <rect x="{bar_x}" y="{y}" width="{bar_width}" height="{bar_height}" '
            f'class="{color_class}" opacity="0.85" rx="2"/>'
        )

        # Draw percentage label
        label_x = bar_x + bar_width + 8 if diff_pct >= 0 else bar_x - 8
        anchor = "start" if diff_pct >= 0 else "end"
        svg_lines.append(
            f'  <text x="{label_x}" y="{y + bar_height / 2 + 5}" '
            f'text-anchor="{anchor}" class="{color_class}" font-weight="bold">{diff_pct:+.1f}%</text>'
        )

    # Draw center line
    center_x = margin_left + (width - margin_left - margin_right) / 2
    svg_lines.append(
        f'  <line x1="{center_x}" y1="{margin_top - 10}" x2="{center_x}" '
        f'y2="{height - 35}" stroke="#333" stroke-width="2" opacity="0.5"/>'
    )

    # Draw 0% label
    svg_lines.append(
        f'  <text x="{center_x}" y="{margin_top - 15}" text-anchor="middle" '
        f'class="axis-label" font-weight="bold">0%</text>'
    )

    # Draw side labels (baseline on left, current on right)
    svg_lines.extend(
        [
            f'  <text x="{margin_left + 20}" y="50" text-anchor="start" class="side-label">← Baseline ({baseline_name})</text>',
            f'  <text x="{width - margin_right - 20}" y="50" text-anchor="end" class="side-label">Current ({current_name}) →</text>',
        ]
    )

    # Add legend
    legend_y = height - 15
    svg_lines.extend(
        [
            f'  <rect x="50" y="{legend_y - 10}" width="15" height="15" class="improvement" opacity="0.85" rx="2"/>',
            f'  <text x="70" y="{legend_y}" class="axis-label">Faster (&lt;-5%)</text>',
            f'  <rect x="180" y="{legend_y - 10}" width="15" height="15" class="neutral" opacity="0.85" rx="2"/>',
            f'  <text x="200" y="{legend_y}" class="axis-label">Similar (±5%)</text>',
            f'  <rect x="310" y="{legend_y - 10}" width="15" height="15" class="regression" opacity="0.85" rx="2"/>',
            f'  <text x="330" y="{legend_y}" class="axis-label">Slower (&gt;+5%)</text>',
        ]
    )

    svg_lines.append("</svg>")

    with open(output_path, "w") as f:
        f.write("\n".join(svg_lines))

    print(f"SVG chart saved to: {output_path}")


def find_version_benchmark():
    """Find the latest version benchmark file."""
    benchmarks_dir = Path("benchmarks")
    if not benchmarks_dir.exists():
        return None

    # Find version-suffixed benchmarks (excluding 'latest')
    version_files = sorted(
        [f for f in benchmarks_dir.glob("jsonpath-python-*.json") if "latest" not in f.name],
        key=lambda x: x.stat().st_mtime,
    )

    return str(version_files[-1]) if version_files else None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare two benchmark JSON files")
    parser.add_argument("baseline", nargs="?", help="Baseline benchmark JSON file (default: latest version benchmark)")
    parser.add_argument(
        "current", nargs="?", help="Current benchmark JSON file (default: benchmarks/jsonpath-python-latest.json)"
    )
    parser.add_argument("-o", "--output", help="Output SVG file path", default="benchmarks/comparison.svg")

    args = parser.parse_args()

    # Default baseline to newest version benchmark (old code)
    baseline_path = args.baseline
    if not baseline_path:
        baseline_path = find_version_benchmark()
        if not baseline_path:
            print("Error: No version benchmark found in benchmarks/")
            print("Run 'uv run poe perf-version' first to save a version benchmark")
            sys.exit(1)

    # Default current to 'latest' (new code just ran)
    current_path = args.current or "benchmarks/jsonpath-python-latest.json"

    if not Path(baseline_path).exists():
        print(f"Error: Baseline file not found: {baseline_path}")
        sys.exit(1)

    if not Path(current_path).exists():
        print(f"Error: Current file not found: {current_path}")
        sys.exit(1)

    print(f"Comparing: {Path(baseline_path).name} vs {Path(current_path).name}")
    print()

    baseline = load_benchmark(baseline_path)
    current = load_benchmark(current_path)

    comparisons = compare_benchmarks(baseline, current)

    if not comparisons:
        print("No common benchmarks found to compare")
        sys.exit(1)

    generate_text_report(comparisons, baseline, current)
    generate_svg_chart(
        comparisons, args.output, baseline_name=Path(baseline_path).stem, current_name=Path(current_path).stem
    )


if __name__ == "__main__":
    main()
