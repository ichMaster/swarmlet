"""Tests for the static analyzer."""

import pytest
from swarmlet.parser import parse
from swarmlet.analyzer import analyze
from swarmlet.errors import SwarmletStaticError


def analyze_source(source: str):
    prog = parse(source)
    return analyze(prog)


def test_valid_forest_fire():
    """A valid forest fire program should pass analysis."""
    source = """
    world 100 x 100 wrap
    cell states Empty | Tree | Fire
    param p_grow = 0.01
    param p_fire = 0.0001
    let cell Fire = Empty
    let cell Tree =
        if any Fire then Fire
        else if random () < p_fire then Fire
        else Tree
    let cell Empty =
        if random () < p_grow then Tree
        else Empty
    init cell = Empty
    """
    analyze_source(source)  # should not raise


def test_duplicate_cell_state():
    with pytest.raises(SwarmletStaticError, match="duplicate cell state"):
        analyze_source("cell states A | B | A")


def test_duplicate_cell_rule():
    with pytest.raises(SwarmletStaticError, match="duplicate cell rule"):
        analyze_source("""
        cell states A | B
        let cell A = B
        let cell A = A
        """)


def test_let_shadows_builtin():
    with pytest.raises(SwarmletStaticError, match="shadows a built-in"):
        analyze_source("""
        cell states A | B
        init cell = let random = 5 in A
        """)


def test_heading_required_without_heading():
    with pytest.raises(SwarmletStaticError, match="heading field"):
        analyze_source("""
        cell states A | B
        agent Ant { carrying = 0 }
        let agent Ant = move forward
        init cell = A
        """)


def test_heading_required_with_heading():
    """Agent with heading field should be able to use forward."""
    analyze_source("""
    cell states A | B
    agent Ant { carrying = 0, heading = 0 }
    let agent Ant = move forward
    init cell = A
    """)


def test_unknown_agent_type_in_init():
    with pytest.raises(SwarmletStaticError, match="unknown agent type"):
        analyze_source("""
        cell states A | B
        init agent Ghost 100
        """)


def test_unknown_agent_type_in_spawn():
    with pytest.raises(SwarmletStaticError, match="unknown agent type"):
        analyze_source("""
        cell states A | B
        agent Ant { heading = 0 }
        let agent Ant = spawn Ghost
        init cell = A
        """)


def test_set_cell_field_annotated():
    """set pheromone in agent context where pheromone is a cell field -> cell deposit."""
    source = """
    cell states A | B
    field pheromone = 0.0
    agent Ant { heading = 0 }
    let agent Ant = set pheromone = 1.0
    init cell = A
    """
    prog = parse(source)
    a = analyze(prog)
    # Find the AgentRule
    from swarmlet import ast as A
    agent_rule = [d for d in prog.decls if isinstance(d, A.AgentRule)][0]
    assert hasattr(agent_rule.body, "_target")
    assert agent_rule.body._target == "cell"


def test_set_agent_field_annotated():
    """set energy in agent context where energy is an agent field -> agent field write."""
    source = """
    cell states A | B
    agent Ant { energy = 10 }
    let agent Ant = set energy = 5
    init cell = A
    """
    prog = parse(source)
    a = analyze(prog)
    from swarmlet import ast as A
    agent_rule = [d for d in prog.decls if isinstance(d, A.AgentRule)][0]
    assert hasattr(agent_rule.body, "_target")
    assert agent_rule.body._target == "agent"


def test_set_unknown_field():
    with pytest.raises(SwarmletStaticError, match="unknown field"):
        analyze_source("""
        cell states A | B
        agent Ant { heading = 0 }
        let agent Ant = set foo = 1
        init cell = A
        """)


def test_multiple_errors_collected():
    """Multiple errors should be collected and reported together."""
    with pytest.raises(SwarmletStaticError) as exc_info:
        analyze_source("""
        cell states A | B | A
        agent Ant { heading = 0 }
        let agent Ant = spawn Ghost
        """)
    msg = str(exc_info.value)
    assert "duplicate cell state" in msg
    assert "unknown agent type" in msg


def test_agent_context_builtin_in_cell_rule():
    """Using agent-only builtin (like self) in cell rule should error."""
    with pytest.raises(SwarmletStaticError, match="agent rules"):
        analyze_source("""
        cell states A | B
        let cell A = if self == A then B else A
        """)


def test_x_y_outside_init():
    """x and y can only be used in init context."""
    with pytest.raises(SwarmletStaticError, match="init context"):
        analyze_source("""
        cell states A | B
        let cell A = if x > 50 then B else A
        """)
