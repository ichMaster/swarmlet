# Swarmlet Syntax Cheatsheet

Compact reference. Full semantics in [Swarmlet-SPEC.md](../../specification/Swarmlet-SPEC.md).

## 1. World declaration
```
world 100 x 100 wrap        # toroidal (default); use `bounded` for OOB = Void
```

## 2. Cell states
```
cell states Empty | Tree | Fire | Ash    # first state = default for init cell
```

## 3. Cell fields
```
field pheromone = 0.0       # default value, must be const
```

## 4. Parameters
```
param growth_rate = 0.001   # numeric constant, overridable via API/CLI
```

## 5. Agent declaration
```
agent Ant  { carrying = 0, heading = 0 }    # heading enables forward/back/left/right
agent Wolf { energy = 20 }
```

## 6. Cell rules
```
let cell Fire = Ash                                            # single expr -> new state
let cell Empty = if random () < 0.001 then Tree else Empty     # if/else
let cell Tree = match any Fire with | true -> Fire | _ -> Tree # match
let cell _ = seq { set pheromone = field pheromone * 0.98 }    # seq + set/become
```
`let cell <S>` matches that state; `let cell _` is wildcard. Duplicate patterns = static error.

## 7. Agent rules
```
let agent Bird = move forward                                  # single action
let agent Sheep = if self.energy <= 0 then die else stay       # if/else action
let agent Ant = seq { set carrying = 1; move (argmax_neighbor pheromone) }
let agent Wolf = match cell_state with | Grass -> stay | _ -> kill Sheep
```
Actions: `stay`, `die`, `move <dir>`, `set f = e`, `spawn T`, `kill T`, `seq`, `if`, `match`.

## 8. Initialization
```
init cell = if random () < 0.5 then Tree else Empty            # per-cell, x,y bound
init field v = if x > 95 and x < 105 then 0.5 else 0.0         # per-cell field
init agent Ant 200                                             # spawn N at random cells
```

## 9. Expressions
```
let r = random () in if r < 0.5 then Tree else Empty           # let ... in
if cond then a else b                                          # if/then/else (else required)
match e with | Tree | Sapling when ok -> a | _ -> b            # match (leading | required)
a and b   a or b   not a                                       # boolean
a + b   a - b   a * b   a / b   a mod b   -a                   # arithmetic
a == b   a != b   a < b   a <= b   a > b   a >= b              # comparison
self.heading                                                   # field access (dot)
count Tree   look 1 0   clamp x 0.0 1.0                        # whitespace application
```

## 10. Pattern syntax
```
| _              -> ...     # wildcard
| Tree           -> ...     # state name (idents in patterns are literals, NOT bindings)
| 0              -> ...     # number (equality match)
| true           -> ...     # boolean
| Tree | Sapling -> ...     # or-pattern (shares body and guard)
| Tree when cond -> ...     # guard
```
**No variable bindings in v0.1.** Use `let` + `if` for value-dependent branches.

---

## Built-in quick reference

### Random (6.1)
| Built-in | Args | Returns | Description |
|---|---|---|---|
| `random` | `()` | float | uniform in [0, 1) |
| `random_int` | `n` | int | uniform in [0, n) |
| `random_dir` | `()` | direction | uniform Moore direction |

### Cell context (6.2) — in cell rules and `init`
| Built-in | Args | Returns | Description |
|---|---|---|---|
| `state` | — | state | current cell's state |
| `field` | `name` | float | current cell's named field |
| `x` | — | int | column (init only) |
| `y` | — | int | row (init only) |
| `count` | `S` | int | Moore neighbors in state `S` |
| `count_in` | `S N` | int | neighbors in `S` within neighborhood `N` |
| `any` | `S` | bool | any Moore neighbor in `S` |
| `sum_field` | `name` | float | sum over Moore neighbors |
| `sum_field_in` | `name N` | float | sum over neighborhood `N` |
| `mean_field` | `name` | float | mean over Moore neighbors |
| `max_field` | `name` | float | max over Moore neighbors |
| `min_field` | `name` | float | min over Moore neighbors |
| `laplacian` | `name` | float | 9-point stencil Laplacian |
| `neighbor` | `dx dy` | state | neighbor state at offset |
| `neighbor_field` | `dx dy name` | float | neighbor field at offset |
| `distance_to` | `S` | int | Chebyshev dist to nearest `S` (r<=16); -1 if none |
| `gradient_to` | `S` | direction | dir toward nearest `S` (r<=16); `STAY` if none |

### Agent context (6.3) — in agent rules
| Built-in | Args | Returns | Description |
|---|---|---|---|
| `self` | — | agent | current agent (use with `.field`) |
| `cell_state` | — | state | state of cell agent stands on |
| `cell_field` | `name` | float | field on agent's cell |
| `look` | `dx dy` | state | cell state at offset from agent |
| `look_field` | `dx dy name` | float | cell field at offset |
| `argmax_neighbor` | `name` | direction | dir to neighbor with max field |
| `argmin_neighbor` | `name` | direction | dir to neighbor with min field |
| `agents_in_radius` | `r` | int | other agents (any type) within `r` |
| `agents_of_type_in_radius` | `T r` | int | other agents of type `T` within `r` |
| `nearest_agent_dir` | `r` | direction | dir to nearest other agent; `STAY` if none |
| `nearest_agent_of_type_dir` | `T r` | direction | dir to nearest agent of type `T`; `STAY` if none |
| `mean_heading_in_radius` | `r` | direction | vector-mean heading of others in `r` |
| `min_in_radius` | `name r` | float | min cell field over cells within `r` |
| `max_in_radius` | `name r` | float | max cell field over cells within `r` |

### Math (6.4)
| Built-in | Args | Returns | Description |
|---|---|---|---|
| `abs` | `x` | number | absolute value |
| `min` | `a b` | number | minimum |
| `max` | `a b` | number | maximum |
| `sqrt` | `x` | number | square root |
| `exp` | `x` | number | e^x |
| `floor` | `x` | number | round toward -inf |
| `mod` | `a b` | number | modulo (also infix `mod`) |
| `clamp` | `x lo hi` | number | clamp x to [lo, hi] |

### Direction helpers (6.5)
| Helper | Args | Returns | Description |
|---|---|---|---|
| `forward` | — | direction | agent's heading (requires `heading` field) |
| `back` | — | direction | `(heading + 4) mod 8` |
| `left` | — | direction | `(heading + 6) mod 8` (90° turn) |
| `right` | — | direction | `(heading + 2) mod 8` (90° turn) |
| `dir` | `dx dy` | direction | absolute dir from offset, dx,dy ∈ {-1,0,1} |
| `STAY` | — | direction | sentinel = -1; `move STAY` ≡ `stay` |

Direction arithmetic is implicit `mod 8`: `(self.heading + 4) mod 8` rotates 180°.

---

## Direction encoding (clockwise from East; y-axis points down, origin top-left)
| Code | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | -1 |
|---|---|---|---|---|---|---|---|---|---|
| Name | E | SE | S | SW | W | NW | N | NE | STAY |
| dx | +1 | +1 | 0 | -1 | -1 | -1 | 0 | +1 | 0 |
| dy | 0 | +1 | +1 | +1 | 0 | -1 | -1 | -1 | 0 |

---

## Common idioms

**Probabilistic transition** (forest fire growth):
```
let cell Empty = if random () < growth_rate then Tree else Empty
```

**Decay a field** (pheromone evaporation):
```
let cell _ = seq { set pheromone = field pheromone * evaporation }
```

**Move toward gradient** (ants following pheromone):
```
if self.carrying == 0 then move (argmax_neighbor pheromone)
                      else move (random_dir ())
```

**Flee from target** (sheep avoiding wolves):
```
let wolf_dir = nearest_agent_of_type_dir Wolf sheep_vision in
if agents_of_type_in_radius Wolf sheep_vision > 0
  then move ((wolf_dir + 4) mod 8) else move (random_dir ())
```

**Reproduce when fed** (wolf-sheep):
```
if self.energy > sheep_repro_thresh
  then seq { set energy = sheep_repro_cost; spawn Sheep } else stay
```

**Metabolism + death** (within-action visibility — second stmt sees decremented energy):
```
seq { set energy = self.energy - 1; if self.energy <= 0 then die else stay }
```
