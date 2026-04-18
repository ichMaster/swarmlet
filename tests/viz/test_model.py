"""Tests for swarmlet.viz.model (SWARMLET-029)."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import swarmlet.viz as viz
from swarmlet.viz.model import AgentRecord, Snapshot, WorldInfo, load_snapshots


def _valid_dict(h: int = 2, w: int = 3, legend=("Empty", "Tree"), agents=None):
    states = np.zeros((h, w), dtype=np.int8)
    return {
        "t": 0,
        "world": {"w": w, "h": h, "wrap": True},
        "states": states,
        "states_legend": list(legend),
        "fields": {"heat": np.zeros((h, w), dtype=np.float32)},
        "agents": agents if agents is not None else [],
    }


def test_from_dict_valid_returns_frozen_snapshot():
    s = Snapshot.from_dict(_valid_dict())
    assert isinstance(s, Snapshot)
    assert s.t == 0
    assert s.world == WorldInfo(w=3, h=2, wrap=True)
    assert s.states_legend == ("Empty", "Tree")
    assert s.states.shape == (2, 3)
    with pytest.raises((AttributeError, Exception)):
        s.t = 99  # frozen


def test_snapshot_is_hashable():
    s1 = Snapshot.from_dict(_valid_dict())
    s2 = Snapshot.from_dict(_valid_dict())
    assert hash(s1) == hash(s2)


def test_states_shape_mismatch_raises():
    d = _valid_dict()
    d["states"] = np.zeros((5, 5), dtype=np.int8)
    with pytest.raises(viz.SnapshotError, match="states.shape"):
        Snapshot.from_dict(d)


def test_states_dtype_must_be_integer():
    d = _valid_dict()
    d["states"] = np.zeros((2, 3), dtype=np.float32)
    with pytest.raises(viz.SnapshotError, match="must be integer"):
        Snapshot.from_dict(d)


def test_states_negative_index_raises():
    d = _valid_dict()
    d["states"] = np.full((2, 3), -1, dtype=np.int8)
    with pytest.raises(viz.SnapshotError, match="negative"):
        Snapshot.from_dict(d)


def test_states_index_out_of_legend_raises():
    d = _valid_dict()
    d["states"] = np.full((2, 3), 7, dtype=np.int8)
    with pytest.raises(viz.SnapshotError, match="out of legend"):
        Snapshot.from_dict(d)


def test_field_shape_mismatch_raises():
    d = _valid_dict()
    d["fields"] = {"heat": np.zeros((1, 1), dtype=np.float32)}
    with pytest.raises(viz.SnapshotError, match="field 'heat' shape"):
        Snapshot.from_dict(d)


def test_field_dtype_must_be_float():
    d = _valid_dict()
    d["fields"] = {"heat": np.zeros((2, 3), dtype=np.int32)}
    with pytest.raises(viz.SnapshotError, match="floating point"):
        Snapshot.from_dict(d)


def test_agent_x_out_of_bounds_raises():
    d = _valid_dict(agents=[{"id": 1, "type": "Ant", "x": 99, "y": 0}])
    with pytest.raises(viz.SnapshotError, match="out of bounds"):
        Snapshot.from_dict(d)


def test_agent_y_out_of_bounds_raises():
    d = _valid_dict(agents=[{"id": 1, "type": "Ant", "x": 0, "y": 99}])
    with pytest.raises(viz.SnapshotError, match="out of bounds"):
        Snapshot.from_dict(d)


def test_duplicate_agent_id_raises():
    d = _valid_dict(agents=[
        {"id": 1, "type": "Ant", "x": 0, "y": 0},
        {"id": 1, "type": "Ant", "x": 1, "y": 1},
    ])
    with pytest.raises(viz.SnapshotError, match="duplicate agent id"):
        Snapshot.from_dict(d)


def test_missing_required_key_raises():
    d = _valid_dict()
    del d["states"]
    with pytest.raises(viz.SnapshotError, match="missing required key"):
        Snapshot.from_dict(d)


def test_load_snapshots_round_trip(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent.parent
    example = repo_root / "swarmlet" / "examples" / "forest_fire.swl"
    out = tmp_path / "ff.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "swarmlet", "run", str(example),
         "--ticks", "5", "--seed", "1", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"swarmlet run failed: {result.stderr}"
    snaps = load_snapshots(out)
    assert len(snaps) == 6
    assert all(isinstance(s, Snapshot) for s in snaps)
    assert snaps[0].world.w > 0 and snaps[0].world.h > 0


def test_public_api_exposes_load_snapshots(tmp_path):
    """The package-level load_snapshots() forwards to the model implementation."""
    p = tmp_path / "snaps.jsonl"
    p.write_text(
        '{"tick": 0, "width": 2, "height": 1, "topology": "wrap", '
        '"states": [["A", "B"]], "fields": {}, "agents": []}\n'
    )
    snaps = viz.load_snapshots(p)
    assert len(snaps) == 1
    assert isinstance(snaps[0], Snapshot)
