"""Tests for AST node definitions."""

from swarmlet.ast import (
    Program, WorldDecl, StatesDecl, FieldDecl, ParamDecl, AgentDecl,
    CellRule, AgentRule, InitCell, InitField, InitAgent,
    Num, Bool, Var, BinOp, UnOp, Call, Dot, If, Let, Match,
    Pattern, MatchCase,
    CellExpr, CellSeq, CellBecome, CellSet,
    AStay, ADie, AMove, ASet, ASpawn, AKill, ASeq, AIf, AMatch, ActionCase,
)


def test_all_names_importable():
    """from swarmlet.ast import * should expose all node types."""
    from swarmlet import ast as ast_mod
    expected = {
        "Program", "WorldDecl", "StatesDecl", "FieldDecl", "ParamDecl", "AgentDecl",
        "CellRule", "AgentRule", "InitCell", "InitField", "InitAgent",
        "Num", "Bool", "Var", "BinOp", "UnOp", "Call", "Dot", "If", "Let", "Match",
        "Pattern", "MatchCase",
        "CellExpr", "CellSeq", "CellBecome", "CellSet",
        "AStay", "ADie", "AMove", "ASet", "ASpawn", "AKill", "ASeq", "AIf", "AMatch", "ActionCase",
    }
    available = {name for name in dir(ast_mod) if not name.startswith("_")}
    for name in expected:
        assert name in available, f"{name} not found in swarmlet.ast"


def test_world_decl():
    w = WorldDecl(width=100, height=80, topology="wrap", line=1)
    assert w.width == 100
    assert w.height == 80
    assert w.topology == "wrap"
    assert w.line == 1
    assert "100x80" in repr(w)


def test_cell_rule():
    body = CellExpr(expr=Var("Empty", line=5), line=5)
    rule = CellRule(pattern="Tree", body=body, line=4)
    assert rule.pattern == "Tree"
    assert rule.line == 4
    assert isinstance(rule.body, CellExpr)


def test_agent_rule_with_seq():
    seq = ASeq(actions=[
        ASet(field_name="energy", expr=BinOp("+", Dot(Var("self"), "energy"), Num(1)), line=10),
        AMove(direction=Call("forward", [], line=11), line=11),
    ], line=10)
    rule = AgentRule(agent_type="Ant", body=seq, line=9)
    assert rule.agent_type == "Ant"
    assert isinstance(rule.body, ASeq)
    assert len(rule.body.actions) == 2


def test_match_expression():
    cases = [
        MatchCase(
            patterns=[Pattern("ident", "Tree")],
            guard=None,
            body=Var("Empty"),
            line=3,
        ),
        MatchCase(
            patterns=[Pattern("wildcard", None), Pattern("ident", "Empty")],
            guard=BinOp(">", Call("count", [Var("Tree")]), Num(2)),
            body=Var("Tree"),
            line=4,
        ),
    ]
    m = Match(subject=Call("state", []), cases=cases, line=2)
    assert len(m.cases) == 2
    assert m.cases[1].guard is not None
    assert len(m.cases[1].patterns) == 2


def test_nodes_are_frozen():
    n = Num(value=42, line=1)
    try:
        n.value = 99
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_aseq_construction():
    seq = ASeq(actions=[
        ASet("pheromone", Num(1.0), line=1),
        AMove(Var("forward", line=2), line=2),
        ASpawn("Ant", line=3),
        AKill("Wolf", line=4),
        ADie(line=5),
    ], line=1)
    assert len(seq.actions) == 5
    assert isinstance(seq.actions[0], ASet)
    assert isinstance(seq.actions[4], ADie)


def test_init_nodes():
    ic = InitCell(expr=Var("Empty"), line=1)
    assert isinstance(ic.expr, Var)

    ifld = InitField(field_name="heat", expr=Num(0.0), line=2)
    assert ifld.field_name == "heat"

    ia = InitAgent(agent_type="Ant", count=100, line=3)
    assert ia.count == 100
