---
description: Implement all GitHub issues for a specific phase of the Swarmlet project. Fetches issues by phase label, then implements each one sequentially — coding, testing, fixing, committing, pushing, and closing. Manages product version as MAJOR.STAGE.PHASE.
argument-hint: "[phase-number] [--stage N] [--major N]"
---

# Implement Phase $ARGUMENTS

You are implementing all GitHub issues for a specific phase of the Swarmlet project.

## Argument parsing

Parse the arguments from `$ARGUMENTS`:

- **First positional argument** = phase number (required). Example: `1`, `2`, `11`
- **`--stage N`** (optional) = set the stage (middle component `yy` of the version). If omitted, keep the current value from the `VERSION` file
- **`--major N`** (optional) = set the major version (first component `xx` of the version). If omitted, keep the current value from the `VERSION` file

Examples:
- `/implement-phase 1` — implement phase 1, version becomes `0.1.1` (keeps current major=0, stage=1, sets phase=1)
- `/implement-phase 3 --stage 2` — implement phase 3, version becomes `0.2.3`
- `/implement-phase 1 --major 1 --stage 2` — implement phase 1, version becomes `1.2.1`

## Current version

Read the `VERSION` file at the repo root. If it doesn't exist, assume `0.1.0`.

## Version management

The project uses semantic-like versioning in the `VERSION` file at the repo root: `MAJOR.STAGE.PHASE`

| Component | Meaning | Source |
|-----------|---------|--------|
| `MAJOR` (xx) | Major product change | Set by user via `--major N`, otherwise preserved from `VERSION` |
| `STAGE` (yy) | Stage in the product line (e.g., Stage 1 = interpreter) | Set by user via `--stage N`, otherwise preserved from `VERSION` |
| `PHASE` (zz) | Phase number being implemented | Automatically set to the phase number argument |

### Version update procedure

At the START of the phase implementation (before any issue work):

1. Read the current version from the `VERSION` file
2. Parse it as `MAJOR.STAGE.PHASE`
3. Apply overrides from arguments:
   - If `--major N` was given, set MAJOR = N
   - If `--stage N` was given, set STAGE = N
   - Always set PHASE = the phase number argument
4. Write the new version to the `VERSION` file
5. If `pyproject.toml` exists, update the `version = "..."` field there too
6. If `swarmlet/__init__.py` exists and contains `__version__`, update it too
7. Commit the version bump:
   ```
   git add VERSION pyproject.toml swarmlet/__init__.py
   git commit -m "bump version to MAJOR.STAGE.PHASE"
   git push origin main
   ```

## Context

- The specification is in `specification/Swarmlet-SPEC.md` — always consult it for design decisions
- Issues are tracked on GitHub with labels like `phase:1-foundation`, `phase:2-lexer-parser`, etc.
- Each issue has acceptance criteria as checkboxes in the body
- Issues have dependency chains — implement them in dependency order

## Phase label mapping

Map the phase number to the GitHub label:

| Phase | Label |
|-------|-------|
| 1 | `phase:1-foundation` |
| 2 | `phase:2-lexer-parser` |
| 3 | `phase:3-builtins` |
| 4 | `phase:4-evaluator` |
| 5 | `phase:5-engine` |
| 6 | `phase:6-frontend` |
| 7 | `phase:7-examples` |
| 8 | `phase:8-quality` |
| 9 | `phase:9-docs` |
| 11 | `phase:11-education` |

## Step 0 — Fetch issues

Use the phase label from the mapping above and fetch all open issues for this phase. Run via Bash:

```bash
gh issue list --repo ichMaster/swarmlet --label "<phase-label>" --state open --json number,title,body --limit 50
```

## Workflow — for each issue in dependency order

Repeat the following cycle for every open issue in this phase, processing them in dependency order (lowest issue number first unless dependencies dictate otherwise):

### 1. Understand the issue

- Read the issue body carefully — extract the "What needs to be done" and "Acceptance criteria" sections
- Check dependencies: if the issue depends on issues from a prior phase, verify those are closed. If they depend on issues within this phase, implement those first
- Read the relevant sections of `specification/Swarmlet-SPEC.md` referenced by the issue
- Read any existing source files that will be modified

### 2. Implement

- Create or modify the source files as described in the issue
- Follow the project conventions from `CLAUDE.md`
- Write clean, minimal code — no extra abstractions, no speculative features
- All code goes in the `swarmlet/` package unless the issue says otherwise
- All tests go in `tests/unit/` or `tests/integration/` as specified

### 3. Write tests

- Write the tests specified in the issue (minimum counts are in the acceptance criteria)
- Tests should be self-contained — each test sets up its own fixtures
- Use pytest conventions (function-based tests, descriptive names)

### 4. Validate

Run the tests for the current issue:

```bash
python -m pytest tests/unit/<relevant_test_file>.py -v
```

If integration tests are specified:

```bash
python -m pytest tests/integration/<relevant_test_file>.py -v
```

Also run ALL existing tests to check for regressions:

```bash
python -m pytest tests/ -v
```

### 5. Fix failures

- If any tests fail, read the error output carefully
- Fix the implementation (not the tests, unless the test itself is wrong)
- Re-run the failing tests
- Repeat until all tests pass (both new and existing)

### 6. Verify acceptance criteria

Go through each acceptance criterion checkbox in the issue body and verify it is met. If any criterion requires a specific command or assertion, run it.

### 7. Commit and push

Create a focused commit for this issue:

```bash
git add <specific files changed>
git commit -m "SWARMLET-NNN: <issue title>

<brief description of what was implemented>

Closes #<issue-number>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push origin main
```

### 8. Close the issue

```bash
gh issue close <issue-number> --repo ichMaster/swarmlet
```

### 9. Move to the next issue

Repeat from step 1 for the next issue in this phase.

## Completion

After all issues in the phase are implemented, committed, pushed, and closed:

1. Run the full test suite one final time: `python -m pytest tests/ -v`
2. Create a git tag for the version: `git tag v<MAJOR.STAGE.PHASE> && git push origin v<MAJOR.STAGE.PHASE>`
3. Report a summary:
   - Version: `MAJOR.STAGE.PHASE`
   - Issues closed: list each with number and title
   - Tests: total count passing
   - Any notes or warnings

## Permissions

All necessary permissions are pre-configured in `.claude/settings.json`. The following are auto-allowed without prompts:

- **Bash**: `git`, `gh`, `pip`, `python`, `pytest`, `mkdir`, `ls`, `cat`, `cp`, `mv`, `rm`, `find`, `grep`, `echo`, `swarmlet`, `sed`, `awk`, `diff`, `tee`, `xargs`, and shell variable assignments
- **File tools**: `Read`, `Write`, `Edit`, `Glob`, `Grep`
- **Orchestration**: `Agent`, `TodoWrite`
- **Skills**: `implement-phase`, `update-config`

No manual confirmation should be required during phase execution. If a command is unexpectedly blocked, add it to `.claude/settings.json` under `permissions.allow` using the pattern `"Bash(command:*)"`.

## Important rules

- NEVER skip tests. Every issue specifies minimum test counts — meet or exceed them.
- NEVER commit broken code. All tests must pass before committing.
- NEVER modify tests just to make them pass — fix the implementation instead.
- If an issue's dependencies from a PRIOR phase are not yet implemented (issues still open), STOP and report this to the user rather than implementing out of order.
- Keep commits atomic — one commit per issue, not one giant commit for the whole phase.
- Always push after each commit so progress is saved.
- Read `specification/Swarmlet-SPEC.md` whenever you're unsure about language semantics or design decisions.
- The version bump commit is ALWAYS the first commit of a phase run.
