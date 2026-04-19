"""Composite frame renderer combining cell, field, and agent layers.

A single ``render_frame(snap, spec)`` call produces a complete matplotlib
Figure ready to save or compose into a video. Cells and fields are mutually
exclusive as background (field wins if both are requested) — layering a
categorical grid underneath a continuous colormap produces visual noise.
Agents are always rendered as an overlay on top.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Generator, Iterable, Optional, Tuple

import matplotlib.pyplot as plt

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.agents import render_agents
from swarmlet.viz.render.cells import render_cell_states
from swarmlet.viz.render.fields import render_cell_field


@dataclass
class FrameSpec:
    """Declarative recipe for a frame: which layers, which colors, which labels."""

    show_cells: bool = True
    cells_palette: Optional[Dict[str, str]] = None
    cells_cmap: Optional[str] = None
    show_field: Optional[str] = None
    field_cmap: str = "viridis"
    field_vmin: Optional[float] = None
    field_vmax: Optional[float] = None
    field_log_scale: bool = False
    field_colorbar: bool = True
    show_agents: bool = True
    agents_by_type: bool = True
    agents_palette: Optional[Dict[str, str]] = None
    agent_marker_size: Optional[float] = None
    show_agent_heading: bool = False
    title_template: str = "t = {t}"
    figsize: Tuple[float, float] = (8.0, 8.0)
    dpi: int = 100


def render_frame(snap: Snapshot, spec: Optional[FrameSpec] = None) -> plt.Figure:
    """Render a single snapshot to a new matplotlib Figure using *spec*."""
    spec = spec or FrameSpec()
    fig, ax = plt.subplots(figsize=spec.figsize, dpi=spec.dpi)

    if spec.show_field:
        render_cell_field(
            snap,
            spec.show_field,
            ax,
            cmap=spec.field_cmap,
            vmin=spec.field_vmin,
            vmax=spec.field_vmax,
            log_scale=spec.field_log_scale,
            colorbar=spec.field_colorbar,
        )
    elif spec.show_cells:
        render_cell_states(
            snap,
            ax,
            cmap=spec.cells_cmap,
            palette=spec.cells_palette,
        )

    if spec.show_agents:
        render_agents(
            snap,
            ax,
            by_type=spec.agents_by_type,
            type_palette=spec.agents_palette,
            marker_size=spec.agent_marker_size,
            show_heading=spec.show_agent_heading,
        )

    title = spec.title_template.format(t=snap.t)
    if title:
        ax.set_title(title)
    ax.set_xlim(-0.5, snap.world.w - 0.5)
    ax.set_ylim(snap.world.h - 0.5, -0.5)
    fig.tight_layout()
    return fig


def render_frames(
    snapshots: Iterable[Snapshot],
    spec: Optional[FrameSpec] = None,
) -> Generator[plt.Figure, None, None]:
    """Yield one matplotlib Figure per snapshot — closes are the caller's job."""
    spec = spec or FrameSpec()
    for snap in snapshots:
        yield render_frame(snap, spec)
