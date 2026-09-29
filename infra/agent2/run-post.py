"""CLI for the Agent2 post-draft crew (Researcher → Writer → Editor)."""
from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agent2"))

from crew_post import run_post_draft  # noqa: E402
from llm import model_name  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", metavar="TOPIC", help="run once for TOPIC and exit")
    parser.add_argument("--quiet", action="store_true", help="less crew verbose output")
    args = parser.parse_args()
    verbose = not args.quiet

    if args.once:
        print(run_post_draft(args.once, verbose=verbose))
        return

    print(f"Agent2 черновик поста (model={model_name()}). Пустая строка или 'exit' — выход.")
    while True:
        try:
            topic = input("\nТема> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not topic or topic.lower() in {"exit", "quit"}:
            return
        print()
        print(run_post_draft(topic, verbose=verbose))


if __name__ == "__main__":
    main()
