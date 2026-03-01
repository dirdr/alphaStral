"""
LocalAgent: loads a HuggingFace model locally and runs inference with MLX (Apple Silicon).

Usage: local:<hf-model-id>  e.g. local:mistral-hackaton-2026/ministral-3b-pokemon-showdown
"""

from __future__ import annotations

import logging
import os

from mlx_lm import generate, load

from bot.agents._shared import LLMBattleAgent

logger = logging.getLogger(__name__)


class LocalAgent(LLMBattleAgent):
    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self._model = None
        self._tokenizer = None
        self._load_model()

    def _load_model(self) -> None:
        hf_token = os.environ.get("HF_TOKEN")
        logger.info("Loading model %s with MLX...", self._model_id)
        print(f"Loading {self._model_id} with MLX (first load may take a few minutes)...")
        self._model, self._tokenizer = load(self._model_id, tokenizer_config={"token": hf_token})
        print("Model loaded.")

    def _call_api(self, messages: list[dict]) -> str:
        prompt = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        raw = generate(self._model, self._tokenizer, prompt=prompt, max_tokens=200, verbose=False)
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
        logger.warning("[local] raw='%s'", raw[:300])
        return raw
