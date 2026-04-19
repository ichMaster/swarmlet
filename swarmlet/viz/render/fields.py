"""Continuous field renderer.

Renders a single named scalar field from a snapshot as a colormapped heatmap,
with optional log scale, fixed color range, and colorbar. Suitable for
reaction-diffusion concentrations and pheromone fields.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm, Normalize

from swarmlet.viz.model import Snapshot


def _get_field(snap: Snapshot, name: str) -> np.ndarray:
    for fname, arr in snap.fields:
        if fname == name:
            return arr
    available = [n for n, _ in snap.fields]
    raise KeyError(f"field '{name}' not found in snapshot. Available: {available}")


def render_cell_field(
    snap: Snapshot,
    field_name: str,
    ax: plt.Axes,
    cmap: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    log_scale: bool = False,
    colorbar: bool = True,
) -> None:
    """Render a named scalar field as a colormapped image onto *ax*."""
    arr = _get_field(snap, field_name)
    if log_scale:
        positive = arr[arr > 0]
        if vmin is not None and vmin > 0:
            lo = vmin
        elif positive.size:
            lo = float(positive.min())
        else:
            lo = 1e-12
        if vmax is not None:
            hi = vmax
        elif positive.size:
            hi = float(positive.max())
        else:
            hi = lo * 10
        if hi <= lo:
            hi = lo * 10
        norm = LogNorm(vmin=lo, vmax=hi)
    else:
        lo = vmin if vmin is not None else (float(np.min(arr)) if arr.size else 0.0)
        hi = vmax if vmax is not None else (float(np.max(arr)) if arr.size else 1.0)
        if hi <= lo:
            hi = lo + 1e-9
        norm = Normalize(vmin=lo, vmax=hi)

    im = ax.imshow(
        arr,
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        origin="upper",
    )
    ax.set_xticks([])
    ax.set_yticks([])

    if colorbar:
        ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def make_field_figure(
    snap: Snapshot,
    field_name: str,
    cmap: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    log_scale: bool = False,
    colorbar: bool = True,
    figsize=(6.0, 6.0),
    dpi: int = 100,
) -> plt.Figure:
    """Create a standalone Figure showing only the field layer."""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    render_cell_field(
        snap,
        field_name,
        ax,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        log_scale=log_scale,
        colorbar=colorbar,
    )
    fig.tight_layout()
    return fig


def compute_field_range(
    snapshots: Iterable[Snapshot],
    field_name: str,
) -> Tuple[float, float]:
    """Return (min, max) of *field_name* across all *snapshots*.

    Used to fix a single color scale across an animation and avoid per-frame
    rescaling (a common source of flicker in videos).
    """
    mins: List[float] = []
    maxs: List[float] = []
    for snap in snapshots:
        arr = _get_field(snap, field_name)
        if arr.size == 0:
            continue
        mins.append(float(np.min(arr)))
        maxs.append(float(np.max(arr)))
    if not mins:
        return (0.0, 1.0)
    return (min(mins), max(maxs))
