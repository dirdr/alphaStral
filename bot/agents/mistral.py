"""
MistralAgent: calls the Mistral API each turn to choose a battle action.

Reads MISTRAL_API_KEY from the environment automatically (mistralai SDK default).
Falls back to a random legal action on any API or parsing failure.
"""

from __future__ import annotations

import logging

from mistralai import Mistral

from bot.agent import BattleAgent
from bot.agents._shared import _SYSTEM_PROMPT, _build_prompt, _parse_action, _random_fallback
from bot.schema import BattleAction, BattleState

logger = logging.getLogger(__name__)


class MistralAgent(BattleAgent):
    """Calls the Mistral chat API to pick a move each turn."""

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id
        self._client = Mistral()  # reads MISTRAL_API_KEY from env

    @property
    def name(self) -> str:
        return self._model_id

    def choose_action(self, state: BattleState) -> BattleAction:
        prompt = _build_prompt(state)
        logger.debug("[%s] Prompt:\n%s", self._model_id, prompt)

        try:
            response = self._client.chat.complete(
                model=self._model_id,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            logger.debug("[%s] Raw response: %s", self._model_id, raw)
            action = _parse_action(raw, state, self._model_id)
        except Exception as exc:
            logger.warning(
                "[%s] API/parse error (%s), falling back to random.", self._model_id, exc
            )
            action = _random_fallback(state)

        logger.debug("[%s] Chose: %s", self._model_id, action)
        return action
