"""Integration test for ant foraging example."""

import os
import numpy as np
from swarmlet.parser import parse
from swarmlet.engine import World

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples", "ants.swl")


def test_ants_runs():
    """Ant foraging runs 50 ticks without errors."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(50)
    assert w.tick_count == 50
    assert len(w.agents) == 200


def test_ants_pheromone_variance():
    """After 50 ticks, pheromone field should have some variance."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(50)
    var = np.var(w.fields["pheromone"])
    assert var > 0
