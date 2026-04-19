"""Categorical cell-state renderer.

Maps each integer state value to a fixed color. Suitable for pure cellular
automata like forest fire where cells have a small discrete set of states.
"""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from swarmlet.viz.model import Snapshot


def _default_cmap_name(n_states: int) -> str:
    return "tab10" if n_states <= 10 else "tab20"


def _build_colors(legend, cmap: Optional[str], palette: Optional[Dict[str, str]]):
    n = len(legend)
    if palette is not None:
        missing = [name for name in legend if name not in palette]
        if missing:
            raise KeyError(
                f"palette is missing colors for states: {missing}"
            )
        return [palette[name] for name in legend]
    cmap_name = cmap or _default_cmap_name(n)
    base = plt.get_cmap(cmap_name)
    if hasattr(base, "colors") and len(base.colors) >= n:
        return [base.colors[i] for i in range(n)]
    return [base(i / max(n - 1, 1)) for i in range(n)]


def render_cell_states(
    snap: Snapshot,
    ax: plt.Axes,
    cmap: Optional[str] = None,
    palette: Optional[Dict[str, str]] = None,
    show_legend: bool = True,
) -> None:
    """Render cell states as a categorical heatmap onto *ax*.

    Args:
        snap: the snapshot to render.
        ax: matplotlib Axes to draw into.
        cmap: name of a matplotlib categorical colormap (e.g. ``"tab10"``).
        palette: explicit mapping ``{state_name: color}`` overriding *cmap*.
        show_legend: whether to draw a legend with state names.
    """
    legend = list(snap.states_legend)
    colors = _build_colors(legend, cmap, palette)
    listed = ListedColormap(colors)
    bounds = np.arange(len(legend) + 1) - 0.5
    norm = BoundaryNorm(bounds, listed.N)

    ax.imshow(
        snap.states,
        cmap=listed,
        norm=norm,
        interpolation="nearest",
        origin="upper",
    )
    ax.set_xticks([])
    ax.set_yticks([])

    if show_legend:
        handles = [
            mpatches.Patch(color=colors[i], label=legend[i])
            for i in range(len(legend))
        ]
        ax.legend(
            handles=handles,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )


def make_cell_figure(
    snap: Snapshot,
    cmap: Optional[str] = None,
    palette: Optional[Dict[str, str]] = None,
    show_legend: bool = True,
    figsize=(6.0, 6.0),
    dpi: int = 100,
) -> plt.Figure:
    """Create a standalone Figure showing only the cell-state layer."""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    render_cell_states(snap, ax, cmap=cmap, palette=palette, show_legend=show_legend)
    fig.tight_layout()
    return fig
