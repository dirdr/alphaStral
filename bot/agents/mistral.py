"""
MistralAgent: calls the Mistral API each turn to choose a battle action.

Reads MISTRAL_API_KEY from the environment (loaded via load_dotenv() in main.py).
Falls back to a random legal action on any API or parsing failure.
"""

from __future__ import annotations

import logging
import os
import time

from mistralai import Mistral
from mistralai.models import SDKError

from bot.agents._shared import LLMBattleAgent

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [5, 15, 30]  # seconds between retries on 429


class MistralAgent(LLMBattleAgent):
    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    def _call_api(self, messages: list[dict]) -> str:
        for attempt, delay in enumerate([0] + _RETRY_DELAYS):
            if delay:
                logger.warning(
                    "[%s] Rate limited — retrying in %ds (attempt %d/%d).",
                    self._model_id,
                    delay,
                    attempt,
                    len(_RETRY_DELAYS),
                )
                time.sleep(delay)
            try:
                r = self._client.chat.complete(
                    model=self._model_id,
                    messages=messages,
                    response_format={"type": "json_object"},
                    max_tokens=150,
                )
                return r.choices[0].message.content or ""
            except (OSError, AttributeError):
                self._client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
            except SDKError as e:
                if e.status_code != 429:
                    raise
        raise SDKError("Rate limit exceeded after all retries", None, "")
