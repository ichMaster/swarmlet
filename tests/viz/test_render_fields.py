"""Tests for swarmlet.viz.render.fields (SWARMLET-031)."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.fields import (
    compute_field_range,
    make_field_figure,
    render_cell_field,
)


def _snap(h=4, w=4, field_name="heat", field_values=None, t=0):
    if field_values is None:
        field_values = np.linspace(0.0, 1.0, h * w, dtype=np.float32).reshape(h, w)
    return Snapshot.from_dict(
        {
            "t": t,
            "world": {"w": w, "h": h, "wrap": True},
            "states": np.zeros((h, w), dtype=np.int8),
            "states_legend": ["Empty"],
            "fields": {field_name: field_values},
            "agents": [],
        }
    )


def test_render_default_settings():
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_field(snap, "heat", ax)
    assert ax.get_images(), "expected an image drawn"
    plt.close(fig)


def test_render_respects_custom_vmin_vmax():
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_field(snap, "heat", ax, vmin=0.2, vmax=0.8)
    norm = ax.get_images()[0].norm
    assert norm.vmin == pytest.approx(0.2)
    assert norm.vmax == pytest.approx(0.8)
    plt.close(fig)


def test_render_log_scale_handles_zeros():
    h = w = 3
    values = np.array([[0.0, 0.1, 1.0], [0.0, 10.0, 100.0], [0.01, 0.5, 5.0]], dtype=np.float32)
    snap = _snap(h=h, w=w, field_values=values)
    fig, ax = plt.subplots()
    render_cell_field(snap, "heat", ax, log_scale=True)
    from matplotlib.colors import LogNorm
    assert isinstance(ax.get_images()[0].norm, LogNorm)
    plt.close(fig)


def test_render_colorbar_toggle():
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_field(snap, "heat", ax, colorbar=False)
    assert len(fig.axes) == 1, "expected no extra colorbar axes"
    plt.close(fig)

    fig, ax = plt.subplots()
    render_cell_field(snap, "heat", ax, colorbar=True)
    assert len(fig.axes) >= 2, "expected a colorbar axes"
    plt.close(fig)


def test_missing_field_raises():
    snap = _snap()
    fig, ax = plt.subplots()
    with pytest.raises(KeyError):
        render_cell_field(snap, "does_not_exist", ax)
    plt.close(fig)


def test_compute_field_range_across_snapshots():
    snaps = [
        _snap(field_values=np.full((4, 4), 0.25, dtype=np.float32), t=0),
        _snap(field_values=np.full((4, 4), 0.75, dtype=np.float32), t=1),
        _snap(field_values=np.full((4, 4), 0.5, dtype=np.float32), t=2),
    ]
    lo, hi = compute_field_range(snaps, "heat")
    assert lo == pytest.approx(0.25)
    assert hi == pytest.approx(0.75)


def test_make_field_figure_returns_figure():
    snap = _snap()
    fig = make_field_figure(snap, "heat")
    assert fig.axes
    plt.close(fig)
