"""Tests for the expression evaluator."""

import numpy as np
import pytest
from swarmlet import ast as A
from swarmlet.eval import eval_expr, ExprContext
from swarmlet.builtins import EvalContext
from swarmlet.errors import SwarmletRuntimeError


def make_ctx(seed=42, locals=None, params=None, cell_states=None):
    rng = np.random.default_rng(seed)
    return ExprContext(
        rng=rng,
        locals=locals or {},
        params=params or {},
        cell_states=cell_states or set(),
        builtin_ctx=EvalContext(rng=rng),
    )


def test_num():
    assert eval_expr(A.Num(42.0), make_ctx()) == 42.0


def test_bool():
    assert eval_expr(A.Bool(True), make_ctx()) is True


def test_arithmetic():
    # 1 + 2 * 3 = 7
    expr = A.BinOp("+", A.Num(1.0), A.BinOp("*", A.Num(2.0), A.Num(3.0)))
    assert eval_expr(expr, make_ctx()) == 7.0


def test_comparison():
    expr = A.BinOp(">", A.Num(5.0), A.Num(3.0))
    assert eval_expr(expr, make_ctx()) is True


def test_boolean_ops():
    expr = A.BinOp("and", A.Bool(True), A.Bool(False))
    assert eval_expr(expr, make_ctx()) is False

    expr = A.BinOp("or", A.Bool(True), A.Bool(False))
    assert eval_expr(expr, make_ctx()) is True


def test_unary_not():
    expr = A.UnOp("not", A.Bool(True))
    assert eval_expr(expr, make_ctx()) is False


def test_unary_minus():
    expr = A.UnOp("-", A.Num(5.0))
    assert eval_expr(expr, make_ctx()) == -5.0


def test_let_expression():
    # let x = 5 in x + 1
    expr = A.Let("x", A.Num(5.0), A.BinOp("+", A.Var("x"), A.Num(1.0)))
    assert eval_expr(expr, make_ctx()) == 6.0


def test_let_nested_shadowing():
    # let x = 5 in let x = 10 in x => 10
    expr = A.Let("x", A.Num(5.0),
                 A.Let("x", A.Num(10.0), A.Var("x")))
    assert eval_expr(expr, make_ctx()) == 10.0


def test_if_then_else():
    expr = A.If(A.Bool(True), A.Num(1.0), A.Num(0.0))
    assert eval_expr(expr, make_ctx()) == 1.0

    expr = A.If(A.Bool(False), A.Num(1.0), A.Num(0.0))
    assert eval_expr(expr, make_ctx()) == 0.0


def test_match_single_case():
    # match 5 with | Tree -> 1 | _ -> 2
    expr = A.Match(
        subject=A.Num(5.0),
        cases=[
            A.MatchCase([A.Pattern("ident", "Tree")], None, A.Num(1.0)),
            A.MatchCase([A.Pattern("wildcard", None)], None, A.Num(2.0)),
        ],
    )
    assert eval_expr(expr, make_ctx()) == 2.0


def test_match_state():
    ctx = make_ctx(cell_states={"Tree", "Fire"})
    expr = A.Match(
        subject=A.Var("Tree"),
        cases=[
            A.MatchCase([A.Pattern("ident", "Tree")], None, A.Num(1.0)),
            A.MatchCase([A.Pattern("wildcard", None)], None, A.Num(2.0)),
        ],
    )
    assert eval_expr(expr, ctx) == 1.0


def test_match_with_guard():
    expr = A.Match(
        subject=A.Num(5.0),
        cases=[
            A.MatchCase(
                [A.Pattern("wildcard", None)],
                A.BinOp(">", A.Num(5.0), A.Num(10.0)),  # guard fails
                A.Num(1.0),
            ),
            A.MatchCase([A.Pattern("wildcard", None)], None, A.Num(2.0)),
        ],
    )
    assert eval_expr(expr, make_ctx()) == 2.0


def test_match_or_patterns():
    ctx = make_ctx(cell_states={"A", "B", "C"})
    expr = A.Match(
        subject=A.Var("B"),
        cases=[
            A.MatchCase(
                [A.Pattern("ident", "A"), A.Pattern("ident", "B")],
                None, A.Num(1.0),
            ),
            A.MatchCase([A.Pattern("wildcard", None)], None, A.Num(2.0)),
        ],
    )
    assert eval_expr(expr, ctx) == 1.0


def test_non_exhaustive_match():
    expr = A.Match(
        subject=A.Num(99.0),
        cases=[
            A.MatchCase([A.Pattern("number", 1.0)], None, A.Num(1.0)),
        ],
    )
    with pytest.raises(SwarmletRuntimeError, match="non-exhaustive"):
        eval_expr(expr, make_ctx())


def test_type_error_comparison():
    """Comparing a state to a number with < should raise."""
    ctx = make_ctx(cell_states={"Tree"})
    expr = A.BinOp("<", A.Var("Tree"), A.Num(5.0))
    with pytest.raises(SwarmletRuntimeError, match="expected number"):
        eval_expr(expr, ctx)


def test_var_from_locals():
    ctx = make_ctx(locals={"x": 42.0})
    assert eval_expr(A.Var("x"), ctx) == 42.0


def test_var_from_params():
    ctx = make_ctx(params={"p_fire": 0.001})
    assert eval_expr(A.Var("p_fire"), ctx) == 0.001


def test_call_builtin():
    ctx = make_ctx(seed=42)
    expr = A.Call("abs", [A.UnOp("-", A.Num(7.0))])
    assert eval_expr(expr, ctx) == 7.0


def test_equality_states():
    ctx = make_ctx(cell_states={"Tree", "Fire"})
    expr = A.BinOp("==", A.Var("Tree"), A.Var("Tree"))
    assert eval_expr(expr, ctx) is True

    expr = A.BinOp("==", A.Var("Tree"), A.Var("Fire"))
    assert eval_expr(expr, ctx) is False


def test_division_by_zero():
    expr = A.BinOp("/", A.Num(1.0), A.Num(0.0))
    with pytest.raises(SwarmletRuntimeError, match="division by zero"):
        eval_expr(expr, make_ctx())
