"""Tests for the parser — cell rules and agent actions."""

import pytest
from swarmlet.parser import parse
from swarmlet import ast as A
from swarmlet.errors import SwarmletStaticError


def test_cell_rule_simple_expr():
    """let cell Tree = Fire"""
    prog = parse("let cell Tree = Fire")
    r = prog.decls[0]
    assert isinstance(r, A.CellRule)
    assert r.pattern == "Tree"
    assert isinstance(r.body, A.CellExpr)
    assert isinstance(r.body.expr, A.Var)
    assert r.body.expr.name == "Fire"


def test_cell_rule_wildcard():
    """let cell _ = state"""
    prog = parse("let cell _ = state")
    r = prog.decls[0]
    assert r.pattern == "_"


def test_cell_rule_seq_body():
    """Cell rule with seq body containing set statement."""
    prog = parse("let cell _ = seq { set pheromone = pheromone * 0.98 }")
    r = prog.decls[0]
    assert isinstance(r.body, A.CellSeq)
    assert len(r.body.stmts) == 1
    assert isinstance(r.body.stmts[0], A.CellSet)
    assert r.body.stmts[0].field_name == "pheromone"


def test_cell_rule_seq_become_and_set():
    prog = parse("let cell Tree = seq { become Fire ; set heat = 1.0 }")
    r = prog.decls[0]
    assert isinstance(r.body, A.CellSeq)
    assert len(r.body.stmts) == 2
    assert isinstance(r.body.stmts[0], A.CellBecome)
    assert isinstance(r.body.stmts[1], A.CellSet)


def test_agent_rule_stay():
    prog = parse("let agent Ant = stay")
    r = prog.decls[0]
    assert isinstance(r, A.AgentRule)
    assert r.agent_type == "Ant"
    assert isinstance(r.body, A.AStay)


def test_agent_rule_die():
    prog = parse("let agent Ant = die")
    r = prog.decls[0]
    assert isinstance(r.body, A.ADie)


def test_agent_rule_move():
    prog = parse("let agent Ant = move forward")
    r = prog.decls[0]
    assert isinstance(r.body, A.AMove)


def test_agent_rule_set():
    prog = parse("let agent Ant = set energy = 10")
    r = prog.decls[0]
    assert isinstance(r.body, A.ASet)
    assert r.body.field_name == "energy"


def test_agent_rule_spawn():
    prog = parse("let agent Ant = spawn Ant")
    r = prog.decls[0]
    assert isinstance(r.body, A.ASpawn)
    assert r.body.agent_type == "Ant"


def test_agent_rule_kill():
    prog = parse("let agent Wolf = kill Sheep")
    r = prog.decls[0]
    assert isinstance(r.body, A.AKill)
    assert r.body.agent_type == "Sheep"


def test_agent_rule_seq():
    prog = parse("let agent Ant = seq { stay ; move forward }")
    r = prog.decls[0]
    assert isinstance(r.body, A.ASeq)
    assert len(r.body.actions) == 2
    assert isinstance(r.body.actions[0], A.AStay)
    assert isinstance(r.body.actions[1], A.AMove)


def test_agent_rule_if():
    prog = parse("let agent Ant = if true then stay else die")
    r = prog.decls[0]
    assert isinstance(r.body, A.AIf)
    assert isinstance(r.body.then_action, A.AStay)
    assert isinstance(r.body.else_action, A.ADie)


def test_agent_rule_match():
    prog = parse("let agent Ant = match cell_state with | Food -> stay | _ -> move forward")
    r = prog.decls[0]
    assert isinstance(r.body, A.AMatch)
    assert len(r.body.cases) == 2


def test_agent_rule_nested_seq():
    prog = parse("""let agent Ant = seq {
        set energy = self.energy + 1 ;
        move forward ;
        spawn Ant
    }""")
    r = prog.decls[0]
    assert isinstance(r.body, A.ASeq)
    assert len(r.body.actions) == 3


def test_forest_fire_parses():
    """A simplified forest fire model should parse without errors."""
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
    prog = parse(source)
    assert len(prog.decls) >= 7


def test_cell_rule_with_match():
    """Cell rule body can be a match expression."""
    source = """
    let cell _ = match state with
        | Fire -> Empty
        | Tree when any Fire -> Fire
        | Tree when random () < 0.0001 -> Fire
        | Empty when random () < 0.01 -> Tree
        | _ -> state
    """
    prog = parse(source)
    r = prog.decls[0]
    assert isinstance(r, A.CellRule)
    body = r.body
    assert isinstance(body, A.CellExpr)
    assert isinstance(body.expr, A.Match)
    assert len(body.expr.cases) == 5
