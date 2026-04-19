"""Contact-sheet export — one PNG showing N evenly-spaced frames in a grid.

Designed for documentation: one image that summarizes the arc of a simulation
without the weight of a video file. Sub-frames share a common color scale
across picked snapshots to keep the visual story coherent.
"""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Sequence, Union

import matplotlib.pyplot as plt

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.agents import render_agents
from swarmlet.viz.render.cells import render_cell_states
from swarmlet.viz.render.composite import FrameSpec
from swarmlet.viz.render.fields import compute_field_range, render_cell_field


def _pick_snapshots(snapshots: Sequence[Snapshot], n_frames: int) -> List[Snapshot]:
    if len(snapshots) <= n_frames:
        return list(snapshots)
    step = (len(snapshots) - 1) / (n_frames - 1) if n_frames > 1 else 0
    indices = [int(round(i * step)) for i in range(n_frames)]
    return [snapshots[i] for i in indices]


def write_contact_sheet(
    snapshots: Sequence[Snapshot],
    spec: FrameSpec,
    path: Union[str, Path],
    n_frames: int = 12,
    cols: int = 4,
    dpi: int = 150,
    title: Optional[str] = None,
) -> Path:
    """Write an N-tile contact sheet PNG to *path*."""
    snaps = list(snapshots)
    if not snaps:
        raise ValueError("write_contact_sheet: empty snapshot list")
    if n_frames <= 0:
        raise ValueError(f"n_frames must be > 0, got {n_frames}")
    if cols <= 0:
        raise ValueError(f"cols must be > 0, got {cols}")

    picked = _pick_snapshots(snaps, n_frames)
    rows = math.ceil(len(picked) / cols)

    if spec.show_field and spec.field_vmin is None and spec.field_vmax is None:
        lo, hi = compute_field_range(picked, spec.show_field)
        spec = replace(spec, field_vmin=lo, field_vmax=hi)

    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(cols * 2.2, rows * 2.2),
        dpi=dpi,
        squeeze=False,
    )

    for idx, snap in enumerate(picked):
        r, c = divmod(idx, cols)
        ax = axes[r][c]
        if spec.show_field:
            render_cell_field(
                snap,
                spec.show_field,
                ax,
                cmap=spec.field_cmap,
                vmin=spec.field_vmin,
                vmax=spec.field_vmax,
                log_scale=spec.field_log_scale,
                colorbar=False,
            )
        elif spec.show_cells:
            render_cell_states(
                snap,
                ax,
                cmap=spec.cells_cmap,
                palette=spec.cells_palette,
                show_legend=False,
            )
        if spec.show_agents:
            render_agents(
                snap,
                ax,
                by_type=spec.agents_by_type,
                type_palette=spec.agents_palette,
                marker_size=spec.agent_marker_size,
                show_heading=spec.show_agent_heading,
                show_legend=False,
            )
        ax.set_title(f"t = {snap.t}", fontsize="x-small")
        ax.set_xticks([])
        ax.set_yticks([])

    for idx in range(len(picked), rows * cols):
        r, c = divmod(idx, cols)
        axes[r][c].axis("off")

    if title:
        fig.suptitle(title)
    fig.tight_layout()

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(target, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(fig)
    return target
