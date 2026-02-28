"""
AgentPlayer: poke-env bridge. Written once, never modified.

Wires together StateExtractor → BattleAgent → ActionParser.
To use a different model, pass a different BattleAgent — that's all.
"""

from __future__ import annotations

import logging

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.player import Player

from bot.agent import BattleAgent
from bot.extractor import StateExtractor
from bot.parser import ActionParser

logger = logging.getLogger(__name__)


class AgentPlayer(Player):
    def __init__(self, agent: BattleAgent, **kwargs) -> None:
        super().__init__(**kwargs)
        self._agent = agent
        self._extractor = StateExtractor()
        self._parser = ActionParser()

    @property
    def agent(self) -> BattleAgent:
        return self._agent

    def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        state = self._extractor.extract(battle)
        action = self._agent.choose_action(state)

        logger.debug(
            "[%s] Turn %d · %s (%.0f%% HP) vs %s (%.0f%% HP) · moves=%s switches=%s → %s",
            self.username,
            battle.turn,
            state.active.species,
            state.active.hp * 100,
            state.opp_active.species,
            state.opp_active.hp * 100,
            state.moves,
            state.switches,
            action,
        )

        return self._parser.parse(action, battle, self)
