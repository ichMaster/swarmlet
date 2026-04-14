"""Integration test for Gray-Scott reaction-diffusion example."""

import os
import numpy as np
from swarmlet.parser import parse
from swarmlet.engine import World

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples", "gray_scott.swl")


def test_gray_scott_runs():
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(10)
    assert w.tick_count == 10


def test_gray_scott_v_field_nonzero():
    """V field should have nonzero values after some ticks."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(10)
    v_var = np.var(w.fields["v"])
    assert v_var > 0
