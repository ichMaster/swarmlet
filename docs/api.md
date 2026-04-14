# Swarmlet API Reference

## Parsing

### `swarmlet.parser.parse(source: str) -> Program`

Parse Swarmlet source code into a Program AST.

```python
from swarmlet.parser import parse

prog = parse(open("forest_fire.swl").read())
```

Raises `SwarmletStaticError` on syntax errors with line/column information.

## Analysis

### `swarmlet.analyzer.analyze(prog: Program) -> Analyzer`

Run static semantic analysis on a parsed program. Detects duplicate declarations, undeclared names, context violations, and ambiguous `set` targets.

```python
from swarmlet.analyzer import analyze

analyzer = analyze(prog)  # raises SwarmletStaticError if any errors found
```

Errors are collected and reported together in a single exception.

## World

### `World(program, seed=0, params=None)`

Create a new world from a parsed program.

```python
from swarmlet.engine import World

world = World(prog, seed=42)
world = World(prog, seed=42, params={"growth_rate": 0.005})
```

**Parameters:**
- `program` — a `Program` AST from `parse()`
- `seed` — integer RNG seed for deterministic simulation
- `params` — optional dict of parameter overrides (name -> float)

### `World.step(n=1)`

Run `n` simulation ticks. Each tick consists of:
1. Cell phase (evaluate cell rules, write to fresh snapshot)
2. Agent phase (evaluate agent rules, collect intents, apply with conflict resolution)

```python
world.step(1000)
```

### `World.snapshot() -> dict`

Return the current world state as a dictionary:

```python
snap = world.snapshot()
```

**Snapshot structure:**
```python
{
    "tick": 42,
    "width": 100,
    "height": 100,
    "topology": "wrap",
    "states": [["Empty", "Tree", ...], ...],  # 2D list of state names
    "fields": {"pheromone": [[0.0, ...], ...]},  # field name -> 2D list
    "agents": [
        {"id": 0, "type": "Ant", "x": 5, "y": 10, "fields": {"carrying": 0.0}}
    ]
}
```

### `World.to_json() -> str`

Return `snapshot()` as a JSON string.

### `World.reset(seed=None)`

Reset the world to its initial state. If `seed` is provided, use the new seed. Otherwise, reuse the original seed.

```python
world.reset(seed=43)  # different random initialization
world.reset()         # same seed as construction
```

### `World.tick_count`

Current tick number (starts at 0, increments after each `step(1)`).

### World attributes

- `world.width`, `world.height` — grid dimensions
- `world.topology` — `"wrap"` or `"bounded"`
- `world.agents` — list of `AgentRecord` objects
- `world.states` — numpy array of state indices (shape: height x width)
- `world.fields` — dict of field name -> numpy array (shape: height x width)
- `world.state_names` — list of state name strings
- `world.get_state(x, y)` — state name at position, respects topology
- `world.get_field(x, y, name)` — field value at position, respects topology

## Snapshot serialization

### `swarmlet.snapshot.write_jsonl(world, path, ticks, every=1, progress=None)`

Run simulation and write snapshots as line-delimited JSON.

```python
from swarmlet.snapshot import write_jsonl
write_jsonl(world, "output.jsonl", ticks=1000, every=10)
```

### `swarmlet.snapshot.write_npz(world, path, ticks, every=1, progress=None)`

Run simulation and write snapshots as compressed numpy archive.

### `swarmlet.snapshot.read_jsonl(path) -> list`

Read snapshots from a JSONL file.

## Exceptions

### `SwarmletError`

Root exception for all Swarmlet errors.

### `SwarmletStaticError(line, col, message)`

Raised for lexer, parser, and analyzer errors.

```
SwarmletStaticError at line 5, col 12: expected '=' but got 'Tree'
```

### `SwarmletRuntimeError(message, line=None)`

Raised for evaluator and engine errors (type errors, non-exhaustive match, division by zero).

```
SwarmletRuntimeError: non-exhaustive match
SwarmletRuntimeError at line 10: expected number but got state
```

## CLI

```
swarmlet run <file> [--ticks N] [--seed N] [--out PATH] [--every N] [--param KEY=VALUE]
swarmlet check <file>
swarmlet --version
```

See `swarmlet run --help` for full usage.
