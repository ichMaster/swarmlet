"""Tests for the parser — expressions and pattern matching."""

import pytest
from swarmlet.parser import parse, Parser
from swarmlet.lexer import tokenize
from swarmlet import ast as A
from swarmlet.errors import SwarmletStaticError


def parse_expr(source: str) -> A.Any:
    """Helper: parse a source as 'init cell = <expr>' and return the expr."""
    prog = parse(f"init cell = {source}")
    assert isinstance(prog.decls[0], A.InitCell)
    return prog.decls[0].expr


def test_arithmetic_precedence():
    """1 + 2 * 3 should parse as BinOp(+, 1, BinOp(*, 2, 3))"""
    expr = parse_expr("1 + 2 * 3")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "+"
    assert isinstance(expr.left, A.Num)
    assert expr.left.value == 1.0
    assert isinstance(expr.right, A.BinOp)
    assert expr.right.op == "*"
    assert expr.right.left.value == 2.0
    assert expr.right.right.value == 3.0


def test_comparison():
    expr = parse_expr("x > 2")
    assert isinstance(expr, A.BinOp)
    assert expr.op == ">"


def test_boolean_operators():
    """not a and b: 'not' binds tighter than 'and'"""
    expr = parse_expr("not a and b")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "and"
    assert isinstance(expr.left, A.UnOp)
    assert expr.left.op == "not"


def test_or_and_precedence():
    expr = parse_expr("a or b and c")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "or"
    assert isinstance(expr.right, A.BinOp)
    assert expr.right.op == "and"


def test_let_expression():
    expr = parse_expr("let x = 5 in x + 1")
    assert isinstance(expr, A.Let)
    assert expr.name == "x"
    assert isinstance(expr.value, A.Num)
    assert isinstance(expr.body, A.BinOp)


def test_if_then_else():
    expr = parse_expr("if true then 1 else 0")
    assert isinstance(expr, A.If)
    assert isinstance(expr.cond, A.Bool)
    assert expr.cond.value is True
    assert isinstance(expr.then_expr, A.Num)
    assert isinstance(expr.else_expr, A.Num)


def test_match_single_case():
    expr = parse_expr("match x with | Tree -> Fire")
    assert isinstance(expr, A.Match)
    assert isinstance(expr.subject, A.Var)
    assert len(expr.cases) == 1
    assert expr.cases[0].patterns[0].value == "Tree"


def test_match_multi_case():
    expr = parse_expr("match x with | Tree -> Fire | Fire -> Empty | _ -> x")
    assert isinstance(expr, A.Match)
    assert len(expr.cases) == 3
    assert expr.cases[2].patterns[0].kind == "wildcard"


def test_match_with_guard():
    expr = parse_expr("match x with | Tree when y > 2 -> Fire | _ -> x")
    assert isinstance(expr, A.Match)
    assert expr.cases[0].guard is not None
    assert isinstance(expr.cases[0].guard, A.BinOp)


def test_or_patterns():
    expr = parse_expr("match x with | Tree | Bush -> Fire | _ -> x")
    assert isinstance(expr, A.Match)
    assert len(expr.cases[0].patterns) == 2
    assert expr.cases[0].patterns[0].value == "Tree"
    assert expr.cases[0].patterns[1].value == "Bush"


def test_function_application():
    expr = parse_expr("count Tree")
    assert isinstance(expr, A.Call)
    assert expr.func == "count"
    assert len(expr.args) == 1
    assert isinstance(expr.args[0], A.Var)
    assert expr.args[0].name == "Tree"


def test_multi_arg_function():
    expr = parse_expr("look 1 0")
    assert isinstance(expr, A.Call)
    assert expr.func == "look"
    assert len(expr.args) == 2


def test_dot_access():
    expr = parse_expr("self.heading")
    assert isinstance(expr, A.Dot)
    assert isinstance(expr.expr, A.Var)
    assert expr.expr.name == "self"
    assert expr.field_name == "heading"


def test_parenthesized_nested_match():
    """Parenthesized nested match should parse without error."""
    expr = parse_expr(
        "match x with | Tree -> (match y with | Fire -> Empty | _ -> Tree) | _ -> x"
    )
    assert isinstance(expr, A.Match)
    assert isinstance(expr.cases[0].body, A.Match)


def test_bare_nested_match_error():
    """Bare nested match (without parens) should produce an error."""
    with pytest.raises(SwarmletStaticError) as exc_info:
        parse_expr(
            "match x with | Tree -> match y with | Fire -> Empty | _ -> Tree"
        )
    assert "nested match must be parenthesized" in str(exc_info.value)


def test_unary_minus():
    expr = parse_expr("-5")
    assert isinstance(expr, A.UnOp)
    assert expr.op == "-"
    assert isinstance(expr.operand, A.Num)


def test_parenthesized_grouping():
    expr = parse_expr("(1 + 2) * 3")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "*"
    assert isinstance(expr.left, A.BinOp)
    assert expr.left.op == "+"


def test_mod_operator():
    expr = parse_expr("x mod 8")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "mod"


def test_unit_literal():
    expr = parse_expr("random ()")
    assert isinstance(expr, A.Call)
    assert expr.func == "random"


def test_chained_comparison():
    """Only one comparison allowed per level."""
    expr = parse_expr("a == b")
    assert isinstance(expr, A.BinOp)
    assert expr.op == "=="
