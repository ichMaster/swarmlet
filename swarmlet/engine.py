"""World class — 2D grid state, tick logic, intent application."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from swarmlet import ast as A
from swarmlet.builtins import EvalContext, STAY, dir_offset
from swarmlet.eval import eval_expr, ExprContext
from swarmlet.errors import SwarmletRuntimeError


# ---------------------------------------------------------------------------
# Agent record
# ---------------------------------------------------------------------------

@dataclass
class AgentRecord:
    """Runtime representation of a single agent."""
    id: int
    agent_type: str
    x: int
    y: int
    fields: Dict[str, float]
    alive: bool = True

    def copy(self) -> AgentRecord:
        return AgentRecord(
            id=self.id, agent_type=self.agent_type,
            x=self.x, y=self.y,
            fields=dict(self.fields), alive=self.alive,
        )


# ---------------------------------------------------------------------------
# Intent record (for agent phase)
# ---------------------------------------------------------------------------

@dataclass
class Intent:
    """Accumulates actions for a single agent during one tick."""
    agent_id: int
    move_dir: int = STAY  # -1 = no movement
    agent_field_writes: Dict[str, float] = field(default_factory=dict)
    cell_field_deposits: List[Tuple[str, float]] = field(default_factory=list)
    spawn_types: List[str] = field(default_factory=list)
    kill_targets: List[str] = field(default_factory=list)
    die: bool = False


# ---------------------------------------------------------------------------
# World class
# ---------------------------------------------------------------------------

class World:
    """Swarmlet world — holds grid state, agents, and runs simulation."""

    def __init__(self, program: A.Program, seed: int = 0, params: Optional[Dict[str, float]] = None):
        self.program = program
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.tick_count = 0

        # Extract declarations
        self._extract_decls(params)

        # Initialize grid
        self.width: int = self._world_width
        self.height: int = self._world_height
        self.topology: str = self._world_topology

        # State array: stores state name index per cell
        self.state_names: List[str] = list(self._cell_states_list)
        self.state_to_idx: Dict[str, int] = {s: i for i, s in enumerate(self.state_names)}
        self.states = np.zeros((self.height, self.width), dtype=np.int32)

        # Field arrays
        self.field_names: List[str] = list(self._field_defaults.keys())
        self.fields: Dict[str, np.ndarray] = {}
        for fname, default in self._field_defaults.items():
            self.fields[fname] = np.full((self.height, self.width), default, dtype=np.float64)

        # Agents
        self.agents: List[AgentRecord] = []
        self._next_agent_id = 0

        # Run initialization
        self._run_init()

    def _extract_decls(self, param_overrides: Optional[Dict[str, float]]):
        """Extract declarations from the program AST."""
        self._world_width = 10
        self._world_height = 10
        self._world_topology = "wrap"
        self._cell_states_list: List[str] = []
        self._field_defaults: Dict[str, float] = {}
        self._agent_decls: Dict[str, Dict[str, float]] = {}
        self._params: Dict[str, float] = {}
        self._cell_rules: Dict[str, Any] = {}  # pattern -> body
        self._agent_rules: Dict[str, Any] = {}  # type -> body
        self._init_cell: Optional[Any] = None
        self._init_fields: Dict[str, Any] = {}
        self._init_agents: List[Tuple[str, int]] = []

        for decl in self.program.decls:
            if isinstance(decl, A.WorldDecl):
                self._world_width = decl.width
                self._world_height = decl.height
                self._world_topology = decl.topology
            elif isinstance(decl, A.StatesDecl):
                self._cell_states_list = list(decl.names)
            elif isinstance(decl, A.FieldDecl):
                self._field_defaults[decl.name] = float(decl.default)
            elif isinstance(decl, A.ParamDecl):
                self._params[decl.name] = float(decl.value)
            elif isinstance(decl, A.AgentDecl):
                self._agent_decls[decl.name] = {n: float(v) for n, v in decl.fields}
            elif isinstance(decl, A.CellRule):
                self._cell_rules[decl.pattern] = decl.body
            elif isinstance(decl, A.AgentRule):
                self._agent_rules[decl.agent_type] = decl.body
            elif isinstance(decl, A.InitCell):
                self._init_cell = decl.expr
            elif isinstance(decl, A.InitField):
                self._init_fields[decl.field_name] = decl.expr
            elif isinstance(decl, A.InitAgent):
                self._init_agents.append((decl.agent_type, decl.count))

        # Apply param overrides
        if param_overrides:
            for k, v in param_overrides.items():
                self._params[k] = v

    def _run_init(self):
        """Run initialization expressions."""
        # Init cells
        if self._init_cell is not None:
            for y in range(self.height):
                for x in range(self.width):
                    ctx = self._make_init_ctx(x, y)
                    val = eval_expr(self._init_cell, ctx)
                    if isinstance(val, str) and val in self.state_to_idx:
                        self.states[y, x] = self.state_to_idx[val]

        # Init fields
        for fname, expr in self._init_fields.items():
            for y in range(self.height):
                for x in range(self.width):
                    ctx = self._make_init_ctx(x, y)
                    val = eval_expr(expr, ctx)
                    self.fields[fname][y, x] = float(val)

        # Init agents
        for agent_type, count in self._init_agents:
            for _ in range(count):
                ax = int(self.rng.integers(0, self.width))
                ay = int(self.rng.integers(0, self.height))
                default_fields = dict(self._agent_decls.get(agent_type, {}))
                agent = AgentRecord(
                    id=self._next_agent_id,
                    agent_type=agent_type,
                    x=ax, y=ay,
                    fields=default_fields,
                )
                self._next_agent_id += 1
                self.agents.append(agent)

    def _make_init_ctx(self, x: int, y: int) -> ExprContext:
        return ExprContext(
            rng=self.rng,
            params=self._params,
            cell_states=set(self.state_names),
            builtin_ctx=EvalContext(rng=self.rng),
            cell_xy=(x, y),
            world=self,
            is_init=True,
            locals={"x": float(x), "y": float(y)},
        )

    def _make_cell_ctx(self, x: int, y: int) -> ExprContext:
        return ExprContext(
            rng=self.rng,
            params=self._params,
            cell_states=set(self.state_names),
            builtin_ctx=EvalContext(rng=self.rng),
            cell_xy=(x, y),
            world=self,
        )

    def _make_agent_ctx(self, agent: AgentRecord) -> ExprContext:
        heading = agent.fields.get("heading")
        return ExprContext(
            rng=self.rng,
            params=self._params,
            cell_states=set(self.state_names),
            builtin_ctx=EvalContext(
                rng=self.rng,
                agent_heading=int(heading) if heading is not None else None,
            ),
            cell_xy=(agent.x, agent.y),
            world=self,
            agent=agent,
        )

    # ----- Grid helpers -----

    def get_state(self, x: int, y: int) -> Optional[str]:
        """Get cell state name at (x, y), respecting topology."""
        nx, ny = self._wrap(x, y)
        if nx is None:
            return None  # bounded, out of range
        return self.state_names[self.states[ny, nx]]

    def get_field(self, x: int, y: int, fname: str) -> float:
        nx, ny = self._wrap(x, y)
        if nx is None:
            return 0.0
        return float(self.fields[fname][ny, nx])

    def _wrap(self, x: int, y: int) -> Tuple[Optional[int], Optional[int]]:
        if self.topology == "wrap":
            return x % self.width, y % self.height
        if 0 <= x < self.width and 0 <= y < self.height:
            return x, y
        return None, None

    def _spawn_agent(self, agent_type: str, x: int, y: int) -> AgentRecord:
        default_fields = dict(self._agent_decls.get(agent_type, {}))
        agent = AgentRecord(
            id=self._next_agent_id,
            agent_type=agent_type,
            x=x, y=y,
            fields=default_fields,
        )
        self._next_agent_id += 1
        return agent

    # ----- Tick -----

    def step(self, n: int = 1):
        """Run n ticks."""
        for _ in range(n):
            self._cell_phase()
            self._agent_phase()
            self.tick_count += 1

    def _cell_phase(self):
        """Evaluate cell rules for every cell, writing into fresh arrays."""
        next_states = self.states.copy()
        next_fields = {fn: arr.copy() for fn, arr in self.fields.items()}

        for y in range(self.height):
            for x in range(self.width):
                state_name = self.state_names[self.states[y, x]]
                body = self._cell_rules.get(state_name) or self._cell_rules.get("_")
                if body is None:
                    continue

                ctx = self._make_cell_ctx(x, y)

                if isinstance(body, A.CellExpr):
                    result = eval_expr(body.expr, ctx)
                    if isinstance(result, str) and result in self.state_to_idx:
                        next_states[y, x] = self.state_to_idx[result]
                elif isinstance(body, A.CellSeq):
                    new_state = state_name
                    new_fields = {}
                    for stmt in body.stmts:
                        if isinstance(stmt, A.CellBecome):
                            result = eval_expr(stmt.expr, ctx)
                            if isinstance(result, str):
                                new_state = result
                        elif isinstance(stmt, A.CellSet):
                            val = eval_expr(stmt.expr, ctx)
                            new_fields[stmt.field_name] = float(val)
                    if new_state in self.state_to_idx:
                        next_states[y, x] = self.state_to_idx[new_state]
                    for fn, val in new_fields.items():
                        if fn in next_fields:
                            next_fields[fn][y, x] = val
                else:
                    # Body is a raw expression (match, if, etc.)
                    result = eval_expr(body, ctx)
                    if isinstance(result, str) and result in self.state_to_idx:
                        next_states[y, x] = self.state_to_idx[result]

        self.states = next_states
        self.fields = next_fields

    def _agent_phase(self):
        """Evaluate agent rules and apply intents."""
        if not self.agents:
            return

        # Shuffle agents deterministically
        indices = list(range(len(self.agents)))
        self.rng.shuffle(indices)

        intents: List[Tuple[AgentRecord, Intent]] = []

        for idx in indices:
            agent = self.agents[idx]
            if not agent.alive:
                continue
            body = self._agent_rules.get(agent.agent_type)
            if body is None:
                continue

            intent = Intent(agent_id=agent.id)
            # Create a copy-on-write agent view for within-action visibility
            agent_view = agent.copy()
            ctx = self._make_agent_ctx(agent_view)

            self._eval_action(body, ctx, intent, agent_view)
            intents.append((agent, intent))

        # Apply intents in order (SPEC section 2.3)
        self._apply_intents(intents)

    def _eval_action(self, node: Any, ctx: ExprContext, intent: Intent, agent_view: AgentRecord):
        """Evaluate an action AST node, mutating the intent."""
        if isinstance(node, A.AStay):
            pass
        elif isinstance(node, A.ADie):
            intent.die = True
        elif isinstance(node, A.AMove):
            d = eval_expr(node.direction, ctx)
            if isinstance(d, (int, float)):
                intent.move_dir = int(d)
        elif isinstance(node, A.ASet):
            val = eval_expr(node.expr, ctx)
            target = getattr(node, "_target", None)
            if target == "agent":
                intent.agent_field_writes[node.field_name] = float(val)
                # Within-action visibility: update the agent view
                agent_view.fields[node.field_name] = float(val)
                ctx.agent = agent_view
                # Update builtin context heading if needed
                if node.field_name == "heading" and ctx.builtin_ctx:
                    ctx.builtin_ctx.agent_heading = int(val)
            elif target == "cell":
                intent.cell_field_deposits.append((node.field_name, float(val)))
            else:
                # Try to figure out from context
                if node.field_name in self._field_defaults:
                    intent.cell_field_deposits.append((node.field_name, float(val)))
                elif ctx.agent and node.field_name in ctx.agent.fields:
                    intent.agent_field_writes[node.field_name] = float(val)
                    agent_view.fields[node.field_name] = float(val)
                    ctx.agent = agent_view
        elif isinstance(node, A.ASpawn):
            intent.spawn_types.append(node.agent_type)
        elif isinstance(node, A.AKill):
            intent.kill_targets.append(node.agent_type)
        elif isinstance(node, A.ASeq):
            for action in node.actions:
                self._eval_action(action, ctx, intent, agent_view)
        elif isinstance(node, A.AIf):
            cond = eval_expr(node.cond, ctx)
            if cond:
                self._eval_action(node.then_action, ctx, intent, agent_view)
            else:
                self._eval_action(node.else_action, ctx, intent, agent_view)
        elif isinstance(node, A.AMatch):
            subject = eval_expr(node.subject, ctx)
            matched = False
            for case in node.cases:
                from swarmlet.eval import _match_case
                if _match_case(case, subject, ctx):
                    self._eval_action(case.body, ctx, intent, agent_view)
                    matched = True
                    break
            if not matched:
                raise SwarmletRuntimeError("non-exhaustive action match", line=node.line)

    def _apply_intents(self, intents: List[Tuple[AgentRecord, Intent]]):
        """Apply collected intents in SPEC section 2.3 order."""
        # 1. Movement conflicts
        move_targets: Dict[Tuple[int, int], List[Tuple[AgentRecord, Intent]]] = {}
        for agent, intent in intents:
            if intent.move_dir != STAY and not intent.die:
                dx, dy = dir_offset(intent.move_dir)
                nx, ny = self._wrap(agent.x + dx, agent.y + dy)
                if nx is not None:
                    target = (nx, ny)
                    move_targets.setdefault(target, []).append((agent, intent))

        # Resolve conflicts: one winner per cell
        for target, movers in move_targets.items():
            if len(movers) == 1:
                winner_agent, _ = movers[0]
                winner_agent.x, winner_agent.y = target
            else:
                winner_idx = int(self.rng.integers(0, len(movers)))
                for i, (ag, _) in enumerate(movers):
                    if i == winner_idx:
                        ag.x, ag.y = target

        # 3. Agent field writes
        for agent, intent in intents:
            for fname, val in intent.agent_field_writes.items():
                agent.fields[fname] = val

        # 4. Cell field deposits (summation)
        for agent, intent in intents:
            for fname, val in intent.cell_field_deposits:
                if fname in self.fields:
                    nx, ny = self._wrap(agent.x, agent.y)
                    if nx is not None:
                        self.fields[fname][ny, nx] += val

        # 5. Kill intents
        for agent, intent in intents:
            for target_type in intent.kill_targets:
                # Find one co-located agent of the target type
                candidates = [
                    a for a in self.agents
                    if a.alive and a.agent_type == target_type
                    and a.x == agent.x and a.y == agent.y
                    and a.id != agent.id
                ]
                if candidates:
                    victim = candidates[int(self.rng.integers(0, len(candidates)))]
                    victim.alive = False

        # 6. Spawn intents
        new_agents = []
        for agent, intent in intents:
            for spawn_type in intent.spawn_types:
                new_agents.append(self._spawn_agent(spawn_type, agent.x, agent.y))
        self.agents.extend(new_agents)

        # 7. Death intents
        for agent, intent in intents:
            if intent.die:
                agent.alive = False

        # Remove dead agents
        self.agents = [a for a in self.agents if a.alive]

    # ----- Snapshot -----

    def snapshot(self) -> Dict[str, Any]:
        """Return current world state as a dictionary."""
        state_grid = [[self.state_names[self.states[y, x]]
                        for x in range(self.width)]
                       for y in range(self.height)]
        field_data = {fn: arr.tolist() for fn, arr in self.fields.items()}
        agents = [
            {"id": a.id, "type": a.agent_type, "x": a.x, "y": a.y, "fields": dict(a.fields)}
            for a in self.agents if a.alive
        ]
        return {
            "tick": self.tick_count,
            "width": self.width,
            "height": self.height,
            "topology": self.topology,
            "states": state_grid,
            "fields": field_data,
            "agents": agents,
        }

    def to_json(self) -> str:
        return json.dumps(self.snapshot())

    def reset(self, seed: Optional[int] = None):
        """Reset to initial state."""
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.tick_count = 0
        self.states = np.zeros((self.height, self.width), dtype=np.int32)
        for fname in self.fields:
            self.fields[fname] = np.full(
                (self.height, self.width), self._field_defaults.get(fname, 0.0), dtype=np.float64
            )
        self.agents = []
        self._next_agent_id = 0
        self._run_init()
