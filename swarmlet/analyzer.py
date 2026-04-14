"""Static semantic analysis — name resolution, type checking, duplicate detection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from swarmlet import ast as A
from swarmlet.builtins import (
    BUILTIN_NAMES, CELL_CONTEXT_ONLY, AGENT_CONTEXT_ONLY,
    HEADING_REQUIRED, INIT_ONLY,
)
from swarmlet.errors import SwarmletStaticError


class Analyzer:
    """Walk a parsed Program and perform semantic checks.

    Collects all errors and raises a single SwarmletStaticError at the end.
    """

    def __init__(self):
        self.errors: List[str] = []
        # Registries built from declarations
        self.cell_states: Set[str] = set()
        self.cell_fields: Set[str] = set()
        self.agent_types: Dict[str, Set[str]] = {}  # name -> set of field names
        self.params: Set[str] = set()
        self.cell_rule_patterns: Set[str] = set()
        # Context tracking
        self.context: str = "top"  # "top", "cell", "agent", "init_cell", "init_field", "init_agent"
        self.current_agent_type: Optional[str] = None

    def _err(self, line: int, msg: str):
        self.errors.append(f"line {line}: {msg}")

    def analyze(self, prog: A.Program):
        """Analyze the program. Raises SwarmletStaticError if any errors found."""
        # First pass: collect declarations
        self._collect_decls(prog)
        # Second pass: check rules and expressions
        self._check_rules(prog)
        # Report errors
        if self.errors:
            msg = f"{len(self.errors)} static error(s):\n" + "\n".join(f"  {e}" for e in self.errors)
            raise SwarmletStaticError(message=msg)

    def _collect_decls(self, prog: A.Program):
        for decl in prog.decls:
            if isinstance(decl, A.StatesDecl):
                for name in decl.names:
                    if name in self.cell_states:
                        self._err(decl.line, f"duplicate cell state '{name}'")
                    self.cell_states.add(name)
            elif isinstance(decl, A.FieldDecl):
                if decl.name in self.cell_fields:
                    self._err(decl.line, f"duplicate field declaration '{decl.name}'")
                self.cell_fields.add(decl.name)
            elif isinstance(decl, A.ParamDecl):
                if decl.name in self.params:
                    self._err(decl.line, f"duplicate param '{decl.name}'")
                self.params.add(decl.name)
            elif isinstance(decl, A.AgentDecl):
                if decl.name in self.agent_types:
                    self._err(decl.line, f"duplicate agent type '{decl.name}'")
                fields = set()
                for fname, _ in decl.fields:
                    fields.add(fname)
                self.agent_types[decl.name] = fields

    def _check_rules(self, prog: A.Program):
        for decl in prog.decls:
            if isinstance(decl, A.CellRule):
                self._check_cell_rule(decl)
            elif isinstance(decl, A.AgentRule):
                self._check_agent_rule(decl)
            elif isinstance(decl, A.InitCell):
                self.context = "init_cell"
                self._check_expr(decl.expr)
                self.context = "top"
            elif isinstance(decl, A.InitField):
                self.context = "init_field"
                self._check_expr(decl.expr)
                self.context = "top"
            elif isinstance(decl, A.InitAgent):
                if decl.agent_type not in self.agent_types:
                    self._err(decl.line, f"unknown agent type '{decl.agent_type}' in init")

    def _check_cell_rule(self, rule: A.CellRule):
        # Check duplicate cell rule patterns
        if rule.pattern in self.cell_rule_patterns:
            self._err(rule.line, f"duplicate cell rule for pattern '{rule.pattern}'")
        self.cell_rule_patterns.add(rule.pattern)

        # Check pattern references a valid state (or is wildcard)
        if rule.pattern != "_" and self.cell_states and rule.pattern not in self.cell_states:
            self._err(rule.line, f"cell rule pattern '{rule.pattern}' is not a declared state")

        self.context = "cell"
        self._check_cell_body(rule.body)
        self.context = "top"

    def _check_cell_body(self, body: Any):
        if isinstance(body, A.CellExpr):
            self._check_expr(body.expr)
        elif isinstance(body, A.CellSeq):
            for stmt in body.stmts:
                if isinstance(stmt, A.CellBecome):
                    self._check_expr(stmt.expr)
                elif isinstance(stmt, A.CellSet):
                    if stmt.field_name not in self.cell_fields:
                        self._err(stmt.line, f"unknown cell field '{stmt.field_name}' in set")
                    self._check_expr(stmt.expr)

    def _check_agent_rule(self, rule: A.AgentRule):
        if rule.agent_type not in self.agent_types:
            self._err(rule.line, f"unknown agent type '{rule.agent_type}' in agent rule")
        self.context = "agent"
        self.current_agent_type = rule.agent_type
        self._check_action(rule.body)
        self.context = "top"
        self.current_agent_type = None

    def _check_action(self, action: Any):
        if isinstance(action, (A.AStay, A.ADie)):
            pass
        elif isinstance(action, A.AMove):
            self._check_expr(action.direction)
        elif isinstance(action, A.ASet):
            self._annotate_set(action)
            self._check_expr(action.expr)
        elif isinstance(action, A.ASpawn):
            if action.agent_type not in self.agent_types:
                self._err(action.line, f"unknown agent type '{action.agent_type}' in spawn")
        elif isinstance(action, A.AKill):
            if action.agent_type not in self.agent_types:
                self._err(action.line, f"unknown agent type '{action.agent_type}' in kill")
        elif isinstance(action, A.ASeq):
            for a in action.actions:
                self._check_action(a)
        elif isinstance(action, A.AIf):
            self._check_expr(action.cond)
            self._check_action(action.then_action)
            self._check_action(action.else_action)
        elif isinstance(action, A.AMatch):
            self._check_expr(action.subject)
            for case in action.cases:
                if case.guard:
                    self._check_expr(case.guard)
                self._check_action(case.body)

    def _annotate_set(self, action: A.ASet):
        """Determine whether a 'set' in agent context targets a cell field or agent field."""
        name = action.field_name
        is_cell = name in self.cell_fields
        is_agent = False
        if self.current_agent_type and self.current_agent_type in self.agent_types:
            is_agent = name in self.agent_types[self.current_agent_type]

        if is_cell and is_agent:
            self._err(action.line,
                      f"ambiguous set: '{name}' is both a cell field and an agent field")
        elif not is_cell and not is_agent:
            self._err(action.line,
                      f"unknown field '{name}' in set — not a cell field or agent field")
        # We use object.__setattr__ since ASet is frozen
        if is_cell:
            object.__setattr__(action, "_target", "cell")
        elif is_agent:
            object.__setattr__(action, "_target", "agent")

    def _check_expr(self, expr: Any):
        if isinstance(expr, (A.Num, A.Bool)):
            pass
        elif isinstance(expr, A.Var):
            self._check_name(expr.name, expr.line)
        elif isinstance(expr, A.BinOp):
            self._check_expr(expr.left)
            self._check_expr(expr.right)
        elif isinstance(expr, A.UnOp):
            self._check_expr(expr.operand)
        elif isinstance(expr, A.Call):
            self._check_call(expr)
        elif isinstance(expr, A.Dot):
            self._check_expr(expr.expr)
        elif isinstance(expr, A.If):
            self._check_expr(expr.cond)
            self._check_expr(expr.then_expr)
            self._check_expr(expr.else_expr)
        elif isinstance(expr, A.Let):
            if expr.name in BUILTIN_NAMES:
                self._err(expr.line, f"let binding '{expr.name}' shadows a built-in")
            self._check_expr(expr.value)
            self._check_expr(expr.body)
        elif isinstance(expr, A.Match):
            self._check_expr(expr.subject)
            for case in expr.cases:
                if case.guard:
                    self._check_expr(case.guard)
                self._check_expr(case.body)

    def _check_name(self, name: str, line: int):
        """Check if a name reference is valid in the current context."""
        # Known names: cell states, params, builtins, agent fields (via self.field)
        if name in self.cell_states:
            return
        if name in self.params:
            return
        if name in BUILTIN_NAMES:
            self._check_builtin_context(name, line)
            return
        if name in self.cell_fields:
            return
        # Agent field names are accessed via self.field, not bare names
        # But let-bound variables and function args are not tracked in this simple analyzer
        # So we allow unknown names (they may be let-bound)

    def _check_call(self, call: A.Call):
        """Check a function call."""
        name = call.func
        if name in BUILTIN_NAMES:
            self._check_builtin_context(name, call.line)
        for arg in call.args:
            self._check_expr(arg)

    def _check_builtin_context(self, name: str, line: int):
        """Check that a builtin is used in the correct context."""
        if name in INIT_ONLY:
            if self.context not in ("init_cell", "init_field"):
                self._err(line, f"'{name}' can only be used in init context")

        if name in HEADING_REQUIRED:
            if self.context == "agent" and self.current_agent_type:
                agent_fields = self.agent_types.get(self.current_agent_type, set())
                if "heading" not in agent_fields:
                    self._err(line,
                              f"'{name}' requires agent '{self.current_agent_type}' "
                              f"to have a heading field")
            elif self.context != "agent":
                self._err(line, f"'{name}' can only be used in agent rules")

        if name in AGENT_CONTEXT_ONLY and self.context == "cell":
            self._err(line, f"'{name}' can only be used in agent rules, not cell rules")

        if name in CELL_CONTEXT_ONLY and self.context == "agent":
            # Cell-context builtins in agent rules — some have agent equivalents
            # For simplicity in v0.1, we allow it (they read from the agent's current cell)
            pass


def analyze(prog: A.Program):
    """Analyze a parsed Program. Raises SwarmletStaticError on errors."""
    analyzer = Analyzer()
    analyzer.analyze(prog)
    return analyzer
