"""
Extension point: implement BattleAgent to plug in any decision model.

Adding a new model requires only creating a new subclass here.
The AgentPlayer bridge and BattleRunner never need to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from bot.schema import BattleAction, BattleState


class BattleAgent(ABC):
    """Abstract decision engine.

    Receives a fully-typed BattleState, returns a BattleAction.
    Knows nothing about poke-env internals — pure game logic.
    """

    @abstractmethod
    def choose_action(self, state: BattleState) -> BattleAction:
        """Choose the next action given the current battle state."""
        ...

    @property
    def name(self) -> str:
        """Human-readable identifier used in logs and reports."""
        return self.__class__.__name__
