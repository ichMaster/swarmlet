"""Parser — recursive descent producing AST nodes from token stream."""

from __future__ import annotations

from typing import Any, List, Optional

from swarmlet.lexer import Token, tokenize
from swarmlet.errors import SwarmletStaticError
from swarmlet import ast as A


class Parser:
    """Recursive descent parser for Swarmlet programs."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ----- helpers -----

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def peek_kind(self) -> str:
        return self.tokens[self.pos].kind

    def at(self, *kinds: str) -> bool:
        return self.peek_kind() in kinds

    def eat(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            self._error(f"expected {kind!r} but got {tok.kind!r} ({tok.value!r})")
        self.pos += 1
        return tok

    def eat_ident(self) -> Token:
        """Eat an IDENT token or a keyword being used as an identifier name."""
        tok = self.peek()
        if tok.kind == "IDENT":
            self.pos += 1
            return tok
        self._error(f"expected identifier but got {tok.kind!r}")

    def match(self, kind: str) -> Optional[Token]:
        if self.peek_kind() == kind:
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok
        return None

    def _error(self, msg: str):
        tok = self.peek()
        raise SwarmletStaticError(tok.line, tok.col, msg)

    # ----- top-level -----

    def parse_program(self) -> A.Program:
        decls = []
        while not self.at("EOF"):
            decls.append(self.parse_decl())
        return A.Program(decls=decls, line=1)

    def parse_decl(self) -> Any:
        k = self.peek_kind()
        if k == "world":
            return self.parse_world_decl()
        if k == "cell":
            return self.parse_cell_decl()
        if k == "field":
            return self.parse_field_decl()
        if k == "param":
            return self.parse_param_decl()
        if k == "agent":
            return self.parse_agent_decl()
        if k == "let":
            return self.parse_let_decl()
        if k == "init":
            return self.parse_init_decl()
        self._error(f"expected declaration but got {k!r}")

    # ----- declarations -----

    def parse_world_decl(self) -> A.WorldDecl:
        tok = self.eat("world")
        w_tok = self.eat("NUMBER")
        # Expect 'x' as an identifier
        x_tok = self.peek()
        if x_tok.kind == "IDENT" and x_tok.value == "x":
            self.pos += 1
        else:
            self._error("expected 'x' in world declaration")
        h_tok = self.eat("NUMBER")
        topology = "wrap"  # default
        if self.at("wrap"):
            self.eat("wrap")
            topology = "wrap"
        elif self.at("bounded"):
            self.eat("bounded")
            topology = "bounded"
        return A.WorldDecl(
            width=int(w_tok.value), height=int(h_tok.value),
            topology=topology, line=tok.line,
        )

    def parse_cell_decl(self) -> Any:
        tok = self.eat("cell")
        if self.at("states"):
            return self.parse_states_decl(tok)
        # Otherwise it's part of a cell rule — but that starts with 'let cell'
        # This shouldn't happen at top-level; 'cell' without 'states' at decl level is an error
        self._error("expected 'states' after 'cell'")

    def parse_states_decl(self, cell_tok: Token) -> A.StatesDecl:
        self.eat("states")
        names = [self.eat_ident().value]
        while self.match("|"):
            names.append(self.eat_ident().value)
        return A.StatesDecl(names=names, line=cell_tok.line)

    def parse_field_decl(self) -> A.FieldDecl:
        tok = self.eat("field")
        name = self.eat_ident().value
        self.eat("=")
        value = self.parse_const_expr()
        return A.FieldDecl(name=name, default=value, line=tok.line)

    def parse_param_decl(self) -> A.ParamDecl:
        tok = self.eat("param")
        name = self.eat_ident().value
        self.eat("=")
        value = self.parse_const_expr()
        return A.ParamDecl(name=name, value=value, line=tok.line)

    def parse_agent_decl(self) -> A.AgentDecl:
        tok = self.eat("agent")
        name = self.eat_ident().value
        self.eat("{")
        fields = []
        if not self.at("}"):
            fields.append(self._parse_agent_field())
            while self.match(","):
                if self.at("}"):
                    break
                fields.append(self._parse_agent_field())
        self.eat("}")
        return A.AgentDecl(name=name, fields=fields, line=tok.line)

    def _parse_agent_field(self):
        name = self.eat_ident().value
        self.eat("=")
        value = self.parse_const_expr()
        return (name, value)

    def parse_let_decl(self) -> Any:
        tok = self.eat("let")
        if self.at("cell"):
            return self.parse_cell_rule(tok)
        if self.at("agent"):
            return self.parse_agent_rule(tok)
        self._error("expected 'cell' or 'agent' after 'let'")

    def parse_cell_rule(self, let_tok: Token) -> A.CellRule:
        self.eat("cell")
        # Pattern: identifier or _
        if self.at("IDENT"):
            pattern = self.eat_ident().value
        elif self.match("_"):
            pattern = "_"
        else:
            # Could be a keyword used as state name? Try eating it.
            pattern = self.eat_ident().value
        self.eat("=")
        body = self.parse_cell_body()
        return A.CellRule(pattern=pattern, body=body, line=let_tok.line)

    def parse_cell_body(self) -> Any:
        if self.at("seq"):
            return self.parse_cell_seq()
        expr = self.parse_expr()
        return A.CellExpr(expr=expr, line=expr.line if hasattr(expr, "line") else 0)

    def parse_cell_seq(self) -> A.CellSeq:
        tok = self.eat("seq")
        self.eat("{")
        stmts = [self.parse_cell_stmt()]
        while self.match(";"):
            if self.at("}"):
                break
            stmts.append(self.parse_cell_stmt())
        self.eat("}")
        return A.CellSeq(stmts=stmts, line=tok.line)

    def parse_cell_stmt(self) -> Any:
        if self.at("become"):
            tok = self.eat("become")
            expr = self.parse_expr()
            return A.CellBecome(expr=expr, line=tok.line)
        if self.at("set"):
            tok = self.eat("set")
            name = self.eat_ident().value
            self.eat("=")
            expr = self.parse_expr()
            return A.CellSet(field_name=name, expr=expr, line=tok.line)
        self._error("expected 'become' or 'set' in cell seq block")

    def parse_agent_rule(self, let_tok: Token) -> A.AgentRule:
        self.eat("agent")
        name = self.eat_ident().value
        self.eat("=")
        action = self.parse_action()
        return A.AgentRule(agent_type=name, body=action, line=let_tok.line)

    def parse_init_decl(self) -> Any:
        tok = self.eat("init")
        if self.at("cell"):
            self.eat("cell")
            self.eat("=")
            expr = self.parse_expr()
            return A.InitCell(expr=expr, line=tok.line)
        if self.at("field"):
            self.eat("field")
            name = self.eat_ident().value
            self.eat("=")
            expr = self.parse_expr()
            return A.InitField(field_name=name, expr=expr, line=tok.line)
        if self.at("agent"):
            self.eat("agent")
            name = self.eat_ident().value
            count_tok = self.eat("NUMBER")
            return A.InitAgent(agent_type=name, count=int(count_tok.value), line=tok.line)
        self._error("expected 'cell', 'field', or 'agent' after 'init'")

    # ----- const_expr -----

    def parse_const_expr(self) -> Any:
        """Parse a constant expression: number, bool, or -number."""
        neg = False
        if self.match("-"):
            neg = True
        if self.at("NUMBER"):
            tok = self.eat("NUMBER")
            val = tok.value
            return -val if neg else val
        if neg:
            self._error("expected number after '-'")
        if self.at("true"):
            self.eat("true")
            return True
        if self.at("false"):
            self.eat("false")
            return False
        self._error("expected constant expression (number or boolean)")

    # ----- expressions (will be fully implemented in SWARMLET-006) -----

    def parse_expr(self) -> Any:
        return self._parse_or_expr()

    def _parse_or_expr(self) -> Any:
        left = self._parse_and_expr()
        while self.at("or"):
            tok = self.eat("or")
            right = self._parse_and_expr()
            left = A.BinOp(op="or", left=left, right=right, line=tok.line)
        return left

    def _parse_and_expr(self) -> Any:
        left = self._parse_not_expr()
        while self.at("and"):
            tok = self.eat("and")
            right = self._parse_not_expr()
            left = A.BinOp(op="and", left=left, right=right, line=tok.line)
        return left

    def _parse_not_expr(self) -> Any:
        if self.at("not"):
            tok = self.eat("not")
            operand = self._parse_not_expr()
            return A.UnOp(op="not", operand=operand, line=tok.line)
        return self._parse_cmp_expr()

    def _parse_cmp_expr(self) -> Any:
        left = self._parse_add_expr()
        if self.at("==", "!=", "<", "<=", ">", ">="):
            tok = self.tokens[self.pos]
            self.pos += 1
            right = self._parse_add_expr()
            left = A.BinOp(op=tok.kind, left=left, right=right, line=tok.line)
        return left

    def _parse_add_expr(self) -> Any:
        left = self._parse_mul_expr()
        while self.at("+", "-"):
            tok = self.tokens[self.pos]
            self.pos += 1
            right = self._parse_mul_expr()
            left = A.BinOp(op=tok.kind, left=left, right=right, line=tok.line)
        return left

    def _parse_mul_expr(self) -> Any:
        left = self._parse_unary()
        while self.at("*", "/", "mod"):
            tok = self.tokens[self.pos]
            self.pos += 1
            right = self._parse_unary()
            left = A.BinOp(op=tok.kind, left=left, right=right, line=tok.line)
        return left

    def _parse_unary(self) -> Any:
        if self.at("-"):
            tok = self.eat("-")
            operand = self._parse_unary()
            return A.UnOp(op="-", operand=operand, line=tok.line)
        return self._parse_app_expr()

    def _parse_app_expr(self) -> Any:
        """Parse function application: f arg1 arg2 ...

        The tricky part: we need to know when to stop consuming arguments.
        Arguments are postfix expressions (atoms with optional dot access).
        We stop when we see something that can't start an atom.
        """
        expr = self._parse_postfix()
        # If expr is a Var (function name), collect arguments
        if isinstance(expr, A.Var) and self._can_start_atom():
            func = expr.name
            args = []
            while self._can_start_atom():
                args.append(self._parse_postfix())
            return A.Call(func=func, args=args, line=expr.line)
        return expr

    def _can_start_atom(self) -> bool:
        """Can the current token start an atom expression?"""
        k = self.peek_kind()
        if k in ("NUMBER", "IDENT", "(", "true", "false"):
            return True
        # Keywords used as builtin function names or state names in arguments
        if k in ("moore", "neumann", "radius", "forward", "back", "left", "right",
                  "field", "state", "cell", "agent", "die", "stay"):
            return True
        return False

    def _parse_postfix(self) -> Any:
        expr = self._parse_atom()
        while self.at("."):
            self.eat(".")
            name = self.eat_ident().value
            expr = A.Dot(expr=expr, field_name=name, line=expr.line)
        return expr

    def _parse_atom(self) -> Any:
        tok = self.peek()

        if tok.kind == "NUMBER":
            self.pos += 1
            return A.Num(value=tok.value, line=tok.line)

        if tok.kind == "true":
            self.pos += 1
            return A.Bool(value=True, line=tok.line)

        if tok.kind == "false":
            self.pos += 1
            return A.Bool(value=False, line=tok.line)

        if tok.kind == "(":
            self.pos += 1
            # Unit literal: ()
            if self.at(")"):
                self.eat(")")
                return A.Num(value=0, line=tok.line)  # unit as 0 / void
            # Check for nested match that must be parenthesized
            if self.at("match"):
                expr = self._parse_match_expr()
                self.eat(")")
                return expr
            expr = self.parse_expr()
            self.eat(")")
            return expr

        if tok.kind == "IDENT":
            self.pos += 1
            return A.Var(name=tok.value, line=tok.line)

        # Keywords that can appear as identifiers in expression context
        # (builtin function names and neighborhood selectors)
        if tok.kind in ("moore", "neumann", "radius", "forward", "back", "left", "right",
                         "field", "state", "cell", "agent", "die", "stay"):
            self.pos += 1
            return A.Var(name=tok.value, line=tok.line)

        self._error(f"expected expression but got {tok.kind!r}")

    # ----- match / if / let expressions -----

    def _parse_match_or_if_or_let(self) -> Any:
        """Dispatch to match, if, or let if the current token starts one."""
        if self.at("match"):
            return self._parse_match_expr()
        if self.at("if"):
            return self._parse_if_expr()
        if self.at("let"):
            return self._parse_let_expr()
        return self._parse_or_expr()

    def _parse_match_expr(self) -> A.Match:
        tok = self.eat("match")
        subject = self._parse_or_expr()
        self.eat("with")
        cases = []
        while self.at("|"):
            cases.append(self._parse_match_case())
        if not cases:
            self._error("match expression requires at least one case")
        return A.Match(subject=subject, cases=cases, line=tok.line)

    def _parse_match_case(self) -> A.MatchCase:
        tok = self.eat("|")
        patterns = [self._parse_pattern()]
        while self.at("|"):
            # Check if this is an or-pattern or a new case
            # If next after | is a pattern-like thing followed by -> or when, it's an or-pattern
            # Simplification: | followed by pattern, if next is | or when or ->, it's or-pattern
            saved = self.pos
            self.pos += 1  # skip |
            if self._looks_like_pattern():
                patterns.append(self._parse_pattern())
            else:
                self.pos = saved
                break
        guard = None
        if self.at("when"):
            self.eat("when")
            guard = self._parse_or_expr()
        self.eat("->")
        # Check for bare nested match (must be parenthesized)
        if self.at("match"):
            self._error("nested match must be parenthesized")
        body = self.parse_expr()
        return A.MatchCase(patterns=patterns, guard=guard, body=body, line=tok.line)

    def _looks_like_pattern(self) -> bool:
        """Check if current position looks like a pattern (for or-pattern disambiguation)."""
        k = self.peek_kind()
        return k in ("IDENT", "NUMBER", "true", "false", "_")

    def _parse_pattern(self) -> A.Pattern:
        tok = self.peek()
        if tok.kind == "IDENT":
            self.pos += 1
            return A.Pattern(kind="ident", value=tok.value, line=tok.line)
        if tok.kind == "NUMBER":
            self.pos += 1
            return A.Pattern(kind="number", value=tok.value, line=tok.line)
        if tok.kind == "true":
            self.pos += 1
            return A.Pattern(kind="bool", value=True, line=tok.line)
        if tok.kind == "false":
            self.pos += 1
            return A.Pattern(kind="bool", value=False, line=tok.line)
        if tok.kind == "_":
            self.pos += 1
            return A.Pattern(kind="wildcard", value=None, line=tok.line)
        # State names that are keywords
        if tok.kind in ("forward", "back", "left", "right", "moore", "neumann",
                         "stay", "die", "kill", "spawn", "move", "set", "become",
                         "seq", "wrap", "bounded"):
            self.pos += 1
            return A.Pattern(kind="ident", value=tok.value, line=tok.line)
        self._error(f"expected pattern but got {tok.kind!r}")

    def _parse_if_expr(self) -> A.If:
        tok = self.eat("if")
        cond = self.parse_expr()
        self.eat("then")
        then_expr = self.parse_expr()
        self.eat("else")
        else_expr = self.parse_expr()
        return A.If(cond=cond, then_expr=then_expr, else_expr=else_expr, line=tok.line)

    def _parse_let_expr(self) -> A.Let:
        tok = self.eat("let")
        # Disambiguate: let <IDENT> = ... in ... (expression)
        # vs let cell/agent ... (declaration — but that's handled at decl level)
        name = self.eat_ident().value
        self.eat("=")
        value = self.parse_expr()
        self.eat("in")
        body = self.parse_expr()
        return A.Let(name=name, value=value, body=body, line=tok.line)

    # Override parse_expr to dispatch to match/if/let
    def parse_expr(self) -> Any:
        if self.at("match"):
            # Bare match at expression level is OK (top-level match)
            return self._parse_match_expr()
        if self.at("if"):
            return self._parse_if_expr()
        if self.at("let") and not self._is_let_decl():
            return self._parse_let_expr()
        return self._parse_or_expr()

    def _is_let_decl(self) -> bool:
        """Look ahead to see if 'let' is followed by 'cell' or 'agent' (declaration)."""
        if self.pos + 1 < len(self.tokens):
            next_kind = self.tokens[self.pos + 1].kind
            return next_kind in ("cell", "agent")
        return False

    # ----- actions (will be fully implemented in SWARMLET-007) -----

    def parse_action(self) -> Any:
        tok = self.peek()

        if self.at("stay"):
            self.eat("stay")
            return A.AStay(line=tok.line)

        if self.at("die"):
            self.eat("die")
            return A.ADie(line=tok.line)

        if self.at("move"):
            self.eat("move")
            direction = self.parse_expr()
            return A.AMove(direction=direction, line=tok.line)

        if self.at("set"):
            self.eat("set")
            name = self.eat_ident().value
            self.eat("=")
            expr = self.parse_expr()
            return A.ASet(field_name=name, expr=expr, line=tok.line)

        if self.at("spawn"):
            self.eat("spawn")
            name = self.eat_ident().value
            return A.ASpawn(agent_type=name, line=tok.line)

        if self.at("kill"):
            self.eat("kill")
            name = self.eat_ident().value
            return A.AKill(agent_type=name, line=tok.line)

        if self.at("seq"):
            return self.parse_action_seq()

        if self.at("if"):
            return self.parse_action_if()

        if self.at("match"):
            return self.parse_action_match()

        self._error(f"expected action but got {tok.kind!r}")

    def parse_action_seq(self) -> A.ASeq:
        tok = self.eat("seq")
        self.eat("{")
        actions = [self.parse_action()]
        while self.match(";"):
            if self.at("}"):
                break
            actions.append(self.parse_action())
        self.eat("}")
        return A.ASeq(actions=actions, line=tok.line)

    def parse_action_if(self) -> A.AIf:
        tok = self.eat("if")
        cond = self.parse_expr()
        self.eat("then")
        then_action = self.parse_action()
        self.eat("else")
        else_action = self.parse_action()
        return A.AIf(cond=cond, then_action=then_action, else_action=else_action, line=tok.line)

    def parse_action_match(self) -> A.AMatch:
        tok = self.eat("match")
        subject = self._parse_or_expr()
        self.eat("with")
        cases = []
        while self.at("|"):
            cases.append(self._parse_action_case())
        if not cases:
            self._error("match action requires at least one case")
        return A.AMatch(subject=subject, cases=cases, line=tok.line)

    def _parse_action_case(self) -> A.ActionCase:
        tok = self.eat("|")
        patterns = [self._parse_pattern()]
        while self.at("|"):
            saved = self.pos
            self.pos += 1
            if self._looks_like_pattern():
                patterns.append(self._parse_pattern())
            else:
                self.pos = saved
                break
        guard = None
        if self.at("when"):
            self.eat("when")
            guard = self._parse_or_expr()
        self.eat("->")
        if self.at("match"):
            self._error("nested match must be parenthesized")
        body = self.parse_action()
        return A.ActionCase(patterns=patterns, guard=guard, body=body, line=tok.line)


def parse(source: str) -> A.Program:
    """Parse Swarmlet source code into a Program AST."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse_program()
