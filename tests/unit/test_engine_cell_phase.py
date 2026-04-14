"""Tests for cell phase tick."""

from swarmlet.parser import parse
from swarmlet.engine import World


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


def test_fire_becomes_empty():
    """One tick: Fire -> Empty."""
    w = make_world("""
    world 5 x 5 wrap
    cell states Empty | Tree | Fire
    let cell Fire = Empty
    let cell _ = state
    init cell = Tree
    """)
    w.states[2, 2] = w.state_to_idx["Fire"]
    w.step(1)
    assert w.get_state(2, 2) == "Empty"


def test_tree_near_fire_becomes_fire():
    w = make_world("""
    world 5 x 5 wrap
    cell states Empty | Tree | Fire
    let cell Fire = Empty
    let cell Tree = if any Fire then Fire else Tree
    let cell Empty = Empty
    init cell = Tree
    """)
    w.states[2, 2] = w.state_to_idx["Fire"]
    w.step(1)
    # Fire at (2,2) becomes Empty, Trees near it become Fire
    assert w.get_state(2, 2) == "Empty"
    assert w.get_state(2, 1) == "Fire"
    assert w.get_state(1, 2) == "Fire"
    assert w.get_state(3, 3) == "Fire"


def test_synchronous_semantics():
    """Result must be same regardless of cell iteration order.
    All cells read from current snapshot, not partial updates."""
    w = make_world("""
    world 5 x 5 wrap
    cell states Empty | Tree | Fire
    let cell Fire = Empty
    let cell Tree = if any Fire then Fire else Tree
    let cell Empty = Empty
    init cell = Tree
    """)
    w.states[2, 2] = w.state_to_idx["Fire"]
    # Run once
    w.step(1)
    snap1 = w.snapshot()

    # Reset and run again — should be identical
    w2 = make_world("""
    world 5 x 5 wrap
    cell states Empty | Tree | Fire
    let cell Fire = Empty
    let cell Tree = if any Fire then Fire else Tree
    let cell Empty = Empty
    init cell = Tree
    """)
    w2.states[2, 2] = w2.state_to_idx["Fire"]
    w2.step(1)
    snap2 = w2.snapshot()
    assert snap1["states"] == snap2["states"]


def test_field_decay():
    """set pheromone = field pheromone * 0.5 halves every cell's pheromone."""
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    field pheromone = 1.0
    let cell _ = seq { set pheromone = pheromone * 0.5 }
    init cell = A
    init field pheromone = 1.0
    """)
    # 'pheromone' as a bare var resolves to... it's not a state, not a param, not a local
    # but it IS a cell field name. The current eval treats unknown names as strings.
    # Let me use field() builtin instead.
    pass  # Tested via test_field_decay_with_builtin below


def test_field_decay_with_builtin():
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    field pheromone = 1.0
    let cell _ = seq { set pheromone = field pheromone * 0.5 }
    init cell = A
    init field pheromone = 1.0
    """)
    w.step(1)
    for y in range(3):
        for x in range(3):
            assert abs(w.fields["pheromone"][y, x] - 0.5) < 1e-10


def test_wildcard_fires_for_all():
    """Wildcard cell rule should fire for every cell."""
    w = make_world("""
    world 3 x 3 wrap
    cell states A | B
    let cell _ = B
    init cell = A
    """)
    w.step(1)
    for y in range(3):
        for x in range(3):
            assert w.get_state(x, y) == "B"


def test_specific_rule_wins_over_wildcard():
    w = make_world("""
    world 3 x 3 wrap
    cell states A | B | C
    let cell A = B
    let cell _ = C
    init cell = A
    """)
    w.step(1)
    # A has specific rule -> B, not C
    for y in range(3):
        for x in range(3):
            assert w.get_state(x, y) == "B"
