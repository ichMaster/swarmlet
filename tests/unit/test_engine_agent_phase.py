"""Tests for the agent phase with conflict resolution."""

from swarmlet.parser import parse
from swarmlet.engine import World, AgentRecord


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


def test_single_agent_move():
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = move forward
    init cell = A
    """)
    a = AgentRecord(id=0, agent_type="Bot", x=5, y=5, fields={"heading": 0.0})
    w.agents = [a]
    w._next_agent_id = 1
    w.step(1)
    assert w.agents[0].x == 6  # Moved East


def test_movement_conflict_resolution():
    """Two agents moving to same cell: one wins, other stays."""
    w = make_world("""
    world 10 x 10 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = move forward
    init cell = A
    """)
    # Two agents moving East from adjacent positions
    a1 = AgentRecord(id=0, agent_type="Bot", x=4, y=5, fields={"heading": 0.0})
    a2 = AgentRecord(id=1, agent_type="Bot", x=5, y=5, fields={"heading": 0.0})
    # a1 wants (5,5), a2 wants (6,5) — no conflict here
    # Let's set them both to want the same cell
    # a1 at (4,5) heading East -> wants (5,5)
    # a2 at (5,5) heading West (4) -> wants (4,5)
    a2.fields["heading"] = 4.0  # West
    w.agents = [a1, a2]
    w._next_agent_id = 2
    # Before: a1=(4,5), a2=(5,5). a1 wants (5,5), a2 wants (4,5). No conflict.
    # Actually they cross, not collide. Let me use same target.
    a1 = AgentRecord(id=0, agent_type="Bot", x=4, y=5, fields={"heading": 0.0})  # East -> (5,5)
    a2 = AgentRecord(id=1, agent_type="Bot", x=5, y=4, fields={"heading": 2.0})  # South -> (5,5)
    w.agents = [a1, a2]
    w.step(1)
    # One should be at (5,5), other stayed at original position
    positions = sorted([(a.x, a.y) for a in w.agents])
    assert (5, 5) in positions  # One made it


def test_spawn_creates_agent():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = spawn Bot
    init cell = A
    init agent Bot 1
    """)
    w.step(1)
    assert len(w.agents) == 2


def test_die_removes_agent():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = die
    init cell = A
    init agent Bot 5
    """)
    w.step(1)
    assert len(w.agents) == 0


def test_kill_removes_target():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Wolf { heading = 0 }
    agent Sheep { heading = 0 }
    let agent Wolf = kill Sheep
    let agent Sheep = stay
    init cell = A
    """)
    wolf = AgentRecord(id=0, agent_type="Wolf", x=3, y=3, fields={"heading": 0.0})
    sheep1 = AgentRecord(id=1, agent_type="Sheep", x=3, y=3, fields={"heading": 0.0})
    sheep2 = AgentRecord(id=2, agent_type="Sheep", x=3, y=3, fields={"heading": 0.0})
    w.agents = [wolf, sheep1, sheep2]
    w._next_agent_id = 3
    w.step(1)
    sheep_alive = [a for a in w.agents if a.agent_type == "Sheep"]
    assert len(sheep_alive) == 1  # One killed


def test_cell_field_deposit_accumulation():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field ph = 0.0
    agent Ant { heading = 0 }
    let agent Ant = set ph = 1.0
    init cell = A
    """)
    a1 = AgentRecord(id=0, agent_type="Ant", x=2, y=2, fields={"heading": 0.0})
    a2 = AgentRecord(id=1, agent_type="Ant", x=2, y=2, fields={"heading": 0.0})
    w.agents = [a1, a2]
    w._next_agent_id = 2
    w.step(1)
    assert w.fields["ph"][2, 2] == 2.0


def test_spawned_does_not_act_same_tick():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Bot { heading = 0 }
    let agent Bot = spawn Bot
    init cell = A
    init agent Bot 1
    """)
    w.step(1)
    assert len(w.agents) == 2  # Only 1 spawn, not chain


def test_killed_agent_gone_next_tick():
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    agent Wolf { heading = 0 }
    agent Sheep { heading = 0 }
    let agent Wolf = kill Sheep
    let agent Sheep = stay
    init cell = A
    """)
    wolf = AgentRecord(id=0, agent_type="Wolf", x=3, y=3, fields={"heading": 0.0})
    sheep = AgentRecord(id=1, agent_type="Sheep", x=3, y=3, fields={"heading": 0.0})
    w.agents = [wolf, sheep]
    w._next_agent_id = 2
    w.step(1)
    assert len([a for a in w.agents if a.agent_type == "Sheep"]) == 0
    w.step(1)
    assert len([a for a in w.agents if a.agent_type == "Sheep"]) == 0


def test_determinism_100_steps():
    source = """
    world 10 x 10 wrap
    cell states A | B
    agent Bot { heading = 0 }
    let cell A = if random () < 0.01 then B else A
    let cell B = A
    let agent Bot = move forward
    init cell = A
    init agent Bot 5
    """
    w1 = make_world(source, seed=42)
    w1.step(100)
    s1 = w1.snapshot()

    w2 = make_world(source, seed=42)
    w2.step(100)
    s2 = w2.snapshot()

    assert s1["states"] == s2["states"]
    assert [(a["x"], a["y"]) for a in s1["agents"]] == [(a["x"], a["y"]) for a in s2["agents"]]


def test_step_100_no_errors():
    """A small predator-prey world should run 100 ticks without errors."""
    w = make_world("""
    world 10 x 10 wrap
    cell states Grass | Empty
    agent Wolf { heading = 0, energy = 5 }
    agent Sheep { heading = 0, energy = 3 }
    let cell Grass = if random () < 0.1 then Empty else Grass
    let cell Empty = if random () < 0.05 then Grass else Empty
    let agent Wolf = seq {
        move forward ;
        set energy = self.energy - 1 ;
        if self.energy <= 0 then die else stay
    }
    let agent Sheep = move forward
    init cell = Grass
    init agent Wolf 3
    init agent Sheep 5
    """)
    w.step(100)
    # Should complete without errors
    assert w.tick_count == 100
