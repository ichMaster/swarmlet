"""swarmlet-viz CLI entry point.

Subcommands:
    render <snapshots_file> --out <path> [options]
    info <snapshots_file>
    version

Output format is inferred from the ``--out`` extension:

    .mp4              -> MP4 video
    .gif              -> animated GIF
    _sheet.png        -> contact sheet (grid of N frames)
    .png              -> single-frame PNG

Errors are printed as human-readable messages — no Python tracebacks.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Tuple

from swarmlet import __version__


def _parse_figsize(value: str) -> Tuple[float, float]:
    try:
        parts = value.lower().split("x")
        if len(parts) != 2:
            raise ValueError
        return (float(parts[0]), float(parts[1]))
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            f"--figsize expects 'WxH' (e.g. '8x6'), got {value!r}"
        ) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swarmlet-viz",
        description="Offline visualizer for Swarmlet snapshot files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render snapshots to an output file")
    render.add_argument("snapshots", help="JSONL or NPZ snapshot file")
    render.add_argument("--out", required=True, help="Output path (format inferred from extension)")
    render.add_argument("--preset", help="Apply a built-in preset by name")
    render.add_argument("--field", help="Show this field as background (replaces cells)")
    render.add_argument("--cells-cmap", help="Categorical colormap name for cell states")
    render.add_argument("--field-cmap", help="Continuous colormap for the field layer")
    render.add_argument("--field-vmin", type=float, help="Field color-scale minimum")
    render.add_argument("--field-vmax", type=float, help="Field color-scale maximum")
    render.add_argument("--field-log-scale", action="store_true", help="Use LogNorm for the field")
    render.add_argument("--no-cells", action="store_true", help="Do not draw cell-state background")
    render.add_argument("--no-agents", action="store_true", help="Do not draw agent overlay")
    render.add_argument("--show-heading", action="store_true", help="Draw heading arrows on agents")
    render.add_argument("--fps", type=int, help="Frames per second (default 30 mp4, 15 gif)")
    render.add_argument("--quality", type=int, default=7, help="MP4 quality 1-10 (default 7)")
    render.add_argument("--every", type=int, default=1, help="Keep every Nth snapshot")
    render.add_argument("--frames", type=int, default=12, help="Contact-sheet frame count")
    render.add_argument("--cols", type=int, default=4, help="Contact-sheet columns")
    render.add_argument("--tick", type=int, help="PNG tick to render (default: last)")
    render.add_argument("--title", help="Optional title (PNG/contact sheet) or title template ({t} is the tick)")
    render.add_argument("--dpi", type=int, default=150, help="Raster DPI")
    render.add_argument("--figsize", type=_parse_figsize, help="Figure size as WxH in inches (e.g. 8x6)")

    info = subparsers.add_parser("info", help="Print metadata about a snapshot file")
    info.add_argument("snapshots", help="JSONL or NPZ snapshot file")

    subparsers.add_parser("version", help="Print swarmlet-viz version")

    return parser


def _dispatch_format(out: Path) -> str:
    name = out.name.lower()
    if name.endswith("_sheet.png"):
        return "sheet"
    if name.endswith(".png"):
        return "png"
    if name.endswith(".gif"):
        return "gif"
    if name.endswith(".mp4"):
        return "mp4"
    raise ValueError(
        f"unsupported output extension for '{out}': expected .mp4, .gif, .png, or *_sheet.png"
    )


def _build_spec(args: argparse.Namespace):
    from swarmlet.viz.presets import PRESETS
    from swarmlet.viz.render.composite import FrameSpec

    if args.preset:
        if args.preset not in PRESETS:
            raise ValueError(
                f"unknown preset '{args.preset}'. Available: {sorted(PRESETS)}"
            )
        spec = replace(PRESETS[args.preset])
    else:
        spec = FrameSpec()

    overrides: dict = {}
    if args.no_cells:
        overrides["show_cells"] = False
    if args.no_agents:
        overrides["show_agents"] = False
    if args.field is not None:
        overrides["show_field"] = args.field
    if args.cells_cmap is not None:
        overrides["cells_cmap"] = args.cells_cmap
    if args.field_cmap is not None:
        overrides["field_cmap"] = args.field_cmap
    if args.field_vmin is not None:
        overrides["field_vmin"] = args.field_vmin
    if args.field_vmax is not None:
        overrides["field_vmax"] = args.field_vmax
    if args.field_log_scale:
        overrides["field_log_scale"] = True
    if args.show_heading:
        overrides["show_agent_heading"] = True
    if args.title is not None:
        overrides["title_template"] = args.title
    if args.figsize is not None:
        overrides["figsize"] = args.figsize
    if args.dpi is not None:
        overrides["dpi"] = args.dpi

    return replace(spec, **overrides) if overrides else spec


def _render(args: argparse.Namespace) -> int:
    from swarmlet.viz.model import load_snapshots
    from swarmlet.viz.output.gif import write_gif
    from swarmlet.viz.output.mp4 import write_mp4
    from swarmlet.viz.output.png import write_png, write_png_from_snapshots
    from swarmlet.viz.output.sheet import write_contact_sheet

    snaps_path = Path(args.snapshots)
    if not snaps_path.exists():
        print(f"swarmlet-viz: snapshot file not found: {snaps_path}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    fmt = _dispatch_format(out_path)

    snaps = load_snapshots(snaps_path)
    if args.every > 1:
        snaps = snaps[:: args.every]
    if not snaps:
        print("swarmlet-viz: no snapshots to render", file=sys.stderr)
        return 2

    spec = _build_spec(args)

    start = time.time()
    frame_count = 0
    if fmt == "mp4":
        fps = args.fps if args.fps is not None else 30
        write_mp4(snaps, spec, out_path, fps=fps, quality=args.quality)
        frame_count = len(snaps)
    elif fmt == "gif":
        fps = args.fps if args.fps is not None else 15
        write_gif(snaps, spec, out_path, fps=fps)
        frame_count = len(snaps)
    elif fmt == "png":
        if args.tick is not None:
            write_png_from_snapshots(snaps, args.tick, spec, out_path, dpi=args.dpi)
        else:
            write_png(snaps[-1], spec, out_path, dpi=args.dpi)
        frame_count = 1
    elif fmt == "sheet":
        write_contact_sheet(
            snaps,
            spec,
            out_path,
            n_frames=args.frames,
            cols=args.cols,
            dpi=args.dpi,
            title=args.title if args.title and "{" not in args.title else None,
        )
        frame_count = min(args.frames, len(snaps))

    elapsed = time.time() - start
    print(
        f"swarmlet-viz: rendered {frame_count} frame(s) from {snaps_path} "
        f"to {out_path} in {elapsed:.2f}s"
    )
    return 0


def _info(args: argparse.Namespace) -> int:
    from swarmlet.viz.model import load_snapshots

    snaps_path = Path(args.snapshots)
    if not snaps_path.exists():
        print(f"swarmlet-viz: snapshot file not found: {snaps_path}", file=sys.stderr)
        return 2

    snaps = load_snapshots(snaps_path)
    if not snaps:
        print(f"{snaps_path}: empty snapshot file")
        return 0

    first = snaps[0]
    print(f"file: {snaps_path}")
    print(f"snapshots: {len(snaps)}")
    print(f"world: {first.world.w} x {first.world.h} (wrap={first.world.wrap})")
    print(f"states_legend: {', '.join(first.states_legend)}")
    if first.fields:
        print(f"fields: {', '.join(name for name, _ in first.fields)}")
    else:
        print("fields: (none)")
    agent_counts: dict = {}
    for s in snaps:
        for a in s.agents:
            agent_counts[a.type] = max(agent_counts.get(a.type, 0), 1)
    first_types = {a.type for a in first.agents}
    last_types = {a.type for a in snaps[-1].agents}
    all_types = sorted(first_types | last_types)
    if all_types:
        print(f"agent types: {', '.join(all_types)}")
        print(
            f"agents @ t={first.t}: {len(first.agents)} | "
            f"agents @ t={snaps[-1].t}: {len(snaps[-1].agents)}"
        )
    else:
        print("agent types: (none)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "render":
            return _render(args)
        if args.command == "info":
            return _info(args)
        if args.command == "version":
            print(f"swarmlet-viz {__version__}")
            return 0
    except ValueError as exc:
        print(f"swarmlet-viz: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"swarmlet-viz: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"swarmlet-viz: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
