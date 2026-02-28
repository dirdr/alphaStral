"""
MistralAgent: calls the Mistral API each turn to choose a battle action.

Reads MISTRAL_API_KEY from the environment (loaded via load_dotenv() in main.py).
Falls back to a random legal action on any API or parsing failure.
"""

from __future__ import annotations

import os

from mistralai import Mistral

from bot.agents._shared import LLMBattleAgent


class MistralAgent(LLMBattleAgent):
    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    def _call_api(self, messages: list[dict]) -> str:
        try:
            r = self._client.chat.complete(
                model=self._model_id,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=150,
            )
        except (OSError, AttributeError):
            # HTTP connection was broken (e.g. after a KeyboardInterrupt) — recreate client.
            self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
            r = self._client.chat.complete(
                model=self._model_id,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=150,
            )
        return r.choices[0].message.content or ""
