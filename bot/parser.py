"""
ActionParser: converts a BattleAction into a poke-env BattleOrder.

Falls back to a random legal move if the action is invalid.
Logs every fallback so we can track model reliability.
"""

from __future__ import annotations

import logging

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.player import Player

from bot.schema import BattleAction, MoveAction, SwitchAction

logger = logging.getLogger(__name__)


class ActionParser:
    """Translates BattleAction → poke-env BattleOrder.

    Requires a reference to the Player instance to call create_order()
    and choose_random_move() for fallbacks.
    """

    def parse(
        self,
        action: BattleAction,
        battle: AbstractBattle,
        player: Player,
    ) -> BattleOrder:
        if isinstance(action, MoveAction):
            return self._parse_move(action, battle, player)
        elif isinstance(action, SwitchAction):
            return self._parse_switch(action, battle, player)
        else:
            logger.warning("Unknown action type %s — falling back to random.", type(action))
            return player.choose_random_move(battle)

    def _parse_move(
        self, action: MoveAction, battle: AbstractBattle, player: Player
    ) -> BattleOrder:
        move = next(
            (m for m in battle.available_moves if m.id == action.move_id),
            None,
        )
        if move is None:
            logger.warning(
                "Move '%s' not in available moves %s — falling back to random.",
                action.move_id,
                [m.id for m in battle.available_moves],
            )
            return player.choose_random_move(battle)

        logger.debug("Parsed move: %s (tera=%s)", move.id, action.tera)
        return player.create_order(move, terastallize=action.tera)

    def _parse_switch(
        self, action: SwitchAction, battle: AbstractBattle, player: Player
    ) -> BattleOrder:
        target = next(
            (p for p in battle.available_switches if p.species == action.switch_to),
            None,
        )
        if target is None:
            logger.warning(
                "Switch target '%s' not in available switches %s — falling back to random.",
                action.switch_to,
                [p.species for p in battle.available_switches],
            )
            return player.choose_random_move(battle)

        logger.debug("Parsed switch: → %s", target.species)
        return player.create_order(target)
