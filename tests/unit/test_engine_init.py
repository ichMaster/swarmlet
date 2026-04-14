"""Tests for World class, snapshot, and initialization."""

import json
from swarmlet.parser import parse
from swarmlet.engine import World


def make_world(source: str, seed: int = 42, params=None) -> World:
    prog = parse(source)
    return World(prog, seed=seed, params=params)


def test_empty_world():
    w = make_world("world 5 x 5 wrap\ncell states A | B")
    assert w.width == 5
    assert w.height == 5
    assert w.topology == "wrap"


def test_init_cell():
    w = make_world("""
    world 3 x 3 wrap
    cell states Empty | Tree
    init cell = Empty
    """)
    snap = w.snapshot()
    for row in snap["states"]:
        for cell in row:
            assert cell == "Empty"


def test_init_field():
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    field heat = 0.0
    init cell = A
    init field heat = 1.5
    """)
    snap = w.snapshot()
    for row in snap["fields"]["heat"]:
        for val in row:
            assert val == 1.5


def test_init_agent():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Ant { heading = 0 }
    init cell = A
    init agent Ant 20
    """)
    assert len(w.agents) == 20
    for a in w.agents:
        assert a.agent_type == "Ant"
        assert 0 <= a.x < 10
        assert 0 <= a.y < 10
        assert a.fields["heading"] == 0.0


def test_snapshot_structure():
    w = make_world("""
    world 3 x 3 wrap
    cell states A | B
    field heat = 0.0
    agent Bot { energy = 5 }
    init cell = A
    init agent Bot 2
    """)
    snap = w.snapshot()
    assert "tick" in snap
    assert "width" in snap
    assert "height" in snap
    assert "topology" in snap
    assert "states" in snap
    assert "fields" in snap
    assert "agents" in snap
    assert snap["tick"] == 0
    assert len(snap["agents"]) == 2


def test_to_json():
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    init cell = A
    """)
    j = w.to_json()
    data = json.loads(j)
    assert data["width"] == 3


def test_reset_reproducibility():
    source = """
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    init cell = A
    init agent Bot 10
    """
    w1 = make_world(source, seed=42)
    positions1 = [(a.x, a.y) for a in w1.agents]

    w1.reset(seed=42)
    positions2 = [(a.x, a.y) for a in w1.agents]
    assert positions1 == positions2


def test_reset_different_seed():
    source = """
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    init cell = A
    init agent Bot 10
    """
    w = make_world(source, seed=42)
    pos42 = [(a.x, a.y) for a in w.agents]

    w.reset(seed=43)
    pos43 = [(a.x, a.y) for a in w.agents]
    assert len(pos42) == len(pos43) == 10
    assert pos42 != pos43  # different seed -> different positions


def test_param_overrides():
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    param rate = 0.5
    init cell = A
    """, params={"rate": 0.99})
    assert w._params["rate"] == 0.99
