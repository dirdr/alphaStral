"""RandomAgent: picks a random legal action each turn."""

from __future__ import annotations

import random
import uuid

from bot.agent import BattleAgent
from bot.schema import BattleAction, BattleState, MoveAction, SwitchAction


class RandomAgent(BattleAgent):
    """Chooses uniformly at random between all legal moves and switches."""

    def __init__(self) -> None:
        self._name = f"random-{uuid.uuid4().hex[:6]}"

    @property
    def name(self) -> str:
        return self._name

    def choose_action(self, state: BattleState) -> BattleAction:
        all_options: list[BattleAction] = [
            MoveAction(move_id=move_id) for move_id in state.moves
        ] + [SwitchAction(switch_to=species) for species in state.switches]

        if not all_options:
            # Forced pass (e.g. only struggle available — shouldn't happen in normal flow)
            return MoveAction(move_id="struggle")

        return random.choice(all_options)
