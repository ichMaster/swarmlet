"""Tests for swarmlet.viz.render.composite (SWARMLET-033)."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.composite import FrameSpec, render_frame, render_frames


def _snap(t=0, with_field=True, with_agents=True):
    h = w = 6
    fields = {}
    if with_field:
        fields["pheromone"] = np.linspace(0.0, 1.0, h * w, dtype=np.float32).reshape(h, w)
    agents = []
    if with_agents:
        agents = [
            {"type": "Ant", "id": 1, "x": 1, "y": 1, "heading": 0},
            {"type": "Ant", "id": 2, "x": 3, "y": 4, "heading": 2},
        ]
    return Snapshot.from_dict(
        {
            "t": t,
            "world": {"w": w, "h": h, "wrap": True},
            "states": (np.arange(h * w, dtype=np.int8) % 3).reshape(h, w),
            "states_legend": ["Empty", "Tree", "Fire"],
            "fields": fields,
            "agents": agents,
        }
    )


def test_default_spec_renders_cells_and_agents():
    snap = _snap()
    fig = render_frame(snap)
    assert fig.axes, "expected at least one axes"
    ax = fig.axes[0]
    assert ax.get_title() == "t = 0"
    assert ax.get_images(), "cells should have been drawn"
    plt.close(fig)


def test_field_takes_precedence_over_cells():
    snap = _snap()
    spec = FrameSpec(show_cells=True, show_field="pheromone")
    fig = render_frame(snap, spec)
    ax = fig.axes[0]
    images = ax.get_images()
    assert images, "expected a field image"
    assert images[0].get_cmap().name == "viridis"
    plt.close(fig)


def test_agents_overlay_added():
    snap = _snap()
    spec = FrameSpec(show_field="pheromone")
    fig = render_frame(snap, spec)
    ax = fig.axes[0]
    assert any(c for c in ax.collections), "agents scatter missing"
    plt.close(fig)


def test_no_agents_no_cells_no_field():
    snap = _snap(with_field=False, with_agents=False)
    spec = FrameSpec(show_cells=False, show_agents=False, show_field=None)
    fig = render_frame(snap, spec)
    ax = fig.axes[0]
    assert not ax.get_images()
    assert not ax.collections
    plt.close(fig)


def test_render_frames_is_generator():
    snaps = [_snap(t=i) for i in range(3)]
    gen = render_frames(snaps, FrameSpec())
    import types
    assert isinstance(gen, types.GeneratorType)
    figs = list(gen)
    assert len(figs) == 3
    for fig in figs:
        plt.close(fig)


def test_title_template_interpolation():
    snap = _snap(t=42)
    spec = FrameSpec(title_template="tick {t}")
    fig = render_frame(snap, spec)
    assert fig.axes[0].get_title() == "tick 42"
    plt.close(fig)
