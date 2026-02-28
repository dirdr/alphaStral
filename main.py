"""
AlphaStral — entry point.

Local server (default — no auth required):
    uv run python main.py --p1 random --p2 random --n 1
    uv run python main.py --p1 random --p2 random --n 10

Public Showdown server (requires credentials in .env):
    uv run python main.py --p1 random --p2 random --n 1 --showdown

Start a local server with:
    npx -y pokemon-showdown
"""

from __future__ import annotations

import argparse

from poke_env import LocalhostServerConfiguration, ShowdownServerConfiguration

from benchmark.runner import BattleRunner
from bot.agent import BattleAgent
from bot.agents.random import RandomAgent


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
    args = parser.parse_args()

    agent1 = build_agent(args.p1)
    agent2 = build_agent(args.p2)
    server = ShowdownServerConfiguration if args.showdown else LocalhostServerConfiguration

    server_label = "showdown" if args.showdown else "local"
    print(
        f"AlphaStral — {args.p1} vs {args.p2} · {args.n} battle(s) · {args.format} · {server_label}"
    )
    print()

    runner = BattleRunner(server_configuration=server, battle_format=args.format)
    runner.run(agent1, agent2, n_battles=args.n)


if __name__ == "__main__":
    main()
