"""Lexer — tokenizes Swarmlet source into a list of Tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from swarmlet.errors import SwarmletStaticError


@dataclass(frozen=True)
class Token:
    """A single lexical token with source position information."""
    kind: str
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"


KEYWORDS = frozenset({
    "world", "cell", "states", "field", "agent", "let", "init", "param",
    "match", "with", "when",
    "if", "then", "else", "in",
    "move", "stay", "set", "become", "spawn", "die", "kill", "seq",
    "true", "false", "wrap", "bounded",
    "and", "or", "not", "mod",
    "moore", "neumann", "radius",
    "forward", "back", "left", "right",
    "_",
})

# Two-character operators (checked before single-char)
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "->"}

# Single-character operators/punctuation
SINGLE_CHAR_OPS = frozenset("+-*/=<>|,;:.(){}")


def tokenize(source: str) -> List[Token]:
    """Tokenize Swarmlet source code into a list of Tokens.

    Appends an EOF token at the end. Raises SwarmletStaticError on
    unexpected characters.
    """
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    length = len(source)

    while i < length:
        ch = source[i]

        # Newline
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        # Whitespace (non-newline)
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Comment
        if ch == "#":
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Number
        if ch.isdigit():
            start = i
            start_col = col
            while i < length and source[i].isdigit():
                i += 1
                col += 1
            if i < length and source[i] == "." and (i + 1 < length and source[i + 1].isdigit()):
                i += 1
                col += 1
                while i < length and source[i].isdigit():
                    i += 1
                    col += 1
            text = source[start:i]
            value = float(text) if "." in text else float(int(text))
            tokens.append(Token("NUMBER", value, line, start_col))
            continue

        # Identifier or keyword
        if ch.isalpha() or ch == "_":
            start = i
            start_col = col
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
                col += 1
            text = source[start:i]
            if text in KEYWORDS:
                tokens.append(Token(text, text, line, start_col))
            else:
                tokens.append(Token("IDENT", text, line, start_col))
            continue

        # Two-character operators
        if i + 1 < length:
            two = source[i:i + 2]
            if two in TWO_CHAR_OPS:
                tokens.append(Token(two, two, line, col))
                i += 2
                col += 2
                continue

        # Single-character operators
        if ch in SINGLE_CHAR_OPS:
            tokens.append(Token(ch, ch, line, col))
            i += 1
            col += 1
            continue

        # Unexpected character
        raise SwarmletStaticError(line, col, f"unexpected character {ch!r}")

    tokens.append(Token("EOF", None, line, col))
    return tokens
