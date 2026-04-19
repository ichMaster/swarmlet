"""Tests for swarmlet.viz.output.sheet (SWARMLET-037)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.sheet import _pick_snapshots, write_contact_sheet
from swarmlet.viz.render.composite import FrameSpec


def _snap(t=0, fill=0.0):
    h = w = 4
    return Snapshot.from_dict(
        {
            "t": t,
            "world": {"w": w, "h": h, "wrap": True},
            "states": (np.arange(h * w, dtype=np.int8) % 2).reshape(h, w),
            "states_legend": ["A", "B"],
            "fields": {"heat": np.full((h, w), fill, dtype=np.float32)},
            "agents": [],
        }
    )


def test_contact_sheet_is_written(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(24)]
    out = tmp_path / "sheet.png"
    write_contact_sheet(
        snaps,
        FrameSpec(),
        out,
        n_frames=12,
        cols=4,
        dpi=80,
    )
    assert out.exists()
    assert out.stat().st_size > 1000


def test_pick_snapshots_evenly_spaced():
    snaps = [_snap(t=i) for i in range(10)]
    picked = _pick_snapshots(snaps, n_frames=5)
    ticks = [s.t for s in picked]
    assert ticks == [0, 2, 5, 7, 9] or ticks[0] == 0 and ticks[-1] == 9
    assert len(picked) == 5


def test_pick_snapshots_fewer_than_requested():
    snaps = [_snap(t=i) for i in range(3)]
    picked = _pick_snapshots(snaps, n_frames=10)
    assert len(picked) == 3


def test_title_is_applied(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(8)]
    out = tmp_path / "titled.png"
    write_contact_sheet(
        snaps,
        FrameSpec(),
        out,
        n_frames=6,
        cols=3,
        dpi=80,
        title="Hello",
    )
    assert out.exists()


def test_auto_field_range_across_picked_frames(tmp_path: Path):
    snaps = [_snap(t=i, fill=i * 0.1) for i in range(10)]
    out = tmp_path / "field_sheet.png"
    write_contact_sheet(
        snaps,
        FrameSpec(show_cells=False, show_field="heat"),
        out,
        n_frames=4,
        cols=2,
        dpi=80,
    )
    assert out.exists()


def test_invalid_args_raise(tmp_path: Path):
    snaps = [_snap()]
    with pytest.raises(ValueError):
        write_contact_sheet([], FrameSpec(), tmp_path / "a.png")
    with pytest.raises(ValueError):
        write_contact_sheet(snaps, FrameSpec(), tmp_path / "b.png", n_frames=0)
    with pytest.raises(ValueError):
        write_contact_sheet(snaps, FrameSpec(), tmp_path / "c.png", cols=0)
