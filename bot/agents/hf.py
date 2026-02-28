"""
HFAgent: calls the HuggingFace Inference API each turn to choose a battle action.

Uses text_generation with the Mistral instruction format, matching the training
data distribution (plain-text move name output). Converts the raw response to
JSON before passing it to the shared parser.
"""

from __future__ import annotations

import json
import logging
import os
import re

from huggingface_hub import InferenceClient

from bot.agents._shared import LLMBattleAgent
from bot.schema import BattleState

logger = logging.getLogger(__name__)


def _build_finetuned_prompt(state: BattleState) -> str:
    """Prompt format matching the fine-tuning training data."""
    a = state.active
    o = state.opp_active
    return (
        f"Turn {state.turn}. Weather: {state.weather}. "
        f"Your pokemon: {a.species} ({a.hp * 100:.0f}/100 HP, {a.status or 'healthy'}). "
        f"Opponent: {o.species} ({o.hp * 100:.0f}/100 HP, {o.status or 'healthy'}). "
        f"Available moves: {', '.join(state.moves)}. "
        f"What move do you use?"
    )


class HFAgent(LLMBattleAgent):
    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self._client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))
        self._current_state: BattleState | None = None

    def choose_action(self, state: BattleState):
        self._current_state = state
        return super().choose_action(state)

    def _call_api(self, messages: list[dict]) -> str:
        prompt = _build_finetuned_prompt(self._current_state)
        instruct_prompt = f"<s>[INST] {prompt} [/INST]"
        raw = self._client.text_generation(
            instruct_prompt,
            model=self._model_id,
            max_new_tokens=50,
        )
        # raw is e.g. "Flash Cannon (fire, 90pw, special)"
        # Extract move name and convert to Showdown ID
        move_name = raw.strip().split("(")[0].strip()
        move_id = re.sub(r"[^a-z0-9]", "", move_name.lower())
        logger.debug("[%s] raw='%s' → move_id='%s'", self._model_id, raw.strip(), move_id)
        return json.dumps({"action_type": "move", "move_id": move_id, "tera": False})
