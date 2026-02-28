"""Export a BenchmarkReport to a structured JSON file."""

from __future__ import annotations

import dataclasses
import json

from benchmark.types import BenchmarkReport


def write_report(report: BenchmarkReport, path: str) -> None:
    data = {
        "summary": {
            "p1_agent": report.p1_agent,
            "p2_agent": report.p2_agent,
            "n_games": report.n_games,
            "p1_wins": report.p1_wins,
            "p2_wins": report.p2_wins,
            "draws": report.draws,
            "p1_win_rate": report.p1_win_rate,
            "avg_game_length": report.avg_game_length,
            "total_duration_s": report.total_duration_s,
            "p1_avg_decision_ms": report.p1_avg_decision_ms(),
            "p2_avg_decision_ms": report.p2_avg_decision_ms(),
            "p1_fallback_rate": report.p1_fallback_rate(),
            "p2_fallback_rate": report.p2_fallback_rate(),
        },
        "battles": [dataclasses.asdict(r) for r in report.results],
        "turn_stats": [dataclasses.asdict(t) for t in report.turn_stats],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
