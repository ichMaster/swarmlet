"""Expression and action evaluation against world snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from swarmlet import ast as A
from swarmlet.builtins import BUILTINS, EvalContext, STAY
from swarmlet.errors import SwarmletRuntimeError


# ---------------------------------------------------------------------------
# Value representation
# ---------------------------------------------------------------------------
# Values at runtime are plain Python objects: float, bool, str (state names),
# int (directions), None (void). We tag-check at operators.

def _type_tag(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "state"
    if v is None:
        return "void"
    return "unknown"


def _ensure_number(v: Any, line: int, ctx_msg: str = "") -> float:
    if isinstance(v, bool):
        raise SwarmletRuntimeError(f"expected number but got bool{ctx_msg}", line=line)
    if isinstance(v, (int, float)):
        return float(v)
    raise SwarmletRuntimeError(
        f"expected number but got {_type_tag(v)}{ctx_msg}", line=line
    )


def _ensure_bool(v: Any, line: int) -> bool:
    if isinstance(v, bool):
        return v
    raise SwarmletRuntimeError(
        f"expected bool but got {_type_tag(v)}", line=line
    )


# ---------------------------------------------------------------------------
# Expression evaluation context
# ---------------------------------------------------------------------------

@dataclass
class ExprContext:
    """Full evaluation context for expressions."""
    # Seeded RNG
    rng: np.random.Generator
    # Local variable bindings (let-bound)
    locals: Dict[str, Any] = field(default_factory=dict)
    # Declared parameters (from param declarations)
    params: Dict[str, Any] = field(default_factory=dict)
    # Declared cell states
    cell_states: set = field(default_factory=set)
    # Builtin eval context (for calling builtins)
    builtin_ctx: Optional[EvalContext] = None
    # Cell context (set during cell rule / init evaluation)
    cell_xy: Optional[Tuple[int, int]] = None
    # World reference (for builtins that need it, added in later phases)
    world: Any = None
    # Agent reference (for agent rules)
    agent: Any = None
    # Is this an init context?
    is_init: bool = False

    def child(self, **overrides) -> ExprContext:
        """Create a child context with overrides (e.g., new locals from let)."""
        new_locals = dict(self.locals)
        if "locals" in overrides:
            new_locals.update(overrides.pop("locals"))
        return ExprContext(
            rng=self.rng,
            locals=new_locals,
            params=self.params,
            cell_states=self.cell_states,
            builtin_ctx=overrides.get("builtin_ctx", self.builtin_ctx),
            cell_xy=overrides.get("cell_xy", self.cell_xy),
            world=overrides.get("world", self.world),
            agent=overrides.get("agent", self.agent),
            is_init=overrides.get("is_init", self.is_init),
        )


# ---------------------------------------------------------------------------
# Expression evaluator
# ---------------------------------------------------------------------------

def eval_expr(node: Any, ctx: ExprContext) -> Any:
    """Evaluate an expression AST node, returning a runtime value."""

    if isinstance(node, A.Num):
        return node.value

    if isinstance(node, A.Bool):
        return node.value

    if isinstance(node, A.Var):
        return _eval_var(node, ctx)

    if isinstance(node, A.BinOp):
        return _eval_binop(node, ctx)

    if isinstance(node, A.UnOp):
        return _eval_unop(node, ctx)

    if isinstance(node, A.Call):
        return _eval_call(node, ctx)

    if isinstance(node, A.Dot):
        return _eval_dot(node, ctx)

    if isinstance(node, A.If):
        cond = eval_expr(node.cond, ctx)
        cond_val = _ensure_bool(cond, node.line)
        if cond_val:
            return eval_expr(node.then_expr, ctx)
        return eval_expr(node.else_expr, ctx)

    if isinstance(node, A.Let):
        val = eval_expr(node.value, ctx)
        child_ctx = ctx.child(locals={node.name: val})
        return eval_expr(node.body, child_ctx)

    if isinstance(node, A.Match):
        return _eval_match(node, ctx)

    raise SwarmletRuntimeError(f"unknown expression node: {type(node).__name__}", line=getattr(node, "line", 0))


def _eval_var(node: A.Var, ctx: ExprContext) -> Any:
    name = node.name
    # Check locals first
    if name in ctx.locals:
        return ctx.locals[name]
    # Check params
    if name in ctx.params:
        return ctx.params[name]
    # Check if it's a cell state name
    if name in ctx.cell_states:
        return name  # state value
    # Check builtins (0-arity only, e.g., STAY, state)
    if name in BUILTINS:
        spec = BUILTINS[name]
        if spec.arity == 0:
            bctx = ctx.builtin_ctx or EvalContext(rng=ctx.rng)
            return spec.func(bctx)
    # Could be an unresolved reference — return as state-like string
    return name


def _eval_binop(node: A.BinOp, ctx: ExprContext) -> Any:
    op = node.op
    left = eval_expr(node.left, ctx)
    right = eval_expr(node.right, ctx)

    if op == "and":
        return _ensure_bool(left, node.line) and _ensure_bool(right, node.line)
    if op == "or":
        return _ensure_bool(left, node.line) or _ensure_bool(right, node.line)

    if op in ("==", "!="):
        if op == "==":
            return left == right
        return left != right

    if op in ("<", "<=", ">", ">="):
        l = _ensure_number(left, node.line, f" in '{op}'")
        r = _ensure_number(right, node.line, f" in '{op}'")
        if op == "<": return l < r
        if op == "<=": return l <= r
        if op == ">": return l > r
        return l >= r

    if op in ("+", "-", "*", "/", "mod"):
        l = _ensure_number(left, node.line)
        r = _ensure_number(right, node.line)
        if op == "+": return l + r
        if op == "-": return l - r
        if op == "*": return l * r
        if op == "/":
            if r == 0:
                raise SwarmletRuntimeError("division by zero", line=node.line)
            return l / r
        if op == "mod":
            return float(int(l) % int(r))

    raise SwarmletRuntimeError(f"unknown binary operator '{op}'", line=node.line)


def _eval_unop(node: A.UnOp, ctx: ExprContext) -> Any:
    operand = eval_expr(node.operand, ctx)
    if node.op == "-":
        return -_ensure_number(operand, node.line)
    if node.op == "not":
        return not _ensure_bool(operand, node.line)
    raise SwarmletRuntimeError(f"unknown unary operator '{node.op}'", line=node.line)


def _eval_call(node: A.Call, ctx: ExprContext) -> Any:
    name = node.func
    if name in BUILTINS:
        spec = BUILTINS[name]
        bctx = ctx.builtin_ctx or EvalContext(rng=ctx.rng)
        args = [eval_expr(a, ctx) for a in node.args]
        return spec.func(bctx, *args)
    # Could be a user-defined function or unresolved — error
    raise SwarmletRuntimeError(f"unknown function '{name}'", line=node.line)


def _eval_dot(node: A.Dot, ctx: ExprContext) -> Any:
    obj = eval_expr(node.expr, ctx)
    # Agent field access: self.field_name
    if ctx.agent is not None and hasattr(ctx.agent, "fields"):
        if node.field_name in ctx.agent.fields:
            return ctx.agent.fields[node.field_name]
    # Dict-like access for agent records
    if isinstance(obj, dict) and node.field_name in obj:
        return obj[node.field_name]
    if hasattr(obj, node.field_name):
        return getattr(obj, node.field_name)
    raise SwarmletRuntimeError(
        f"cannot access field '{node.field_name}'", line=node.line
    )


def _eval_match(node: A.Match, ctx: ExprContext) -> Any:
    subject = eval_expr(node.subject, ctx)
    for case in node.cases:
        if _match_case(case, subject, ctx):
            return eval_expr(case.body, ctx)
    raise SwarmletRuntimeError("non-exhaustive match", line=node.line)


def _match_case(case: A.MatchCase, subject: Any, ctx: ExprContext) -> bool:
    """Check if any pattern in the case matches, and guard passes."""
    matched = any(_match_pattern(p, subject) for p in case.patterns)
    if not matched:
        return False
    if case.guard is not None:
        guard_val = eval_expr(case.guard, ctx)
        return _ensure_bool(guard_val, case.line)
    return True


def _match_pattern(pattern: A.Pattern, subject: Any) -> bool:
    if pattern.kind == "wildcard":
        return True
    if pattern.kind == "ident":
        # Match state names
        return subject == pattern.value
    if pattern.kind == "number":
        return isinstance(subject, (int, float)) and not isinstance(subject, bool) and subject == pattern.value
    if pattern.kind == "bool":
        return isinstance(subject, bool) and subject == pattern.value
    return False
