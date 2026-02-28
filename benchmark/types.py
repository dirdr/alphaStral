"""Typed result containers for benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BattleResult:
    game_id: str
    p1_agent: str  # agent.name
    p2_agent: str
    winner: str  # "p1" | "p2" | "draw"
    n_turns: int
    timestamp: float


@dataclass
class BenchmarkReport:
    p1_agent: str
    p2_agent: str
    n_games: int
    p1_wins: int
    p2_wins: int
    draws: int
    results: list[BattleResult] = field(default_factory=list)

    @property
    def p1_win_rate(self) -> float:
        if self.n_games == 0:
            return 0.0
        return self.p1_wins / self.n_games

    @property
    def avg_game_length(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.n_turns for r in self.results) / len(self.results)
