"""Loads a benchmark JSON report from disk."""

from __future__ import annotations

import json
from pathlib import Path


def load_report(path: str | Path) -> dict:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    missing = {"summary", "battles", "turn_stats"} - data.keys()
    if missing:
        raise ValueError(f"Report missing required keys: {missing}")

    return data
