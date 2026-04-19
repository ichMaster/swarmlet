"""MP4 video export via imageio[ffmpeg].

Render each snapshot with :func:`render_frame`, convert the figure to an RGB
numpy array, feed to ``imageio.get_writer`` with the ffmpeg plugin. Figures
are closed immediately after each frame so long simulations do not leak
matplotlib state.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

import imageio.v2 as imageio
import matplotlib.pyplot as plt
import numpy as np

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.composite import FrameSpec, render_frame
from swarmlet.viz.render.fields import compute_field_range


def _figure_to_rgb(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    rgb = rgba[:, :, :3].copy()
    # imageio/ffmpeg prefer even dimensions for yuv420p encoding
    h, w, _ = rgb.shape
    if h % 2:
        rgb = rgb[:-1, :, :]
    if w % 2:
        rgb = rgb[:, :-1, :]
    return rgb


def _resolve_auto_range(snapshots: Sequence[Snapshot], spec: FrameSpec) -> FrameSpec:
    if spec.show_field and spec.field_vmin is None and spec.field_vmax is None:
        lo, hi = compute_field_range(snapshots, spec.show_field)
        return replace(spec, field_vmin=lo, field_vmax=hi)
    return spec


def write_mp4(
    snapshots: Sequence[Snapshot],
    spec: FrameSpec,
    path: Union[str, Path],
    fps: int = 30,
    quality: int = 7,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """Encode *snapshots* as an MP4 at *path* using the configured FrameSpec."""
    snaps: List[Snapshot] = list(snapshots)
    if not snaps:
        raise ValueError("write_mp4: empty snapshot list")

    spec = _resolve_auto_range(snaps, spec)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    total = len(snaps)
    writer = imageio.get_writer(
        str(target),
        fps=fps,
        quality=quality,
        codec="libx264",
        macro_block_size=1,
    )
    try:
        for i, snap in enumerate(snaps):
            fig = render_frame(snap, spec)
            try:
                writer.append_data(_figure_to_rgb(fig))
            finally:
                plt.close(fig)
            if progress_callback is not None:
                progress_callback(i + 1, total)
    finally:
        writer.close()

    return target
