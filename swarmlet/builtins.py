"""Built-in function registry and direction encoding for Swarmlet."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Direction encoding (Appendix B of SPEC.md)
# ---------------------------------------------------------------------------
# Clockwise from East, y-axis points down.

STAY = -1

DIRECTIONS: List[Tuple[int, int]] = [
    (+1,  0),   # 0 = E
    (+1, +1),   # 1 = SE
    ( 0, +1),   # 2 = S
    (-1, +1),   # 3 = SW
    (-1,  0),   # 4 = W
    (-1, -1),   # 5 = NW
    ( 0, -1),   # 6 = N
    (+1, -1),   # 7 = NE
]


def dir_offset(d: int) -> Tuple[int, int]:
    """Return (dx, dy) for direction d. STAY returns (0, 0)."""
    if d == STAY:
        return (0, 0)
    return DIRECTIONS[d % 8]


def rotate_dir(d: int, steps: int) -> int:
    """Rotate direction d by steps (each step = 45 degrees clockwise)."""
    if d == STAY:
        return STAY
    return (d + steps) % 8


# ---------------------------------------------------------------------------
# Built-in name sets (SPEC.md section 6)
# ---------------------------------------------------------------------------

# Section 6.1 — Random
_RANDOM_BUILTINS = frozenset({"random", "random_int", "random_dir"})

# Section 6.2 — Cell context
_CELL_CONTEXT_BUILTINS = frozenset({
    "state", "field",
    "x", "y",
    "count", "count_in",
    "any",
    "sum_field", "sum_field_in",
    "mean_field", "max_field", "min_field",
    "laplacian",
    "neighbor", "neighbor_field",
    "distance_to", "gradient_to",
})

# Section 6.3 — Agent context
_AGENT_CONTEXT_BUILTINS = frozenset({
    "self",
    "cell_state", "cell_field",
    "look", "look_field",
    "argmax_neighbor", "argmin_neighbor",
    "agents_in_radius", "agents_of_type_in_radius",
    "nearest_agent_dir", "nearest_agent_of_type_dir",
    "mean_heading_in_radius",
    "min_in_radius", "max_in_radius",
})

# Section 6.4 — Math
_MATH_BUILTINS = frozenset({
    "abs", "min", "max", "sqrt", "exp", "floor", "mod", "clamp",
})

# Section 6.5 — Direction helpers
_DIRECTION_BUILTINS = frozenset({
    "forward", "back", "left", "right",
    "dir", "STAY",
})

# All built-in names
BUILTIN_NAMES: FrozenSet[str] = (
    _RANDOM_BUILTINS
    | _CELL_CONTEXT_BUILTINS
    | _AGENT_CONTEXT_BUILTINS
    | _MATH_BUILTINS
    | _DIRECTION_BUILTINS
)

# Context-specific subsets for the static analyzer
CELL_CONTEXT_ONLY: FrozenSet[str] = _CELL_CONTEXT_BUILTINS - {"state", "field"}
# state and field can appear in both contexts (cell_state/cell_field in agent context are separate names)

AGENT_CONTEXT_ONLY: FrozenSet[str] = _AGENT_CONTEXT_BUILTINS

# Builtins that require the agent to have a heading field
HEADING_REQUIRED: FrozenSet[str] = frozenset({"forward", "back", "left", "right"})

# Init-context only builtins (x, y are only valid in init context)
INIT_ONLY: FrozenSet[str] = frozenset({"x", "y"})


# ---------------------------------------------------------------------------
# Evaluation context (passed to built-in implementations)
# ---------------------------------------------------------------------------

@dataclass
class EvalContext:
    """Runtime context passed to built-in functions during evaluation."""
    rng: np.random.Generator
    # Agent context (set when evaluating agent rules)
    agent_heading: Optional[int] = None
    # Additional fields will be added in later phases (world, cell position, etc.)


# ---------------------------------------------------------------------------
# BuiltinSpec and registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BuiltinSpec:
    """Specification for a built-in function."""
    name: str
    arity: int  # -1 for variadic / context-dependent
    func: Callable  # (ctx, *args) -> value


def _make_builtins() -> Dict[str, BuiltinSpec]:
    """Build the BUILTINS registry with all implemented functions."""
    registry: Dict[str, BuiltinSpec] = {}

    def reg(name: str, arity: int, func: Callable):
        registry[name] = BuiltinSpec(name=name, arity=arity, func=func)

    # --- Random (6.1) ---
    reg("random", 0, lambda ctx: ctx.rng.random())
    reg("random_int", 1, lambda ctx, n: int(ctx.rng.integers(0, int(n))))
    reg("random_dir", 0, lambda ctx: int(ctx.rng.integers(0, 8)))

    # --- Math (6.4) ---
    reg("abs", 1, lambda ctx, x: abs(x))
    reg("min", 2, lambda ctx, a, b: min(a, b))
    reg("max", 2, lambda ctx, a, b: max(a, b))
    reg("sqrt", 1, lambda ctx, x: math.sqrt(x))
    reg("exp", 1, lambda ctx, x: math.exp(x))
    reg("floor", 1, lambda ctx, x: float(math.floor(x)))
    reg("mod", 2, lambda ctx, a, b: float(int(a) % int(b)))
    reg("clamp", 3, lambda ctx, x, lo, hi: max(lo, min(x, hi)))

    # --- Direction helpers (6.5) ---
    reg("dir", 2, _builtin_dir)
    reg("STAY", 0, lambda ctx: STAY)
    reg("forward", 0, lambda ctx: _relative_dir(ctx, 0))
    reg("back", 0, lambda ctx: _relative_dir(ctx, 4))
    reg("left", 0, lambda ctx: _relative_dir(ctx, 6))
    reg("right", 0, lambda ctx: _relative_dir(ctx, 2))

    return registry


def _builtin_dir(ctx: EvalContext, dx: float, dy: float) -> int:
    """Construct absolute direction from (dx, dy) offset."""
    idx = int(dx), int(dy)
    for i, d in enumerate(DIRECTIONS):
        if d == idx:
            return i
    return STAY


def _relative_dir(ctx: EvalContext, offset: int) -> int:
    """Compute direction relative to agent heading."""
    if ctx.agent_heading is None:
        from swarmlet.errors import SwarmletRuntimeError
        raise SwarmletRuntimeError("direction helper requires agent with heading field")
    return rotate_dir(ctx.agent_heading, offset)


BUILTINS: Dict[str, BuiltinSpec] = _make_builtins()
