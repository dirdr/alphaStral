"""
AgentPlayer: poke-env bridge. Written once, never modified.

Wires together StateExtractor → BattleAgent → ActionParser.
To use a different model, pass a different BattleAgent — that's all.
"""

from __future__ import annotations

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.player import Player

from bot.agent import BattleAgent
from bot.extractor import StateExtractor
from bot.parser import ActionParser


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
        return self._parser.parse(action, battle, self)
