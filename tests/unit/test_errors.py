"""Tests for Token model and error hierarchy."""

from swarmlet.lexer import Token
from swarmlet.errors import SwarmletError, SwarmletStaticError, SwarmletRuntimeError


def test_token_creation_and_fields():
    t = Token(kind="IDENT", value="Tree", line=1, col=5)
    assert t.kind == "IDENT"
    assert t.value == "Tree"
    assert t.line == 1
    assert t.col == 5


def test_token_is_frozen():
    t = Token(kind="NUM", value=42, line=2, col=1)
    try:
        t.kind = "OTHER"
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_token_is_hashable():
    t1 = Token(kind="IDENT", value="Tree", line=1, col=5)
    t2 = Token(kind="IDENT", value="Tree", line=1, col=5)
    assert hash(t1) == hash(t2)
    assert t1 == t2
    s = {t1, t2}
    assert len(s) == 1


def test_token_repr():
    t = Token(kind="IDENT", value="Tree", line=1, col=5)
    assert repr(t) == "Token(IDENT, 'Tree', 1:5)"


def test_static_error_with_position():
    e = SwarmletStaticError(5, 12, "unexpected character")
    assert str(e) == "SwarmletStaticError at line 5, col 12: unexpected character"
    assert e.line == 5
    assert e.col == 12


def test_static_error_line_only():
    e = SwarmletStaticError(line=3, message="duplicate rule")
    assert str(e) == "SwarmletStaticError at line 3: duplicate rule"


def test_static_error_no_position():
    e = SwarmletStaticError(message="general error")
    assert str(e) == "SwarmletStaticError: general error"


def test_runtime_error_with_line():
    e = SwarmletRuntimeError("non-exhaustive match", line=10)
    assert str(e) == "SwarmletRuntimeError at line 10: non-exhaustive match"


def test_runtime_error_no_line():
    e = SwarmletRuntimeError("non-exhaustive match")
    assert str(e) == "SwarmletRuntimeError: non-exhaustive match"


def test_error_hierarchy():
    assert issubclass(SwarmletStaticError, SwarmletError)
    assert issubclass(SwarmletRuntimeError, SwarmletError)
    assert issubclass(SwarmletError, Exception)


def test_errors_are_catchable():
    try:
        raise SwarmletStaticError(1, 1, "test")
    except SwarmletError:
        pass

    try:
        raise SwarmletRuntimeError("test")
    except SwarmletError:
        pass
