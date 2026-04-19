"""Animated GIF export via imageio (pillow backend).

Same structure as MP4 export: render each frame, feed to a streaming writer,
close figures eagerly. GIFs are chunky per-frame so default ``fps`` is lower
and a ``subsample`` parameter keeps file sizes reasonable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

import imageio.v2 as imageio
import matplotlib.pyplot as plt

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.mp4 import _figure_to_rgb, _resolve_auto_range
from swarmlet.viz.render.composite import FrameSpec, render_frame


def write_gif(
    snapshots: Sequence[Snapshot],
    spec: FrameSpec,
    path: Union[str, Path],
    fps: int = 15,
    loop: int = 0,
    subsample: int = 1,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """Encode *snapshots* as an animated GIF at *path*."""
    if subsample < 1:
        raise ValueError(f"subsample must be >= 1, got {subsample}")

    snaps: List[Snapshot] = list(snapshots)[::subsample]
    if not snaps:
        raise ValueError("write_gif: empty snapshot list (after subsample)")

    spec = _resolve_auto_range(snaps, spec)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    total = len(snaps)
    duration = 1.0 / fps
    writer = imageio.get_writer(
        str(target),
        mode="I",
        duration=duration,
        loop=loop,
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
