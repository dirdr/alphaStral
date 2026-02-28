"""
Shared prompt-building, response-parsing, and base class for LLM battle agents.

Both MistralAgent and HFAgent inherit LLMBattleAgent from here.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from abc import abstractmethod

from benchmark.types import TurnStat
from bot.agent import BattleAgent
from bot.schema import BattleAction, BattleState, MoveAction, SideConditions, SwitchAction

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a competitive Pokémon player. Your goal is to win battles.
Follow these principles strictly, in priority order:

DECISION PRIORITY (apply top to bottom each turn):
1. KO NOW — if you can knock out the opponent this turn, use the most damaging move.
2. ESCAPE BAD MATCHUP — if the opponent is super-effective against you AND you have \
a resist on your bench, switch to it.
3. HIT SUPER-EFFECTIVELY — use a super-effective move if available.
4. SETUP — use a stat-boosting move (Swords Dance, Nasty Plot, Calm Mind…) only when \
the opponent clearly cannot KO you next turn.
5. STATUS — use a status move (Toxic, Will-O-Wisp, Thunder Wave…) when you have a \
significant HP advantage.
6. BEST MOVE — otherwise use your highest base-power move.

SWITCHING RULES:
- Switch when your type is weak to the opponent's last used move AND a bench Pokémon \
resists or is immune to it.
- Never switch into a fainted or critically low HP Pokémon unless it is your only option.
- Preserve your strongest Pokémon for the late game.

TYPE CHART (attacker > defender):
Fire     > Grass, Ice, Bug, Steel
Water    > Fire, Rock, Ground
Electric > Water, Flying  |  immune: Ground
Grass    > Water, Rock, Ground
Ice      > Dragon, Flying, Grass, Ground
Fighting > Normal, Rock, Steel, Ice, Dark
Ground   > Fire, Electric, Poison, Rock, Steel  |  immune: Flying
Psychic  > Fighting, Poison
Dark     > Psychic, Ghost
Dragon   > Dragon
Steel    > Ice, Rock, Fairy
Fairy    > Dragon, Dark, Fighting
Ghost    > Ghost, Psychic
Poison   > Grass, Fairy
Rock     > Fire, Ice, Flying, Bug
Flying   > Grass, Fighting, Bug
Bug      > Grass, Psychic, Dark

TERASTALLIZATION:
Use tera when it lets you hit super-effectively for a KO, or removes a weakness that \
would otherwise cause you to faint.

Respond ONLY with a single valid JSON object — no markdown, no explanation outside it.
"""


def _fmt_mon(species: str, hp: float, status: str | None, fainted: bool) -> str:
    if fainted:
        return f"{species} [fainted]"
    s = f"{species} {hp * 100:.0f}%HP"
    if status:
        s += f" [{status}]"
    return s


def _side_str(s: SideConditions) -> str:
    parts = []
    if s.sr:
        parts.append("stealth_rock")
    if s.spikes:
        parts.append(f"spikes×{s.spikes}")
    if s.toxic_spikes:
        parts.append(f"toxic_spikes×{s.toxic_spikes}")
    if s.reflect:
        parts.append("reflect")
    if s.light_screen:
        parts.append("light_screen")
    if s.tailwind:
        parts.append("tailwind")
    return ", ".join(parts) if parts else "none"


def _build_prompt(state: BattleState) -> str:
    lines: list[str] = []
    lines.append(f"Turn {state.turn}")
    lines.append("")

    # Active mons
    a = state.active
    boosts = ", ".join(f"{k}:{v:+d}" for k, v in a.boosts.items() if v != 0)
    active_line = f"Your active: {a.species} {a.hp * 100:.0f}%HP"
    if a.status:
        active_line += f" [{a.status}]"
    if boosts:
        active_line += f" boosts={boosts}"
    if a.ability:
        active_line += f" ability={a.ability}"
    if a.item:
        active_line += f" item={a.item}"
    if a.terastallized:
        active_line += f" [terastallized:{a.tera_type}]"
    elif a.tera_type and state.can_tera:
        active_line += f" (can tera:{a.tera_type})"
    if a.moves:
        active_line += f" known_moves={a.moves}"
    lines.append(active_line)

    o = state.opp_active
    opp_boosts = ", ".join(f"{k}:{v:+d}" for k, v in o.boosts.items() if v != 0)
    opp_line = f"Opponent active: {o.species} {o.hp * 100:.0f}%HP"
    if o.status:
        opp_line += f" [{o.status}]"
    if opp_boosts:
        opp_line += f" boosts={opp_boosts}"
    if o.terastallized:
        opp_line += f" [terastallized:{o.tera_type}]"
    if o.moves:
        opp_line += f" known_moves={o.moves}"
    lines.append(opp_line)

    lines.append("")

    # Bench
    if state.team:
        bench = ", ".join(_fmt_mon(m.species, m.hp, m.status, m.fainted) for m in state.team)
        lines.append(f"Your bench: {bench}")
    if state.opp_team:
        opp_bench = ", ".join(
            _fmt_mon(m.species, m.hp, m.status, m.fainted) for m in state.opp_team
        )
        lines.append(f"Opponent revealed bench: {opp_bench}")

    # Field
    lines.append("")
    lines.append(f"Weather: {state.weather}  Terrain: {state.terrain}")
    if state.field:
        lines.append(f"Field conditions: {', '.join(state.field)}")

    lines.append(f"Your side: {_side_str(state.my_side)}")
    lines.append(f"Opponent side: {_side_str(state.opp_side)}")

    # Actions
    lines.append("")
    lines.append(f"Available moves: {state.moves if state.moves else '(none)'}")
    lines.append(f"Available switches: {state.switches if state.switches else '(none)'}")

    # Instruction
    lines.append("")
    lines.append(
        "Choose one action. Respond ONLY with a JSON object matching one of these shapes:\n"
        '  {"action_type": "move", "move_id": "<id>", "tera": false, "reasoning": "..."}\n'
        '  {"action_type": "switch", "switch_to": "<species>", "reasoning": "..."}'
    )

    return "\n".join(lines)


def _random_fallback(state: BattleState) -> BattleAction:
    options: list[BattleAction] = [MoveAction(move_id=m) for m in state.moves] + [
        SwitchAction(switch_to=s) for s in state.switches
    ]
    if not options:
        return MoveAction(move_id="struggle")
    return random.choice(options)


def _parse_action(raw: str, state: BattleState, model_id: str) -> BattleAction:
    """Parse a model response into a legal BattleAction.

    Tries strict JSON first, then falls back to extracting a JSON object
    from free-text responses (e.g. wrapped in markdown code fences).
    Returns a random legal action if parsing fails or the chosen action is illegal.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            logger.warning("[%s] No JSON found in response — falling back.", model_id)
            return _random_fallback(state)
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            logger.warning("[%s] Could not parse extracted JSON — falling back.", model_id)
            return _random_fallback(state)

    action_type = data.get("action_type")

    if action_type == "move":
        move_id = str(data.get("move_id", "")).strip()
        if move_id not in state.moves:
            logger.warning(
                "[%s] Model chose move '%s' not in legal moves %s — falling back.",
                model_id,
                move_id,
                state.moves,
            )
            return _random_fallback(state)
        return MoveAction(
            move_id=move_id,
            tera=bool(data.get("tera", False)),
            reasoning=str(data.get("reasoning", "")),
        )

    if action_type == "switch":
        switch_to = str(data.get("switch_to", "")).strip()
        if switch_to not in state.switches:
            logger.warning(
                "[%s] Model chose switch '%s' not in legal switches %s — falling back.",
                model_id,
                switch_to,
                state.switches,
            )
            return _random_fallback(state)
        return SwitchAction(
            switch_to=switch_to,
            reasoning=str(data.get("reasoning", "")),
        )

    logger.warning("[%s] Unknown action_type '%s' — falling back.", model_id, action_type)
    return _random_fallback(state)


class LLMBattleAgent(BattleAgent):
    """Base class for LLM agents with per-battle conversation history.

    Subclasses only need to implement _call_api(messages) -> str.
    History resets automatically at turn 1 of each new battle.
    """

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id
        self._histories: dict[str, list[dict]] = {}  # battle_tag -> messages
        self._turn_stats: list[TurnStat] = []

    @property
    def name(self) -> str:
        return self._model_id

    @property
    def turn_stats(self) -> list[TurnStat]:
        return self._turn_stats

    @abstractmethod
    def _call_api(self, messages: list[dict]) -> str:
        """Call the model and return raw text response."""
        ...

    def choose_action(self, state: BattleState) -> BattleAction:
        tag = state.battle_tag or str(id(self))
        if state.turn == 1 or tag not in self._histories:
            self._histories[tag] = []

        history = self._histories[tag]
        prompt = _build_prompt(state)
        messages = (
            [{"role": "system", "content": _SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": prompt}]
        )

        logger.debug("[%s] Turn %d · history=%d msgs", self._model_id, state.turn, len(history))

        t0 = time.perf_counter()
        try:
            raw = self._call_api(messages)
            decision_ms = (time.perf_counter() - t0) * 1000
            logger.debug("[%s] Response: %s", self._model_id, raw)
            action = _parse_action(raw, state, self._model_id)
            used_fallback = False
            history += [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": raw},
            ]
        except Exception as exc:
            decision_ms = (time.perf_counter() - t0) * 1000
            logger.warning("[%s] Error (%s), falling back to random.", self._model_id, exc)
            action = _random_fallback(state)
            used_fallback = True

        self._turn_stats.append(
            TurnStat(
                battle_tag=tag,
                turn=state.turn,
                agent=self._model_id,
                decision_ms=decision_ms,
                used_fallback=used_fallback,
                history_msgs=len(history),
                action_type=type(action).__name__.replace("Action", "").lower(),
            )
        )

        logger.debug("[%s] Chose: %s", self._model_id, action)
        return action
