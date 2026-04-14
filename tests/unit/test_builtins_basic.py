"""Tests for built-in function implementations — random, math, direction helpers."""

import numpy as np
import pytest
from swarmlet.builtins import BUILTINS, EvalContext, STAY
from swarmlet.errors import SwarmletRuntimeError


def make_ctx(seed=42, heading=None):
    return EvalContext(rng=np.random.default_rng(seed), agent_heading=heading)


def call(name, *args, ctx=None):
    if ctx is None:
        ctx = make_ctx()
    spec = BUILTINS[name]
    return spec.func(ctx, *args)


# --- Random ---

def test_random_in_range():
    ctx = make_ctx(seed=123)
    for _ in range(100):
        val = call("random", ctx=ctx)
        assert 0.0 <= val < 1.0


def test_random_int_range():
    ctx = make_ctx(seed=456)
    for _ in range(100):
        val = call("random_int", 10, ctx=ctx)
        assert 0 <= val < 10
        assert isinstance(val, int)


def test_random_dir_range():
    ctx = make_ctx(seed=789)
    vals = set()
    for _ in range(1000):
        d = call("random_dir", ctx=ctx)
        assert 0 <= d <= 7
        vals.add(d)
    # With 1000 samples, all 8 directions should appear
    assert len(vals) == 8


def test_random_deterministic():
    """Same seed produces same sequence."""
    ctx1 = make_ctx(seed=42)
    ctx2 = make_ctx(seed=42)
    for _ in range(10):
        assert call("random", ctx=ctx1) == call("random", ctx=ctx2)


# --- Math ---

def test_abs():
    assert call("abs", -5.0) == 5.0
    assert call("abs", 3.0) == 3.0


def test_min_max():
    assert call("min", 3.0, 7.0) == 3.0
    assert call("max", 3.0, 7.0) == 7.0


def test_sqrt():
    assert call("sqrt", 9.0) == 3.0


def test_exp():
    assert abs(call("exp", 0.0) - 1.0) < 1e-10


def test_floor():
    assert call("floor", 3.7) == 3.0
    assert call("floor", -1.2) == -2.0


def test_mod():
    assert call("mod", 7.0, 3.0) == 1.0


def test_clamp():
    assert call("clamp", 5.0, 0.0, 3.0) == 3.0
    assert call("clamp", -1.0, 0.0, 3.0) == 0.0
    assert call("clamp", 2.0, 0.0, 3.0) == 2.0


# --- Direction helpers ---

def test_dir_from_offset():
    assert call("dir", 1.0, 0.0) == 0   # East
    assert call("dir", 0.0, 1.0) == 2   # South
    assert call("dir", 0.0, 0.0) == STAY


def test_stay_constant():
    assert call("STAY") == STAY


def test_forward_back_left_right():
    for heading in range(8):
        ctx = make_ctx(heading=heading)
        assert call("forward", ctx=ctx) == heading
        assert call("back", ctx=ctx) == (heading + 4) % 8
        assert call("right", ctx=ctx) == (heading + 2) % 8
        assert call("left", ctx=ctx) == (heading + 6) % 8


def test_forward_without_heading_raises():
    ctx = make_ctx(heading=None)
    with pytest.raises(SwarmletRuntimeError, match="heading"):
        call("forward", ctx=ctx)
