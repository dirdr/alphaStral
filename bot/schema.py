"""
Data contract shared between the battle bot and the data pipeline.

Both the StateExtractor (live battles) and parse_log.py (replay parsing)
must produce BattleState instances conforming to this schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PokemonState:
    species: str
    hp: float
    fainted: bool
    status: str | None  # "brn" | "par" | "slp" | "frz" | "psn" | "tox" | None


@dataclass
class ActivePokemonState(PokemonState):
    boosts: dict[str, int] = field(
        default_factory=lambda: {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
    )
    ability: str | None = None
    item: str | None = None
    tera_type: str | None = None
    terastallized: bool = False
    moves: list[str] = field(default_factory=list)  # Showdown move IDs


@dataclass
class SideConditions:
    sr: bool = False
    spikes: int = 0  # 0–3
    toxic_spikes: int = 0  # 0–2
    reflect: bool = False
    light_screen: bool = False
    tailwind: bool = False


@dataclass
class BattleState:
    turn: int
    active: ActivePokemonState
    opp_active: ActivePokemonState  # only revealed information
    team: list[PokemonState]  # bench (not active)
    opp_team: list[PokemonState]  # only revealed mons
    weather: str  # "none" | "rain" | "sun" | "sand" | "snow"
    terrain: str  # "none" | "electric" | "grassy" | "psychic" | "misty"
    field: list[str]  # e.g. ["trick_room"]
    my_side: SideConditions
    opp_side: SideConditions
    can_tera: bool
    moves: list[str]  # available move IDs for this turn
    switches: list[str]  # available switch target species names


@dataclass
class MoveAction:
    move_id: str
    tera: bool = False
    reasoning: str = ""


@dataclass
class SwitchAction:
    switch_to: str
    reasoning: str = ""


BattleAction = MoveAction | SwitchAction
