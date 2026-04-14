"""CLI entry point — run and check commands via argparse."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="swarmlet",
        description="Swarmlet — simulate cellular automata and agent-based swarms on a 2D grid",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a Swarmlet program")
    run_parser.add_argument("file", help="Path to .swl file")
    run_parser.add_argument("-t", "--ticks", type=int, default=100, help="Number of ticks to simulate")
    run_parser.add_argument("-o", "--output", help="Output file path (.jsonl or .npz)")
    run_parser.add_argument("-s", "--seed", type=int, default=42, help="RNG seed for deterministic runs")

    check_parser = subparsers.add_parser("check", help="Parse and analyze without execution")
    check_parser.add_argument("file", help="Path to .swl file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        print(f"swarmlet run: not yet implemented (file={args.file}, ticks={args.ticks})")
        sys.exit(1)

    if args.command == "check":
        print(f"swarmlet check: not yet implemented (file={args.file})")
        sys.exit(1)
