# Swarmlet v0.1 — Language Specification

**Status:** Final draft, ready for implementation
**Audience:** language designer (Vitalii), Claude Code (implementation)
**Scope:** v0.1 minimal viable language. Non-goals are listed explicitly in section 14.

---

## 1. Overview

Swarmlet is a small functional language for simulating **cellular automata and agent-based swarms on a 2D grid**. A Swarmlet program declaratively describes:

- a **world** (grid dimensions, topology),
- **cell states** and optional **cell fields** (continuous scalar layers),
- **agent types** with their own fields,
- **rules** that compute, at each tick, the next state of every cell and the next action of every agent,
- **initialization** of cells, fields, and initial agent populations.

Rules are pure functions of the current world snapshot. The runtime executes ticks deterministically (given a seed) by reading from a snapshot and writing into a fresh next snapshot.

The interpreter is a **pure engine**. It does not draw anything. It exposes the world state as a structured object (numpy-compatible arrays + agent records) and as JSON snapshots. Visualization, recording, and integration with external simulators are separate consumers of this state.

### 1.1 Influences

Swarmlet borrows its **conceptual world model** from NetLogo (turtles + patches, neighborhoods, two-phase ticks, toroidal default), its **syntax** from the OCaml/ML family (`let`, `match ... with | ... ->`, `when` guards), and its **field operator vocabulary** from Protelis and the field calculus tradition (`gradient_to`, `distance_to`, `min_in_radius`, `laplacian`). See section 15 for related work.

The design philosophy is "the smallest language that lets you write Boids, ants, predator-prey, reaction-diffusion, and forest fire elegantly, and nothing more."

---

## 2. Execution model

### 2.1 World

A Swarmlet world is a 2D grid of size `W x H`. Topology is either:

- `wrap` — toroidal (default),
- `bounded` — out-of-bounds neighbors are treated as a special `Void` state.

Each cell has:

- a **discrete state** (one symbol from the user-declared cell-state enum),
- zero or more **float fields**, declared globally and present on every cell.

Coordinates are integer `(x, y)` with `x ∈ [0, W)` (column) and `y ∈ [0, H)` (row). Origin is top-left.

### 2.2 Agents

An agent is a typed entity with:

- integer position `(x, y)` on the grid,
- user-declared fields (numbers),
- an optional `heading` field (integer 0..7, encoding the 8 Moore directions clockwise starting from East = 0), enabling forward-relative actions (`forward`, `left`, `right`, `back`).

Multiple agents may occupy the same cell. There is no built-in exclusion in v0.1.

### 2.3 Tick

One tick consists of two phases, executed strictly in order:

1. **Cell phase.** For every cell in the grid, the runtime evaluates the matching `let cell` rule against the current world snapshot and produces a new cell state and new field values. All updates are written into a fresh snapshot. Cell rules cannot see updates from this same tick.

2. **Agent phase.** For every agent (in randomized order, but deterministic given the seed), the runtime evaluates the matching `let agent` rule against the world snapshot produced by the cell phase. Each agent rule produces an **intent record** describing what the agent wants to do. All intents are collected, then **applied atomically** with conflict resolution.

Conflict resolution rules, applied in this exact order:

1. **Movement conflicts.** If multiple agents intend to move into the same cell, one is chosen uniformly at random (deterministic given seed); the others execute `stay` instead.
2. **Movements applied.**
3. **Agent field writes applied.**
4. **Cell field deposits applied.** Multiple agents writing to the same cell field accumulate by **summation** (this is the natural semantics for pheromone deposits).
5. **Kill intents applied.** Each `kill T` intent removes one agent of type `T` co-located with the killer (chosen uniformly at random if multiple). If two agents both attempt to kill the same target, one succeeds and the other's `kill` is silently dropped (but its energy gain, computed earlier in its action body, is NOT undone — see section 12.4 for the documented quirk).
6. **Spawn intents applied.** New agents are queued and start acting on the next tick. They receive the **default field values** declared on the agent type. There is no inheritance from the parent in v0.1.
7. **Death intents applied.**

### 2.4 Determinism

Given a fixed RNG seed and the same program, two runs must produce identical sequences of snapshots. All randomness flows through the interpreter's seeded RNG. Iteration order over agents is shuffled per tick using the same seeded RNG.

### 2.5 Neighborhoods

Built-in neighborhood selectors:

- `moore` — the 8 surrounding cells (default for cell rules)
- `neumann` — the 4 orthogonal neighbors
- `radius r` — all cells within Chebyshev distance `r` (excluding self)

Neighborhoods respect the world topology (toroidal or bounded).

---

## 3. Lexical structure

### 3.1 Source encoding

UTF-8. Line endings are insignificant. Indentation is insignificant — the language is delimited by keywords and braces, not by layout.

### 3.2 Comments

`#` to end of line. No block comments in v0.1.

### 3.3 Identifiers

`[A-Za-z_][A-Za-z0-9_]*`. State names conventionally start with an uppercase letter (`Tree`, `Empty`, `Sheep`); field and variable names with lowercase (`pheromone`, `carrying`). This is convention, not enforced — the parser disambiguates by declaration context.

### 3.4 Literals

- Integer: `42`, `0`
- Float: `3.14`, `0.001`
- Boolean: `true`, `false`

### 3.5 Reserved keywords

```
world cell states field agent let init param
match with when
if then else in
move stay set become spawn die kill seq
true false wrap bounded
and or not mod
moore neumann radius
forward back left right
```

### 3.6 Operators

```
+  -  *  /
==  !=  <  <=  >  >=
->  =  |  ,  ;  :  .
( )  { }
```

Operator precedence, lowest to highest:

1. `or`
2. `and`
3. `not`
4. `==`, `!=`, `<`, `<=`, `>`, `>=`
5. `+`, `-`
6. `*`, `/`, `mod`
7. unary `-`
8. function application, field access (`.`)

Function application is whitespace-separated, OCaml-style: `count Tree`, `look 1 0`, `radius 3`. Parentheses are used only for grouping and for unit `()`. Field access uses dot: `self.heading`.

---

## 4. Grammar (EBNF)

```
program     ::= decl+

decl        ::= world_decl
              | states_decl
              | field_decl
              | agent_decl
              | param_decl
              | cell_rule
              | agent_rule
              | init_decl

world_decl  ::= "world" NUMBER "x" NUMBER ("wrap" | "bounded")?

states_decl ::= "cell" "states" IDENT ("|" IDENT)+

field_decl  ::= "field" IDENT "=" const_expr
                                                # default value, must be constant

param_decl  ::= "param" IDENT "=" const_expr
                                                # named numeric constant, can be overridden via API

agent_decl  ::= "agent" IDENT "{" agent_fields? "}"
agent_fields::= agent_field ("," agent_field)*
agent_field ::= IDENT "=" const_expr

cell_rule   ::= "let" "cell" cell_pattern "=" cell_body
cell_pattern::= IDENT | "_"                     # state name or wildcard
cell_body   ::= expr                            # must evaluate to a state name
              | "seq" "{" cell_stmt (";" cell_stmt)* "}"
cell_stmt   ::= "become" expr
              | "set" IDENT "=" expr            # set cell field

agent_rule  ::= "let" "agent" IDENT "=" action

init_decl   ::= "init" "cell" "=" expr          # called once per cell at t=0
              | "init" "field" IDENT "=" expr   # called once per cell at t=0; expr -> float
              | "init" "agent" IDENT NUMBER     # spawn N agents at random cells

# expressions
expr        ::= match_expr | if_expr | let_expr | or_expr

match_expr  ::= "match" expr "with" match_case+
match_case  ::= "|" pattern_alts ("when" expr)? "->" expr
pattern_alts::= pattern ("|" pattern)*
pattern     ::= IDENT | NUMBER | "true" | "false" | "_"

if_expr     ::= "if" expr "then" expr "else" expr
let_expr    ::= "let" IDENT "=" expr "in" expr

or_expr     ::= and_expr ("or" and_expr)*
and_expr    ::= not_expr ("and" not_expr)*
not_expr    ::= "not" not_expr | cmp_expr
cmp_expr    ::= add_expr (cmp_op add_expr)?
add_expr    ::= mul_expr (("+"|"-") mul_expr)*
mul_expr    ::= unary (("*"|"/"|"mod") unary)*
unary       ::= "-" unary | app_expr
app_expr    ::= postfix postfix*                # left-assoc whitespace application
postfix     ::= atom ("." IDENT)*
atom        ::= NUMBER
              | "true" | "false"
              | "(" ")"                          # unit
              | "(" expr ")"                     # grouping (also REQUIRED to nest a match)
              | IDENT

# actions (agent rules only)
action      ::= "stay"
              | "die"
              | "move" expr                      # expr -> direction
              | "set" IDENT "=" expr             # set agent field OR cell field
              | "spawn" IDENT
              | "kill" IDENT                     # kill one co-located agent of type IDENT
              | "seq" "{" action (";" action)* "}"
              | "if" expr "then" action "else" action
              | "match" expr "with" action_case+
action_case ::= "|" pattern_alts ("when" expr)? "->" action

const_expr  ::= NUMBER | "true" | "false" | "-" NUMBER
```

### 4.1 Notes on the grammar

- **Nested `match` must be parenthesized.** This avoids the classic ML "dangling match" ambiguity. The parser emits a clear error "nested match must be parenthesized" if a bare `match` appears as the body of a case.
- **The leading `|` before the first case is required.** Both for `match_expr` and for `match` actions. This makes the grammar uniform and the visual layout symmetric.
- **`cell_rule` with a state-name pattern matches only cells in that state.** `_` is a catch-all that runs for every cell. If both are present, the more specific rule wins. It is a static error to declare two rules with the same cell pattern.
- **`cell_body` can be a plain expression** (returning a new state symbol — the cell field values are then unchanged) **or a `seq` block** of `become` / `set` statements (allowing field mutation).
- **Declaration order is free.** The recommended order is `world` → `param` → `cell states` → `field` → `agent` → `let` → `init`, but the parser accepts any ordering. All references are resolved after parsing in a single semantic pass.
- **`set` in agent actions** dispatches based on the field name: if it matches a declared cell field, it is a deposit on the agent's current cell; if it matches a declared agent field, it writes to the agent. It is a static error if a name matches both, and a static error if it matches neither.

---

## 5. Type system

Swarmlet v0.1 has a small dynamic type system. Values at runtime are tagged as one of:

| Tag | Description |
|---|---|
| `number` | int or float, unified internally as Python `float` for arithmetic |
| `bool` | `true` or `false` |
| `state` | a symbol from the declared cell-state enum |
| `direction` | an integer 0..7 (Moore directions, East=0, clockwise), with a sentinel `STAY` value (-1) |
| `agent_type` | an agent type name, used by built-ins like `agents_of_type_in_radius` and `kill` |
| `void` | the out-of-bounds sentinel, only produced by neighborhood lookups in `bounded` worlds |

There is no `string`, no `list`, no `tuple`, no user-defined type. Pattern matching distinguishes states from numbers from booleans.

Type errors (e.g. comparing a state to a number with `<`) are runtime errors with the offending source line.

---

## 6. Built-in functions

All built-ins are pure functions over the current world snapshot.

### 6.1 Random

| Function | Returns | Description |
|---|---|---|
| `random ()` | float in [0, 1) | uniform |
| `random_int n` | int in [0, n) | uniform |
| `random_dir ()` | direction | uniform Moore direction |

### 6.2 Cell context (in cell rules and `init field` / `init cell`)

These functions implicitly refer to the cell currently being evaluated.

| Function | Returns | Description |
|---|---|---|
| `state` | state | current cell's state |
| `field name` | float | current cell's named field |
| `x` | int | column index of current cell (init context only) |
| `y` | int | row index of current cell (init context only) |
| `count S` | int | number of Moore neighbors in state `S` |
| `count_in S N` | int | number of neighbors in state `S` within neighborhood `N` |
| `any S` | bool | true if at least one Moore neighbor is in state `S` |
| `sum_field name` | float | sum of named field over Moore neighbors |
| `sum_field_in name N` | float | sum over neighborhood `N` |
| `mean_field name` | float | mean over Moore neighbors |
| `max_field name` | float | max over Moore neighbors |
| `min_field name` | float | min over Moore neighbors |
| `laplacian name` | float | discrete Laplacian, 9-point stencil (center -1, orthogonal 0.2, diagonal 0.05) |
| `neighbor dx dy` | state | neighbor at relative offset; respects topology |
| `neighbor_field dx dy name` | float | named field at offset |
| `distance_to S` | int | Chebyshev distance to nearest cell in state `S` within radius 16; returns `-1` if none |
| `gradient_to S` | direction | direction toward nearest cell in state `S` within radius 16; returns `STAY` if none |

### 6.3 Agent context (in agent rules)

These implicitly refer to the agent currently being evaluated. The agent also has dot-access to its declared fields (`self.carrying`, `self.heading`).

| Function | Returns | Description |
|---|---|---|
| `self` | agent | current agent (use with `.field`) |
| `cell_state` | state | state of the cell this agent stands on |
| `cell_field name` | float | a field on the current cell |
| `look dx dy` | state | state of cell at offset from agent |
| `look_field dx dy name` | float | field of cell at offset |
| `argmax_neighbor name` | direction | Moore direction toward neighbor with highest value of `name` |
| `argmin_neighbor name` | direction | symmetric |
| `agents_in_radius r` | int | count of other agents (any type) within Chebyshev distance `r` |
| `agents_of_type_in_radius T r` | int | count of other agents of type `T` within radius `r` |
| `nearest_agent_dir r` | direction | direction toward nearest other agent within `r`, `STAY` if none |
| `nearest_agent_of_type_dir T r` | direction | direction toward nearest agent of type `T` within `r`, `STAY` if none |
| `mean_heading_in_radius r` | direction | mean heading of other agents within `r` (vector-averaged on the unit circle, then quantized to nearest Moore direction); `STAY` if none |
| `min_in_radius name r` | float | min value of cell field `name` over cells within `r` |
| `max_in_radius name r` | float | max value of cell field `name` over cells within `r` |

### 6.4 Math

`abs x`, `min a b`, `max a b`, `sqrt x`, `exp x`, `floor x`, `mod a b`, `clamp x lo hi`.

### 6.5 Direction helpers

- `forward`, `back`, `left`, `right` are valid only in agent rules and only when the agent has a `heading` field. They evaluate to the absolute Moore direction relative to the current heading.
- `dir dx dy` constructs an absolute direction from a small offset `(dx, dy) ∈ {-1, 0, 1}²`.
- `STAY` is the sentinel direction meaning "do not move". Using it as the argument of `move` is equivalent to writing `stay` as the action.
- Adding integers to a direction: `(self.heading + 4) mod 8` rotates 180°. Direction arithmetic is implicit integer arithmetic mod 8.

---

## 7. Semantics in detail

### 7.1 Cell rule dispatch

For each cell `c` in the snapshot, the runtime selects exactly one cell rule:

1. If a rule is declared with `let cell <S> = ...` where `<S>` is `c`'s current state, that rule is chosen.
2. Otherwise, if a wildcard rule `let cell _ = ...` exists, it is chosen.
3. Otherwise, the cell is unchanged.

It is a static error to declare two rules with the same cell pattern.

### 7.2 Cell body evaluation

If `cell_body` is a plain expression, it must evaluate to a state symbol; that becomes the new state of the cell. Field values carry over unchanged.

If `cell_body` is a `seq` block, each statement is executed against an intent record:

- `become S` sets the new state.
- `set f = e` sets the new value of cell field `f`.

If `become` is not called, the state is unchanged. Multiple `become` statements: the last one wins. `seq` is sequential in declaration order, not concurrent.

### 7.3 Agent rule evaluation

For each agent `a` (in randomized seeded order), the runtime locates `let agent <T> = ...` where `<T>` is `a`'s type. It evaluates the action, accumulating intents:

- `stay` — no movement intent.
- `die` — death intent.
- `move d` — movement intent toward direction `d`. If `d` is `STAY`, no movement.
- `set f = e` — field-write intent on agent `a`, or cell-field deposit if `f` is a cell field (dispatched by name).
- `spawn T` — spawn intent: a new agent of type `T` at the current agent's cell.
- `kill T` — intent to remove one agent of type `T` co-located with this agent.
- `seq` runs sub-actions in order against the same intent record.
- `if cond then a else b` evaluates `cond` and runs the chosen branch.
- `match e with | ... -> action | ...` is the action-level analog of expression `match`.

After all agents have produced intents, the runtime applies them per the order in section 2.3.

**Within-action visibility:** within a single agent's action, `set` writes to the agent's own fields are visible to subsequent reads in the same `seq` block (the intent record is also a local view). This means:

```
seq {
  set energy = self.energy - 1;
  if self.energy <= 0 then die else stay
}
```

works correctly — the second statement sees the decremented energy. Without this, `seq` would be useless. Cell-field deposits, however, are NOT visible within the same action — they only apply after intents are collected.

### 7.4 Pattern matching semantics

`match e with | p1 when g1 -> b1 | p2 -> b2 | _ -> b3` evaluates `e`, then tries each case top to bottom. A case matches if its pattern (or any of its or-patterns) matches the value AND its `when` guard (if present) evaluates to true. The body of the first matching case is the result. If no case matches, this is a runtime error — users should always include `_`.

Pattern semantics:

- `_` matches anything.
- A `NUMBER` pattern matches by equality.
- `true` / `false` patterns match the corresponding boolean.
- An `IDENT` pattern matches if the scrutinee is a state symbol with that exact name. **Identifiers in pattern position are always interpreted as state-name literals**, never as variable bindings. There are no variable-binding patterns in v0.1.

This restriction is intentional: it makes patterns unambiguous without a static type pass.

Or-patterns share the body and the guard: `| Tree | Sapling when condition -> body` matches if the value is `Tree` or `Sapling` AND `condition` is true.

### 7.5 `let` scoping

`let x = e1 in e2` evaluates `e1`, binds `x` for the dynamic extent of `e2`. Lexically scoped, no mutation. It is a **static error** to shadow a built-in name. It is allowed to shadow another `let` binding in an outer scope.

### 7.6 Nested match must be parenthesized

```
# WRONG — parser error
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false ->
      match random () with
      | p when p < 0.0001 -> Fire
      | _ -> Tree

# RIGHT
let cell Tree =
  match any Fire with
  | true  -> Fire
  | false ->
      (match random () with
       | p when p < 0.0001 -> Fire
       | _ -> Tree)

# IDIOMATIC (flatten with let)
let cell Tree =
  let spark = random () < 0.0001 in
  if any Fire then Fire
  else if spark then Fire
  else Tree
```

The third form is the recommended Swarmlet idiom.

---

## 8. Initialization

`init cell = expr` is evaluated once per cell at t=0. The expression must return a state symbol. `x` and `y` are bound to the cell's coordinates inside this expression. If absent, every cell is initialized to the **first** state name in the `cell states` declaration.

`init field <n> = expr` is evaluated once per cell at t=0. The expression must return a float, which becomes the initial value of that field at this cell. `x` and `y` are bound. If absent, fields use their declared default everywhere.

`init agent T N` spawns `N` agents of type `T` at uniformly random cells. Their fields are initialized to declared defaults. If multiple `init agent T N` declarations exist for the same `T`, the counts are summed.

---

## 9. Engine API (Python embedding)

The interpreter is delivered as a Python package `swarmlet`. Public surface:

```python
from swarmlet import load

world = load("forest_fire.swl", seed=42)
# Optionally override params declared with `param`:
world = load("gray_scott.swl", seed=42, params={"feed": 0.055, "kill": 0.062})

world.step()                  # one tick
world.step(n=100)             # n ticks
snap = world.snapshot()       # see structure below
world.to_json()               # JSON-serializable dict for the same snapshot
world.reset(seed=43)          # back to t=0 with a new seed
world.t                       # current tick count (read-only)
world.params                  # dict of current param values (read-only)
```

### 9.1 Snapshot structure

```python
{
    "t": int,                                    # tick number
    "world": {"w": int, "h": int, "wrap": bool},
    "states": ndarray[H, W],                     # int8, indices into states_legend
    "states_legend": ["Empty", "Tree", "Fire", "Ash"],
    "fields": {                                  # name -> float32 array
        "pheromone": ndarray[H, W],
    },
    "agents": [
        {"type": "Ant", "id": 17, "x": 12, "y": 34, "carrying": 0, "heading": 3},
        ...
    ],
}
```

The snapshot is the **only** way to observe state. Visualizers, recorders, and external simulators all consume snapshots.

### 9.2 CLI entry point

```
swarmlet run program.swl --ticks 1000 --seed 42 --out snapshots.jsonl
swarmlet run program.swl --ticks 1000 --seed 42 --out frames.npz
swarmlet run program.swl --ticks 1000 --seed 42 --param feed=0.055 --param kill=0.062
swarmlet check program.swl                       # parse + semantic check, no run
```

`--out` with `.jsonl` writes one snapshot per line. With `.npz` writes a compressed numpy archive (one entry per tick named `t000000`, `t000001`, …). `--every N` reduces output to every Nth tick.

---

## 10. Errors

**Static (parse / load time):**

- syntax errors with line and column,
- duplicate cell-state names,
- duplicate cell rules for the same state,
- references to undeclared states, fields, agent types, params, or built-ins,
- `let` shadowing a built-in,
- `set f = e` in an agent action where `f` matches both a cell field and an agent field, or matches neither,
- nested `match` without parentheses,
- `forward` / `back` / `left` / `right` used in an agent type without `heading`.

Static errors abort `load` with a `SwarmletStaticError` Python exception listing all errors found.

**Runtime (per-tick):**

- type errors (e.g. comparing a state to a float),
- non-exhaustive `match` (no case matched),
- division by zero,
- `field` lookup with an undeclared name (should be caught statically, but defensive runtime check exists),
- spawning an agent type at an out-of-bounds cell in a `bounded` world.

Runtime errors abort `step` and surface as `SwarmletRuntimeError` with the offending source line and tick number.

---

## 11. Reference examples (source code)

Five reference programs that together exercise every feature in the spec. Each is the **acceptance criterion** for "the language works." Section 12 walks through them line by line.

### 11.1 Forest fire (pure CA, no agents)

```
# Drossel-Schwabl forest fire model.
# Trees grow on empty cells, occasionally ignite, and burn to ash.
# Ash slowly clears back to empty.

world 100 x 100 wrap

cell states Empty | Tree | Fire | Ash

param growth_rate     = 0.001
param ignition_rate   = 0.00005
param ash_clear_rate  = 0.02

let cell Empty =
  let grow = random () < growth_rate in
  if grow then Tree else Empty

let cell Tree =
  let spark = random () < ignition_rate in
  if any Fire then Fire
  else if spark then Fire
  else Tree

let cell Fire = Ash

let cell Ash =
  let clear = random () < ash_clear_rate in
  if clear then Empty else Ash

init cell =
  let r = random () in
  if r < 0.5 then Tree else Empty
```

### 11.2 Ant foraging (agents + stigmergy via fields)

```
# Classic ant colony optimization on a grid.
# Ants wander, find food, return home laying pheromone.
# Other ants follow the pheromone gradient toward food.

world 80 x 80 wrap

cell states Empty | Food | Nest
field pheromone = 0.0

param evaporation = 0.98
param deposit     = 1.0

agent Ant {
  carrying = 0,
  heading  = 0
}

# Pheromone evaporates everywhere on every tick.
let cell _ =
  seq {
    set pheromone = field pheromone * evaporation
  }

let agent Ant =
  seq {
    if cell_state == Food and self.carrying == 0
      then set carrying = 1
      else stay;

    if self.carrying == 1 and cell_state == Nest
      then set carrying = 0
      else stay;

    if self.carrying == 1
      then set pheromone = cell_field pheromone + deposit
      else stay;

    if self.carrying == 0
      then move (argmax_neighbor pheromone)
      else move (random_dir ())
  }

init cell =
  let r = random () in
  if r < 0.02 then Food
  else if r < 0.025 then Nest
  else Empty

init agent Ant 200
```

### 11.3 Boids-on-grid (local coordination via heading averaging)

```
# Discretized Boids: separation and alignment on a grid.
# Cohesion is implicit in the toroidal world.

world 80 x 80 wrap

cell states Empty

param vision          = 3
param crowd_threshold = 5

agent Bird {
  heading = 0
}

let agent Bird =
  let crowd = agents_in_radius vision in
  let avg   = mean_heading_in_radius vision in
  seq {
    # Separation: too many neighbors -> turn 180°
    if crowd > crowd_threshold
      then set heading = (self.heading + 4) mod 8
      else stay;

    # Alignment: align with mean heading of nearby flock
    if crowd > 0 and crowd <= crowd_threshold
      then set heading = avg
      else stay;

    move forward
  }

init cell = Empty
init agent Bird 120
```

### 11.4 Predator-prey (Lotka–Volterra with explicit kills)

```
# Wolves chase and kill sheep. Sheep eat grass and flee from wolves.
# Both reproduce when well-fed and starve when not.

world 100 x 100 wrap

cell states Empty | Grass

field grass_age = 0.0

param grass_regrow_age   = 30.0
param sheep_eat_gain     = 4
param sheep_repro_thresh = 20
param sheep_repro_cost   = 10
param wolf_kill_gain     = 8
param wolf_repro_thresh  = 30
param wolf_repro_cost    = 15
param wolf_vision        = 5
param sheep_vision       = 4

agent Sheep {
  energy = 10
}

agent Wolf {
  energy = 20
}

# Empty cells age toward becoming Grass.
let cell Empty =
  seq {
    set grass_age = field grass_age + 1.0;
    if field grass_age > grass_regrow_age
      then become Grass
      else stay
  }

# Grass cells reset their age (grass is fresh).
let cell Grass =
  seq {
    set grass_age = 0.0
  }

let agent Sheep =
  seq {
    set energy = self.energy - 1;

    if cell_state == Grass
      then set energy = self.energy + sheep_eat_gain
      else stay;

    let wolf_dir   = nearest_agent_of_type_dir Wolf sheep_vision in
    let wolf_count = agents_of_type_in_radius Wolf sheep_vision in
    if wolf_count > 0
      then move ((wolf_dir + 4) mod 8)
      else move (random_dir ());

    if self.energy > sheep_repro_thresh
      then seq { set energy = sheep_repro_cost; spawn Sheep }
      else stay;

    if self.energy <= 0 then die else stay
  }

let agent Wolf =
  seq {
    set energy = self.energy - 1;

    if agents_of_type_in_radius Sheep 0 > 0
      then seq {
             kill Sheep;
             set energy = self.energy + wolf_kill_gain
           }
      else stay;

    let prey_dir   = nearest_agent_of_type_dir Sheep wolf_vision in
    let prey_count = agents_of_type_in_radius Sheep wolf_vision in
    if prey_count > 0
      then move prey_dir
      else move (random_dir ());

    if self.energy > wolf_repro_thresh
      then seq { set energy = wolf_repro_cost; spawn Wolf }
      else stay;

    if self.energy <= 0 then die else stay
  }

init cell =
  let r = random () in
  if r < 0.4 then Grass else Empty

init agent Sheep 200
init agent Wolf 40
```

### 11.5 Reaction-diffusion (Gray-Scott)

```
# Gray-Scott reaction-diffusion. Two chemicals U and V interact
# according to: U + 2V -> 3V, with V decaying at rate F+k.
# Famous patterns: spots, stripes, mitosis, coral.

world 200 x 200 wrap

cell states Solvent

field u = 1.0
field v = 0.0

param Du   = 0.16
param Dv   = 0.08
param feed = 0.060
param kill = 0.062

let cell _ =
  let cu  = field u in
  let cv  = field v in
  let lu  = laplacian u in
  let lv  = laplacian v in
  let uvv = cu * cv * cv in
  let du  = Du * lu - uvv + feed * (1.0 - cu) in
  let dv  = Dv * lv + uvv - (feed + kill) * cv in
  seq {
    set u = clamp (cu + du) 0.0 1.0;
    set v = clamp (cv + dv) 0.0 1.0
  }

# Seed a 10x10 square of V (and reduced U) in the center.
init field v =
  if x > 95 and x < 105 and y > 95 and y < 105
    then 0.5
    else 0.0

init field u =
  if x > 95 and x < 105 and y > 95 and y < 105
    then 0.5
    else 1.0

init cell = Solvent
```

---

## 12. Walkthrough of each example

This section is the **acceptance test description**. If the implementation can run each example for 1000 ticks and produce sensible aggregate statistics, the implementation is correct. Each walkthrough explains what every construct does and which feature of the spec it exercises.

### 12.1 Forest fire walkthrough

```
world 100 x 100 wrap
```
Declares a toroidal 100×100 grid. `wrap` is the default and could be omitted.

```
cell states Empty | Tree | Fire | Ash
```
Four cell states. `Empty` is first, so it would be the default initial state if `init cell` were absent.

```
param growth_rate    = 0.001
param ignition_rate  = 0.00005
param ash_clear_rate = 0.02
```
Three named constants. They behave as constants inside the program but can be overridden when loading: `load("forest_fire.swl", seed=42, params={"growth_rate": 0.005})`. This is the v0.1 way to make models tunable without editing source.

```
let cell Empty =
  let grow = random () < growth_rate in
  if grow then Tree else Empty
```
Cell-rule for `Empty` cells. `let grow = ... in ...` binds a local variable for clarity. `random ()` returns a float in [0, 1). Result is a state symbol.

```
let cell Tree =
  let spark = random () < ignition_rate in
  if any Fire then Fire
  else if spark then Fire
  else Tree
```
The **canonical Swarmlet idiom**: bind random outcomes to locals, then chain `if/else if/else` branching on states and locals. No nested `match`, no parentheses needed.

```
let cell Fire = Ash
```
Single-expression body: every burning cell becomes ash next tick.

```
let cell Ash =
  let clear = random () < ash_clear_rate in
  if clear then Empty else Ash
```
Symmetric to `Empty` rule.

```
init cell =
  let r = random () in
  if r < 0.5 then Tree else Empty
```
Seeds the world: roughly half trees, half empty.

**Features exercised:** `world`, `cell states`, `param`, `let cell` (with state pattern, no wildcard), `let ... in`, `if/else if/else`, `random`, comparison, `any`, `init cell`.

**Acceptance check:** after 1000 ticks with seed=42, all four states should be present in non-trivial proportions (no state is more than 90% or less than 1% of cells). Determinism: two runs with seed=42 produce identical state count histograms.

### 12.2 Ant foraging walkthrough

```
world 80 x 80 wrap

cell states Empty | Food | Nest
field pheromone = 0.0
```
Three states plus a continuous `pheromone` field with default 0.0 everywhere. The field is global — every cell has a pheromone value.

```
param evaporation = 0.98
param deposit     = 1.0
```
Tunable knobs.

```
agent Ant {
  carrying = 0,
  heading  = 0
}
```
One agent type. `heading = 0` enables `forward`/`left`/`right`/`back`.

```
let cell _ =
  seq {
    set pheromone = field pheromone * evaporation
  }
```
A wildcard cell rule — runs for every cell regardless of state. Uses `seq` because we need to write a field value. `field pheromone` reads the current pheromone, multiplied by evaporation, written back. State stays unchanged because there's no `become`.

```
let agent Ant =
  seq {
    if cell_state == Food and self.carrying == 0
      then set carrying = 1
      else stay;
    ...
  }
```
The agent rule body is an action, not an expression. `seq` chains four sub-actions. Each `if ... then ... else stay` is an action. `cell_state` is the state of the cell the ant stands on; `self.carrying` is the ant's own field via dot access.

The four sub-actions in order:

1. **Pick up food** if standing on `Food` empty-handed.
2. **Drop food** if standing on `Nest` while carrying.
3. **Deposit pheromone** on the current cell if carrying — `set pheromone = ...` here is dispatched to the **cell field** because `pheromone` is a declared cell field, not an agent field.
4. **Move**: if not carrying, follow pheromone gradient (`argmax_neighbor pheromone`); if carrying, wander randomly.

This is the classic ACO algorithm in 25 lines.

```
init cell = ...
init agent Ant 200
```
Seed cells (2% food, 0.5% nest, rest empty) and spawn 200 ants at random positions.

**Features exercised:** `field`, `agent` declaration, wildcard `let cell _`, `seq` cell body, `set` on cell field from cell rule, `set` on agent field, `set` on cell field from agent rule (deposit dispatch), `argmax_neighbor`, `random_dir`, action `seq`, action `if/else`, `init agent`.

**Acceptance check:** after 200 ticks with seed=42, the pheromone field should have variance > 0 (ants are depositing) and total mass > 0 but bounded (evaporation works). After 500 ticks, average ant `carrying` should be measurable (some ants are carrying food).

### 12.3 Boids walkthrough

```
agent Bird {
  heading = 0
}
```
One agent type with only a heading. Cells are essentially a coordinate grid (`Empty` is the only state).

```
let agent Bird =
  let crowd = agents_in_radius vision in
  let avg   = mean_heading_in_radius vision in
  seq {
    if crowd > crowd_threshold
      then set heading = (self.heading + 4) mod 8
      else stay;

    if crowd > 0 and crowd <= crowd_threshold
      then set heading = avg
      else stay;

    move forward
  }
```

Two `let` bindings at the start of the action — they read the world once and reuse the values across the three sub-actions. The first sub-action implements **separation** (turn 180° if crowded). The second implements **alignment** (face mean heading). The third moves forward in the direction of the (possibly updated) heading.

**Note on within-action visibility:** the `move forward` at the end uses the heading **as it would be after the `set heading` updates apply**, because within one agent's `seq`, agent-field updates are visible to subsequent reads. This is documented in section 7.3.

**Features exercised:** `agents_in_radius`, `mean_heading_in_radius`, `forward`, integer arithmetic on directions (`mod 8`), within-action field-update visibility.

**Acceptance check:** after 500 ticks with seed=42, the global heading distribution should be **non-uniform** (alignment causes flocking), measurable as variance of heading histogram below the uniform baseline. Birds should not all collapse to one cell (separation works), measurable as average pairwise distance > some floor.

### 12.4 Predator-prey walkthrough

The most feature-rich example. Exercises `kill`, `spawn`, `die`, multiple agent types, cell field for grass regrowth.

```
agent Sheep { energy = 10 }
agent Wolf  { energy = 20 }
```
Two agent types, each with an energy field. Default starting energies differ.

```
let cell Empty =
  seq {
    set grass_age = field grass_age + 1.0;
    if field grass_age > grass_regrow_age
      then become Grass
      else stay
  }
```
Empty cells track time since last grazed. When old enough, they become grass.

```
let cell Grass =
  seq {
    set grass_age = 0.0
  }
```
Grass cells keep their `grass_age` reset.

**Note on the grazing limitation:** in v0.1, sheep cannot directly mutate the cell they're standing on — only cell rules can `become` a new state. So "sheep eats grass and the cell becomes empty" is not directly expressible. Instead, this model uses an indirect mechanism: grass cells reset `grass_age`, and empty cells age until they regrow. A more faithful grazing model would require agent-driven cell mutation, which is a v0.2 feature. This is documented in section 14 as a known v0.1 limitation.

The sheep rule:

```
let agent Sheep =
  seq {
    set energy = self.energy - 1;
```
Metabolism: lose 1 energy per tick.

```
    if cell_state == Grass
      then set energy = self.energy + sheep_eat_gain
      else stay;
```
Eat: gain energy if standing on grass.

```
    let wolf_dir   = nearest_agent_of_type_dir Wolf sheep_vision in
    let wolf_count = agents_of_type_in_radius Wolf sheep_vision in
    if wolf_count > 0
      then move ((wolf_dir + 4) mod 8)
      else move (random_dir ());
```
Flee: bind the nearest wolf direction and count. If any wolves visible, flee in the **opposite** direction (`+4 mod 8`). Otherwise random walk.

```
    if self.energy > sheep_repro_thresh
      then seq { set energy = sheep_repro_cost; spawn Sheep }
      else stay;
```
Reproduce: above threshold, set energy to the reproduction cost and spawn a new sheep. The new sheep starts with **default** energy=10 next tick — it does NOT inherit from parent.

```
    if self.energy <= 0 then die else stay
```
Starve.

The wolf rule is symmetric, plus the kill mechanic:

```
    if agents_of_type_in_radius Sheep 0 > 0
      then seq {
             kill Sheep;
             set energy = self.energy + wolf_kill_gain
           }
      else stay;
```

**This is the inter-agent kill.** `agents_of_type_in_radius Sheep 0` checks if any sheep are co-located (radius 0 = same cell). If so, `kill Sheep` is an intent to remove one such sheep when intents apply. The wolf gains energy in the same `seq`.

The kill is **deferred**: it happens during intent application, after all agents have produced their intents. **Documented quirk:** within one tick, two wolves on the same cell competing for the same sheep — conflict resolution picks one wolf to succeed, the other's `kill` intent is silently dropped, but the energy gain (computed earlier in the action body) is NOT undone. So a wolf might "steal" energy from a kill that was actually applied to a different wolf. To get strict accounting, v0.2 would need conditional intents. For v0.1 this is acceptable noise — predator-prey dynamics still converge to the expected oscillation pattern.

**Features exercised:** two agent types, `kill`, `spawn`, `die`, energy accounting, `nearest_agent_of_type_dir`, `agents_of_type_in_radius`, multi-step `seq` actions, direction arithmetic, cell field that ages over time, parameterization, `become` from a cell rule.

**Acceptance check:** after 500 ticks with seed=42, both species should still exist (neither went extinct). The population time series should show the characteristic Lotka–Volterra oscillation: when sheep peak, wolves peak shortly after, then sheep crash, then wolves crash, repeat. Measurable by computing population sums at every tick and checking that both series have at least one full oscillation period within 500 ticks.

### 12.5 Reaction-diffusion walkthrough

```
cell states Solvent
```
**Only one state.** This is unusual but legal. The state machine is trivial; all dynamics are in the fields.

```
field u = 1.0
field v = 0.0
```
Two fields, U and V.

```
param Du   = 0.16
param Dv   = 0.08
param feed = 0.060
param kill = 0.062
```
The four Gray-Scott parameters. Different `feed`/`kill` give wildly different patterns — the user can sweep them via CLI or Python without editing the source.

```
let cell _ =
  let cu  = field u in
  let cv  = field v in
  let lu  = laplacian u in
  let lv  = laplacian v in
  let uvv = cu * cv * cv in
  let du  = Du * lu - uvv + feed * (1.0 - cu) in
  let dv  = Dv * lv + uvv - (feed + kill) * cv in
  seq {
    set u = clamp (cu + du) 0.0 1.0;
    set v = clamp (cv + dv) 0.0 1.0
  }
```
The classic Gray-Scott update equations. `let` bindings at the top read the cell's current state once and reuse it.

`laplacian u` computes the discrete Laplacian of field U at the current cell — a single function call replaces a 9-cell weighted sum. This is the Protelis-inspired part of the spec: field operators are first-class.

`set u = clamp (cu + du) 0.0 1.0` writes the new field value. `clamp` takes three arguments via whitespace application: `clamp x lo hi`.

```
init field v =
  if x > 95 and x < 105 and y > 95 and y < 105
    then 0.5
    else 0.0
```
Per-cell field initialization with positional access via `x` and `y`. Seeds a 10×10 square of V in the center; rest is zero. Without this, V would be uniformly 0 and nothing would ever happen — Gray-Scott needs a perturbation to start.

**Features exercised:** single-state CA (`Solvent`), multiple cell fields, `laplacian`, `param`, `init field` with `x`/`y` positional access, `clamp`, multi-line `seq` cell body for multiple field updates.

**Acceptance check:** after 5000 ticks with seed=42 and default parameters, the V field should have visible spatial structure (variance > 0.01) extending well beyond the original 10×10 seed region. Sweeping `feed` and `kill` should produce visibly different patterns (this is verified informally, not numerically — the test just checks that runs with different params produce different field statistics).

---

## 13. Implementation guidance

This section is for the implementer (Claude Code) — what's expected, what shortcuts are allowed, what to test.

### 13.1 Recommended layering

```
swarmlet/
├── __init__.py            # public API: load(), SwarmletStaticError, SwarmletRuntimeError
├── lexer.py               # tokenize(source) -> List[Token]
├── parser.py              # parse(tokens) -> Program AST
├── ast.py                 # dataclasses for AST nodes
├── analyzer.py            # semantic checks: name resolution, type-of-set dispatch
├── eval.py                # expression and action evaluators
├── engine.py              # World class, tick logic, intent application
├── builtins.py            # implementations of all Section 6 functions
├── snapshot.py            # snapshot serialization (numpy + JSON)
├── cli.py                 # `swarmlet` command-line entry point
└── examples/
    ├── forest_fire.swl
    ├── ants.swl
    ├── boids.swl
    ├── wolf_sheep.swl
    └── gray_scott.swl
```

### 13.2 Recommended dependencies

- `numpy` for grid storage and field operations.
- No parser generator. Hand-written recursive descent is fine and recommended; the grammar is small.
- `pytest` for the test suite.
- `click` or stdlib `argparse` for the CLI.

### 13.3 Performance expectations for v0.1

This is a v0.1 reference implementation, not a production engine. Targets:

- Forest fire 100×100, 1000 ticks: **under 5 seconds**.
- Ant foraging 80×80 with 200 ants, 1000 ticks: **under 30 seconds**.
- Gray-Scott 200×200, 1000 ticks: **under 60 seconds**.

If `laplacian` and field reductions are vectorized via numpy on the entire grid (not cell-by-cell Python loops), Gray-Scott will be fast enough. Cell-by-cell evaluation in pure Python is acceptable for everything else.

### 13.4 Test categories

1. **Lexer tests** — token sequences for each construct.
2. **Parser tests** — round-trip representative programs.
3. **Static analyzer tests** — duplicate rules, undeclared names, shadowing, set-dispatch ambiguity, `forward` without `heading`.
4. **Evaluator tests** — match semantics, `let` scoping, guards, or-patterns, nested-match-must-be-parenthesized error.
5. **Engine tests** — single-tick state transitions for tiny worlds with hand-computed expected outputs.
6. **Determinism tests** — same seed produces same snapshots across runs (hash the sequence).
7. **Reference example tests** — each of the five examples loads, runs, and meets its acceptance check from section 12.
8. **Snapshot serialization tests** — round-trip JSON and `.npz`.

### 13.5 Definition of done for v0.1

- All grammar in section 4 parses correctly.
- All built-ins in section 6 implemented.
- All five reference examples run for the required number of ticks without errors and meet their acceptance checks.
- All static and runtime errors in section 10 are detected and reported with line numbers.
- CLI works: `swarmlet run`, `swarmlet check`, `--out .jsonl`, `--out .npz`, `--seed`, `--param`.
- Determinism property holds: identical seed → identical snapshot sequence (hash-verified).
- Test coverage of the engine ≥ 80%.
- A short README explains how to install and run the examples.

---

## 14. Non-goals for v0.1 (explicit)

These will not be implemented in v0.1 and should not be designed around:

- 3D worlds.
- Continuous (sub-cell) agent positions.
- User-defined functions (only `let ... in`).
- User-defined types beyond cell-state enums.
- Agents inheriting field values from a parent on `spawn` (children get defaults only).
- Conditional or transactional intents (kill that fails to consume energy if the kill target was claimed by another agent).
- Mutating cell state from agent actions (`become` is cell-rule only; this is the reason the wolf-sheep grazing model is indirect).
- Multi-threading or GPU execution.
- REPL or hot reload.
- Multiple programs / module system.
- Strings, lists, dicts as first-class values.
- Variable-binding patterns in `match`.
- Built-in visualization. The visualizer is a separate package consuming snapshots.
- Network sync, save/load mid-simulation.
- Real-time deployment to physical robots (this is the Protelis/ScaFi shaped problem, not Swarmlet's).

---

## 15. Related work

Swarmlet stands on the shoulders of three traditions:

**NetLogo** (Wilensky, 1999) — the canonical agent-based modeling language. Swarmlet borrows NetLogo's conceptual world model: turtles + patches, two-phase ticks, toroidal wrapping by default, per-entity attribute declaration, neighborhood as a first-class concept. NetLogo's syntax (Logo-derived imperative) is **not** borrowed — Swarmlet uses ML syntax instead. The four agent-based reference examples (Boids, ants, wolf-sheep, fire) all exist in the NetLogo Models Library and serve as informal correctness references.

**OCaml / ML family** (Milner et al., late 1970s onward) — Swarmlet's syntax is a small subset of OCaml: `let`, `match ... with | pattern when guard -> body`, `if/then/else`, whitespace function application, no curly braces around blocks (except `seq`). Swarmlet adds a domain-specific top level (`let cell`, `let agent`, `init`) and removes everything OCaml has that isn't needed: modules, polymorphism, records, variants, classes, references.

**Protelis** (Pianini, Beal, Viroli, 2015) and the **field calculus** tradition — Swarmlet borrows the *vocabulary* of field operators: `gradient_to`, `distance_to`, `min_in_radius`, `laplacian`. These come from a different paradigm (aggregate programming, where you specify global behavior and the runtime decomposes it to local rules) but the operators themselves are useful in Swarmlet's local-rules paradigm too. Protelis is the recommended target if and when Vitalii moves from simulation to deployment on physical swarms — Swarmlet is **not** a replacement for Protelis, just a simulation playground that shares some of its operator vocabulary.

Other systems considered and not adopted as direct references:

- **Mesa** (Python ABM library) — not a language.
- **MASON** (Java ABM library) — not a language.
- **StarLogo / StarLogo Nova** — block-based, targeted at children.
- **Repast** — Java/Groovy, large and academic.
- **Golly** with RuleTable format — only CA, no agents.

---

## Appendix A — File extension and conventions

- File extension: `.swl`
- Recommended file layout (not enforced): `world` → `param` → `cell states` → `field` → `agent` → `let cell` → `let agent` → `init`
- Recommended formatter convention: 2-space indent, `|` aligned with `match`, body of each case indented 4 spaces from `|`.

## Appendix B — Direction encoding

Heading and direction values are integers 0..7 encoding the 8 Moore directions, **clockwise starting from East**:

| Value | Direction | (dx, dy) |
|---|---|---|
| 0 | E   | (+1,  0) |
| 1 | SE  | (+1, +1) |
| 2 | S   | ( 0, +1) |
| 3 | SW  | (-1, +1) |
| 4 | W   | (-1,  0) |
| 5 | NW  | (-1, -1) |
| 6 | N   | ( 0, -1) |
| 7 | NE  | (+1, -1) |
| -1 | STAY | ( 0, 0) |

The y-axis points **down** (origin top-left), so "S" (south) means increasing y. This matches typical screen coordinates and numpy array indexing.

`forward` for an agent with heading H evaluates to direction H. `back` to `(H+4) mod 8`. `right` to `(H+2) mod 8`. `left` to `(H+6) mod 8`. (Right/left are 90° turns, so they skip the diagonal — `right` of East is South, not Southeast.)
