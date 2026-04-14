"""Tests for the Swarmlet lexer."""

import pytest
from swarmlet.lexer import tokenize, Token
from swarmlet.errors import SwarmletStaticError


def kinds(source: str):
    """Helper: return list of token kinds (excluding EOF)."""
    return [t.kind for t in tokenize(source) if t.kind != "EOF"]


def test_basic_declaration():
    tokens = tokenize("let cell Tree = Fire")
    ks = [t.kind for t in tokens]
    assert ks == ["let", "cell", "IDENT", "=", "IDENT", "EOF"]
    assert tokens[2].value == "Tree"
    assert tokens[4].value == "Fire"
    # Check positions
    assert tokens[0].line == 1
    assert tokens[0].col == 1
    assert tokens[2].col == 10


def test_world_decl():
    tokens = tokenize("world 100 x 100 wrap")
    ks = [t.kind for t in tokens]
    # 'x' is tokenized as IDENT; parser will handle it as dimension separator
    assert ks == ["world", "NUMBER", "IDENT", "NUMBER", "wrap", "EOF"]
    assert tokens[1].value == 100.0
    assert tokens[2].value == "x"
    assert tokens[3].value == 100.0


def test_cell_states():
    ks = kinds("cell states Empty | Tree | Fire")
    assert ks == ["cell", "states", "IDENT", "|", "IDENT", "|", "IDENT"]


def test_numbers_int_and_float():
    tokens = tokenize("42 3.14 0 0.001")
    nums = [t.value for t in tokens if t.kind == "NUMBER"]
    assert nums == [42.0, 3.14, 0.0, 0.001]


def test_multi_char_operators():
    ks = kinds("== != <= >= ->")
    assert ks == ["==", "!=", "<=", ">=", "->"]


def test_single_char_operators():
    ks = kinds("+ - * / = < > | , ; : . ( ) { }")
    assert ks == ["+", "-", "*", "/", "=", "<", ">", "|", ",", ";", ":", ".", "(", ")", "{", "}"]


def test_keywords():
    source = "world cell states field agent let init param match with when if then else in"
    ks = kinds(source)
    expected = source.split()
    assert ks == expected


def test_action_keywords():
    source = "move stay set become spawn die kill seq"
    ks = kinds(source)
    assert ks == source.split()


def test_boolean_keywords():
    tokens = tokenize("true false")
    assert tokens[0].kind == "true"
    assert tokens[1].kind == "false"


def test_comments_skipped():
    tokens = tokenize("let # this is a comment\ncell")
    ks = [t.kind for t in tokens if t.kind != "EOF"]
    assert ks == ["let", "cell"]


def test_newlines_increment_line():
    tokens = tokenize("let\ncell\nTree")
    lines = [(t.kind, t.line) for t in tokens if t.kind != "EOF"]
    assert lines == [("let", 1), ("cell", 2), ("IDENT", 3)]


def test_unexpected_character():
    with pytest.raises(SwarmletStaticError) as exc_info:
        tokenize("let @bad")
    assert "unexpected character" in str(exc_info.value)
    assert exc_info.value.line == 1
    assert exc_info.value.col == 5


def test_agent_decl():
    ks = kinds("agent Ant { carrying = 0, heading = 0 }")
    assert ks == ["agent", "IDENT", "{", "IDENT", "=", "NUMBER", ",", "IDENT", "=", "NUMBER", "}"]


def test_complex_expression():
    # 'state' is a builtin function name, tokenized as IDENT (not a keyword)
    # 'count' is also a builtin, tokenized as IDENT
    ks = kinds("if count Tree > 2 then Fire else state")
    assert ks == ["if", "IDENT", "IDENT", ">", "NUMBER", "then", "IDENT", "else", "IDENT"]


def test_direction_keywords():
    ks = kinds("forward back left right")
    assert ks == ["forward", "back", "left", "right"]


def test_identifier_starting_with_x():
    """'x' alone after a number is the dimension separator, but 'xyz' is an identifier."""
    ks = kinds("xyz")
    assert ks == ["IDENT"]


def test_dot_access():
    ks = kinds("self.heading")
    assert ks == ["IDENT", ".", "IDENT"]


def test_match_expr():
    ks = kinds("match state with | Tree when random () < 0.01 -> Fire | _ -> state")
    assert "match" in ks
    assert "with" in ks
    assert "when" in ks
    assert "->" in ks


def test_unit_literal():
    ks = kinds("random ()")
    assert ks == ["IDENT", "(", ")"]


def test_eof_at_end():
    tokens = tokenize("")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"
