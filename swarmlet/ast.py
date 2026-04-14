"""AST node definitions — frozen dataclasses for all Swarmlet constructs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Top-level program
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Program:
    """Root node: a list of declarations."""
    decls: List[Any]
    line: int = 0


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorldDecl:
    """world W x H [wrap|bounded]"""
    width: int
    height: int
    topology: str  # "wrap" or "bounded"
    line: int = 0

    def __repr__(self) -> str:
        return f"WorldDecl({self.width}x{self.height}, {self.topology}, line={self.line})"


@dataclass(frozen=True)
class StatesDecl:
    """cell states S1 | S2 | ..."""
    names: List[str]
    line: int = 0

    def __repr__(self) -> str:
        return f"StatesDecl({' | '.join(self.names)}, line={self.line})"


@dataclass(frozen=True)
class FieldDecl:
    """field name = const_expr"""
    name: str
    default: Any  # a constant expression (number or bool)
    line: int = 0

    def __repr__(self) -> str:
        return f"FieldDecl({self.name}={self.default}, line={self.line})"


@dataclass(frozen=True)
class ParamDecl:
    """param name = const_expr"""
    name: str
    value: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"ParamDecl({self.name}={self.value}, line={self.line})"


@dataclass(frozen=True)
class AgentDecl:
    """agent Name { field1 = val, field2 = val }"""
    name: str
    fields: List[tuple]  # list of (name, default_value) pairs
    line: int = 0

    def __repr__(self) -> str:
        fs = ", ".join(f"{n}={v}" for n, v in self.fields)
        return f"AgentDecl({self.name} {{{fs}}}, line={self.line})"


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Num:
    """Numeric literal."""
    value: float
    line: int = 0

    def __repr__(self) -> str:
        return f"Num({self.value})"


@dataclass(frozen=True)
class Bool:
    """Boolean literal."""
    value: bool
    line: int = 0

    def __repr__(self) -> str:
        return f"Bool({self.value})"


@dataclass(frozen=True)
class Var:
    """Variable or state-name reference."""
    name: str
    line: int = 0

    def __repr__(self) -> str:
        return f"Var({self.name})"


@dataclass(frozen=True)
class BinOp:
    """Binary operation: left op right."""
    op: str
    left: Any
    right: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"BinOp({self.op}, {self.left}, {self.right})"


@dataclass(frozen=True)
class UnOp:
    """Unary operation: op operand."""
    op: str
    operand: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"UnOp({self.op}, {self.operand})"


@dataclass(frozen=True)
class Call:
    """Function application: func arg1 arg2 ..."""
    func: str
    args: List[Any]
    line: int = 0

    def __repr__(self) -> str:
        args_str = ", ".join(repr(a) for a in self.args)
        return f"Call({self.func}, [{args_str}])"


@dataclass(frozen=True)
class Dot:
    """Field access: expr.field"""
    expr: Any
    field_name: str
    line: int = 0

    def __repr__(self) -> str:
        return f"Dot({self.expr}, {self.field_name})"


@dataclass(frozen=True)
class If:
    """if cond then then_expr else else_expr"""
    cond: Any
    then_expr: Any
    else_expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"If({self.cond}, {self.then_expr}, {self.else_expr})"


@dataclass(frozen=True)
class Let:
    """let name = value in body"""
    name: str
    value: Any
    body: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"Let({self.name}, {self.value}, {self.body})"


@dataclass(frozen=True)
class Pattern:
    """A single pattern in a match arm."""
    kind: str  # "wildcard", "ident", "number", "bool"
    value: Any  # None for wildcard, str for ident, float for number, bool for bool
    line: int = 0

    def __repr__(self) -> str:
        if self.kind == "wildcard":
            return "Pattern(_)"
        return f"Pattern({self.kind}, {self.value!r})"


@dataclass(frozen=True)
class MatchCase:
    """A single case in a match expression: | patterns when guard -> body"""
    patterns: List[Pattern]  # or-patterns
    guard: Optional[Any]  # optional when-guard expression
    body: Any
    line: int = 0

    def __repr__(self) -> str:
        pats = " | ".join(repr(p) for p in self.patterns)
        g = f" when {self.guard}" if self.guard else ""
        return f"MatchCase({pats}{g} -> {self.body})"


@dataclass(frozen=True)
class Match:
    """match expr with | case1 | case2 ..."""
    subject: Any
    cases: List[MatchCase]
    line: int = 0

    def __repr__(self) -> str:
        return f"Match({self.subject}, [{len(self.cases)} cases])"


# ---------------------------------------------------------------------------
# Cell rule bodies
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CellBecome:
    """become expr — set cell's next state."""
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"CellBecome({self.expr})"


@dataclass(frozen=True)
class CellSet:
    """set field = expr — set a cell field."""
    field_name: str
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"CellSet({self.field_name}, {self.expr})"


@dataclass(frozen=True)
class CellSeq:
    """seq { stmt1; stmt2; ... } — sequence of cell statements."""
    stmts: List[Any]  # list of CellBecome / CellSet
    line: int = 0

    def __repr__(self) -> str:
        return f"CellSeq([{len(self.stmts)} stmts])"


@dataclass(frozen=True)
class CellLetSeq:
    """let name = expr in seq { ... } — a let binding wrapping a cell seq."""
    name: str
    value: Any
    body: Any  # CellSeq or nested CellLetSeq
    line: int = 0

    def __repr__(self) -> str:
        return f"CellLetSeq({self.name}, {self.value}, {self.body})"


@dataclass(frozen=True)
class CellExpr:
    """A plain expression used as a cell body (returns new state)."""
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"CellExpr({self.expr})"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CellRule:
    """let cell pattern = body"""
    pattern: str  # state name or "_"
    body: Any  # CellExpr, CellSeq, If, Match
    line: int = 0

    def __repr__(self) -> str:
        return f"CellRule({self.pattern}, {self.body})"


@dataclass(frozen=True)
class AgentRule:
    """let agent TypeName = action"""
    agent_type: str
    body: Any  # an action node
    line: int = 0

    def __repr__(self) -> str:
        return f"AgentRule({self.agent_type}, {self.body})"


# ---------------------------------------------------------------------------
# Actions (agent rules only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AStay:
    """stay action."""
    line: int = 0

    def __repr__(self) -> str:
        return "AStay()"


@dataclass(frozen=True)
class ADie:
    """die action."""
    line: int = 0

    def __repr__(self) -> str:
        return "ADie()"


@dataclass(frozen=True)
class AMove:
    """move expr — move in a direction."""
    direction: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"AMove({self.direction})"


@dataclass(frozen=True)
class ASet:
    """set field = expr — set agent or cell field."""
    field_name: str
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"ASet({self.field_name}, {self.expr})"


@dataclass(frozen=True)
class ALetIn:
    """let name = expr in action — bind a value for use in an action."""
    name: str
    value: Any
    body: Any  # an action node
    line: int = 0

    def __repr__(self) -> str:
        return f"ALetIn({self.name}, {self.value}, {self.body})"


@dataclass(frozen=True)
class ASpawn:
    """spawn AgentType — create a new agent."""
    agent_type: str
    line: int = 0

    def __repr__(self) -> str:
        return f"ASpawn({self.agent_type})"


@dataclass(frozen=True)
class AKill:
    """kill AgentType — kill one co-located agent of given type."""
    agent_type: str
    line: int = 0

    def __repr__(self) -> str:
        return f"AKill({self.agent_type})"


@dataclass(frozen=True)
class ASeq:
    """seq { action1; action2; ... } — sequence of actions."""
    actions: List[Any]
    line: int = 0

    def __repr__(self) -> str:
        return f"ASeq([{len(self.actions)} actions])"


@dataclass(frozen=True)
class AIf:
    """if expr then action else action — conditional action."""
    cond: Any
    then_action: Any
    else_action: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"AIf({self.cond}, {self.then_action}, {self.else_action})"


@dataclass(frozen=True)
class AMatch:
    """match expr with | case1 | case2 ... — pattern-match action."""
    subject: Any
    cases: List[Any]  # list of ActionCase
    line: int = 0

    def __repr__(self) -> str:
        return f"AMatch({self.subject}, [{len(self.cases)} cases])"


@dataclass(frozen=True)
class ActionCase:
    """A single case in an action match: | patterns when guard -> action"""
    patterns: List[Pattern]
    guard: Optional[Any]
    body: Any  # an action node
    line: int = 0

    def __repr__(self) -> str:
        pats = " | ".join(repr(p) for p in self.patterns)
        g = f" when {self.guard}" if self.guard else ""
        return f"ActionCase({pats}{g} -> {self.body})"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InitCell:
    """init cell = expr"""
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"InitCell({self.expr})"


@dataclass(frozen=True)
class InitField:
    """init field name = expr"""
    field_name: str
    expr: Any
    line: int = 0

    def __repr__(self) -> str:
        return f"InitField({self.field_name}, {self.expr})"


@dataclass(frozen=True)
class InitAgent:
    """init agent TypeName count"""
    agent_type: str
    count: int
    line: int = 0

    def __repr__(self) -> str:
        return f"InitAgent({self.agent_type}, {self.count})"
