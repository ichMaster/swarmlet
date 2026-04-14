"""Tests for the parser — top-level declarations."""

import pytest
from swarmlet.parser import parse
from swarmlet import ast as A
from swarmlet.errors import SwarmletStaticError


def test_world_decl_wrap():
    prog = parse("world 100 x 100 wrap")
    assert len(prog.decls) == 1
    w = prog.decls[0]
    assert isinstance(w, A.WorldDecl)
    assert w.width == 100
    assert w.height == 100
    assert w.topology == "wrap"


def test_world_decl_bounded():
    prog = parse("world 50 x 30 bounded")
    w = prog.decls[0]
    assert w.width == 50
    assert w.height == 30
    assert w.topology == "bounded"


def test_world_decl_default_topology():
    prog = parse("world 64 x 64")
    w = prog.decls[0]
    assert w.topology == "wrap"


def test_cell_states():
    prog = parse("cell states Empty | Tree | Fire")
    s = prog.decls[0]
    assert isinstance(s, A.StatesDecl)
    assert s.names == ["Empty", "Tree", "Fire"]


def test_field_decl():
    prog = parse("field pheromone = 0.0")
    f = prog.decls[0]
    assert isinstance(f, A.FieldDecl)
    assert f.name == "pheromone"
    assert f.default == 0.0


def test_field_decl_negative():
    prog = parse("field temperature = -10")
    f = prog.decls[0]
    assert f.default == -10.0


def test_param_decl():
    prog = parse("param decay_rate = 0.98")
    p = prog.decls[0]
    assert isinstance(p, A.ParamDecl)
    assert p.name == "decay_rate"
    assert p.value == 0.98


def test_agent_decl():
    prog = parse("agent Ant { carrying = 0, heading = 0 }")
    a = prog.decls[0]
    assert isinstance(a, A.AgentDecl)
    assert a.name == "Ant"
    assert a.fields == [("carrying", 0.0), ("heading", 0.0)]


def test_agent_decl_empty():
    prog = parse("agent Marker { }")
    a = prog.decls[0]
    assert isinstance(a, A.AgentDecl)
    assert a.fields == []


def test_init_cell():
    prog = parse("init cell = Empty")
    i = prog.decls[0]
    assert isinstance(i, A.InitCell)


def test_init_field():
    prog = parse("init field pheromone = 0.0")
    i = prog.decls[0]
    assert isinstance(i, A.InitField)
    assert i.field_name == "pheromone"


def test_init_agent():
    prog = parse("init agent Ant 200")
    i = prog.decls[0]
    assert isinstance(i, A.InitAgent)
    assert i.agent_type == "Ant"
    assert i.count == 200


def test_multiple_decls():
    source = """
    world 100 x 100 wrap
    cell states Empty | Tree | Fire
    field heat = 0.0
    param p_grow = 0.01
    agent Ant { carrying = 0 }
    init agent Ant 100
    """
    prog = parse(source)
    assert len(prog.decls) == 6
    assert isinstance(prog.decls[0], A.WorldDecl)
    assert isinstance(prog.decls[1], A.StatesDecl)
    assert isinstance(prog.decls[2], A.FieldDecl)
    assert isinstance(prog.decls[3], A.ParamDecl)
    assert isinstance(prog.decls[4], A.AgentDecl)
    assert isinstance(prog.decls[5], A.InitAgent)


def test_syntax_error_message():
    with pytest.raises(SwarmletStaticError) as exc_info:
        parse("world 100 y 100")
    assert "expected 'x'" in str(exc_info.value)
    assert exc_info.value.line is not None
