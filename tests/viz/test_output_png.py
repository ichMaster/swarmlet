"""Tests for swarmlet.viz.output.png (SWARMLET-036)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.png import write_png, write_png_from_snapshots
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


def test_png_is_written(tmp_path: Path):
    snap = _snap()
    out = tmp_path / "frame.png"
    write_png(snap, FrameSpec(figsize=(3, 3)), out, dpi=100)
    assert out.exists()
    assert out.stat().st_size > 500


def test_png_respects_dpi(tmp_path: Path):
    snap = _snap()
    lo = tmp_path / "lo.png"
    hi = tmp_path / "hi.png"
    write_png(snap, FrameSpec(figsize=(3, 3)), lo, dpi=50)
    write_png(snap, FrameSpec(figsize=(3, 3)), hi, dpi=200)
    assert hi.stat().st_size > lo.stat().st_size


def test_png_from_snapshots_finds_exact_tick(tmp_path: Path):
    snaps = [_snap(t=i) for i in (0, 10, 20, 30)]
    out = tmp_path / "t20.png"
    write_png_from_snapshots(snaps, tick=20, spec=FrameSpec(figsize=(3, 3)), path=out)
    assert out.exists()


def test_png_from_snapshots_uses_closest_tick(tmp_path: Path):
    snaps = [_snap(t=i) for i in (0, 10, 30)]
    out = tmp_path / "t22.png"
    write_png_from_snapshots(snaps, tick=22, spec=FrameSpec(figsize=(3, 3)), path=out)
    assert out.exists()


def test_empty_snapshot_list_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        write_png_from_snapshots([], 0, FrameSpec(), tmp_path / "nope.png")
