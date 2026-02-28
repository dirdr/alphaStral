"""
BattleRunner: orchestrates N battles between two AgentPlayers.

Knows nothing about which agents are inside the players —
works identically for Random vs Random or Mistral vs Finetuned.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from poke_env import ServerConfiguration
from poke_env.concurrency import POKE_LOOP
from poke_env.ps_client import AccountConfiguration

from benchmark.types import BattleResult, BenchmarkReport
from bot.agent import BattleAgent
from bot.player import AgentPlayer

logger = logging.getLogger(__name__)


class BattleRunner:
    def __init__(
        self,
        server_configuration: ServerConfiguration,
        battle_format: str = "gen9randombattle",
        account1: AccountConfiguration | None = None,
        account2: AccountConfiguration | None = None,
        move_delay: float = 0.0,
    ) -> None:
        self._server_configuration = server_configuration
        self._battle_format = battle_format
        self._account1 = account1
        self._account2 = account2
        self._move_delay = move_delay

    def run(
        self,
        agent1: BattleAgent,
        agent2: BattleAgent,
        n_battles: int,
    ) -> BenchmarkReport:
        # Schedule on POKE_LOOP (poke-env's dedicated event loop thread).
        # battle_against is designed to be awaited from within POKE_LOOP.
        future = asyncio.run_coroutine_threadsafe(
            self._run_async(agent1, agent2, n_battles), POKE_LOOP
        )
        return future.result()

    async def _run_async(
        self,
        agent1: BattleAgent,
        agent2: BattleAgent,
        n_battles: int,
    ) -> BenchmarkReport:
        p1 = AgentPlayer(
            agent=agent1,
            account_configuration=self._account1,
            battle_format=self._battle_format,
            server_configuration=self._server_configuration,
            move_delay=self._move_delay,
        )
        p2 = AgentPlayer(
            agent=agent2,
            account_configuration=self._account2,
            battle_format=self._battle_format,
            server_configuration=self._server_configuration,
            move_delay=self._move_delay,
        )

        is_local = "localhost" in self._server_configuration.websocket_url
        watch_url = (
            "http://localhost.psim.us/?port=8000"
            if is_local
            else f"https://play.pokemonshowdown.com → search '{p1.username}'"
        )

        logger.info(
            "Battle session: %s (%s) vs %s (%s) · %d battle(s) · format=%s",
            agent1.name,
            p1.username,
            agent2.name,
            p2.username,
            n_battles,
            self._battle_format,
        )
        logger.debug("Auth mode: %s", "credentials" if self._account1 else "guest")

        print(f"  {agent1.name} ({p1.username})  vs  {agent2.name} ({p2.username})")
        print(f"  Watch: {watch_url}")
        print()

        start = time.time()
        await p1.battle_against(p2, n_battles=n_battles)
        elapsed = time.time() - start

        results = self._collect_results(p1, p2, agent1.name, agent2.name)
        report = BenchmarkReport(
            p1_agent=agent1.name,
            p2_agent=agent2.name,
            n_games=n_battles,
            p1_wins=p1.n_won_battles,
            p2_wins=p2.n_won_battles,
            draws=n_battles - p1.n_won_battles - p2.n_won_battles,
            results=results,
        )

        logger.info(
            "Done: %d battles in %.1fs · %s %dW/%dL · win rate %.1f%% · avg %.1f turns",
            n_battles,
            elapsed,
            agent1.name,
            p1.n_won_battles,
            p2.n_won_battles,
            report.p1_win_rate * 100,
            report.avg_game_length,
        )

        print(f"  Done — {n_battles} battle(s) in {elapsed:.1f}s")
        print(
            f"  {agent1.name} {p1.n_won_battles}W / {p2.n_won_battles}L · win rate {report.p1_win_rate:.1%} · avg {report.avg_game_length:.1f} turns"
        )

        return report

    def _collect_results(
        self,
        p1: AgentPlayer,
        p2: AgentPlayer,
        name1: str,
        name2: str,
    ) -> list[BattleResult]:
        results = []
        for battle in p1.battles.values():
            winner = "p1" if battle.won else "p2" if battle.lost else "draw"
            results.append(
                BattleResult(
                    game_id=str(uuid.uuid4()),
                    p1_agent=name1,
                    p2_agent=name2,
                    winner=winner,
                    n_turns=battle.turn,
                    timestamp=time.time(),
                )
            )
        return results
