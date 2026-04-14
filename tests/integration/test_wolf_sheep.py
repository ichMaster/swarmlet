"""Integration test for predator-prey (wolf-sheep) example."""

import os
from swarmlet.parser import parse
from swarmlet.engine import World

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples", "wolf_sheep.swl")


def test_wolf_sheep_runs():
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(50)
    assert w.tick_count == 50


def test_wolf_sheep_both_species_alive():
    """Both species should survive at least 50 ticks."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    w.step(50)
    types = {a.agent_type for a in w.agents}
    assert "Sheep" in types
    assert "Wolf" in types


def test_wolf_sheep_kills_happen():
    """Wolves should have killed some sheep (population changes)."""
    with open(EXAMPLE) as f:
        prog = parse(f.read())
    w = World(prog, seed=42)
    initial_sheep = len([a for a in w.agents if a.agent_type == "Sheep"])
    w.step(50)
    # Population should have changed (births, deaths, kills)
    final_sheep = len([a for a in w.agents if a.agent_type == "Sheep"])
    assert final_sheep != initial_sheep
