"""
AlphaStral — entry point.

Local server (default — no auth required):
    uv run python main.py --p1 random --p2 random --n 1
    uv run python main.py --p1 random --p2 random --n 10

Public Showdown server (requires credentials in .env):
    uv run python main.py --p1 random --p2 random --n 1 --showdown

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

from dotenv import load_dotenv
from poke_env import LocalhostServerConfiguration, ShowdownServerConfiguration
from poke_env.ps_client import AccountConfiguration

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


def build_agent(name: str) -> BattleAgent:
    """Agent registry. Add new agents here — nothing else needs to change."""
    match name:
        case "random":
            return RandomAgent()
        # Uncomment when ready:
        # case "mistral-large":
        #     from bot.agents.mistral import MistralAgent
        #     return MistralAgent(model_id="mistral-large-latest")
        # case "mistral-finetuned":
        #     import os
        #     from bot.agents.mistral import MistralAgent
        #     return MistralAgent(model_id=os.environ["FINETUNED_MODEL_ID"])
        case _:
            raise ValueError(f"Unknown agent '{name}'. Available: random")


def main() -> None:
    parser = argparse.ArgumentParser(description="AlphaStral battle runner")
    parser.add_argument("--p1", default="random", help="Agent for player 1")
    parser.add_argument("--p2", default="random", help="Agent for player 2")
    parser.add_argument("--n", type=int, default=1, help="Number of battles")
    parser.add_argument("--format", default="gen9randombattle", help="Battle format")
    parser.add_argument(
        "--showdown",
        action="store_true",
        help="Use public Showdown server (requires credentials). Default: local.",
    )
    parser.add_argument(
        "--move-delay",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Seconds to wait before submitting each move. Use >0 to slow battles for live spectating. Default: 0.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO").upper(),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (also reads LOG_LEVEL env var). Default: INFO.",
    )
    args = parser.parse_args()

    _setup_logging(args.log_level)

    agent1 = build_agent(args.p1)
    agent2 = build_agent(args.p2)
    server = ShowdownServerConfiguration if args.showdown else LocalhostServerConfiguration

    if args.showdown:
        load_dotenv()
        account1 = AccountConfiguration(
            os.environ["SHOWDOWN_USER_1"], os.environ["SHOWDOWN_PASS_1"]
        )
        account2 = AccountConfiguration(
            os.environ["SHOWDOWN_USER_2"], os.environ["SHOWDOWN_PASS_2"]
        )
        logger.debug(
            "Credentials loaded: p1=%s p2=%s (passwords redacted)",
            account1.username,
            account2.username,
        )
    else:
        account1 = account2 = None
        logger.debug("Local mode: using auto-generated guest accounts (no auth).")

    server_label = "showdown" if args.showdown else "local"
    logger.info(
        "Starting: %s vs %s · %d battle(s) · %s · %s",
        args.p1,
        args.p2,
        args.n,
        args.format,
        server_label,
    )
    logger.debug("WebSocket: %s", server.websocket_url)

    print(
        f"AlphaStral — {args.p1} vs {args.p2} · {args.n} battle(s) · {args.format} · {server_label}"
    )
    print()

    runner = BattleRunner(
        server_configuration=server,
        battle_format=args.format,
        account1=account1,
        account2=account2,
        move_delay=args.move_delay,
    )
    runner.run(agent1, agent2, n_battles=args.n)


if __name__ == "__main__":
    main()
