"""Tests for agent context built-in functions."""

import math
from swarmlet.parser import parse
from swarmlet.engine import World, AgentRecord
from swarmlet.builtins import STAY
from swarmlet.eval import (
    _agents_in_radius, _agents_of_type_in_radius,
    _nearest_agent_dir, _nearest_agent_of_type_dir,
    _mean_heading_in_radius, _argmax_neighbor, _argmin_neighbor,
)


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


def _add_agent(w, atype, x, y, fields=None):
    a = AgentRecord(id=w._next_agent_id, agent_type=atype, x=x, y=y,
                    fields=fields or {})
    w._next_agent_id += 1
    w.agents.append(a)
    return a


def test_agents_in_radius_excludes_self():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { }
    init cell = A
    """)
    agent = _add_agent(w, "Bot", 5, 5)
    assert _agents_in_radius(w, agent, 0) == 0
    assert _agents_in_radius(w, agent, 5) == 0


def test_agents_in_radius_counts():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { }
    init cell = A
    """)
    me = _add_agent(w, "Bot", 5, 5)
    _add_agent(w, "Bot", 5, 6)  # distance 1
    _add_agent(w, "Bot", 7, 5)  # distance 2
    _add_agent(w, "Bot", 9, 9)  # distance 4
    assert _agents_in_radius(w, me, 1) == 1
    assert _agents_in_radius(w, me, 2) == 2
    assert _agents_in_radius(w, me, 5) == 3


def test_agents_of_type_in_radius():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Wolf { }
    agent Sheep { }
    init cell = A
    """)
    me = _add_agent(w, "Wolf", 5, 5)
    _add_agent(w, "Wolf", 5, 6)
    _add_agent(w, "Sheep", 5, 7)
    assert _agents_of_type_in_radius(w, me, "Wolf", 3) == 1
    assert _agents_of_type_in_radius(w, me, "Sheep", 3) == 1


def test_nearest_agent_dir_none():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { }
    init cell = A
    """)
    me = _add_agent(w, "Bot", 5, 5)
    assert _nearest_agent_dir(w, me, 5) == STAY


def test_nearest_agent_dir_east():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { }
    init cell = A
    """)
    me = _add_agent(w, "Bot", 5, 5)
    _add_agent(w, "Bot", 7, 5)  # East of me
    d = _nearest_agent_dir(w, me, 5)
    assert d == 0  # East


def test_nearest_agent_of_type_dir():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Wolf { }
    agent Sheep { }
    init cell = A
    """)
    me = _add_agent(w, "Wolf", 5, 5)
    _add_agent(w, "Sheep", 5, 3)  # North
    d = _nearest_agent_of_type_dir(w, me, "Sheep", 5)
    assert d == 6  # North


def test_mean_heading_in_radius():
    """Two agents: one heading East (0), one heading South (2) -> SE (1)."""
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    init cell = A
    """)
    me = _add_agent(w, "Bot", 5, 5, {"heading": 0})
    _add_agent(w, "Bot", 5, 6, {"heading": 0})   # East
    _add_agent(w, "Bot", 6, 5, {"heading": 2})   # South
    d = _mean_heading_in_radius(w, me, 3)
    assert d == 1  # SE (average of E and S)


def test_mean_heading_no_neighbors():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    init cell = A
    """)
    me = _add_agent(w, "Bot", 5, 5, {"heading": 0})
    assert _mean_heading_in_radius(w, me, 3) == STAY


def test_argmax_neighbor():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field heat = 0.0
    init cell = A
    """)
    w.fields["heat"][2, 3] = 10.0  # East of (2, 2)
    d = _argmax_neighbor(w, 2, 2, "heat")
    assert d == 0  # East


def test_argmin_neighbor():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field heat = 5.0
    init cell = A
    init field heat = 5.0
    """)
    # numpy indexing: [y, x]. Set (x=2, y=1) = North of (2,2) to 0
    w.fields["heat"][1, 2] = 0.0  # North of (2, 2)
    d = _argmin_neighbor(w, 2, 2, "heat")
    assert d == 6  # North


def test_cell_state_in_agent():
    """Agent should be able to read cell_state."""
    w = make_world("""
    world 5 x 5 wrap
    cell states Food | Empty
    agent Ant { heading = 0 }
    let agent Ant = if cell_state == Food then stay else move forward
    init cell = Food
    init agent Ant 1
    """)
    # Should run without error
    w.step(1)
