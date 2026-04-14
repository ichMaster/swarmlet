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
    # Check 0-arity world builtins (state, cell_state, self, etc.)
    result = _try_world_builtin(name, [], ctx, node.line)
    if result is not _SENTINEL:
        return result
    # Check builtins (0-arity only, e.g., STAY, forward)
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
    args = [eval_expr(a, ctx) for a in node.args]

    # Try world-context builtins first
    result = _try_world_builtin(name, args, ctx, node.line)
    if result is not _SENTINEL:
        return result

    if name in BUILTINS:
        spec = BUILTINS[name]
        bctx = ctx.builtin_ctx or EvalContext(rng=ctx.rng)
        return spec.func(bctx, *args)
    raise SwarmletRuntimeError(f"unknown function '{name}'", line=node.line)


_SENTINEL = object()


def _try_world_builtin(name: str, args: list, ctx: ExprContext, line: int) -> Any:
    """Try to evaluate a world-context builtin. Returns _SENTINEL if not handled."""
    w = ctx.world
    if w is None:
        return _SENTINEL

    xy = ctx.cell_xy
    if xy is None:
        return _SENTINEL
    cx, cy = xy

    # --- Cell context builtins (section 6.2) ---
    if name == "state":
        return w.get_state(cx, cy)
    if name == "field" and len(args) == 1:
        return w.get_field(cx, cy, str(args[0]))
    if name == "count" and len(args) >= 1:
        target = str(args[0])
        return _count_neighbors(w, cx, cy, target, "moore")
    if name == "count_in" and len(args) >= 2:
        target = str(args[0])
        return _count_neighbors(w, cx, cy, target, args[1])
    if name == "any" and len(args) >= 1:
        return _count_neighbors(w, cx, cy, str(args[0]), "moore") > 0
    if name == "sum_field" and len(args) >= 1:
        return _sum_field_neighbors(w, cx, cy, str(args[0]), "moore")
    if name == "sum_field_in" and len(args) >= 2:
        return _sum_field_neighbors(w, cx, cy, str(args[0]), args[1])
    if name == "mean_field" and len(args) >= 1:
        return _mean_field_neighbors(w, cx, cy, str(args[0]), "moore")
    if name == "max_field" and len(args) >= 1:
        return _extremum_field(w, cx, cy, str(args[0]), "moore", max)
    if name == "min_field" and len(args) >= 1:
        return _extremum_field(w, cx, cy, str(args[0]), "moore", min)
    if name == "laplacian" and len(args) >= 1:
        return _laplacian(w, cx, cy, str(args[0]))
    if name == "neighbor" and len(args) >= 2:
        return w.get_state(cx + int(args[0]), cy + int(args[1]))
    if name == "neighbor_field" and len(args) >= 3:
        return w.get_field(cx + int(args[0]), cy + int(args[1]), str(args[2]))
    if name == "distance_to" and len(args) >= 1:
        return _distance_to(w, cx, cy, str(args[0]))
    if name == "gradient_to" and len(args) >= 1:
        return _gradient_to(w, cx, cy, str(args[0]))

    # --- Agent context builtins (section 6.3) ---
    agent = ctx.agent
    if name == "self" and agent is not None:
        return agent
    if name == "cell_state" and agent is not None:
        return w.get_state(agent.x, agent.y)
    if name == "cell_field" and len(args) >= 1 and agent is not None:
        return w.get_field(agent.x, agent.y, str(args[0]))
    if name == "look" and len(args) >= 2 and agent is not None:
        return w.get_state(agent.x + int(args[0]), agent.y + int(args[1]))
    if name == "look_field" and len(args) >= 3 and agent is not None:
        return w.get_field(agent.x + int(args[0]), agent.y + int(args[1]), str(args[2]))
    if name == "agents_in_radius" and len(args) >= 1 and agent is not None:
        return _agents_in_radius(w, agent, int(args[0]))
    if name == "agents_of_type_in_radius" and len(args) >= 2 and agent is not None:
        return _agents_of_type_in_radius(w, agent, str(args[0]), int(args[1]))
    if name == "nearest_agent_dir" and len(args) >= 1 and agent is not None:
        return _nearest_agent_dir(w, agent, int(args[0]))
    if name == "nearest_agent_of_type_dir" and len(args) >= 2 and agent is not None:
        return _nearest_agent_of_type_dir(w, agent, str(args[0]), int(args[1]))
    if name == "argmax_neighbor" and len(args) >= 1 and agent is not None:
        return _argmax_neighbor(w, agent.x, agent.y, str(args[0]))
    if name == "argmin_neighbor" and len(args) >= 1 and agent is not None:
        return _argmin_neighbor(w, agent.x, agent.y, str(args[0]))
    if name == "mean_heading_in_radius" and len(args) >= 1 and agent is not None:
        return _mean_heading_in_radius(w, agent, int(args[0]))
    if name == "min_in_radius" and len(args) >= 2 and agent is not None:
        return _min_in_radius(w, agent.x, agent.y, str(args[0]), int(args[1]))
    if name == "max_in_radius" and len(args) >= 2 and agent is not None:
        return _max_in_radius(w, agent.x, agent.y, str(args[0]), int(args[1]))

    return _SENTINEL


# ---------------------------------------------------------------------------
# Neighborhood helpers
# ---------------------------------------------------------------------------

_MOORE_OFFSETS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
_NEUMANN_OFFSETS = [(0, -1), (-1, 0), (1, 0), (0, 1)]


def _get_offsets(neighborhood):
    if neighborhood == "moore":
        return _MOORE_OFFSETS
    if neighborhood == "neumann":
        return _NEUMANN_OFFSETS
    # radius N
    if isinstance(neighborhood, (int, float)):
        r = int(neighborhood)
        return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                if (dx, dy) != (0, 0) and max(abs(dx), abs(dy)) <= r]
    return _MOORE_OFFSETS


def _count_neighbors(w, cx, cy, target_state, neighborhood):
    count = 0
    for dx, dy in _get_offsets(neighborhood):
        s = w.get_state(cx + dx, cy + dy)
        if s == target_state:
            count += 1
    return count


def _sum_field_neighbors(w, cx, cy, fname, neighborhood):
    total = 0.0
    for dx, dy in _get_offsets(neighborhood):
        total += w.get_field(cx + dx, cy + dy, fname)
    return total


def _mean_field_neighbors(w, cx, cy, fname, neighborhood):
    offsets = _get_offsets(neighborhood)
    if not offsets:
        return 0.0
    return _sum_field_neighbors(w, cx, cy, fname, neighborhood) / len(offsets)


def _extremum_field(w, cx, cy, fname, neighborhood, fn):
    vals = [w.get_field(cx + dx, cy + dy, fname) for dx, dy in _get_offsets(neighborhood)]
    return fn(vals) if vals else 0.0


def _laplacian(w, cx, cy, fname):
    """9-point stencil: center -1, orthogonal 0.2, diagonal 0.05."""
    center = w.get_field(cx, cy, fname)
    result = -center
    for dx, dy in _NEUMANN_OFFSETS:
        result += 0.2 * w.get_field(cx + dx, cy + dy, fname)
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        result += 0.05 * w.get_field(cx + dx, cy + dy, fname)
    return result


def _distance_to(w, cx, cy, target_state):
    """Chebyshev distance to nearest cell in state, search radius 16."""
    for r in range(1, 17):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) == r:
                    s = w.get_state(cx + dx, cy + dy)
                    if s == target_state:
                        return r
    return -1


def _gradient_to(w, cx, cy, target_state):
    """Direction toward nearest cell in target state, radius 16."""
    from swarmlet.builtins import DIRECTIONS, STAY
    best_dist = 999
    best_dir = STAY
    for r in range(1, 17):
        if r > best_dist:
            break
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                s = w.get_state(cx + dx, cy + dy)
                if s == target_state:
                    dist = max(abs(dx), abs(dy))
                    if dist < best_dist:
                        best_dist = dist
                        # Quantize direction
                        import math
                        angle = math.atan2(dy, dx)
                        idx = round(angle / (math.pi / 4)) % 8
                        best_dir = idx
    return best_dir


# ---------------------------------------------------------------------------
# Agent context helpers
# ---------------------------------------------------------------------------

def _agents_in_radius(w, agent, radius):
    count = 0
    for other in w.agents:
        if other.id == agent.id or not other.alive:
            continue
        dx = abs(other.x - agent.x)
        dy = abs(other.y - agent.y)
        if w.topology == "wrap":
            dx = min(dx, w.width - dx)
            dy = min(dy, w.height - dy)
        if max(dx, dy) <= radius:
            count += 1
    return count


def _agents_of_type_in_radius(w, agent, target_type, radius):
    count = 0
    for other in w.agents:
        if other.id == agent.id or not other.alive:
            continue
        if other.agent_type != target_type:
            continue
        dx = abs(other.x - agent.x)
        dy = abs(other.y - agent.y)
        if w.topology == "wrap":
            dx = min(dx, w.width - dx)
            dy = min(dy, w.height - dy)
        if max(dx, dy) <= radius:
            count += 1
    return count


def _nearest_agent_dir(w, agent, radius):
    return _nearest_dir_impl(w, agent, radius, None)


def _nearest_agent_of_type_dir(w, agent, target_type, radius):
    return _nearest_dir_impl(w, agent, radius, target_type)


def _nearest_dir_impl(w, agent, radius, target_type):
    import math
    best_dist = 999
    best_dx, best_dy = 0, 0
    for other in w.agents:
        if other.id == agent.id or not other.alive:
            continue
        if target_type and other.agent_type != target_type:
            continue
        dx = other.x - agent.x
        dy = other.y - agent.y
        if w.topology == "wrap":
            if abs(dx) > w.width // 2:
                dx = dx - w.width if dx > 0 else dx + w.width
            if abs(dy) > w.height // 2:
                dy = dy - w.height if dy > 0 else dy + w.height
        dist = max(abs(dx), abs(dy))
        if dist <= radius and dist < best_dist:
            best_dist = dist
            best_dx, best_dy = dx, dy
    if best_dist == 999:
        return STAY
    angle = math.atan2(best_dy, best_dx)
    return round(angle / (math.pi / 4)) % 8


def _argmax_neighbor(w, cx, cy, fname):
    best_val = float("-inf")
    best_dir = STAY
    from swarmlet.builtins import DIRECTIONS
    for i, (dx, dy) in enumerate(DIRECTIONS):
        val = w.get_field(cx + dx, cy + dy, fname)
        if val > best_val:
            best_val = val
            best_dir = i
    return best_dir


def _argmin_neighbor(w, cx, cy, fname):
    best_val = float("inf")
    best_dir = STAY
    from swarmlet.builtins import DIRECTIONS
    for i, (dx, dy) in enumerate(DIRECTIONS):
        val = w.get_field(cx + dx, cy + dy, fname)
        if val < best_val:
            best_val = val
            best_dir = i
    return best_dir


def _mean_heading_in_radius(w, agent, radius):
    import math
    sx, sy = 0.0, 0.0
    count = 0
    for other in w.agents:
        if other.id == agent.id or not other.alive:
            continue
        if "heading" not in other.fields:
            continue
        dx = abs(other.x - agent.x)
        dy = abs(other.y - agent.y)
        if w.topology == "wrap":
            dx = min(dx, w.width - dx)
            dy = min(dy, w.height - dy)
        if max(dx, dy) <= radius:
            h = other.fields["heading"]
            angle = h * math.pi / 4
            sx += math.cos(angle)
            sy += math.sin(angle)
            count += 1
    if count == 0:
        return STAY
    avg_angle = math.atan2(sy, sx)
    return round(avg_angle / (math.pi / 4)) % 8


def _min_in_radius(w, cx, cy, fname, radius):
    best = float("inf")
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if (dx, dy) == (0, 0):
                continue
            if max(abs(dx), abs(dy)) <= radius:
                val = w.get_field(cx + dx, cy + dy, fname)
                if val < best:
                    best = val
    return best if best != float("inf") else 0.0


def _max_in_radius(w, cx, cy, fname, radius):
    best = float("-inf")
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if (dx, dy) == (0, 0):
                continue
            if max(abs(dx), abs(dy)) <= radius:
                val = w.get_field(cx + dx, cy + dy, fname)
                if val > best:
                    best = val
    return best if best != float("-inf") else 0.0


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
