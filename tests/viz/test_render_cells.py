"""Tests for swarmlet.viz.render.cells (SWARMLET-030)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.cells import (
    _default_cmap_name,
    make_cell_figure,
    render_cell_states,
)


def _snap(h=5, w=5, legend=("Empty", "Tree", "Fire", "Ash"), states=None):
    if states is None:
        states = np.arange(h * w, dtype=np.int8).reshape(h, w) % len(legend)
    return Snapshot.from_dict(
        {
            "t": 0,
            "world": {"w": w, "h": h, "wrap": True},
            "states": states,
            "states_legend": list(legend),
            "fields": {},
            "agents": [],
        }
    )


def test_default_cmap_small_legend_uses_tab10():
    assert _default_cmap_name(4) == "tab10"
    assert _default_cmap_name(10) == "tab10"


def test_default_cmap_large_legend_uses_tab20():
    assert _default_cmap_name(11) == "tab20"


def test_render_to_png_produces_non_empty_file(tmp_path: Path):
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_states(snap, ax)
    out = tmp_path / "cells.png"
    fig.savefig(out, dpi=80, bbox_inches="tight")
    plt.close(fig)
    assert out.exists()
    assert out.stat().st_size > 500


def test_custom_palette_is_used():
    snap = _snap()
    palette = {"Empty": "#ffffff", "Tree": "#00ff00", "Fire": "#ff0000", "Ash": "#222222"}
    fig, ax = plt.subplots()
    render_cell_states(snap, ax, palette=palette)
    image = ax.get_images()[0]
    colors_used = image.get_cmap().colors
    assert len(colors_used) == 4
    plt.close(fig)


def test_legend_shows_all_state_labels():
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_states(snap, ax)
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Empty", "Tree", "Fire", "Ash"]
    plt.close(fig)


def test_missing_palette_color_raises():
    snap = _snap()
    incomplete = {"Empty": "#fff", "Tree": "#0f0"}
    fig, ax = plt.subplots()
    with pytest.raises(KeyError):
        render_cell_states(snap, ax, palette=incomplete)
    plt.close(fig)


def test_make_cell_figure_returns_figure():
    snap = _snap()
    fig = make_cell_figure(snap)
    assert fig.axes, "figure should have at least one axes"
    plt.close(fig)


def test_render_removes_axis_ticks():
    snap = _snap()
    fig, ax = plt.subplots()
    render_cell_states(snap, ax)
    assert list(ax.get_xticks()) == []
    assert list(ax.get_yticks()) == []
    plt.close(fig)
