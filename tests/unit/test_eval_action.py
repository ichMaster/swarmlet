"""Tests for action evaluator with intent record."""

import pytest
from swarmlet.parser import parse
from swarmlet.engine import World, AgentRecord, Intent
from swarmlet.errors import SwarmletRuntimeError


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


def test_stay_action():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = stay
    init cell = A
    init agent Bot 1
    """)
    x0, y0 = w.agents[0].x, w.agents[0].y
    w.step(1)
    assert w.agents[0].x == x0
    assert w.agents[0].y == y0


def test_die_action():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = die
    init cell = A
    init agent Bot 3
    """)
    assert len(w.agents) == 3
    w.step(1)
    assert len(w.agents) == 0


def test_move_action():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = move forward
    init cell = A
    """)
    from swarmlet.engine import AgentRecord
    a = AgentRecord(id=0, agent_type="Bot", x=5, y=5, fields={"heading": 0.0})
    w.agents = [a]
    w._next_agent_id = 1
    w.step(1)
    assert w.agents[0].x == 6  # Moved East


def test_set_agent_field():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { energy = 10 }
    let agent Bot = set energy = 5
    init cell = A
    init agent Bot 1
    """)
    w.step(1)
    assert w.agents[0].fields["energy"] == 5.0


def test_spawn_action():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = spawn Bot
    init cell = A
    init agent Bot 1
    """)
    assert len(w.agents) == 1
    w.step(1)
    assert len(w.agents) == 2
    # Spawned agent has default fields
    spawned = [a for a in w.agents if a.id != w.agents[0].id]
    assert len(spawned) == 1


def test_kill_action():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Wolf { heading = 0 }
    agent Sheep { heading = 0 }
    let agent Wolf = kill Sheep
    let agent Sheep = stay
    init cell = A
    """)
    from swarmlet.engine import AgentRecord
    wolf = AgentRecord(id=0, agent_type="Wolf", x=3, y=3, fields={"heading": 0.0})
    sheep = AgentRecord(id=1, agent_type="Sheep", x=3, y=3, fields={"heading": 0.0})
    w.agents = [wolf, sheep]
    w._next_agent_id = 2
    w.step(1)
    types = [a.agent_type for a in w.agents]
    assert "Wolf" in types
    assert "Sheep" not in types


def test_seq_with_energy_decrement():
    """Critical test: seq { set energy = self.energy - 1; if self.energy <= 0 then die else stay }"""
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { energy = 1 }
    let agent Bot = seq {
        set energy = self.energy - 1 ;
        if self.energy <= 0 then die else stay
    }
    init cell = A
    init agent Bot 1
    """)
    assert w.agents[0].fields["energy"] == 1.0
    w.step(1)
    # Energy was 1, decremented to 0, then die triggers
    assert len(w.agents) == 0


def test_cell_field_deposit():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field pheromone = 0.0
    agent Ant { heading = 0 }
    let agent Ant = set pheromone = 1.0
    init cell = A
    init agent Ant 1
    """)
    ax, ay = w.agents[0].x, w.agents[0].y
    w.step(1)
    assert w.fields["pheromone"][ay, ax] == 1.0


def test_cell_field_deposit_accumulation():
    """Two agents on same cell depositing should sum."""
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field pheromone = 0.0
    agent Ant { heading = 0 }
    let agent Ant = set pheromone = 1.0
    init cell = A
    """)
    from swarmlet.engine import AgentRecord
    a1 = AgentRecord(id=0, agent_type="Ant", x=2, y=2, fields={"heading": 0.0})
    a2 = AgentRecord(id=1, agent_type="Ant", x=2, y=2, fields={"heading": 0.0})
    w.agents = [a1, a2]
    w._next_agent_id = 2
    w.step(1)
    assert w.fields["pheromone"][2, 2] == 2.0


def test_action_if():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { energy = 5 }
    let agent Bot = if self.energy > 3 then stay else die
    init cell = A
    init agent Bot 1
    """)
    w.step(1)
    assert len(w.agents) == 1  # energy=5 > 3, so stay


def test_action_match():
    w = make_world("""
    world 5 x 5 wrap
    cell states Food | Empty
    agent Bot { heading = 0 }
    let agent Bot = match cell_state with
        | Food -> stay
        | _ -> move forward
    init cell = Food
    init agent Bot 1
    """)
    x0 = w.agents[0].x
    w.step(1)
    # All cells are Food, so agent stays
    assert w.agents[0].x == x0


def test_spawned_agent_does_not_act_same_tick():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = spawn Bot
    init cell = A
    init agent Bot 1
    """)
    w.step(1)
    # Parent spawned 1 Bot; spawned Bot should not have spawned another
    assert len(w.agents) == 2
