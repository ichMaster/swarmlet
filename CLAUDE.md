# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Swarmlet is a small functional language for simulating cellular automata and agent-based swarms on a 2D grid. It is currently in a **greenfield implementation phase** — the specification is complete but the interpreter has not been built yet.

The authoritative design document is [specification/Swarmlet-SPEC.md](specification/Swarmlet-SPEC.md). The implementation roadmap (26 issues across 9 phases) is in [specification/SWARMLET_ISSUES.md](specification/SWARMLET_ISSUES.md). Always consult these before making design decisions.

## Build & Development Commands

```bash
pip install -e .                          # editable install (once pyproject.toml exists)
pytest tests/                             # run all tests
pytest tests/unit/test_lexer.py           # run a single test file
pytest tests/unit/test_lexer.py::test_fn  # run a single test
pytest --cov=swarmlet                     # coverage report
swarmlet run example.swl -t 1000 -o out.jsonl   # run a program
swarmlet check example.swl               # parse and analyze without execution
```

**Runtime dependency:** numpy. **Dev dependencies:** pytest, pytest-cov.

## Architecture

The interpreter follows a classic pipeline: **source -> tokens -> AST -> analysis -> evaluation -> simulation**.

### Compilation Pipeline
- **Lexer** (`lexer.py`): Tokenizes source into `(kind, value, line, col)` tuples
- **Parser** (`parser.py`): Recursive descent producing AST nodes (declarations, expressions with precedence, cell rules, agent actions)
- **AST** (`ast.py`): Frozen dataclasses for all node types
- **Analyzer** (`analyzer.py`): Static semantic analysis — name resolution, type checking, duplicate detection
- **Evaluator** (`eval.py`): Expression and action evaluation against world snapshots

### Simulation Engine
- **World** (`engine.py`): 2D grid state — cell states + float fields, agent positions + fields
- **Tick**: Two-phase deterministic execution:
  1. **Cell phase**: evaluate matching cell rule per cell, write into fresh snapshot
  2. **Agent phase**: evaluate agent rules in seeded-random order, collect intent records, apply atomically with conflict resolution (movement > field writes > deposits > kill > spawn > death)
- **Builtins** (`builtins.py`): 30+ built-in functions (random, math, cell context, agent context, directions)
- **Snapshot** (`snapshot.py`): Serialization to JSONL and NPZ formats

### CLI
- **Entry point** (`cli.py`): `run` and `check` commands via argparse
- Package entry: `swarmlet = swarmlet.cli:main`

### Error Hierarchy
- `SwarmletError` (root) -> `SwarmletStaticError` (lexer/parser/analyzer) | `SwarmletRuntimeError` (eval/engine)
- Format: `"SwarmletStaticError at line 5, col 12: message"`

## Key Design Constraints

- **Pure functional semantics**: Rules are pure functions of the current snapshot. Cell rules cannot see updates from the same tick.
- **Determinism**: Given the same seed and program, two runs produce identical snapshot sequences. All randomness flows through a seeded RNG.
- **The interpreter is a pure engine**: It does not draw anything. Visualization is a separate consumer (`swarmlet-viz`, planned for Stage 2A).
- **ML-family syntax**: `let`, `match ... with | ... ->`, `when` guards. No mutation, no loops — only pattern matching and recursion.
- **Dynamic type system** with 6 tags: `number`, `bool`, `state`, `direction`, `agent_type`, `void`.

## Implementation Dependency Order

Phases must be followed in order (see SWARMLET_ISSUES.md for full details):
1. Project skeleton, token model, AST, builtin names
2. Lexer -> Parser (declarations -> expressions -> rules)
3. Static analyzer
4. Expression evaluator -> action evaluator
5. World class -> cell/agent builtins -> cell tick -> agent tick with conflict resolution
6. Serialization + CLI
7. Five reference examples (forest fire, ants, boids, wolf-sheep, gray-scott)
8. Determinism harness
9. Documentation

## Permissions

All tool calls are pre-approved in `.claude/settings.json` for uninterrupted development. This includes:

- **Bash**: All common shell commands (`git`, `gh`, `pip`, `python`, `pytest`, `mkdir`, `ls`, `cat`, `cp`, `mv`, `rm`, `find`, `grep`, `echo`, `swarmlet`, etc.)
- **File tools**: `Read`, `Write`, `Edit`, `Glob`, `Grep` — all operations allowed
- **Orchestration**: `Agent`, `TodoWrite` — for task planning and parallel work
- **Skills**: `implement-phase`, `update-config` — project-specific slash commands

When executing issues or phases, no manual confirmation should be needed. If a new command is blocked, add it to `.claude/settings.json` under `permissions.allow`.

## Testing Strategy

- Unit tests per module (lexer >= 10, parser decls >= 6, parser exprs >= 8, analyzer >= 8, eval >= 10, errors >= 4)
- Integration tests: one per reference example, validating full pipeline
- Determinism harness: runs each example twice with same seed, asserts identical snapshots
