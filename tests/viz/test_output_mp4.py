"""Tests for swarmlet.viz.output.mp4 (SWARMLET-034)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.mp4 import _resolve_auto_range, write_mp4
from swarmlet.viz.render.composite import FrameSpec


def _snap(t=0, fill=0.0):
    h = w = 8
    return Snapshot.from_dict(
        {
            "t": t,
            "world": {"w": w, "h": h, "wrap": True},
            "states": (np.arange(h * w, dtype=np.int8) % 3).reshape(h, w),
            "states_legend": ["A", "B", "C"],
            "fields": {"heat": np.full((h, w), fill, dtype=np.float32)},
            "agents": [],
        }
    )


def test_small_simulation_produces_mp4(tmp_path: Path):
    snaps = [_snap(t=i, fill=i * 0.1) for i in range(6)]
    out = tmp_path / "tiny.mp4"
    write_mp4(snaps, FrameSpec(figsize=(2, 2), dpi=80), out, fps=5)
    assert out.exists()
    assert out.stat().st_size > 1000


def test_auto_vmin_vmax_is_computed(tmp_path: Path):
    snaps = [_snap(t=i, fill=i * 0.5) for i in range(3)]
    spec = FrameSpec(show_cells=False, show_field="heat", figsize=(2, 2), dpi=80)
    resolved = _resolve_auto_range(snaps, spec)
    assert resolved.field_vmin == pytest.approx(0.0)
    assert resolved.field_vmax == pytest.approx(1.0)


def test_user_vmin_vmax_is_preserved():
    snaps = [_snap(fill=v) for v in (0.1, 0.3, 0.9)]
    spec = FrameSpec(show_field="heat", field_vmin=-1.0, field_vmax=2.0)
    resolved = _resolve_auto_range(snaps, spec)
    assert resolved.field_vmin == -1.0
    assert resolved.field_vmax == 2.0


def test_progress_callback_fires_once_per_frame(tmp_path: Path):
    snaps = [_snap(t=i) for i in range(4)]
    calls = []
    write_mp4(
        snaps,
        FrameSpec(figsize=(2, 2), dpi=80),
        tmp_path / "cb.mp4",
        fps=5,
        progress_callback=lambda current, total: calls.append((current, total)),
    )
    assert [c[0] for c in calls] == [1, 2, 3, 4]
    assert all(c[1] == 4 for c in calls)


def test_empty_snapshot_list_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        write_mp4([], FrameSpec(), tmp_path / "empty.mp4")
