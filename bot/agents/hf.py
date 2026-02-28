"""
HFAgent: calls the HuggingFace Inference API each turn to choose a battle action.

Reads HF_TOKEN from the environment (required for private/fine-tuned models).
Falls back to a random legal action on any API or parsing failure.
"""

from __future__ import annotations

import os

from huggingface_hub import InferenceClient

from bot.agents._shared import LLMBattleAgent


class HFAgent(LLMBattleAgent):
    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self._client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))

    @property
    def name(self) -> str:
        return self._model_id.split("/")[-1]

    def _call_api(self, messages: list[dict]) -> str:
        r = self._client.chat.completions.create(
            model=self._model_id,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return r.choices[0].message.content or ""
