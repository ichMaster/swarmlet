"""Lexer — tokenizes Swarmlet source into a list of Tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Token:
    """A single lexical token with source position information."""
    kind: str
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"
