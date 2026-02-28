"""
AlphaStral — entry point.

    uv run python main.py --p1 random --p2 random --n 1
    uv run python main.py --p1 random --p2 random --n 10

Start a local server with:
    node pokemon-showdown start --no-security

Log level (default INFO, set via env or flag):
    LOG_LEVEL=DEBUG uv run python main.py ...
    uv run python main.py --log-level DEBUG ...
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from poke_env import LocalhostServerConfiguration

from benchmark.export import write_report
from benchmark.runner import BattleRunner
from bot.agent import BattleAgent
from bot.agents.random import RandomAgent

logger = logging.getLogger(__name__)


def _setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.WARNING)  # silence third-party noise by default

    # Our packages follow the user-specified level.
    for name in ("__main__", "benchmark", "bot"):
        logging.getLogger(name).setLevel(level)

    if level == logging.DEBUG:
        # Also surface poke-env authentication and connection events.
        logging.getLogger("poke_env.ps_client.ps_client").setLevel(logging.DEBUG)


def _safe(name: str) -> str:
    """Sanitize an agent name for use in a filename."""
    return re.sub(r"[^a-zA-Z0-9_-]", "-", name)


def _default_output(p1: str, p2: str, n: int) -> str:
    tag = uuid.uuid4().hex[:6]
    filename = f"{_safe(p1)}_vs_{_safe(p2)}_n{n}_{tag}.json"
    return str(Path("runs") / filename)


def build_agent(name: str) -> BattleAgent:
    """Agent registry. Add new agents here — nothing else needs to change.

    Available agents:
      random
      mistral:<model-id>   e.g. mistral:mistral-large-latest, mistral:ft:your-job-id
      hf:<model-id>        e.g. hf:your-org/your-finetuned-model
    """
    if name == "random":
        return RandomAgent()
    if name.startswith("mistral:"):
        from bot.agents.mistral import MistralAgent

        return MistralAgent(model_id=name.removeprefix("mistral:"))
    if name.startswith("hf:"):
        from bot.agents.hf import HFAgent

        return HFAgent(model_id=name.removeprefix("hf:"))
    raise ValueError(
        f"Unknown agent '{name}'. Available: random, mistral:<model-id>, hf:<model-id>"
    )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="AlphaStral battle runner")
    parser.add_argument("--p1", default="random", help="Agent for player 1")
    parser.add_argument("--p2", default="random", help="Agent for player 2")
    parser.add_argument("--n", type=int, default=1, help="Number of battles")
    parser.add_argument("--format", default="gen9randombattle", help="Battle format")
    parser.add_argument(
        "--move-delay",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Seconds to wait before submitting each move. Use >0 to slow battles for live spectating. Pass 0 to also disable the LLM rate-limit throttle. Default: auto (1 s throttle for LLM agents, 0 for random).",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO").upper(),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (also reads LOG_LEVEL env var). Default: INFO.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Write JSON report to this path (default: runs/<p1>_vs_<p2>_n<n>_<hash>.json).",
    )
    args = parser.parse_args()

    _setup_logging(args.log_level)

    agent1 = build_agent(args.p1)
    agent2 = build_agent(args.p2)

    # If --move-delay 0 is explicit, disable the LLM rate-limit throttle too.
    if args.move_delay == 0:
        from bot.agents._shared import LLMBattleAgent

        for agent in (agent1, agent2):
            if isinstance(agent, LLMBattleAgent):
                agent._throttle_s = 0.0

    logger.info(
        "Starting: %s vs %s · %d battle(s) · %s · local",
        args.p1,
        args.p2,
        args.n,
        args.format,
    )
    logger.debug("WebSocket: %s", LocalhostServerConfiguration.websocket_url)

    print(f"AlphaStral — {args.p1} vs {args.p2} · {args.n} battle(s) · {args.format} · local")
    print()

    runner = BattleRunner(
        server_configuration=LocalhostServerConfiguration,
        battle_format=args.format,
        move_delay=args.move_delay or 0.0,
    )
    report = runner.run(agent1, agent2, n_battles=args.n)

    out = args.output or _default_output(args.p1, args.p2, args.n)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    write_report(report, out)
    print(f"  Report saved to {out}")


if __name__ == "__main__":
    main()
