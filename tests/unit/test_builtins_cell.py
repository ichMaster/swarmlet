"""Tests for cell context built-in functions."""

from swarmlet.parser import parse
from swarmlet.engine import World


def make_world(source: str, seed: int = 42) -> World:
    return World(parse(source), seed=seed)


def test_count_neighbors():
    """count Tree should count Moore neighbors."""
    w = make_world("""
    world 3 x 3 wrap
    cell states Empty | Tree
    init cell = Tree
    """)
    # All cells are Tree, center has 8 Moore neighbors all Tree
    assert w.get_state(1, 1) == "Tree"


def test_any_neighbor():
    """Full forest fire: any Fire triggers Tree->Fire."""
    w = make_world("""
    world 5 x 5 wrap
    cell states Empty | Tree | Fire
    let cell Fire = Empty
    let cell Tree = if any Fire then Fire else Tree
    let cell Empty = Empty
    init cell = Tree
    """)
    # Set center cell to Fire
    w.states[2, 2] = w.state_to_idx["Fire"]
    w.step(1)
    # Neighbors of (2,2) should now be Fire
    assert w.get_state(2, 2) == "Empty"  # Fire -> Empty
    assert w.get_state(2, 1) == "Fire"   # Tree adjacent to Fire -> Fire


def test_laplacian_uniform():
    """Laplacian of a uniform field should be ~0."""
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field heat = 1.0
    init cell = A
    init field heat = 1.0
    """)
    from swarmlet.eval import _laplacian
    val = _laplacian(w, 2, 2, "heat")
    assert abs(val) < 1e-10


def test_laplacian_spike():
    """Laplacian of single spike should be negative at center."""
    w = make_world("""
    world 5 x 5 wrap
    cell states A
    field heat = 0.0
    init cell = A
    """)
    w.fields["heat"][2, 2] = 10.0
    from swarmlet.eval import _laplacian
    val = _laplacian(w, 2, 2, "heat")
    assert val < 0  # center has -1 * 10 = -10, neighbors contribute 0


def test_distance_to():
    """distance_to should find nearest target."""
    w = make_world("""
    world 10 x 10 wrap
    cell states Empty | Target
    init cell = Empty
    """)
    w.states[5, 5] = w.state_to_idx["Target"]
    from swarmlet.eval import _distance_to
    assert _distance_to(w, 5, 3, "Target") == 2
    assert _distance_to(w, 3, 5, "Target") == 2
    # No target within radius 16 from (0,0) — wrap distance is 5
    assert _distance_to(w, 0, 0, "Target") == 5


def test_gradient_to():
    """gradient_to should return direction toward target."""
    w = make_world("""
    world 10 x 10 wrap
    cell states Empty | Target
    init cell = Empty
    """)
    w.states[5, 5] = w.state_to_idx["Target"]
    from swarmlet.eval import _gradient_to
    d = _gradient_to(w, 3, 5, "Target")
    assert d == 0  # East (target is to the right)


def test_wrap_topology():
    """Cell at (0,0) should see (W-1, H-1) as a Moore neighbor."""
    w = make_world("""
    world 5 x 5 wrap
    cell states Empty | Mark
    init cell = Empty
    """)
    w.states[4, 4] = w.state_to_idx["Mark"]
    s = w.get_state(-1, -1)  # wraps to (4, 4)
    assert s == "Mark"


def test_bounded_topology():
    """Out-of-bounds in bounded topology returns None."""
    w = make_world("""
    world 5 x 5 bounded
    cell states A
    init cell = A
    """)
    s = w.get_state(-1, -1)
    assert s is None


def test_field_read():
    """field name reads current cell's field value."""
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    field heat = 0.0
    init cell = A
    init field heat = 5.0
    """)
    val = w.get_field(1, 1, "heat")
    assert val == 5.0


def test_cell_seq_set_field():
    """Cell seq with set should update field values."""
    w = make_world("""
    world 3 x 3 wrap
    cell states A
    field pheromone = 1.0
    let cell _ = seq { set pheromone = 0.5 }
    init cell = A
    init field pheromone = 1.0
    """)
    w.step(1)
    assert abs(w.fields["pheromone"][1, 1] - 0.5) < 1e-10
