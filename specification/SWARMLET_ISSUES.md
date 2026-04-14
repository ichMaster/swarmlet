# Swarmlet Stage 1 — GitHub Issues Plan

## Issues Summary Table

| # | ID | Title | Size | Phase | Dependencies |
|---|---|---|---|---|---|
| 1 | SWARMLET-001 | Project skeleton and packaging | S | 1 — Foundation | -- |
| 2 | SWARMLET-002 | Token model and error hierarchy | S | 1 — Foundation | SWARMLET-001 |
| 3 | SWARMLET-003 | AST node definitions | S | 1 — Foundation | SWARMLET-001 |
| 4 | SWARMLET-004 | Lexer | M | 2 — Lexer & Parser | SWARMLET-002 |
| 5 | SWARMLET-005 | Parser: declarations | M | 2 — Lexer & Parser | SWARMLET-003, SWARMLET-004 |
| 6 | SWARMLET-006 | Parser: expressions and pattern matching | L | 2 — Lexer & Parser | SWARMLET-005 |
| 7 | SWARMLET-007 | Parser: cell rules and agent actions | M | 2 — Lexer & Parser | SWARMLET-006 |
| 8 | SWARMLET-008 | Built-in name registry and direction encoding | S | 3 — Built-ins | SWARMLET-001 |
| 9 | SWARMLET-009 | Built-ins: random, math, direction helpers | S | 3 — Built-ins | SWARMLET-008 |
| 10 | SWARMLET-010 | Static analyzer | M | 3 — Built-ins | SWARMLET-007, SWARMLET-008 |
| 11 | SWARMLET-011 | Expression evaluator | M | 4 — Evaluator | SWARMLET-010 |
| 12 | SWARMLET-012 | World class, snapshot, initialization | M | 5 — Engine | SWARMLET-011 |
| 13 | SWARMLET-013 | Built-ins: cell context | M | 5 — Engine | SWARMLET-012, SWARMLET-009 |
| 14 | SWARMLET-014 | Built-ins: agent context | M | 5 — Engine | SWARMLET-012, SWARMLET-009 |
| 15 | SWARMLET-015 | Action evaluator with intent record | M | 4 — Evaluator | SWARMLET-011, SWARMLET-014 |
| 16 | SWARMLET-016 | Engine: cell phase tick | M | 5 — Engine | SWARMLET-013 |
| 17 | SWARMLET-017 | Engine: agent phase with conflict resolution | L | 5 — Engine | SWARMLET-015, SWARMLET-016 |
| 18 | SWARMLET-018 | Snapshot serialization (JSONL and NPZ) | S | 6 — Frontend | SWARMLET-012 |
| 19 | SWARMLET-019 | CLI: run and check commands | M | 6 — Frontend | SWARMLET-017, SWARMLET-018 |
| 20 | SWARMLET-020 | Example: forest fire | S | 7 — Examples | SWARMLET-019 |
| 21 | SWARMLET-021 | Example: ant foraging | M | 7 — Examples | SWARMLET-020 |
| 22 | SWARMLET-022 | Example: Boids on grid | M | 7 — Examples | SWARMLET-020 |
| 23 | SWARMLET-023 | Example: predator-prey (wolf-sheep) | M | 7 — Examples | SWARMLET-020 |
| 24 | SWARMLET-024 | Example: Gray-Scott reaction-diffusion with vectorized laplacian | L | 7 — Examples | SWARMLET-020, SWARMLET-013 |
| 25 | SWARMLET-025 | Determinism harness and regression tests | S | 8 — Quality | SWARMLET-020, SWARMLET-021, SWARMLET-022, SWARMLET-023, SWARMLET-024 |
| 26 | SWARMLET-026 | Documentation and polish | M | 9 — Documentation | SWARMLET-019, SWARMLET-020, SWARMLET-021, SWARMLET-022, SWARMLET-023, SWARMLET-024 |

**Size legend:** S = ≤ 0.5 day, M = 0.5–1 day, L = 1–2 days

---

## Dependency Tree

```
                    SWARMLET-001 (skeleton)
                          |
              +-----------+------------+
              v           v            v
        SWARMLET-002 SWARMLET-003 SWARMLET-008
        (tokens)     (AST)        (builtin names)
              |           |            |
              v           |            v
        SWARMLET-004      |       SWARMLET-009
        (lexer)           |       (random/math/dirs)
              |           |
              +-----+-----+
                    v
              SWARMLET-005
              (parser: decls)
                    |
                    v
              SWARMLET-006
              (parser: exprs)
                    |
                    v
              SWARMLET-007
              (parser: rules)
                    |
                    v
              SWARMLET-010 <----- SWARMLET-008
              (analyzer)
                    |
                    v
              SWARMLET-011
              (eval: exprs)
                    |
                    v
              SWARMLET-012 <----- SWARMLET-009
              (World + init)
                    |
              +-----+-----+
              v           v
        SWARMLET-013 SWARMLET-014
        (builtins:    (builtins:
         cell ctx)     agent ctx)
              |           |
              v           v
        SWARMLET-016 SWARMLET-015
        (cell phase)  (action eval)
              |           |
              +-----+-----+
                    v
              SWARMLET-017
              (agent phase)
                    |
                    v
              SWARMLET-018 ----- SWARMLET-019
              (serializers)      (CLI)
                                   |
                                   v
                             SWARMLET-020
                             (forest fire)
                                   |
                  +----------------+----------------+
                  v                v                v
            SWARMLET-021     SWARMLET-022    SWARMLET-023
            (ants)           (boids)         (wolf-sheep)
                  |                |                |
                  +----------------+----------------+
                                   |
                             SWARMLET-024
                             (gray-scott + vectorized laplacian)
                                   |
                                   v
                             SWARMLET-025
                             (determinism harness)
                                   |
                                   v
                             SWARMLET-026
                             (docs and polish)
```

**Parallelization hints:**

- SWARMLET-002, SWARMLET-003, and SWARMLET-008 can run in parallel after SWARMLET-001
- SWARMLET-013 and SWARMLET-014 can run in parallel after SWARMLET-012
- SWARMLET-021, SWARMLET-022, SWARMLET-023 can run in parallel after SWARMLET-020. SWARMLET-024 needs SWARMLET-013 explicitly because of the vectorized laplacian fast path
- Example tasks must be merged before SWARMLET-025 (determinism harness covers all five)

---

## Phase 1 — Foundation

### SWARMLET-001 — Project skeleton and packaging

**Description:**
Set up the Python project layout and packaging infrastructure for swarmlet.

**What needs to be done:**
- Create `pyproject.toml` for Python 3.11+ with entry point `swarmlet = swarmlet.cli:main`
- Add `numpy` as a runtime dependency, `pytest` and `pytest-cov` as dev dependencies
- Create `swarmlet/__init__.py` with stub public exports for `load`, `SwarmletStaticError`, `SwarmletRuntimeError`
- Create stub modules: `swarmlet/lexer.py`, `swarmlet/parser.py`, `swarmlet/ast.py`, `swarmlet/analyzer.py`, `swarmlet/eval.py`, `swarmlet/engine.py`, `swarmlet/builtins.py`, `swarmlet/snapshot.py`, `swarmlet/cli.py`
- Create `swarmlet/examples/` directory with `.gitkeep`
- Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- Create `README.md` (minimal, just project name and one-paragraph description from SPEC.md section 1)
- Create `.gitignore` for Python projects
- Ensure `pip install -e .` succeeds and `swarmlet --help` can be invoked (even if it prints a placeholder)

**Dependencies:** None

**Expected result:**
A clean Python project skeleton that installs correctly and has a working (placeholder) CLI entry point.

**Acceptance criteria:**
- [ ] `pip install -e .` exits 0
- [ ] `python -c "import swarmlet"` succeeds
- [ ] `from swarmlet import SwarmletStaticError, SwarmletRuntimeError` succeeds
- [ ] `swarmlet --help` prints something (even a placeholder)
- [ ] Directory layout matches section 13.1 of `SPEC.md`

---

### SWARMLET-002 — Token model and error hierarchy

**Description:**
Define the `Token` dataclass and the exception hierarchy used by all subsequent modules for consistent error reporting with source position information.

**What needs to be done:**
- In `swarmlet/lexer.py`, define `Token` as a frozen dataclass with fields `kind: str`, `value: Any`, `line: int`, `col: int`
- In `swarmlet/__init__.py` (or a new `swarmlet/errors.py` if you prefer separation), define error hierarchy:
  - `SwarmletError` as root
  - `SwarmletStaticError(SwarmletError)` for parse, lex, and analyzer errors
  - `SwarmletRuntimeError(SwarmletError)` for evaluator and engine errors
- Each error carries optional `line` and `col` fields
- `__str__` produces messages like `SwarmletStaticError at line 5, col 12: expected '=' but got 'Tree'`, gracefully omitting position info when not available
- Errors can be instantiated with `(message)`, `(line, col, message)`, or as keyword arguments
- Write ≥4 unit tests in `tests/unit/test_errors.py` covering message formatting with and without position info

**Dependencies:** SWARMLET-001

**Expected result:**
A consistent error hierarchy and a token type that all later modules can use without further refactoring.

**Acceptance criteria:**
- [ ] `Token(kind="IDENT", value="Tree", line=1, col=5)` works and is hashable
- [ ] `str(SwarmletStaticError(5, 12, "unexpected character"))` equals `"SwarmletStaticError at line 5, col 12: unexpected character"`
- [ ] `str(SwarmletRuntimeError("non-exhaustive match"))` equals `"SwarmletRuntimeError: non-exhaustive match"`
- [ ] Both error types are subclasses of `SwarmletError`
- [ ] 4+ unit tests passing

---

### SWARMLET-003 — AST node definitions

**Description:**
Define dataclasses for every AST node in `SPEC.md` section 4. This is the foundation for the parser, analyzer, and evaluator.

**What needs to be done:**
- In `swarmlet/ast.py`, define frozen dataclasses for:
  - Top-level: `Program`, `WorldDecl`, `StatesDecl`, `FieldDecl`, `ParamDecl`, `AgentDecl`, `CellRule`, `AgentRule`, `InitCell`, `InitField`, `InitAgent`
  - Expressions: `Num`, `Bool`, `Var`, `BinOp` (with `op`, `left`, `right`), `UnOp`, `Call` (with `name`, `args`), `Dot` (for `self.field` — fields `obj`, `field`), `If`, `Let`, `Match` (with `scrut`, `cases`)
  - Patterns: `Pattern` (with `kind` in {"wildcard", "ident", "number", "bool"}, `value`)
  - Match cases: `MatchCase` (with `patterns: List[Pattern]`, `guard: Optional[Expr]`, `body`)
  - Cell bodies: `CellExpr` (single expression) and `CellSeq` (list of statements). Cell statements: `CellBecome`, `CellSet`
  - Actions: `AStay`, `ADie`, `AMove`, `ASet`, `ASpawn`, `AKill`, `ASeq`, `AIf`, `AMatch`, `ActionCase`
- Every AST node carries a `line` field for error reporting
- Provide `__repr__` that produces a compact debug form for each node
- Write ≥4 unit tests in `tests/unit/test_ast.py` that construct one of each top-level form

**Dependencies:** SWARMLET-001

**Expected result:**
A complete AST module that all parser, analyzer, and evaluator code can import without further additions.

**Acceptance criteria:**
- [ ] All node classes are frozen dataclasses
- [ ] Each node has a `line` field
- [ ] `from swarmlet.ast import *` works and exposes all the names listed above
- [ ] Construction smoke tests for `WorldDecl`, `CellRule`, `AgentRule`, `Match`, `ASeq` pass

---

## Phase 2 — Lexer & Parser

### SWARMLET-004 — Lexer

**Description:**
Implement `tokenize(source: str) -> List[Token]` covering the full lexical grammar from `SPEC.md` section 3.

**What needs to be done:**
- Implement `tokenize` in `swarmlet/lexer.py` using char-by-char scanning or compiled regex
- Skip whitespace and `#` comments, preserve line and column tracking across newlines
- Handle reserved keywords from section 3.5 — they produce tokens with `kind` equal to the keyword
- Identifiers: `[A-Za-z_][A-Za-z0-9_]*` produce `('IDENT', name)`
- Numbers: integer and float, both produce `('NUMBER', value)` with proper Python int/float
- Booleans `true`/`false` are keywords, not identifiers
- Multi-character operators: `==`, `!=`, `<=`, `>=`, `->`
- Single-character operators from section 3.6
- Append `('EOF', None)` at the end
- Raise `SwarmletStaticError` with line/col on unexpected characters
- Write ≥10 unit tests in `tests/unit/test_lexer.py`

**Dependencies:** SWARMLET-002

**Expected result:**
A lexer that correctly tokenizes every example program in `SPEC.md` section 11 without errors.

**Acceptance criteria:**
- [ ] All five reference examples in `SPEC.md` section 11 tokenize without errors (do not parse them yet)
- [ ] Each multi-char operator (`==`, `!=`, `<=`, `>=`, `->`) is recognized as a single token
- [ ] `tokenize("let cell Tree = Fire")` produces `[let, cell, IDENT(Tree), =, IDENT(Fire), EOF]` with correct line/col
- [ ] Comments are skipped
- [ ] Newlines do not produce tokens but increment line counter
- [ ] Bad character produces `SwarmletStaticError` with line/col
- [ ] 10+ unit tests passing

---

### SWARMLET-005 — Parser: declarations

**Description:**
Implement the recursive descent parser for top-level declarations: `world`, `cell states`, `field`, `param`, `agent`, `init`. This is the parser scaffold; expressions and rule bodies are implemented in subsequent issues.

**What needs to be done:**
- Create `Parser` class in `swarmlet/parser.py` with a token list and position. Helper methods: `peek`, `peek_kind`, `eat`, `expect`, `match`
- Implement the entry point `parse(tokens) -> Program` that loops over declarations and collects them
- Implement parsers for: `world_decl`, `states_decl`, `field_decl`, `param_decl`, `agent_decl`, all three forms of `init_decl` (cell, field, agent)
- `const_expr` parser for default values (numbers and booleans only, with optional unary minus)
- Declaration order is free — collect them in encounter order
- Raise `SwarmletStaticError` with line/col for syntax errors. Error messages should be of the form `expected 'X' at line L col C, got 'Y'`
- Stub method `parse_expr()` that raises `NotImplementedError` so SWARMLET-006 can fill it in
- Stub method `parse_action()` and `parse_cell_body()` for SWARMLET-007
- Write ≥6 unit tests in `tests/unit/test_parser_decls.py`

**Dependencies:** SWARMLET-003, SWARMLET-004

**Expected result:**
A parser that can handle the declaration scaffold of any swarmlet program. Rule bodies are not yet parsed but can be after SWARMLET-006 and SWARMLET-007 land.

**Acceptance criteria:**
- [ ] 6+ unit tests covering each declaration form
- [ ] `world 100 x 100 wrap` parses to `WorldDecl(w=100, h=100, wrap=True)`
- [ ] `cell states Empty | Tree | Fire` parses to `StatesDecl(names=["Empty", "Tree", "Fire"])`
- [ ] `agent Ant { carrying = 0, heading = 0 }` parses to `AgentDecl(name="Ant", fields={"carrying": 0, "heading": 0})`
- [ ] Syntax errors give helpful messages with line and column

---

### SWARMLET-006 — Parser: expressions and pattern matching

**Description:**
Implement the expression parser with correct operator precedence, the `match`/`if`/`let` constructs, and the strict nested-match-must-be-parenthesized rule from section 7.6 of the spec.

**What needs to be done:**
- Implement `parse_expr` calling down through `or_expr`, `and_expr`, `not_expr`, `cmp_expr`, `add_expr`, `mul_expr`, `unary`, `app_expr`, `postfix`, `atom` — matching the precedence table in section 3.6
- Dispatch to `match_expr`, `if_expr`, `let_expr` at the top of `parse_expr` when one of those keywords appears
- `match` parsing rules:
  - The leading `|` before the first case is **required**
  - Each case is `| pattern_alts (when expr)? -> expr`
  - Or-patterns: `| A | B | C -> body` shares the body and guard
  - Patterns are: IDENT, NUMBER, true, false, `_`
  - **Nested match without parentheses is a static error.** When parsing the body of a `match_case`, if the next token is `match`, emit `SwarmletStaticError("nested match must be parenthesized at line X col Y")`. A parenthesized `(match ...)` is fine because it goes through `atom`
- `if` parsing: `if expr then expr else expr` — `else` is mandatory
- `let` parsing: `let IDENT = expr in expr`
- Whitespace function application: in `app_expr`, after parsing one `postfix`, keep parsing additional postfixes as long as the next token can start one (NUMBER, IDENT, true, false, `(`)
- Dot access: `postfix` parses chains of `.IDENT` for `self.field` access
- Write ≥12 unit tests in `tests/unit/test_parser_expr.py`

**Dependencies:** SWARMLET-005

**Expected result:**
A complete expression parser that handles all expression forms in the grammar with correct precedence and the documented restrictions.

**Acceptance criteria:**
- [ ] 12+ unit tests covering: arithmetic precedence, comparison precedence, boolean precedence, `let ... in`, `if/then/else`, `match` with single case, multi-case, `when` guards, or-patterns, function application (0/1/2/3 args), dot access, parenthesized nested match
- [ ] `1 + 2 * 3` parses to `BinOp("+", Num(1), BinOp("*", Num(2), Num(3)))`
- [ ] `not a and b` parses with `not` binding tighter than `and`
- [ ] `match Tree with | Tree -> 1 | _ -> 0` parses correctly with the leading `|` required
- [ ] Bare nested `match` produces a `SwarmletStaticError` with "nested match must be parenthesized" in the message
- [ ] Parenthesized nested `match` parses without error

---

### SWARMLET-007 — Parser: cell rules and agent actions

**Description:**
Implement parsing for `let cell` and `let agent` rules, including `seq` cell bodies and the full action grammar. This closes out the parser feature set; after this issue all five reference examples should parse.

**What needs to be done:**
- Parse `cell_rule`: `let cell <pattern> = <cell_body>`. Pattern is `IDENT` or `_`. Body is either an expression or a `seq { ... }` block
- Parse cell `seq` block: list of `become expr` or `set IDENT = expr` statements separated by `;`
- Parse `agent_rule`: `let agent IDENT = <action>`
- Parse all action forms from the grammar:
  - `stay`, `die`
  - `move expr`
  - `set IDENT = expr`
  - `spawn IDENT`, `kill IDENT`
  - `seq { action ; action ; ... }`
  - `if cond then action else action` (else is mandatory)
  - `match expr with | pattern -> action ...` (action-level match with the same nested-match restriction)
- Action `match` follows the same rule as expression `match`: leading `|` required, nested match must be parenthesized
- Update the `parse(tokens)` entry point dispatcher to recognize `let cell` vs `let agent` after the `let` keyword
- Add a test file `tests/unit/test_parser_examples.py` that loads each of the five `.swl` files (created as stubs in SWARMLET-020..024 — for now copy the source from `SPEC.md` section 11 into temporary string fixtures) and asserts they parse without errors
- Write ≥10 unit tests in `tests/unit/test_parser_rules.py`

**Dependencies:** SWARMLET-006

**Expected result:**
The parser is feature-complete. All five reference examples in `SPEC.md` section 11 parse without errors.

**Acceptance criteria:**
- [ ] 10+ unit tests covering each action form
- [ ] `let cell Tree = Fire` parses as a cell rule with single-expression body
- [ ] `let cell _ = seq { set pheromone = field pheromone * 0.98 }` parses as a wildcard cell rule with seq body
- [ ] `let agent Ant = seq { stay ; move forward }` parses as an agent rule with seq action
- [ ] `seq { if x > 0 then move forward else stay ; spawn Ant }` parses correctly
- [ ] All five reference example sources from `SPEC.md` section 11 parse without errors

---

## Phase 3 — Built-ins and Static Analysis

### SWARMLET-008 — Built-in name registry and direction encoding

**Description:**
Define the canonical sets of built-in names and the direction encoding constants used by both the static analyzer (for shadow checks) and the evaluator (for dispatch). This is the smallest possible foundation that lets the analyzer and evaluator be developed in parallel.

**What needs to be done:**
- In `swarmlet/builtins.py`, define `BUILTIN_NAMES: FrozenSet[str]` containing every built-in name from `SPEC.md` sections 6.1–6.5, plus the special context vars `state`, `x`, `y`, `self`, `cell_state`, plus the direction constants `forward`, `back`, `left`, `right`, `STAY`, plus the neighborhood selectors `moore`, `neumann`, `radius`
- Define `CELL_CONTEXT_ONLY: FrozenSet[str]` = `{"x", "y"}` (only valid in `init` expressions per the spec)
- Define `AGENT_CONTEXT_ONLY: FrozenSet[str]` containing `self`, `cell_state`, `cell_field`, `look`, `look_field`, `argmax_neighbor`, `argmin_neighbor`, `agents_in_radius`, `agents_of_type_in_radius`, `nearest_agent_dir`, `nearest_agent_of_type_dir`, `mean_heading_in_radius`, `min_in_radius`, `max_in_radius`, `forward`, `back`, `left`, `right`
- Define `HEADING_REQUIRED: FrozenSet[str]` = `{"forward", "back", "left", "right"}` for analyzer checks
- Define direction encoding from `SPEC.md` Appendix B as a module-level constant: `DIRECTIONS: List[Tuple[int, int]]` of length 8, indexed by direction value, plus `STAY = -1`
- Provide helper `dir_offset(d: int) -> Tuple[int, int]` that returns the (dx, dy) for a direction value, with `STAY` mapping to `(0, 0)`
- Provide helper `rotate_dir(d: int, steps: int) -> int` that adds `steps` to a direction modulo 8
- Write ≥3 unit tests in `tests/unit/test_builtins_registry.py`

**Dependencies:** SWARMLET-001

**Expected result:**
Stable name sets and direction utilities that all subsequent issues can import without further additions.

**Acceptance criteria:**
- [ ] `from swarmlet.builtins import BUILTIN_NAMES, CELL_CONTEXT_ONLY, AGENT_CONTEXT_ONLY, HEADING_REQUIRED, DIRECTIONS, STAY, dir_offset, rotate_dir` succeeds
- [ ] All four sets are frozen and non-empty
- [ ] `dir_offset(0) == (1, 0)` (East)
- [ ] `dir_offset(2) == (0, 1)` (South — y axis points down)
- [ ] `dir_offset(STAY) == (0, 0)`
- [ ] `rotate_dir(0, 4) == 4` (180-degree rotation)
- [ ] 3+ unit tests passing

---

### SWARMLET-009 — Built-ins: random, math, direction helpers

**Description:**
Implement the simplest built-in functions: random, math, and direction helpers. These do not depend on the world snapshot and can be tested in isolation.

**What needs to be done:**
- In `swarmlet/builtins.py`, define `BuiltinSpec` dataclass with `name: str`, `arity: Optional[int]` (None means variadic), `func: Callable`. Build a global `BUILTINS: Dict[str, BuiltinSpec]` registry
- The evaluator context object (defined here as a stub, fully implemented in SWARMLET-011) provides access to: the seeded RNG, the world snapshot, the current cell coords (or None), the current agent (or None), the local `let` bindings, the params dict
- Implement these built-ins:
  - **Random:** `random()` returning float in [0, 1), `random_int(n)` returning int in [0, n), `random_dir()` returning a direction 0..7
  - **Math:** `abs(x)`, `min(a, b)`, `max(a, b)`, `sqrt(x)`, `exp(x)`, `floor(x)`, `mod(a, b)`, `clamp(x, lo, hi)`
  - **Direction:** `forward`, `back`, `left`, `right` (read agent heading from context), `dir(dx, dy)`, `STAY` constant
- All randomness must go through `ctx.rng`, never `random.random()` or `np.random.random()` directly
- Write ≥10 unit tests in `tests/unit/test_builtins_basic.py`

**Dependencies:** SWARMLET-008

**Expected result:**
A working built-in registry covering all stateless functions, ready to be called by the evaluator.

**Acceptance criteria:**
- [ ] 10+ unit tests covering each function with at least one positive case
- [ ] `random_dir()` returns a value in 0..7 with uniform distribution (statistical test on 10000 samples, chi-square accepted)
- [ ] `forward` / `back` / `left` / `right` correctly compute relative directions for each of the 8 headings
- [ ] `clamp(5, 0, 3)` returns 3; `clamp(-1, 0, 3)` returns 0; `clamp(2, 0, 3)` returns 2
- [ ] All randomness goes through the seeded RNG (verified by setting seed and checking reproducibility)

---

### SWARMLET-010 — Static analyzer

**Description:**
Walk the parsed `Program`, build registries of declared names, and check all references and contextual restrictions. Collect ALL static errors and raise a single `SwarmletStaticError` listing the full set, instead of failing on the first.

**What needs to be done:**
- Create `Analyzer` class in `swarmlet/analyzer.py`
- Build registries: `cell_states: Set[str]`, `cell_fields: Set[str]`, `agent_types: Dict[str, AgentDecl]`, `agent_fields: Dict[str, Set[str]]`, `params: Dict[str, float]`
- Walk all expressions and actions, resolving identifier references. An identifier in expression position can be:
  - A local `let` binding
  - A param
  - A state name (returns the symbol value)
  - A built-in name (calls a built-in with zero args)
  - Otherwise an error
- Walk `set` actions in agent rules. Determine whether the field name is a cell field or an agent field for the enclosing agent type. **Static error if both, or if neither.** Annotate the AST node with the resolved kind so the evaluator can dispatch
- Detect duplicate cell-state declarations
- Detect duplicate cell rules with the same pattern
- Detect `let` shadowing a built-in (use `BUILTIN_NAMES` from SWARMLET-008)
- Detect `forward`, `back`, `left`, `right` used inside an agent rule for a type that does not have a `heading` field
- Detect `x` and `y` used outside `init` context
- Detect agent context built-ins used in cell rules and vice versa
- Collect ALL static errors and raise a single `SwarmletStaticError` with the full list at the end (do not fail on the first)
- Write ≥10 unit tests in `tests/unit/test_analyzer.py`, one per error category

**Dependencies:** SWARMLET-007, SWARMLET-008

**Expected result:**
An analyzer that catches every static error category from `SPEC.md` section 10 with helpful line-number messages, and annotates the AST for the evaluator.

**Acceptance criteria:**
- [ ] 10+ unit tests covering each static error category
- [ ] All five reference examples pass analysis without errors
- [ ] `let pheromone = ...` in a program that already declared `field pheromone` produces a shadowing error
- [ ] `set pheromone = ...` in an agent action where `pheromone` is a cell field is annotated as a cell deposit
- [ ] `set energy = ...` in an agent action where `energy` is an agent field is annotated as an agent field write
- [ ] `set foo = ...` where `foo` is neither an agent nor a cell field produces a static error
- [ ] All static errors from a single program are collected and reported together, not one at a time

---

## Phase 4 — Evaluator

### SWARMLET-011 — Expression evaluator

**Description:**
Implement `eval_expr(node, ctx) -> Value` for every expression AST node, including `match` semantics, `let` scoping, and runtime type checks.

**What needs to be done:**
- In `swarmlet/eval.py`, define `Value` as a tagged union (int, float, bool, state symbol, direction, agent_type, void). Use a small dataclass or just Python's native types with a `kind` tag where needed
- Define `EvalContext` dataclass: `snapshot`, `cell_xy: Optional[Tuple[int, int]]`, `agent: Optional[AgentRecord]`, `intent: Optional[Intent]`, `locals: Dict[str, Value]`, `params: Dict[str, float]`, `rng: numpy.random.Generator`, `is_init: bool`
- Implement `eval_expr` for:
  - `Num`, `Bool`: trivial
  - `Var`: look up local → param → built-in (call with zero args) → state symbol → error
  - `BinOp`: arithmetic, comparison, boolean
  - `UnOp`: unary minus, `not`
  - `Call`: look up built-in by name, evaluate args, call
  - `Dot`: read agent field via `ctx.agent.<field>`
  - `If`: evaluate condition, evaluate chosen branch
  - `Let`: evaluate `e1`, extend `locals`, evaluate `e2` in extended context
  - `Match`: try cases top to bottom (see below)
- Pattern matching algorithm:
  - For each case, check the pattern (or any or-pattern alternative) against the scrutinee
  - `_` matches anything
  - `Num` pattern matches by equality
  - `true`/`false` pattern matches the corresponding boolean
  - `IDENT` pattern matches if the scrutinee is a state symbol with that exact name
  - If the pattern matches AND the optional `when` guard evaluates to true, the case body is evaluated and returned
  - First matching case wins
  - If no case matches, raise `SwarmletRuntimeError("non-exhaustive match at line X")`
- Type errors raise `SwarmletRuntimeError` with the offending line
- Write ≥12 unit tests in `tests/unit/test_eval_expr.py`

**Dependencies:** SWARMLET-010

**Expected result:**
A complete expression evaluator that handles every expression form in the spec.

**Acceptance criteria:**
- [ ] 12+ unit tests covering: arithmetic, comparison, boolean, `let ... in`, `if/then/else`, `match` single-case, multi-case, guards, or-patterns, wildcard, non-exhaustive error
- [ ] `match 5 with | Tree -> 1 | _ -> 2` returns 2 (states do not match numbers, wildcard wins)
- [ ] `let x = 5 in let x = 10 in x` returns 10 (inner shadows outer)
- [ ] Comparing a state to a number with `<` raises `SwarmletRuntimeError`
- [ ] Non-exhaustive `match` with no `_` raises `SwarmletRuntimeError` with the correct line

---

## Phase 5 — Engine

### SWARMLET-012 — World class, snapshot, initialization

**Description:**
Implement the `World` runtime that holds program state, runs initialization, and produces snapshots. This is the central object exposed by `load()`.

**What needs to be done:**
- In `swarmlet/engine.py`, define the `World` class
- Define `AgentRecord` dataclass with `id: int`, `type: str`, `x: int`, `y: int`, plus a dict of declared fields
- Constructor: `World(program, seed, params=None)`. Internal state:
  - `states: numpy.ndarray[H, W]` of int8, indices into `states_legend`
  - `states_legend: List[str]`
  - `fields: Dict[str, numpy.ndarray[H, W]]` of float32
  - `agents: List[AgentRecord]`
  - `t: int = 0`
  - `rng: numpy.random.Generator` seeded from the constructor seed
  - `params: Dict[str, float]` (overrides applied on top of declared defaults)
  - `next_agent_id: int` for assigning unique IDs to spawned agents
- Run initialization at construction:
  - Apply `init cell` for every cell, or default to first state name
  - Apply `init field <name>` for every cell of each field that has such an init, or use the declared default
  - Apply `init agent T N` to spawn N agents at uniformly random positions
- Implement `snapshot()` returning the dict structure from `SPEC.md` section 9.1 — make safe copies of arrays and agent list
- Implement `to_json()` returning a JSON-serializable version (lists instead of ndarrays)
- Implement `reset(seed=None)` that re-runs initialization from scratch with the new seed (or the same seed if None)
- Provide `world.t` and `world.params` as read-only attributes
- Stub `step(n=1)` that raises `NotImplementedError` — it will be filled by SWARMLET-016 and SWARMLET-017
- Write ≥6 unit tests in `tests/unit/test_engine_init.py`

**Dependencies:** SWARMLET-011

**Expected result:**
A `World` class that loads a program, runs all three forms of initialization, and produces correct snapshots. Cannot yet step time, but can be inspected at t=0.

**Acceptance criteria:**
- [ ] 6+ unit tests covering: empty world, world with init cell, world with init field, world with init agent, snapshot structure, reset reproducibility
- [ ] `World(program, seed=42).snapshot()` returns a dict matching the structure in `SPEC.md` section 9.1
- [ ] `to_json()` produces JSON-serializable output (verified by `json.dumps`)
- [ ] `reset(seed=42)` followed by `snapshot()` produces identical state to a fresh `World(program, seed=42).snapshot()`
- [ ] `reset(seed=43)` produces different agent positions but the same population sizes
- [ ] `world.params` reflects both declared defaults and constructor overrides

---

### SWARMLET-013 — Built-ins: cell context

**Description:**
Implement the cell-context built-ins from `SPEC.md` section 6.2 — functions available inside cell rules and `init` expressions.

**What needs to be done:**
- In `swarmlet/builtins.py`, implement and register: `state`, `field`, `x`, `y` (init context only), `count`, `count_in`, `any`, `sum_field`, `sum_field_in`, `mean_field`, `max_field`, `min_field`, `laplacian`, `neighbor`, `neighbor_field`, `distance_to`, `gradient_to`
- All read from the current snapshot (via `ctx.snapshot`) and the current cell coordinates from `ctx.cell_xy`
- Neighborhood iteration helpers: build `moore_offsets`, `neumann_offsets`, and a `radius_offsets(r)` generator. Respect world topology: in `wrap` mode, take coordinates modulo `(W, H)`; in `bounded` mode, return a `void` sentinel for out-of-range cells
- `laplacian` uses the 9-point stencil specified in section 6.2: center weight -1.0, orthogonal neighbors 0.2, diagonal 0.05. (Weights sum to zero, which is required for a Laplacian to vanish on uniform fields.) **Per-cell implementation only** in this issue — the vectorized fast path comes in SWARMLET-024
- `distance_to(S)` and `gradient_to(S)` search out to radius 16 (Chebyshev). Return `-1` and `STAY` respectively if no target found
- Write ≥10 unit tests in `tests/unit/test_builtins_cell.py`. Build hand-crafted 5×5 or 7×7 grids and verify each function

**Dependencies:** SWARMLET-012, SWARMLET-009

**Expected result:**
All cell-context built-ins are implemented and tested on small hand-built worlds. The forest fire and ant pheromone field rules can be evaluated against a real `World` instance.

**Acceptance criteria:**
- [ ] 10+ unit tests passing
- [ ] `laplacian` on a uniform field returns 0 everywhere
- [ ] `laplacian` on a single-spike field returns the expected stencil values
- [ ] `gradient_to` and `distance_to` correctly find a nearest target on a small grid
- [ ] `gradient_to` returns `STAY` when no target within radius 16
- [ ] Wrap topology test: a cell at `(0, 0)` correctly sees `(W-1, H-1)` as a Moore neighbor
- [ ] Bounded topology test: out-of-range neighbors return `void`

---

### SWARMLET-014 — Built-ins: agent context

**Description:**
Implement the agent-context built-ins from `SPEC.md` section 6.3 — functions available inside agent rules.

**What needs to be done:**
- Implement and register: `self`, `cell_state`, `cell_field`, `look`, `look_field`, `argmax_neighbor`, `argmin_neighbor`, `agents_in_radius`, `agents_of_type_in_radius`, `nearest_agent_dir`, `nearest_agent_of_type_dir`, `mean_heading_in_radius`, `min_in_radius`, `max_in_radius`
- Build a per-tick spatial index for agents to make radius queries efficient (a dict from `(x, y)` to list of agents, rebuilt at the start of the agent phase). For v0.1, an O(N) scan per query is also acceptable since the example sizes are small
- `mean_heading_in_radius` algorithm: convert each heading to `(cos(h * pi / 4), sin(h * pi / 4))`, sum across all matching agents, then `atan2` on the sum and quantize to the nearest of 8 Moore directions. Return `STAY` if no other agents in radius
- All "agent count" and "nearest agent" functions must **exclude the current agent itself** — the docs say "other agents"
- Write ≥10 unit tests in `tests/unit/test_builtins_agent.py`. Build tiny worlds with hand-placed agents and verify each function

**Dependencies:** SWARMLET-012, SWARMLET-009

**Expected result:**
All agent-context built-ins are implemented and tested. Boids and predator-prey rule logic can be evaluated against a real World instance.

**Acceptance criteria:**
- [ ] 10+ unit tests passing
- [ ] Tests cover radius=0 (same cell), radius=1, larger radius
- [ ] `mean_heading_in_radius` with two agents heading East and South returns SE (or close — quantized to Moore)
- [ ] `agents_in_radius(0)` for an agent alone on its cell returns 0 (does not count self)
- [ ] `nearest_agent_dir(5)` returns `STAY` when no other agents within 5
- [ ] `agents_of_type_in_radius(Wolf, 3)` correctly counts only Wolves

---

### SWARMLET-015 — Action evaluator with intent record

**Description:**
Implement `eval_action(node, ctx, intent)` that mutates an `Intent` record according to the action AST. This is the runtime counterpart of agent rule evaluation; the engine will collect all intents and apply them atomically in SWARMLET-017.

**What needs to be done:**
- In `swarmlet/eval.py`, define `Intent` dataclass with fields: `agent_id: int`, `move_dir: Optional[int]`, `agent_field_writes: Dict[str, Value]`, `cell_field_deposits: Dict[str, float]`, `spawn_types: List[str]`, `kill_targets: List[str]`, `die: bool`
- Implement `eval_action`:
  - `AStay`: no-op
  - `ADie`: set `intent.die = True`
  - `AMove`: evaluate the direction expression, store in `intent.move_dir`. If the result is `STAY`, leave `move_dir` as None
  - `ASet`: evaluate the value expression. Use the analyzer-attached annotation on the AST node (cell vs agent) to dispatch to either `intent.cell_field_deposits[name]` or `intent.agent_field_writes[name]`
  - `ASpawn`: append the type name to `intent.spawn_types`
  - `AKill`: append the type name to `intent.kill_targets`
  - `ASeq`: run sub-actions sequentially against the same intent record
  - `AIf`: evaluate condition, run chosen branch
  - `AMatch`: like expression match but body is an action; same nested-match restriction
- **Within-action visibility for agent fields:** when `set` writes to an agent field, also update a local view of the agent so subsequent reads via `self.field` in the same `seq` see the new value. Implement this with a copy-on-write `AgentView` wrapper around the original `AgentRecord`. The original is only mutated at intent application time
- **Cell-field deposits do NOT update the local view** — they only apply at intent application time. A subsequent `cell_field` read in the same action sees the pre-tick value
- Write ≥10 unit tests in `tests/unit/test_eval_action.py`

**Dependencies:** SWARMLET-011, SWARMLET-014

**Expected result:**
A complete action evaluator that builds intent records correctly, with the documented within-action visibility semantics for agent fields.

**Acceptance criteria:**
- [ ] 10+ unit tests passing covering each action form
- [ ] **Critical test:** `seq { set energy = self.energy - 1; if self.energy <= 0 then die else stay }` correctly triggers `die` when starting energy was 1
- [ ] Cell-field deposits do not affect within-action `cell_field` reads in the same `seq`
- [ ] Spawn intents accumulate in the list (multiple spawns in one action are all queued)
- [ ] Action `match` with a non-matching scrutinee and no wildcard raises `SwarmletRuntimeError`

---

### SWARMLET-016 — Engine: cell phase tick

**Description:**
Implement the cell phase of `World.step()`. For every cell, evaluate the matching cell rule against the current snapshot and write the result into a fresh next snapshot. After all cells are processed, swap atomically.

**What needs to be done:**
- For each cell `(x, y)` in the grid:
  - Look up the rule for the cell's current state. Fall back to wildcard `_` rule if no specific rule. If no rule at all, copy the cell unchanged
  - Build an `EvalContext` with `cell_xy=(x, y)`, no agent, no intent, snapshot pointing at the **current** state (NOT the new one being built)
  - Evaluate the cell body. If it is a plain expression (`CellExpr`), the result is the new state. If it is a `seq` block (`CellSeq`), walk the statements and accumulate `become` and `set` writes into a small local intent
- Write all results into a fresh `next_states` array and `next_fields` dict. Swap atomically at the end of the phase
- Cell iteration order is irrelevant because all reads come from the current snapshot — tests should verify this
- Write ≥6 unit tests in `tests/unit/test_engine_cell_phase.py`

**Dependencies:** SWARMLET-013

**Expected result:**
The cell phase of the tick is fully implemented. Forest fire can run for arbitrary numbers of ticks (only the cell phase is needed since it has no agents).

**Acceptance criteria:**
- [ ] 6+ unit tests passing
- [ ] One tick of a hand-built forest fire 5×5 grid produces the hand-computed expected next state
- [ ] Synchronous semantics test: a rule that copies the neighbor's state should produce the same result regardless of cell iteration order (verified by running with two different orders)
- [ ] Field update test: `set pheromone = field pheromone * 0.5` halves every cell's pheromone
- [ ] Wildcard cell rule fires for every cell when no specific rule matches
- [ ] Specific rule wins over wildcard when both are declared

---

### SWARMLET-017 — Engine: agent phase with conflict resolution

**Description:**
Implement the agent phase of `World.step()` — the most complex single piece of the engine. Collect intents from all agents, then apply them in the strict order specified in `SPEC.md` section 2.3, with movement conflict resolution and the documented kill-quirk.

**What needs to be done:**
- Shuffle the agent list using `self.rng` (deterministic given seed)
- For each agent, build an `EvalContext` with `agent=<this agent>`, `cell_xy=<agent position>`, snapshot pointing at the post-cell-phase state, and evaluate the rule against a fresh `Intent`
- Collect all intents in a list
- Apply intents in this exact order (per `SPEC.md` section 2.3):
  1. **Movement conflicts:** group movement intents by target cell. For each target with multiple claimants, pick one uniformly at random via `self.rng`; the rest get `stay`
  2. Apply movements: update each winning agent's position
  3. Apply agent field writes from intents
  4. Apply cell field deposits: for each `(cell, field)` pair, sum all deposits and add to the existing field value
  5. Apply kill intents: for each kill, find one target of the requested type co-located with the killer (random pick if multiple). If two killers target the same victim, only one succeeds and the other's kill is silently dropped, **but its energy gain (computed earlier in its action body) is NOT undone**. This is the documented quirk from the spec
  6. Apply spawn intents: queue new agents with default fields, assign new IDs from `next_agent_id`. They will appear in the agent list at the start of the next tick
  7. Apply death intents (and the kill targets from step 5). Remove from agent list
- Increment `self.t`
- Implement `World.step(n=1)` to call `_cell_phase()` then `_agent_phase()` in sequence, repeating `n` times
- Write ≥10 unit tests in `tests/unit/test_engine_agent_phase.py`

**Dependencies:** SWARMLET-015, SWARMLET-016

**Expected result:**
The full tick is implemented. Any of the five reference example sources can be loaded into a `World` and stepped for N ticks without errors.

**Acceptance criteria:**
- [ ] 10+ unit tests covering: single agent moving, two agents moving to same cell (conflict resolution), spawn, die, kill with one target, kill with conflict between two killers, cell field deposit accumulation across multiple agents, spawned agent does not act on the same tick it was created, killed agent is gone next tick
- [ ] `World.step(100)` runs 100 cell + agent phases without errors on a small predator-prey world
- [ ] Determinism: two World instances with the same seed produce identical agent positions after 100 steps
- [ ] After the cell phase, the snapshot the agent phase reads has the new cell states (cell phase result is the input to agent phase)

---

## Phase 6 — Frontend

### SWARMLET-018 — Snapshot serialization (JSONL and NPZ)

**Description:**
Implement two snapshot serialization formats: line-delimited JSON for streaming and inspection, and compressed numpy archives for efficient storage of large runs.

**What needs to be done:**
- In `swarmlet/snapshot.py`, implement `write_jsonl(world, path, ticks, every=1)`:
  - Open the file once, append one snapshot per line by calling `world.to_json()` and `json.dumps`
  - Step the world `every` ticks between writes
  - Stop after `ticks` total ticks
- Implement `write_npz(world, path, ticks, every=1)`:
  - Build a dict of arrays: one entry per snapshot named `t000000`, `t000001`, ... storing the `states` array, plus one entry per field named `<field_name>_t000000`, `<field_name>_t000001`, ...
  - Agent list serialized as a JSON string in a side entry `agents_t000000`, `agents_t000001`, ...
  - Save with `numpy.savez_compressed`
- Both functions accept an optional `progress` callback for long runs
- Write ≥4 unit tests in `tests/unit/test_snapshot.py`. Round-trip test: write JSONL, read it back, verify the parsed snapshots match

**Dependencies:** SWARMLET-012

**Expected result:**
Two working serialization formats. Snapshots can be saved during a run and re-loaded for inspection or replay.

**Acceptance criteria:**
- [ ] 4+ unit tests passing
- [ ] Round-trip test: write 10 snapshots to JSONL, read them back, verify each parses and has the expected `t` and `states` shape
- [ ] NPZ archive contains the expected number of entries
- [ ] `--every 10` correctly thins the output

---

### SWARMLET-019 — CLI: run and check commands

**Description:**
Implement the `swarmlet` command-line interface with the `run` and `check` subcommands, plus `--param` overrides.

**What needs to be done:**
- In `swarmlet/cli.py`, implement `main()` using `argparse`
- Subcommands:
  - `swarmlet run <file> [--ticks N] [--seed N] [--out PATH] [--every N] [--param KEY=VALUE]...`
  - `swarmlet check <file>` — parse and analyze, no run
  - `swarmlet version` — print version
- `--param` parsing: split on `=`, convert value to float. Multiple `--param` flags accumulate into a dict
- `--out` dispatch by extension: `.jsonl` calls `write_jsonl`, `.npz` calls `write_npz`. Other extensions are an error
- `--ticks` defaults to 100, `--seed` defaults to 0, `--every` defaults to 1
- Print summary at the end of `run`: tick count, elapsed seconds, agent counts by type, snapshot count written
- `swarmlet check` exits 0 on a valid file, 1 on a broken file (after printing all static errors)
- Catch `SwarmletStaticError` and `SwarmletRuntimeError` at the top level and print human-readable messages
- Write ≥4 integration tests in `tests/integration/test_cli.py`

**Dependencies:** SWARMLET-017, SWARMLET-018

**Expected result:**
A fully functional CLI that runs swarmlet programs from the command line and saves snapshots in either format.

**Acceptance criteria:**
- [ ] 4+ integration tests passing
- [ ] `swarmlet run swarmlet/examples/forest_fire.swl --ticks 100 --seed 42 --out /tmp/ff.jsonl` produces a valid JSONL with 100 lines
- [ ] `swarmlet run swarmlet/examples/gray_scott.swl --ticks 100 --seed 42 --out /tmp/gs.npz` produces an NPZ file
- [ ] `swarmlet check swarmlet/examples/forest_fire.swl` exits 0
- [ ] `swarmlet check broken.swl` exits 1 with a clear error
- [ ] `swarmlet run gray_scott.swl --param feed=0.055 --param kill=0.062` runs with the overridden params and the summary reflects the new values
- [ ] Summary line at the end includes elapsed seconds and agent counts

---

## Phase 7 — Examples

### SWARMLET-020 — Example: forest fire

**Description:**
Author `swarmlet/examples/forest_fire.swl` (Drossel-Schwabl model) and its acceptance test. This is the simplest example — pure CA, no agents — and serves as the smoke test for the entire pipeline.

**What needs to be done:**
- Create `swarmlet/examples/forest_fire.swl` with the exact source from `SPEC.md` section 11.1
- Write `tests/integration/test_forest_fire.py` that:
  - Loads the file with seed=42 via `swarmlet.load`
  - Steps 1000 ticks
  - Takes a snapshot
  - Asserts all four states (`Empty`, `Tree`, `Fire`, `Ash`) are present in non-trivial proportions: each between 1% and 90% of cells
  - Times the run; emits a warning (not failure) if it exceeds 5 seconds
- Also produce `swarmlet/examples/forest_fire.expected.txt` by running `swarmlet run forest_fire.swl --ticks 100 --seed 42` and capturing stdout (the summary line, not the full snapshot stream). Add a CLI integration test that asserts the output matches

**Dependencies:** SWARMLET-019

**Expected result:**
Forest fire runs end-to-end and produces sensible aggregate statistics. This is the milestone where the engine is demonstrably working.

**Acceptance criteria:**
- [ ] `swarmlet run swarmlet/examples/forest_fire.swl --ticks 1000 --seed 42` runs without errors
- [ ] All four states present in non-trivial proportions after 1000 ticks
- [ ] Performance under 5 seconds for 1000 ticks
- [ ] CLI integration test passes
- [ ] `forest_fire.expected.txt` matches actual output

---

### SWARMLET-021 — Example: ant foraging

**Description:**
Author `swarmlet/examples/ants.swl` (ant colony optimization with stigmergy via a pheromone field) and its acceptance test.

**What needs to be done:**
- Create `swarmlet/examples/ants.swl` with the exact source from `SPEC.md` section 11.2
- Write `tests/integration/test_ants.py` that:
  - Loads with seed=42, steps 200 ticks
  - Asserts the `pheromone` field has variance > 0 (ants are depositing)
  - Asserts total field mass > 0 but bounded (evaporation is working)
  - Steps 300 more ticks (total 500), asserts at least 5% of ants have `carrying == 1` (some have found food)
  - Time warning if > 30 seconds for 1000 ticks
- Produce `ants.expected.txt` (CLI summary line only) and a CLI integration test

**Dependencies:** SWARMLET-020

**Expected result:**
Ant foraging runs end-to-end with the expected emergent stigmergy pattern.

**Acceptance criteria:**
- [ ] `swarmlet run swarmlet/examples/ants.swl --ticks 1000 --seed 42` runs without errors
- [ ] After 200 ticks, pheromone variance > 0 and total mass bounded
- [ ] After 500 ticks, ≥ 5% of ants are carrying food
- [ ] Performance under 30 seconds for 1000 ticks
- [ ] CLI integration test passes

---

### SWARMLET-022 — Example: Boids on grid

**Description:**
Author `swarmlet/examples/boids.swl` (discrete Boids with separation and alignment) and its acceptance test.

**What needs to be done:**
- Create `swarmlet/examples/boids.swl` with the exact source from `SPEC.md` section 11.3
- Write `tests/integration/test_boids.py` that:
  - Loads with seed=42, steps 500 ticks
  - Computes a heading histogram across all birds at tick 500
  - Asserts the variance of the histogram is below the uniform-baseline variance (alignment causes flocking)
  - Computes the average pairwise Chebyshev distance across all bird pairs
  - Asserts average distance > 1.5 (separation prevents collapse)
- Produce `boids.expected.txt` and CLI integration test

**Dependencies:** SWARMLET-020

**Expected result:**
Boids exhibit emergent flocking behavior in the snapshot statistics: alignment is visible as non-uniform headings, separation is visible as non-collapsed positions.

**Acceptance criteria:**
- [ ] `swarmlet run swarmlet/examples/boids.swl --ticks 500 --seed 42` runs without errors
- [ ] Heading histogram variance below uniform baseline at tick 500
- [ ] Average pairwise Chebyshev distance > 1.5 at tick 500
- [ ] CLI integration test passes

---

### SWARMLET-023 — Example: predator-prey (wolf-sheep)

**Description:**
Author `swarmlet/examples/wolf_sheep.swl` (Lotka–Volterra with explicit kills) and its acceptance test. This is the most feature-rich example, exercising `kill`, `spawn`, `die`, multiple agent types, and indirect cell mutation via the `grass_age` timer.

**What needs to be done:**
- Create `swarmlet/examples/wolf_sheep.swl` with the exact source from `SPEC.md` section 11.4
- Write `tests/integration/test_wolf_sheep.py` that:
  - Loads with seed=42, records sheep and wolf populations at every tick for 500 ticks
  - Asserts both species are still alive at tick 500 (population > 0)
  - Asserts at least one full Lotka–Volterra oscillation occurred: the sheep population time series has at least one local maximum and one local minimum within the first 500 ticks
  - The acceptance check is intentionally loose because exact populations depend heavily on the seed — what we want is that the model is qualitatively correct, not numerically reproducible across implementations
- Produce `wolf_sheep.expected.txt` and CLI integration test

**Dependencies:** SWARMLET-020

**Expected result:**
Wolf-sheep predator-prey dynamics demonstrate the documented kill mechanic and produce the characteristic Lotka–Volterra oscillation pattern.

**Acceptance criteria:**
- [ ] `swarmlet run swarmlet/examples/wolf_sheep.swl --ticks 500 --seed 42` runs without errors
- [ ] Both species alive at tick 500
- [ ] Sheep population has at least one local max and one local min in the first 500 ticks
- [ ] Wolves successfully kill sheep (verified by tracking deaths vs starvations)
- [ ] CLI integration test passes

---

### SWARMLET-024 — Example: Gray-Scott reaction-diffusion with vectorized laplacian

**Description:**
Author `swarmlet/examples/gray_scott.swl` (Gray-Scott reaction-diffusion) and its acceptance test. This issue also implements the **vectorized laplacian fast path** that is required for Gray-Scott to run in a reasonable time on a 200×200 grid — without the fast path, pure-Python per-cell evaluation is unusably slow for this example.

**What needs to be done:**
- Create `swarmlet/examples/gray_scott.swl` with the exact source from `SPEC.md` section 11.5
- **Performance optimization (vectorized laplacian fast path):**
  - In `swarmlet/builtins.py`, add a per-tick cache for the Laplacian of each declared field
  - At the start of each cell phase, when the engine begins iterating over cells for a wildcard rule that uses `laplacian`, pre-compute the Laplacian of the entire field once using a single numpy convolution with the 9-point stencil
  - Cache lookups: `laplacian(name)` first checks the per-tick cache and returns the cached value at the current cell; falls back to the slow per-cell path otherwise
  - The fast path applies when the cell rule is `let cell _ = ...` (wildcard, no per-state branching)
  - Reset the cache at the start of every tick
  - Add a comment in the code explaining why this optimization exists and what it does
- Write `tests/integration/test_gray_scott.py` that:
  - Loads with seed=42, steps 5000 ticks
  - Asserts variance of the `v` field > 0.01 (pattern has formed)
  - Asserts there exist nonzero `v` values outside the original 10×10 seed region (the pattern has spread)
  - Performance target: 5000 ticks in under 5 minutes (the 60-second target in the spec is for 1000 ticks)
- Produce `gray_scott.expected.txt` and CLI integration test

**Dependencies:** SWARMLET-020, SWARMLET-013

**Expected result:**
Gray-Scott reaction-diffusion runs at acceptable speed and produces visible patterns. The vectorized laplacian fast path is the only optimization required by v0.1; the rest of the engine remains pure-Python per-cell evaluation.

**Acceptance criteria:**
- [ ] `swarmlet run swarmlet/examples/gray_scott.swl --ticks 5000 --seed 42` runs without errors
- [ ] `v` field variance > 0.01 after 5000 ticks
- [ ] Nonzero `v` values exist outside the original 10×10 seed region
- [ ] 5000 ticks complete in under 5 minutes on a typical laptop
- [ ] Vectorized laplacian fast path is implemented and used (verified by a unit test that times a single tick with and without the optimization)
- [ ] Slow per-cell `laplacian` path still works as a fallback (verified by a unit test on a small grid using a non-wildcard rule)

---

## Phase 8 — Quality

### SWARMLET-025 — Determinism harness and regression tests

**Description:**
Add a determinism regression test that verifies two `World` instances with the same program and same seed produce byte-identical snapshot sequences. This is the safety net against any future change accidentally introducing nondeterminism.

**What needs to be done:**
- Create `tests/integration/test_determinism.py`
- For each of the five reference example files:
  - Construct two `World` instances with seed=42
  - Step both 100 times
  - Hash each snapshot's `states` array and serialized agent list using a stable hash (e.g., `hashlib.sha256` on a deterministic byte representation)
  - Assert the two hash sequences are identical
- Also test that seed=42 vs seed=43 produce **different** hash sequences (sanity check that the seed actually affects RNG)
- Run with `pytest -x` to catch the first failing example
- Document the test in the README under "Testing" so future contributors know it exists and what it guards against

**Dependencies:** SWARMLET-020, SWARMLET-021, SWARMLET-022, SWARMLET-023, SWARMLET-024

**Expected result:**
A regression test that runs on every CI build to catch nondeterminism bugs. Any future change that introduces unseeded randomness will be caught immediately.

**Acceptance criteria:**
- [ ] Test file exists and passes for all five examples
- [ ] Two seed=42 runs produce identical hash sequences
- [ ] Seed=42 vs seed=43 runs produce different hash sequences
- [ ] Test runs in under 60 seconds total
- [ ] README mentions the determinism test under a "Testing" or "CI" section

---

## Phase 9 — Documentation

### SWARMLET-026 — Documentation and polish

**Description:**
Write the user-facing documentation that completes the project: an expanded README with installation and quickstart, an API reference, and a five-minute walkthrough.

**What needs to be done:**
- Expand `README.md` with:
  - One-paragraph project description from `SPEC.md` section 1
  - Installation: `pip install -e .`
  - Quickstart: a 3-line example showing how to run forest fire and inspect the output
  - Link to `SPEC.md` for the full language specification
  - Link to `docs/quickstart.md` for the walkthrough
  - Mention that the visualizer is a separate package (not yet implemented)
  - Link to the determinism test as a CI guarantee
- Create `docs/quickstart.md` with a 5-minute walkthrough:
  - Install
  - Run forest fire example
  - Open the JSONL output and inspect a snapshot
  - Modify a parameter via `--param`
  - Rerun and observe the difference
- Create `docs/api.md` documenting:
  - `swarmlet.load(path, seed, params=None) -> World`
  - `World.step(n=1)`, `World.snapshot()`, `World.to_json()`, `World.reset(seed=None)`
  - `World.t`, `World.params` attributes
  - The snapshot dict structure from `SPEC.md` section 9.1
  - The exception types `SwarmletStaticError` and `SwarmletRuntimeError`
- All docs in English
- Cross-link between docs

**Dependencies:** SWARMLET-019, SWARMLET-020, SWARMLET-021, SWARMLET-022, SWARMLET-023, SWARMLET-024

**Expected result:**
Complete user-facing documentation. A new user can go from `git clone` to running their first modified example in under 10 minutes by following the README and quickstart.

**Acceptance criteria:**
- [ ] `README.md` includes installation, quickstart, links to spec and quickstart, mention of visualizer-as-separate-package, mention of determinism test
- [ ] `docs/quickstart.md` walkthrough runs successfully as documented (verified by manual run)
- [ ] `docs/api.md` covers every public API surface
- [ ] All cross-links work in local markdown preview
- [ ] No broken links

---

## Stage 1 scope notes

**Total effort:** ~10–14 working days sequentially, or ~7–10 days with parallelization (parser/lexer block and built-ins block can overlap; example issues SWARMLET-021, SWARMLET-022, SWARMLET-023 are independent).

**Hard prerequisites for Stage 1:**
- Python 3.11+
- `numpy` (runtime), `pytest`, `pytest-cov` (dev)
- Reading `SPEC.md` end-to-end before starting SWARMLET-001

**Files created during Stage 1:**
- `pyproject.toml`, `README.md`, `.gitignore`
- `swarmlet/` package: `__init__.py`, `lexer.py`, `parser.py`, `ast.py`, `analyzer.py`, `eval.py`, `engine.py`, `builtins.py`, `snapshot.py`, `cli.py`
- `swarmlet/examples/`: `forest_fire.swl`, `ants.swl`, `boids.swl`, `wolf_sheep.swl`, `gray_scott.swl`, plus matching `.expected.txt` files
- `tests/unit/` with one test file per module
- `tests/integration/` with one test file per example plus the determinism test
- `docs/quickstart.md`, `docs/api.md`

**Files NOT touched by Stage 1 (deferred to future stages):**
- Visualizer package (separate stage, separate repo)
- Any deployment to physical robots (Protelis/ScaFi territory, not Swarmlet's)
- Any v0.2 features listed in `SPEC.md` section 14 non-goals

**Critical correctness gates:**
- Within-action visibility for agent fields (SWARMLET-015 — get this right or Boids will be subtly wrong)
- Determinism via seeded RNG (SWARMLET-025 — the regression net)
- Vectorized laplacian fast path (SWARMLET-024 — without this Gray-Scott is unusable)
- All randomness through `ctx.rng`, never through global `random` or `np.random`

**Critical design gates:**
- Nested match must be parenthesized (SWARMLET-006 — clear error message, not a parser crash)
- Set-dispatch in agent actions (SWARMLET-010 — annotated by analyzer, used by evaluator)
- Two-phase tick: cell phase reads from current snapshot, agent phase reads from post-cell snapshot (SWARMLET-016, SWARMLET-017)
- Conflict resolution order is exactly as in `SPEC.md` section 2.3 (SWARMLET-017)

**Companion document:** `SPEC.md` (the language specification). Every section reference in this document points there. If a behavior is unclear, the spec is the source of truth — not this issues document.

**After Stage 1 is merged,** Swarmlet has a working interpreter for all five reference examples, a deterministic CLI for batch runs, snapshot serialization for downstream consumers, and a regression test suite that prevents nondeterminism. Stage 2 (visualizer, v0.2 features, geometry-extension built-ins) can begin.
