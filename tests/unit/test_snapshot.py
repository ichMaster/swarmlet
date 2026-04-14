"""Tests for snapshot serialization (JSONL and NPZ)."""

import json
import os
import tempfile
import numpy as np
from swarmlet.parser import parse
from swarmlet.engine import World
from swarmlet.snapshot import write_jsonl, write_npz, read_jsonl


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


SOURCE = """
world 5 x 5 wrap
cell states A | B
field heat = 0.0
agent Bot { heading = 0 }
let cell A = if random () < 0.1 then B else A
let cell B = A
let agent Bot = move forward
init cell = A
init field heat = 1.0
init agent Bot 2
"""


def test_jsonl_round_trip():
    """Write 10 snapshots to JSONL, read them back, verify."""
    w = make_world(SOURCE)
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        write_jsonl(w, path, ticks=10)
        snapshots = read_jsonl(path)
        assert len(snapshots) == 11  # initial + 10 ticks
        assert snapshots[0]["tick"] == 0
        assert snapshots[-1]["tick"] == 10
        for snap in snapshots:
            assert "states" in snap
            assert "agents" in snap
    finally:
        os.unlink(path)


def test_npz_entry_count():
    """NPZ archive should contain expected number of entries."""
    w = make_world(SOURCE)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        path = f.name
    try:
        write_npz(w, path, ticks=5)
        data = np.load(path, allow_pickle=True)
        # Should have metadata + (5+1 ticks) * (states + heat + agents) = 1 + 6*3 = 19
        assert "metadata" in data
        assert "tick_0_states" in data
        assert "tick_5_states" in data
    finally:
        os.unlink(path)


def test_every_thins_output():
    """--every 5 should produce fewer snapshots."""
    w = make_world(SOURCE)
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        write_jsonl(w, path, ticks=20, every=5)
        snapshots = read_jsonl(path)
        # initial (tick 0) + ticks 5, 10, 15, 20 = 5 snapshots
        assert len(snapshots) == 5
        ticks = [s["tick"] for s in snapshots]
        assert ticks == [0, 5, 10, 15, 20]
    finally:
        os.unlink(path)


def test_progress_callback():
    """Progress callback should be called for each tick."""
    w = make_world(SOURCE)
    calls = []
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        write_jsonl(w, path, ticks=10, progress=lambda t: calls.append(t))
        assert len(calls) == 10
        assert calls == list(range(1, 11))
    finally:
        os.unlink(path)
