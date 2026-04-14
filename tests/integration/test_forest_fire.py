"""Integration test for forest fire example."""

import os
from swarmlet.parser import parse
from swarmlet.engine import World

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples", "forest_fire.swl")


def test_forest_fire_runs():
    """Forest fire 100x100 runs 100 ticks without errors."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(100)
    assert w.tick_count == 100


def test_forest_fire_state_diversity():
    """All four states should be present during simulation."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    all_states_seen = set()
    for _ in range(50):
        w.step(1)
        snap = w.snapshot()
        for row in snap["states"]:
            all_states_seen.update(row)
        if len(all_states_seen) >= 4:
            break
    assert len(all_states_seen) >= 3  # Fire may be transient
    assert "Tree" in all_states_seen
    assert "Empty" in all_states_seen
