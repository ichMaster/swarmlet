"""Built-in function registry and direction encoding for Swarmlet."""

from __future__ import annotations

from typing import FrozenSet, List, Tuple


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
