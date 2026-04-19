"""Tests for swarmlet.viz.output.gif (SWARMLET-035)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import imageio.v2 as imageio
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.gif import write_gif
from swarmlet.viz.render.composite import FrameSpec


def _snap(t=0):
    h = w = 6
    return Snapshot.from_dict(
        {
            "t": t,
            "world": {"w": w, "h": h, "wrap": True},
            "states": (np.arange(h * w, dtype=np.int8) % 2).reshape(h, w),
            "states_legend": ["Dead", "Alive"],
            "fields": {},
            "agents": [],
        }
    )


def test_gif_is_written(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(4)]
    out = tmp_path / "anim.gif"
    write_gif(snaps, FrameSpec(figsize=(2, 2), dpi=80), out, fps=5)
    assert out.exists()
    assert out.stat().st_size > 300


def test_gif_is_multi_frame(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(5)]
    out = tmp_path / "anim.gif"
    write_gif(snaps, FrameSpec(figsize=(2, 2), dpi=80), out, fps=5)
    frames = imageio.mimread(str(out))
    assert len(frames) == 5


def test_subsample_reduces_frames(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(6)]
    out = tmp_path / "sub.gif"
    write_gif(snaps, FrameSpec(figsize=(2, 2), dpi=80), out, fps=5, subsample=2)
    frames = imageio.mimread(str(out))
    assert len(frames) == 3


def test_subsample_zero_raises(tmp_path: Path):
    snaps = [_snap()]
    with pytest.raises(ValueError):
        write_gif(snaps, FrameSpec(), tmp_path / "bad.gif", subsample=0)
