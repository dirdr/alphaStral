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
class TurnStat:
    battle_tag: str
    turn: int
    agent: str
    decision_ms: float  # 0.0 when fallback (no API call completed)
    used_fallback: bool
    history_msgs: int  # context size entering this turn
    action_type: str  # "move" | "switch"


@dataclass
class BenchmarkReport:
    p1_agent: str
    p2_agent: str
    n_games: int
    p1_wins: int
    p2_wins: int
    draws: int
    results: list[BattleResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    turn_stats: list[TurnStat] = field(default_factory=list)

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

    def p1_avg_decision_ms(self) -> float | None:
        rows = [t for t in self.turn_stats if t.agent == self.p1_agent]
        if not rows:
            return None
        return sum(t.decision_ms for t in rows) / len(rows)

    def p2_avg_decision_ms(self) -> float | None:
        rows = [t for t in self.turn_stats if t.agent == self.p2_agent]
        if not rows:
            return None
        return sum(t.decision_ms for t in rows) / len(rows)

    def p1_fallback_rate(self) -> float | None:
        rows = [t for t in self.turn_stats if t.agent == self.p1_agent]
        if not rows:
            return None
        return sum(1 for t in rows if t.used_fallback) / len(rows)

    def p2_fallback_rate(self) -> float | None:
        rows = [t for t in self.turn_stats if t.agent == self.p2_agent]
        if not rows:
            return None
        return sum(1 for t in rows if t.used_fallback) / len(rows)
