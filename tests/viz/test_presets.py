"""Tests for swarmlet.viz.presets (SWARMLET-039)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

from swarmlet.viz.model import Snapshot
from swarmlet.viz.output.png import write_png
from swarmlet.viz.presets import PRESETS
from swarmlet.viz.render.composite import FrameSpec


def test_all_five_presets_exist():
    assert set(PRESETS) == {"forest_fire", "ants", "boids", "wolf_sheep", "gray_scott"}


def test_every_preset_is_a_framespec():
    for name, spec in PRESETS.items():
        assert isinstance(spec, FrameSpec), f"{name} is not a FrameSpec"


def _make_snap(legend, agents=None, fields=None, h=6, w=6):
    return Snapshot.from_dict(
        {
            "t": 0,
            "world": {"w": w, "h": h, "wrap": True},
            "states": np.zeros((h, w), dtype=np.int8),
            "states_legend": list(legend),
            "fields": fields or {},
            "agents": agents or [],
        }
    )


def test_forest_fire_preset_renders(tmp_path: Path):
    snap = _make_snap(["Empty", "Tree", "Fire", "Ash"])
    write_png(snap, PRESETS["forest_fire"], tmp_path / "ff.png", dpi=80)
    assert (tmp_path / "ff.png").exists()


def test_ants_preset_renders(tmp_path: Path):
    snap = _make_snap(
        ["Empty"],
        agents=[{"type": "Ant", "id": 1, "x": 2, "y": 3}],
        fields={"pheromone": np.full((6, 6), 0.2, dtype=np.float32)},
    )
    write_png(snap, PRESETS["ants"], tmp_path / "ants.png", dpi=80)
    assert (tmp_path / "ants.png").exists()


def test_boids_preset_renders_with_heading(tmp_path: Path):
    snap = _make_snap(
        ["Empty"],
        agents=[{"type": "Bird", "id": 1, "x": 3, "y": 3, "heading": 0}],
    )
    write_png(snap, PRESETS["boids"], tmp_path / "boids.png", dpi=80)
    assert (tmp_path / "boids.png").exists()


def test_wolf_sheep_preset_renders(tmp_path: Path):
    snap = _make_snap(
        ["Empty", "Grass"],
        agents=[
            {"type": "Sheep", "id": 1, "x": 1, "y": 1},
            {"type": "Wolf", "id": 2, "x": 4, "y": 4},
        ],
    )
    write_png(snap, PRESETS["wolf_sheep"], tmp_path / "ws.png", dpi=80)
    assert (tmp_path / "ws.png").exists()


def test_gray_scott_preset_renders(tmp_path: Path):
    snap = _make_snap(
        ["Empty"],
        fields={"v": np.linspace(0.0, 0.5, 36, dtype=np.float32).reshape(6, 6)},
    )
    write_png(snap, PRESETS["gray_scott"], tmp_path / "gs.png", dpi=80)
    assert (tmp_path / "gs.png").exists()
