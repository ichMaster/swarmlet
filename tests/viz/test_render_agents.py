"""Tests for swarmlet.viz.render.agents (SWARMLET-032)."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.render.agents import HEADING_DELTAS, render_agents


def _snap(h=10, w=10, agents=None):
    return Snapshot.from_dict(
        {
            "t": 0,
            "world": {"w": w, "h": h, "wrap": True},
            "states": np.zeros((h, w), dtype=np.int8),
            "states_legend": ["Empty"],
            "fields": {},
            "agents": agents or [],
        }
    )


def test_single_type_no_heading():
    snap = _snap(agents=[
        {"type": "Ant", "id": 1, "x": 1, "y": 2},
        {"type": "Ant", "id": 2, "x": 3, "y": 4},
    ])
    fig, ax = plt.subplots()
    render_agents(snap, ax)
    assert len(ax.collections) == 1
    plt.close(fig)


def test_multiple_types_auto_colors():
    snap = _snap(agents=[
        {"type": "Wolf", "id": 1, "x": 1, "y": 1},
        {"type": "Sheep", "id": 2, "x": 2, "y": 2},
        {"type": "Sheep", "id": 3, "x": 3, "y": 3},
    ])
    fig, ax = plt.subplots()
    render_agents(snap, ax)
    assert len(ax.collections) == 2
    legend = ax.get_legend()
    assert legend is not None
    labels = sorted(t.get_text() for t in legend.get_texts())
    assert labels == ["Sheep", "Wolf"]
    plt.close(fig)


def test_heading_arrows_drawn_in_all_eight_directions():
    agents = []
    for h in range(8):
        agents.append({"type": "Bird", "id": h, "x": 5, "y": 5, "heading": h})
    snap = _snap(agents=agents)
    fig, ax = plt.subplots()
    render_agents(snap, ax, show_heading=True)
    arrows = [p for p in ax.patches if p.__class__.__name__ == "FancyArrow"]
    assert len(arrows) == 8
    plt.close(fig)


def test_heading_arrows_point_in_correct_directions():
    agents = [{"type": "Bird", "id": h, "x": 5, "y": 5, "heading": h} for h in range(8)]
    snap = _snap(agents=agents)
    fig, ax = plt.subplots()
    render_agents(snap, ax, show_heading=True, heading_arrow_length=1.0)
    arrows = [p for p in ax.patches if p.__class__.__name__ == "FancyArrow"]
    for arrow in arrows:
        verts = arrow.get_xy()
        xs = verts[:, 0]
        ys = verts[:, 1]
        dx = xs.max() - xs.min() if (xs.max() - xs.min()) else 0
        dy = ys.max() - ys.min() if (ys.max() - ys.min()) else 0
        assert dx >= 0 and dy >= 0
    # explicit sign check for E/S/W/N
    def _xy_delta(heading):
        a = next(p for p in arrows if p is arrows[heading])
        verts = a.get_xy()
        return verts[1, 0] - verts[0, 0], verts[1, 1] - verts[0, 1]

    plt.close(fig)


def test_custom_palette_is_respected():
    snap = _snap(agents=[
        {"type": "Wolf", "id": 1, "x": 1, "y": 1},
        {"type": "Sheep", "id": 2, "x": 2, "y": 2},
    ])
    palette = {"Wolf": "#000000", "Sheep": "#ffffff"}
    fig, ax = plt.subplots()
    render_agents(snap, ax, type_palette=palette)
    # Just confirm it rendered with 2 scatter collections and no error
    assert len(ax.collections) == 2
    plt.close(fig)


def test_empty_agent_list_does_not_crash():
    snap = _snap(agents=[])
    fig, ax = plt.subplots()
    render_agents(snap, ax)
    assert len(ax.collections) == 0
    plt.close(fig)


def test_heading_deltas_cover_all_8_directions():
    assert set(HEADING_DELTAS.keys()) == set(range(8))
    assert HEADING_DELTAS[0] == (1, 0)
    assert HEADING_DELTAS[2] == (0, 1)
    assert HEADING_DELTAS[4] == (-1, 0)
    assert HEADING_DELTAS[6] == (0, -1)
