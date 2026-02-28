"""
StateExtractor: converts a poke-env Battle object into a BattleState.

This is the live-battle counterpart of pipeline/parse_log.py.
Both must produce BattleState instances that match the schema exactly.
"""

from __future__ import annotations

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.battle import Battle
from poke_env.battle.field import Field
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather

from bot.schema import (
    ActivePokemonState,
    BattleState,
    PokemonState,
    SideConditions,
)

_WEATHER_MAP: dict[Weather, str] = {
    Weather.RAINDANCE: "rain",
    Weather.SUNNYDAY: "sun",
    Weather.SANDSTORM: "sand",
    Weather.SNOWSCAPE: "snow",
    Weather.HAIL: "snow",
}

_TERRAIN_MAP: dict[Field, str] = {
    Field.ELECTRIC_TERRAIN: "electric",
    Field.GRASSY_TERRAIN: "grassy",
    Field.PSYCHIC_TERRAIN: "psychic",
    Field.MISTY_TERRAIN: "misty",
}

_FIELD_NAMES: dict[Field, str] = {
    Field.TRICK_ROOM: "trick_room",
    Field.GRAVITY: "gravity",
}


class StateExtractor:
    """Converts a poke-env Battle into a BattleState."""

    def extract(self, battle: AbstractBattle) -> BattleState:
        assert isinstance(battle, Battle), "Only single battles are supported."

        active = self._extract_active(battle.active_pokemon)
        opp_active = self._extract_active(battle.opponent_active_pokemon)

        team = [
            self._extract_bench(mon)
            for mon in battle.team.values()
            if mon.species != (battle.active_pokemon.species if battle.active_pokemon else "")
        ]
        opp_team = [
            self._extract_bench(mon)
            for mon in battle.opponent_team.values()
            if mon.species
            != (battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else "")
        ]

        return BattleState(
            turn=battle.turn,
            active=active,
            opp_active=opp_active,
            team=team,
            opp_team=opp_team,
            weather=self._extract_weather(battle),
            terrain=self._extract_terrain(battle),
            field=self._extract_field(battle),
            my_side=self._extract_side(battle.side_conditions),
            opp_side=self._extract_side(battle.opponent_side_conditions),
            can_tera=battle.can_tera,
            moves=[m.id for m in battle.available_moves],
            switches=[p.species for p in battle.available_switches],
        )

    def _extract_active(self, mon: Pokemon | None) -> ActivePokemonState:
        if mon is None:
            return ActivePokemonState(species="unknown", hp=0.0, fainted=True, status=None)
        return ActivePokemonState(
            species=mon.species,
            hp=mon.current_hp_fraction,
            fainted=mon.fainted,
            status=mon.status.name.lower() if mon.status else None,
            boosts=dict(mon.boosts),
            ability=mon.ability,
            item=mon.item,
            tera_type=mon.tera_type.name.lower() if mon.tera_type else None,
            terastallized=mon.is_terastallized,
            moves=[m.id for m in mon.moves.values()],
        )

    def _extract_bench(self, mon: Pokemon) -> PokemonState:
        return PokemonState(
            species=mon.species,
            hp=mon.current_hp_fraction,
            fainted=mon.fainted,
            status=mon.status.name.lower() if mon.status else None,
        )

    def _extract_weather(self, battle: Battle) -> str:
        for weather in battle.weather:
            if weather in _WEATHER_MAP:
                return _WEATHER_MAP[weather]
        return "none"

    def _extract_terrain(self, battle: Battle) -> str:
        for field in battle.fields:
            if field in _TERRAIN_MAP:
                return _TERRAIN_MAP[field]
        return "none"

    def _extract_field(self, battle: Battle) -> list[str]:
        return [_FIELD_NAMES[f] for f in battle.fields if f in _FIELD_NAMES]

    def _extract_side(self, conditions: dict[SideCondition, int]) -> SideConditions:
        return SideConditions(
            sr=SideCondition.STEALTH_ROCK in conditions,
            spikes=conditions.get(SideCondition.SPIKES, 0),
            toxic_spikes=conditions.get(SideCondition.TOXIC_SPIKES, 0),
            reflect=SideCondition.REFLECT in conditions,
            light_screen=SideCondition.LIGHT_SCREEN in conditions,
            tailwind=SideCondition.TAILWIND in conditions,
        )
