"""CLI entry point — run and check commands via argparse."""

import argparse
import sys
import time

from swarmlet import __version__
from swarmlet.errors import SwarmletError


def main():
    parser = argparse.ArgumentParser(
        prog="swarmlet",
        description="Swarmlet — simulate cellular automata and agent-based swarms on a 2D grid",
    )
    parser.add_argument("--version", action="version", version=f"swarmlet {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run", help="Run a Swarmlet program")
    run_parser.add_argument("file", help="Path to .swl file")
    run_parser.add_argument("-t", "--ticks", type=int, default=100, help="Number of ticks (default: 100)")
    run_parser.add_argument("-o", "--out", help="Output file path (.jsonl or .npz)")
    run_parser.add_argument("-s", "--seed", type=int, default=0, help="RNG seed (default: 0)")
    run_parser.add_argument("-e", "--every", type=int, default=1, help="Write every N-th tick (default: 1)")
    run_parser.add_argument("-p", "--param", action="append", default=[],
                            help="Override a param: KEY=VALUE (can be repeated)")

    # check
    check_parser = subparsers.add_parser("check", help="Parse and analyze without execution")
    check_parser.add_argument("file", help="Path to .swl file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "run":
            _run(args)
        elif args.command == "check":
            _check(args)
    except SwarmletError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_params(param_list):
    """Parse --param KEY=VALUE arguments into a dict."""
    params = {}
    for p in param_list:
        if "=" not in p:
            print(f"Error: invalid --param format: {p!r} (expected KEY=VALUE)", file=sys.stderr)
            sys.exit(1)
        key, val = p.split("=", 1)
        try:
            params[key.strip()] = float(val.strip())
        except ValueError:
            print(f"Error: invalid --param value: {val!r} (must be a number)", file=sys.stderr)
            sys.exit(1)
    return params


def _run(args):
    from swarmlet.parser import parse
    from swarmlet.analyzer import analyze
    from swarmlet.engine import World
    from swarmlet.snapshot import write_jsonl, write_npz

    with open(args.file) as f:
        source = f.read()

    prog = parse(source)
    analyze(prog)

    params = _parse_params(args.param)
    world = World(prog, seed=args.seed, params=params or None)

    start = time.time()

    if args.out:
        ext = args.out.rsplit(".", 1)[-1].lower()
        if ext == "jsonl":
            write_jsonl(world, args.out, ticks=args.ticks, every=args.every)
        elif ext == "npz":
            write_npz(world, args.out, ticks=args.ticks, every=args.every)
        else:
            print(f"Error: unsupported output format: .{ext}", file=sys.stderr)
            sys.exit(1)
    else:
        world.step(args.ticks)

    elapsed = time.time() - start

    # Summary
    snap = world.snapshot()
    agent_counts = {}
    for a in snap["agents"]:
        t = a["type"]
        agent_counts[t] = agent_counts.get(t, 0) + 1

    print(f"Ticks: {args.ticks}")
    print(f"Elapsed: {elapsed:.2f}s")
    if agent_counts:
        for t, c in sorted(agent_counts.items()):
            print(f"  {t}: {c}")
    if args.out:
        snapshot_count = 1 + args.ticks // args.every
        print(f"Snapshots written: {snapshot_count} to {args.out}")


def _check(args):
    from swarmlet.parser import parse
    from swarmlet.analyzer import analyze

    with open(args.file) as f:
        source = f.read()

    prog = parse(source)
    analyze(prog)
    print(f"OK: {args.file} parsed and analyzed successfully")
