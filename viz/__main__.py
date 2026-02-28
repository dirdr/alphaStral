"""CLI: uv run python -m viz <path> [--output <file>]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from viz.loader import load_report
from viz.report import build_report


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m viz",
        description="Generate an HTML benchmark report from a JSON run file.",
    )
    parser.add_argument("path", help="Path to the benchmark JSON file.")
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Output HTML path (default: same location as input, .html extension).",
    )
    args = parser.parse_args()

    source = Path(args.path)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        sys.exit(1)

    out = Path(args.output) if args.output else Path("reports") / source.with_suffix(".html").name

    data = load_report(source)
    html = build_report(data)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
