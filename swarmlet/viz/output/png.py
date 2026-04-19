"""Single-frame PNG export.

A static image of one snapshot. Useful for README hero images, slide decks,
and any context where a single frame communicates the interesting moment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

import matplotlib.pyplot as plt

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.composite import FrameSpec, render_frame


def write_png(
    snap: Snapshot,
    spec: FrameSpec,
    path: Union[str, Path],
    dpi: int = 150,
) -> Path:
    """Save one snapshot to a PNG at *path* at the requested DPI."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig = render_frame(snap, spec)
    try:
        fig.savefig(target, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
    return target


def write_png_from_snapshots(
    snapshots: Sequence[Snapshot],
    tick: int,
    spec: FrameSpec,
    path: Union[str, Path],
    dpi: int = 150,
) -> Path:
    """Find the snapshot with ``t == tick`` (or closest) and save it to PNG."""
    snaps = list(snapshots)
    if not snaps:
        raise ValueError("write_png_from_snapshots: empty snapshot list")
    exact = next((s for s in snaps if s.t == tick), None)
    if exact is not None:
        return write_png(exact, spec, path, dpi=dpi)
    closest = min(snaps, key=lambda s: abs(s.t - tick))
    return write_png(closest, spec, path, dpi=dpi)
