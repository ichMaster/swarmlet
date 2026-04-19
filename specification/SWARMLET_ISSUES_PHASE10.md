# Swarmlet Stage 1 — Phase 10 Addendum: Offline Matplotlib Visualizer

This addendum extends `SWARMLET_ISSUES.md` with a new phase dedicated to an **offline matplotlib-based visualizer** that lives in the same repository as the interpreter. The visualizer consumes snapshot files produced by Stage 1 and produces shareable output: MP4 videos, GIFs, PNG frames, and contact sheets.

The visualizer is an intermediate step before a future web-based interactive viewer (planned as Stage 2, separate repo, not covered here). Phase 10 intentionally stays Python-only, offline, and dependency-light: one language, one virtualenv, one additional CLI command.

## Why the visualizer lives in the same repo

Earlier planning considered a separate repository `swarmlet-viz`. That plan was revised: the visualizer is now integrated as Phase 10 of the main Swarmlet repo. The reasons:

1. **Single install, single version, single CLI.** Users get both `swarmlet` and `swarmlet-viz` commands with one `pip install -e .[viz]`
2. **Shared test infrastructure.** The determinism harness (SWARMLET-025) can be extended to verify that visualization of identical snapshots is bit-identical, which is a valuable regression test
3. **Shared documentation surface.** README, gallery, quickstart, and educational docs all live in one place
4. **Architectural boundary preserved by convention, not by filesystem.** The visualizer imports only from `swarmlet.snapshot` (the snapshot format module) — never from `swarmlet.eval`, `swarmlet.engine`, or `swarmlet.builtins`. This keeps the one-way dependency even though both modules share a repo. The boundary is verified by a lint rule in tests
5. **Lightweight install for those who don't need it.** The visualizer dependencies (`matplotlib`, `imageio[ffmpeg]`, `pillow`) are optional extras. `pip install -e .` installs the interpreter only; `pip install -e .[viz]` adds the visualizer. Users who only want to run simulations and consume JSON snapshots programmatically do not pay the cost of matplotlib

The architectural relationship:

```
┌─────────────────────────────────────────────┐
│  swarmlet repository (this repo)            │
│                                              │
│  ┌──────────────────┐                       │
│  │ swarmlet/        │ (Stage 1: Phase 0-9)  │
│  │   lexer.py       │                       │
│  │   parser.py      │                       │
│  │   engine.py      │                       │
│  │   snapshot.py ───┼──► the contract        │
│  │   cli.py         │                       │
│  └──────┬───────────┘                       │
│         │                                    │
│         │ imports only from swarmlet.snapshot│
│         ▼                                    │
│  ┌──────────────────┐                       │
│  │ swarmlet/viz/    │ (Stage 1: Phase 10)   │
│  │   loader.py      │                       │
│  │   model.py       │                       │
│  │   render/        │                       │
│  │   output/        │                       │
│  │   presets.py     │                       │
│  │   cli.py         │                       │
│  └──────────────────┘                       │
│                                              │
└─────────────────────────────────────────────┘
```

The visualizer is a **consumer** of the interpreter's output, not a peer. It has no knowledge of AST, evaluator, or engine internals. It only knows the snapshot format.

---

## Issues Summary Table — Phase 10

| # | ID | Title | Size | Phase | Dependencies |
|---|---|---|---|---|---|
| 27 | SWARMLET-027 | Viz package skeleton and optional extras | S | 10 — Visualizer | SWARMLET-018 |
| 28 | SWARMLET-028 | Viz snapshot loader (JSONL and NPZ) | S | 10 — Visualizer | SWARMLET-027, SWARMLET-018 |
| 29 | SWARMLET-029 | Viz snapshot data model and validation | S | 10 — Visualizer | SWARMLET-028 |
| 30 | SWARMLET-030 | Viz cell state renderer with categorical colormap | M | 10 — Visualizer | SWARMLET-029 |
| 31 | SWARMLET-031 | Viz cell field renderer with continuous colormap | M | 10 — Visualizer | SWARMLET-029 |
| 32 | SWARMLET-032 | Viz agent overlay renderer | M | 10 — Visualizer | SWARMLET-029 |
| 33 | SWARMLET-033 | Viz composite frame renderer | M | 10 — Visualizer | SWARMLET-030, SWARMLET-031, SWARMLET-032 |
| 34 | SWARMLET-034 | Viz MP4 video export | M | 10 — Visualizer | SWARMLET-033 |
| 35 | SWARMLET-035 | Viz GIF export | S | 10 — Visualizer | SWARMLET-033 |
| 36 | SWARMLET-036 | Viz single-frame PNG export | S | 10 — Visualizer | SWARMLET-033 |
| 37 | SWARMLET-037 | Viz contact sheet export | S | 10 — Visualizer | SWARMLET-033 |
| 38 | SWARMLET-038 | Viz CLI: swarmlet-viz render command | M | 10 — Visualizer | SWARMLET-034, SWARMLET-035, SWARMLET-036, SWARMLET-037 |
| 39 | SWARMLET-039 | Viz presets for the five reference examples | M | 10 — Visualizer | SWARMLET-038, SWARMLET-020..024 |
| 40 | SWARMLET-040 | Viz gallery, README update, and usage docs | S | 10 — Visualizer | SWARMLET-039 |

**Size legend:** S = ≤ 0.5 day, M = 0.5–1 day, L = 1–2 days

**Total Phase 10 effort:** 14 issues, ~5–7 working days for one author working alone, or ~3–4 days with Claude Code drafting and author review.

**Note on issue numbering:** Phase 10 takes IDs SWARMLET-027 through SWARMLET-040. This shifts the educational documentation in `SWARMLET_ISSUES_PHASE11.md` from SWARMLET-027..038 to **SWARMLET-041..052**. The addendum document should be updated with the new numbering, but content remains identical.

---

## Dependency Tree — Phase 10

```
                SWARMLET-018 (snapshot serializers from Phase 6)
                      |
                      v
                SWARMLET-027 (viz skeleton)
                      |
                      v
                SWARMLET-028 (snapshot loader)
                      |
                      v
                SWARMLET-029 (data model)
                      |
       +--------------+---------------+
       v              v               v
  SWARMLET-030  SWARMLET-031    SWARMLET-032
  (cells)       (fields)        (agents)
       |              |               |
       +------+-------+-------+-------+
              v               v
        SWARMLET-033 (composite frame)
              |
     +--------+--------+---------+
     v        v        v         v
SWARMLET- SWARMLET- SWARMLET- SWARMLET-
  034       035       036       037
 (mp4)     (gif)     (png)     (sheet)
     |        |        |         |
     +--------+--------+---------+
                       |
                       v
                SWARMLET-038 (CLI)
                       |
                       +---- depends also on SWARMLET-020..024 (examples exist)
                       |
                       v
                SWARMLET-039 (presets + gallery)
                       |
                       v
                SWARMLET-040 (README update + usage docs)
```

**Parallelization hints:**

- SWARMLET-030, SWARMLET-031, SWARMLET-032 can run in parallel after SWARMLET-029 (three independent renderers)
- SWARMLET-034, SWARMLET-035, SWARMLET-036, SWARMLET-037 can run in parallel after SWARMLET-033 (four independent output formats)
- Phase 10 can start as soon as SWARMLET-018 is merged — no need to wait for the rest of Stage 1. It can proceed in parallel with SWARMLET-019..026

---

## Phase 10 — Visualizer

### SWARMLET-027 — Viz package skeleton and optional extras

**Description:**
Add the visualizer as a sub-package `swarmlet/viz/` inside the main Swarmlet repository. Set up optional dependencies via `pyproject.toml` extras, add the second CLI entry point, create the test directory. This is the foundation issue that establishes the "visualizer lives here, with these dependencies, under this install flag".

**What needs to be done:**

- Create sub-package `swarmlet/viz/` with the following stub modules:
  ```
  swarmlet/viz/
  ├── __init__.py
  ├── loader.py
  ├── model.py
  ├── render/
  │   ├── __init__.py
  │   ├── cells.py
  │   ├── fields.py
  │   ├── agents.py
  │   └── composite.py
  ├── output/
  │   ├── __init__.py
  │   ├── mp4.py
  │   ├── gif.py
  │   ├── png.py
  │   └── sheet.py
  ├── presets.py
  └── cli.py
  ```
- Each stub file contains a module docstring and a placeholder comment. No functionality yet — that's the next 13 issues
- Update `pyproject.toml`:
  - Add `[project.optional-dependencies]` section with `viz = ["matplotlib>=3.8", "imageio[ffmpeg]>=2.34", "pillow>=10.0"]`
  - Add a second entry point in `[project.scripts]`: `swarmlet-viz = "swarmlet.viz.cli:main"` (alongside the existing `swarmlet = "swarmlet.cli:main"`)
- The viz sub-package's `__init__.py` exposes public API stubs: `load_snapshots`, `render_frame`, `FrameSpec`, `SnapshotError`. These are implemented in subsequent issues; for now they are just imports from the eventual modules, or placeholder `NotImplementedError` stubs
- Create `tests/viz/` directory alongside existing `tests/unit/` and `tests/integration/`. Add `tests/viz/__init__.py` and one trivial passing test to confirm pytest discovery
- **Import boundary enforcement:** add a lint test in `tests/viz/test_import_boundary.py` that uses `ast` or `grep` to verify that no file in `swarmlet/viz/` imports from `swarmlet.eval`, `swarmlet.engine`, `swarmlet.parser`, `swarmlet.analyzer`, `swarmlet.ast`, `swarmlet.lexer`, `swarmlet.builtins`. The ONLY allowed import from the parent package is `swarmlet.snapshot`. This lint test is the mechanism that preserves the architectural boundary inside a single repo
- Update the main `README.md` to mention the optional install: "For visualization, install with `pip install -e .[viz]`". Do not write the full viz docs yet — that's SWARMLET-040
- Verify that `pip install -e .` works without viz dependencies (baseline install)
- Verify that `pip install -e .[viz]` installs matplotlib, imageio, pillow
- Verify that `swarmlet-viz --help` runs (even if it just prints "not implemented yet")

**Dependencies:** SWARMLET-018 (snapshot serializers must exist before there is anything to load)

**Expected result:**
A clean sub-package skeleton inside the main repo, installable via optional extras, with the import boundary enforced by a lint test. No functionality yet, but the scaffold is ready for subsequent issues

**Acceptance criteria:**
- [ ] `pip install -e .` (without viz) succeeds and does NOT install matplotlib
- [ ] `pip install -e .[viz]` succeeds and installs matplotlib, imageio-ffmpeg, pillow
- [ ] `swarmlet-viz --help` prints something (even a placeholder)
- [ ] `from swarmlet.viz import load_snapshots, render_frame, FrameSpec, SnapshotError` works (even if the functions raise NotImplementedError)
- [ ] `tests/viz/` directory exists with at least one passing trivial test
- [ ] `tests/viz/test_import_boundary.py` exists and passes (the boundary check is active from day one)
- [ ] README mentions `[viz]` extras install

---

### SWARMLET-028 — Viz snapshot loader (JSONL and NPZ)

**Description:**
Implement the loader that reads snapshot files produced by `swarmlet run --out`. Two formats: JSONL (one snapshot per line) and NPZ (compressed numpy archive). Both produce the same in-memory representation so downstream renderers do not care about the source format.

**What needs to be done:**

- In `swarmlet/viz/loader.py`, implement three functions:
  - `load_jsonl(path: Path) -> List[dict]` — reads a JSONL file, parses each line as JSON, returns a list of snapshot dicts
  - `load_npz(path: Path) -> List[dict]` — reads a `.npz` archive, reconstructs the snapshot list. Format: entries `t000000`, `t000001`, ... for states; `<field_name>_t000000`, ... for each field; `agents_t000000`, ... for the JSON-serialized agent lists
  - `load_file(path: Path) -> List[dict]` — unified entry point that dispatches by extension (`.jsonl` → load_jsonl, `.npz` → load_npz, otherwise raise ValueError)
- Each returned snapshot dict matches the structure from `SPEC.md` section 9.1
- Convert JSON list-of-lists back into numpy arrays (since JSONL stores arrays as nested lists)
- Handle large files efficiently: stream JSONL line by line, do not load entire file into memory at once. For NPZ this is automatic since `np.load` is lazy
- This module does NOT import `swarmlet.snapshot` — it only reads files according to the contract documented in SPEC.md. The loader is completely decoupled from how the snapshots were written
- Write ≥6 unit tests in `tests/viz/test_loader.py`:
  - JSONL with one snapshot
  - JSONL with 100 snapshots
  - NPZ with one snapshot
  - NPZ with 100 snapshots and multiple fields
  - Round-trip: run `swarmlet run forest_fire.swl --out /tmp/tf.jsonl` in a subprocess, then `load_file("/tmp/tf.jsonl")` and verify structure matches
  - Error on unknown extension

**Dependencies:** SWARMLET-027, plus SWARMLET-018 must be merged so there is a real snapshot writer to round-trip against. Also benefits from SWARMLET-020 (forest fire example) for integration testing

**Expected result:**
A loader that consumes any valid output of `swarmlet run --out` and exposes a clean Python API for downstream rendering code

**Acceptance criteria:**
- [ ] 6+ unit tests passing
- [ ] `load_file("snapshots.jsonl")` returns a list of dicts matching SPEC.md section 9.1
- [ ] `load_file("snapshots.npz")` returns the same structure
- [ ] `load_file("snapshots.txt")` raises ValueError with a clear message
- [ ] Round-trip test with forest fire example passes
- [ ] Memory test: a 100 MB JSONL file does not load fully into memory at once

---

### SWARMLET-029 — Viz snapshot data model and validation

**Description:**
Wrap the raw dict-based snapshots in a typed dataclass for downstream code, and add validation. This is the only place in the viz package where code touches the raw dict shape — all downstream renderers use the typed `Snapshot`.

**What needs to be done:**

- In `swarmlet/viz/model.py`, define frozen dataclasses:
  ```python
  @dataclass(frozen=True)
  class WorldInfo:
      w: int
      h: int
      wrap: bool

  @dataclass(frozen=True)
  class AgentRecord:
      type: str
      id: int
      x: int
      y: int
      fields: dict  # remaining named fields

  @dataclass(frozen=True)
  class Snapshot:
      t: int
      world: WorldInfo
      states: np.ndarray              # shape (H, W), int8
      states_legend: List[str]
      fields: Dict[str, np.ndarray]   # name -> shape (H, W), float32
      agents: List[AgentRecord]
  ```
- Implement `Snapshot.from_dict(d: dict) -> Snapshot` that constructs a Snapshot from loader output with validation
- Validation rules (raise `SnapshotError` on violation with a clear message):
  - `states.shape == (h, w)`
  - `states.dtype` is integer
  - `min(states) >= 0` and `max(states) < len(states_legend)`
  - Each field has `shape == (h, w)` and is float
  - Each agent has `0 <= x < w` and `0 <= y < h`
  - Agent IDs are unique across the agents list
- Define `SnapshotError(Exception)` in `swarmlet/viz/__init__.py`
- Implement convenience `load_snapshots(path: Path) -> List[Snapshot]` that combines `loader.load_file` with `Snapshot.from_dict` for each item
- Write ≥6 unit tests in `tests/viz/test_model.py` covering valid snapshots and each validation error category

**Dependencies:** SWARMLET-028

**Expected result:**
A typed, validated model that downstream renderers depend on without worrying about malformed input

**Acceptance criteria:**
- [ ] 6+ unit tests passing
- [ ] `Snapshot.from_dict(valid_dict)` returns a frozen Snapshot
- [ ] Each validation rule has a test that triggers the corresponding error
- [ ] `load_snapshots("forest_fire.jsonl")` returns `List[Snapshot]` ready to render
- [ ] Snapshot is hashable and immutable

---

### SWARMLET-030 — Viz cell state renderer with categorical colormap

**Description:**
Render the cell state grid as a categorical heatmap: each state value maps to a fixed color. This is the basic layer for pure CA examples like forest fire.

**What needs to be done:**

- In `swarmlet/viz/render/cells.py`, implement `render_cell_states(snap: Snapshot, ax: plt.Axes, cmap: Optional[str] = None, palette: Optional[Dict[str, str]] = None)` that:
  - Builds a categorical colormap from `snap.states_legend` — either from a named matplotlib cmap (`tab10`, `Set2`) or from an explicit palette dict
  - Default: `tab10` for ≤10 states, `tab20` otherwise
  - Renders `snap.states` as an `imshow`
  - Adds a legend mapping state names to colors (outside the axes)
  - Removes default axis ticks
  - Returns None (mutates `ax`)
- Provide `make_cell_figure(snap: Snapshot, **kwargs) -> plt.Figure` as a convenience for single-figure use
- Write ≥4 unit tests in `tests/viz/test_render_cells.py`:
  - Renders a 5×5 hand-built snapshot to a figure, saves to temp PNG, asserts non-empty
  - Custom palette is respected
  - Default cmap chosen based on legend length
  - Legend shows correct labels

**Dependencies:** SWARMLET-029

**Expected result:**
A categorical heatmap renderer for any cell state declaration

**Acceptance criteria:**
- [ ] 4+ unit tests passing
- [ ] Forest fire snapshot renders with 4 distinct colors
- [ ] Custom palette `{"Tree": "green", "Fire": "red", ...}` is used when provided
- [ ] Legend appears with correct state labels
- [ ] Output PNG is visually correct (manual check on first run, file size > 0 in automated test)

---

### SWARMLET-031 — Viz cell field renderer with continuous colormap

**Description:**
Render a cell field as a continuous heatmap with optional colorbar, log scale, and clipping. This is what shows pheromone gradients in ants, U/V in Gray-Scott, and any scalar field.

**What needs to be done:**

- In `swarmlet/viz/render/fields.py`, implement `render_cell_field(snap: Snapshot, field_name: str, ax: plt.Axes, cmap: str = "viridis", vmin: Optional[float] = None, vmax: Optional[float] = None, log_scale: bool = False, colorbar: bool = True)` that:
  - Looks up `snap.fields[field_name]`, raises KeyError if absent
  - Renders as `imshow`
  - If vmin/vmax not provided, uses field min/max. If provided, uses them (fixed scale across animation frames)
  - If `log_scale=True`, uses `LogNorm` (clipping zeros)
  - Adds a colorbar if `colorbar=True`
  - Removes axis ticks
- Provide `make_field_figure(snap, field_name, **kwargs) -> plt.Figure`
- Auto-range helper for animations: `compute_field_range(snapshots: List[Snapshot], field_name: str) -> Tuple[float, float]` that returns `(min, max)` across all frames. This prevents color jitter in videos
- Write ≥5 unit tests in `tests/viz/test_render_fields.py`:
  - Renders a field with default settings
  - Custom vmin/vmax
  - Log scale
  - Colorbar on/off
  - `compute_field_range` returns correct values

**Dependencies:** SWARMLET-029

**Expected result:**
A continuous field renderer with right defaults for Gray-Scott and ant pheromone

**Acceptance criteria:**
- [ ] 5+ unit tests passing
- [ ] Pheromone field renders with viridis colormap and visible gradient
- [ ] Log scale handles zero values without crashing
- [ ] `compute_field_range` is monotonic across a snapshot series

---

### SWARMLET-032 — Viz agent overlay renderer

**Description:**
Render agents as points on top of an existing axes. Optionally show heading as arrow, optionally color by type, optionally show legend.

**What needs to be done:**

- In `swarmlet/viz/render/agents.py`, implement `render_agents(snap: Snapshot, ax: plt.Axes, by_type: bool = True, type_palette: Optional[Dict[str, str]] = None, marker_size: float = 20.0, show_heading: bool = False, heading_arrow_length: float = 0.7)` that:
  - Iterates over `snap.agents`
  - If `by_type=True`, groups by `type` and renders each group as a separate scatter with its own color
  - If `show_heading=True` AND agent has `heading` field, draws an arrow from agent position in the heading direction (using encoding from SPEC.md Appendix B: 0..7 clockwise from East)
  - Adds a legend in top-right if `by_type=True`
- Auto-pick default marker size based on grid dimensions
- Default type palette: high-contrast colors that work over colorful fields
- Write ≥5 unit tests in `tests/viz/test_render_agents.py`:
  - Single agent type, no heading
  - Multiple types with auto colors
  - Heading arrows correctly point in the 8 directions
  - Custom palette
  - Empty agent list does not crash

**Dependencies:** SWARMLET-029

**Expected result:**
An overlay renderer for ants, boids, and predator-prey

**Acceptance criteria:**
- [ ] 5+ unit tests passing
- [ ] Wolf-sheep snapshot renders Wolves and Sheep in different colors
- [ ] Boids snapshot with `show_heading=True` shows arrows pointing correctly
- [ ] Empty agent list (forest fire) does not crash

---

### SWARMLET-033 — Viz composite frame renderer

**Description:**
Combine cell, field, and agent renderers into a single function that produces a complete frame from a snapshot. The main entry point used by all four output formats.

**What needs to be done:**

- In `swarmlet/viz/render/composite.py`, define `FrameSpec` dataclass:
  ```python
  @dataclass
  class FrameSpec:
      show_cells: bool = True
      cells_palette: Optional[Dict[str, str]] = None
      cells_cmap: Optional[str] = None
      show_field: Optional[str] = None
      field_cmap: str = "viridis"
      field_vmin: Optional[float] = None
      field_vmax: Optional[float] = None
      field_log_scale: bool = False
      field_colorbar: bool = True
      show_agents: bool = True
      agents_by_type: bool = True
      agents_palette: Optional[Dict[str, str]] = None
      show_agent_heading: bool = False
      title_template: str = "t = {t}"
      figsize: Tuple[float, float] = (8.0, 8.0)
      dpi: int = 100
  ```
- Implement `render_frame(snap: Snapshot, spec: FrameSpec) -> plt.Figure` that:
  1. Creates a figure with the specified figsize and dpi
  2. If `show_field` is set, renders that field as background. Otherwise, if `show_cells=True`, renders cells as background
  3. If `show_agents=True`, overlays agents
  4. Sets title from `spec.title_template.format(t=snap.t)`
  5. Returns the figure
- **Rule:** cells and fields are **mutually exclusive** as background. If both flags are true, field takes precedence. This is documented in the docstring with the rationale (layering categorical on continuous creates visual noise)
- Implement `render_frames(snapshots: List[Snapshot], spec: FrameSpec) -> Generator[plt.Figure, None, None]` that yields figures one by one — used by video/gif exporters to avoid loading all frames in memory
- Write ≥4 unit tests in `tests/viz/test_render_composite.py`

**Dependencies:** SWARMLET-030, SWARMLET-031, SWARMLET-032

**Expected result:**
A single function turning `(Snapshot, FrameSpec)` into a matplotlib figure ready to save or compose into video

**Acceptance criteria:**
- [ ] 4+ unit tests passing
- [ ] `render_frame(forest_fire_snap, FrameSpec())` returns figure with cells visible
- [ ] `render_frame(gray_scott_snap, FrameSpec(show_cells=False, show_field="v"))` returns figure with field visible
- [ ] `render_frame(ants_snap, FrameSpec(show_field="pheromone", show_agents=True))` returns figure with field + agents
- [ ] `render_frames` generator yields figures one at a time without loading all into memory

---

### SWARMLET-034 — Viz MP4 video export

**Description:**
Implement video export: take a list of snapshots and a frame spec, render each frame, encode as MP4. Uses `imageio` with the `ffmpeg` plugin (bundled via `imageio-ffmpeg`, no separate install).

**What needs to be done:**

- In `swarmlet/viz/output/mp4.py`, implement `write_mp4(snapshots: List[Snapshot], spec: FrameSpec, path: Path, fps: int = 30, quality: int = 7, progress_callback: Optional[Callable[[int, int], None]] = None)` that:
  - Computes auto vmin/vmax across all snapshots if `spec.field_vmin` and `spec.field_vmax` are None AND a field is shown — prevents color jitter
  - Opens `imageio.get_writer(path, fps=fps, quality=quality)`
  - For each snapshot, calls `render_frame`, converts figure to numpy RGB array, appends to writer
  - Closes each figure immediately after use (`plt.close(fig)`) to release memory
  - Calls `progress_callback(current, total)` after each frame
- Figure-to-numpy conversion:
  ```python
  fig.canvas.draw()
  rgba = np.asarray(fig.canvas.buffer_rgba())
  rgb = rgba[:, :, :3]
  ```
- Default fps=30 for smooth playback
- Default quality=7 balances file size and visual quality
- Write ≥3 unit tests in `tests/viz/test_output_mp4.py`:
  - Small simulation produces valid MP4
  - Auto vmin/vmax is computed when not provided
  - Progress callback fires correct number of times

**Dependencies:** SWARMLET-033

**Expected result:**
Working MP4 export producing playable videos

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_mp4(forest_fire_snaps, FrameSpec(), "fire.mp4")` produces valid MP4
- [ ] MP4 plays in a standard video player (manual check first run, file size + ffprobe metadata in automated tests)
- [ ] Memory does not grow unbounded during long runs (figures closed after each frame)
- [ ] Progress callback fires once per frame

---

### SWARMLET-035 — Viz GIF export

**Description:**
GIF export for embedding in markdown, social posts, slack. Same pattern as MP4.

**What needs to be done:**

- In `swarmlet/viz/output/gif.py`, implement `write_gif(snapshots: List[Snapshot], spec: FrameSpec, path: Path, fps: int = 15, loop: int = 0, subsample: int = 1, progress_callback: Optional[Callable[[int, int], None]] = None)` that:
  - Mirrors `write_mp4` structure using `imageio.mimsave` or the GIF writer
  - Default fps=15 (lower than MP4, GIFs are bigger per frame)
  - `loop=0` means infinite (standard)
  - `subsample=N` keeps every Nth frame (quick size control)
  - Same figure-to-numpy conversion
  - Same memory management
- Write ≥3 unit tests

**Dependencies:** SWARMLET-033

**Expected result:**
Working GIF export

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_gif(snaps, spec, "fire.gif")` produces valid GIF
- [ ] GIF loops by default
- [ ] `subsample=2` produces half-size GIF

---

### SWARMLET-036 — Viz single-frame PNG export

**Description:**
Single-frame PNG for static documentation, README hero images, slide decks.

**What needs to be done:**

- In `swarmlet/viz/output/png.py`, implement `write_png(snap: Snapshot, spec: FrameSpec, path: Path, dpi: int = 150)` that:
  - Calls `render_frame(snap, spec)`
  - Saves with `fig.savefig(path, dpi=dpi, bbox_inches="tight")`
  - Closes the figure
- Convenience: `write_png_from_snapshots(snapshots: List[Snapshot], tick: int, spec: FrameSpec, path: Path, dpi: int = 150)` that finds the snapshot with `t == tick` (or closest)
- Write ≥3 unit tests

**Dependencies:** SWARMLET-033

**Expected result:**
PNG export for high-quality static images

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_png(snap, FrameSpec(), "frame.png")` produces valid PNG
- [ ] DPI parameter respected
- [ ] `bbox_inches="tight"` removes unnecessary whitespace

---

### SWARMLET-037 — Viz contact sheet export

**Description:**
Contact sheet: one PNG with N evenly-spaced frames as a grid. **Most useful format for documentation** — one image showing the full arc of a simulation.

**What needs to be done:**

- In `swarmlet/viz/output/sheet.py`, implement `write_contact_sheet(snapshots: List[Snapshot], spec: FrameSpec, path: Path, n_frames: int = 12, cols: int = 4, dpi: int = 150, title: Optional[str] = None)` that:
  - Picks `n_frames` evenly-spaced snapshots from input
  - Creates one figure with subplots in `cols × ceil(n_frames/cols)` grid
  - For each picked snapshot, draws into a subplot axes (stripped down: no colorbar, no legend, small title `t = N`)
  - Optional overall title via `fig.suptitle`
  - Saves as single PNG
- Auto vmin/vmax across picked frames for color consistency
- Write ≥3 unit tests

**Dependencies:** SWARMLET-033

**Expected result:**
Contact sheet export producing gallery images for documentation

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_contact_sheet(snaps, spec, "fire_sheet.png", n_frames=12)` produces one PNG with 12 sub-frames in 4×3
- [ ] Frames evenly spaced from snapshot list
- [ ] Sub-frames share color scale (auto-computed across them)
- [ ] Optional title appears at top

---

### SWARMLET-038 — Viz CLI: swarmlet-viz render command

**Description:**
Implement the `swarmlet-viz` command-line interface. Single command, multiple formats, sensible defaults, full flag control.

**What needs to be done:**

- In `swarmlet/viz/cli.py`, implement `main()` using `argparse`
- Subcommands:
  - `swarmlet-viz render <snapshots_file> [options]`
  - `swarmlet-viz info <snapshots_file>` — prints metadata (snapshot count, world size, agent counts, fields) without rendering
  - `swarmlet-viz version`
- `render` options:
  - `--out PATH` — required. Format dispatched by extension: `.mp4`, `.gif`, `.png`, and suffix `_sheet.png` triggers contact sheet
  - `--preset NAME` — apply built-in preset (forest_fire, ants, boids, wolf_sheep, gray_scott). Optional
  - `--field NAME` — show this field as background
  - `--cells-cmap NAME` — categorical cmap
  - `--field-cmap NAME` — continuous cmap
  - `--field-vmin FLOAT`, `--field-vmax FLOAT` — fixed color scale
  - `--no-cells`, `--no-agents` — disable layers
  - `--show-heading` — draw heading arrows
  - `--fps N` — frame rate (default 30 mp4, 15 gif)
  - `--quality N` — video quality 1-10 (default 7)
  - `--every N` — every Nth snapshot
  - `--frames N` — contact sheet frame count (default 12)
  - `--cols N` — contact sheet columns (default 4)
  - `--tick N` — PNG tick to render (default: last)
  - `--title TEXT` — optional title
  - `--dpi N` — raster DPI (default 150)
  - `--figsize WxH` — figure size
- Print summary at end: input file, output file, frame count, elapsed seconds
- Catch errors, print human-readable messages (no Python tracebacks)
- Write ≥4 integration tests in `tests/viz/test_cli.py`

**Dependencies:** SWARMLET-034, SWARMLET-035, SWARMLET-036, SWARMLET-037

**Expected result:**
Working CLI for all four formats with defaults and overrides

**Acceptance criteria:**
- [ ] 4+ integration tests passing
- [ ] `swarmlet-viz render snapshots.jsonl --out fire.mp4` produces MP4
- [ ] `swarmlet-viz render snapshots.jsonl --out fire.gif --every 5` produces subsampled GIF
- [ ] `swarmlet-viz render snapshots.jsonl --out frame.png --tick 100` produces PNG of tick 100
- [ ] `swarmlet-viz render snapshots.jsonl --out fire_sheet.png --frames 16 --cols 4` produces contact sheet
- [ ] `swarmlet-viz info snapshots.jsonl` prints metadata
- [ ] Errors print human-readable messages

---

### SWARMLET-039 — Viz presets for the five reference examples

**Description:**
Define presets for each Stage 1 reference example. Each preset is a `FrameSpec` with optimal settings for that example. `--preset NAME` makes "render this example" a one-flag operation.

**What needs to be done:**

- In `swarmlet/viz/presets.py`, define `PRESETS: Dict[str, FrameSpec]` with one entry per reference example
- **Forest fire:** categorical palette `{Empty: tan, Tree: forest green, Fire: orange-red, Ash: dark gray}`, no field, no agents, title `"Forest Fire — t = {t}"`
- **Ants:** field `pheromone` with `YlOrRd` cmap, no cells background, agents as small black dots, no heading, title `"Ant Foraging — t = {t}"`
- **Boids:** cells background (light gray), no field, agents with heading arrows, palette `{Bird: blue}`, title `"Boids — t = {t}"`
- **Wolf-sheep:** categorical palette `{Empty: brown earth, Grass: bright green}`, no field, agents with palette `{Sheep: white, Wolf: black}`, no heading, title `"Wolf-Sheep — t = {t}"`
- **Gray-Scott:** field `v` with `inferno` cmap, vmin=0.0, vmax=0.5, no cells, no agents, colorbar enabled, title `"Gray-Scott — t = {t}"`
- CLI `--preset` flag loads the matching FrameSpec, then individual flags can override specific fields
- Write ≥3 unit tests verifying each preset is a valid FrameSpec and produces non-empty output
- **Generate gallery contact sheets** as part of this issue:
  - For each of the five examples, run `swarmlet run <example>.swl --ticks N --seed 42 --out /tmp/<name>.jsonl`, then `swarmlet-viz render /tmp/<name>.jsonl --preset <name> --out examples/gallery/<name>_sheet.png --frames 12 --cols 4`
  - Commit the 5 generated contact sheets to `swarmlet/examples/gallery/`
  - These images are the visual proof-of-work for the project and the table-of-contents for the gallery in SWARMLET-040

**Dependencies:** SWARMLET-038, plus SWARMLET-020..024 (reference examples must exist to run the gallery generation)

**Expected result:**
Five working presets, each producing visually clean output. Five gallery contact sheets committed to the repo

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] All five presets defined in `PRESETS`
- [ ] `swarmlet-viz render fire.jsonl --preset forest_fire --out fire.mp4` produces visually correct video
- [ ] `--preset` combined with individual flags allows overriding
- [ ] Five gallery images exist in `swarmlet/examples/gallery/` and are visually meaningful (manual aesthetic check)

---

### SWARMLET-040 — Viz gallery, README update, and usage docs

**Description:**
User-facing documentation for the visualizer: expand the main README with a visualization section, create a usage guide, embed the gallery.

**What needs to be done:**

- Expand `README.md` (project root) with a new section "Visualization":
  - One-paragraph description: "Offline matplotlib renderer for Swarmlet snapshot files. Produces MP4 videos, GIFs, PNG frames, and contact sheets. Install with `pip install -e .[viz]`"
  - Workflow diagram: `swarmlet run → snapshots.jsonl → swarmlet-viz render → output`
  - Quickstart: 4-line example:
    ```
    pip install -e .[viz]
    swarmlet run swarmlet/examples/forest_fire.swl --ticks 1000 --seed 42 --out fire.jsonl
    swarmlet-viz render fire.jsonl --preset forest_fire --out fire.mp4
    ```
  - Gallery section embedding the 5 pre-rendered contact sheets from SWARMLET-039
  - One-liner mentioning "An interactive web viewer (Stage 2B) is planned for future work — it will consume the same snapshot files as this offline renderer"
- Create `docs/viz-usage.md` as reference (not tutorial):
  - All CLI flags and meanings
  - Available presets (list of 5)
  - Tips: fps selection, `--every` for subsampling, fixing color jitter, choosing output format
  - Common workflows: short video for sharing, long video for analysis, contact sheet for documentation
- Update `docs/quickstart.md` (from SWARMLET-026) to mention the viz extras install and point to the viz section of the README

**Dependencies:** SWARMLET-039, plus SWARMLET-026 (main quickstart exists to link from)

**Expected result:**
Complete user-facing documentation for the visualizer, with a visible gallery demonstrating all five examples

**Acceptance criteria:**
- [ ] `README.md` has a "Visualization" section with quickstart and gallery
- [ ] `docs/viz-usage.md` covers all CLI flags and presets
- [ ] All five gallery images render in the README
- [ ] Quickstart runs successfully as written (manual verification)
- [ ] `docs/quickstart.md` mentions the `[viz]` extras install

---

## Phase 10 scope notes

**Total Phase 10 effort:** 14 issues, ~5–7 working days sequentially, or ~3–4 days with parallelization (renderers in parallel, output formats in parallel).

**Hard prerequisites for Phase 10:**
- Stage 1 at minimum at SWARMLET-018 complete (snapshot serialization works)
- SWARMLET-020..024 merged before SWARMLET-039 (examples exist for presets and gallery)

**When Phase 10 can start:**
After SWARMLET-018, Phase 10 can proceed in parallel with SWARMLET-019..026. Phase 10 does not block any Stage 1 issue.

**Files added by Phase 10:**
- `swarmlet/viz/` sub-package with 10+ modules
- `tests/viz/` with ~14 test files
- `swarmlet/examples/gallery/` with 5 contact sheet PNGs
- `docs/viz-usage.md`
- Updates to `pyproject.toml` (optional extras), `README.md` (viz section), `docs/quickstart.md`

**Files NOT touched by Phase 10:**
- Anything in `swarmlet/` outside the new `swarmlet/viz/` sub-package
- No modifications to the interpreter, parser, evaluator, engine, or CLI (except adding the viz entry point in `pyproject.toml`)

**Architectural boundaries enforced inside the single repo:**

1. **One-way import.** `swarmlet/viz/` may import from `swarmlet.snapshot` (the snapshot format contract) ONLY. Imports from `swarmlet.eval`, `swarmlet.engine`, `swarmlet.parser`, `swarmlet.analyzer`, `swarmlet.ast`, `swarmlet.lexer`, `swarmlet.builtins` are forbidden. Enforced by `tests/viz/test_import_boundary.py`
2. **Optional dependency.** `matplotlib`, `imageio`, `pillow` are optional extras, not base dependencies. `pip install -e .` works without them. Base interpreter stays lightweight
3. **Separate CLI.** `swarmlet` and `swarmlet-viz` are two independent entry points. They do not share any flags or config. The viz CLI takes snapshot files, the interpreter CLI takes `.swl` files

**Critical correctness gates:**

- **Snapshot contract compatibility.** The viz loader must accept any valid output of `swarmlet run --out`. Any loader bug is a critical regression. Round-trip test in SWARMLET-028 guards this
- **Memory management in video export.** `write_mp4` and `write_gif` must close matplotlib figures after each frame. Otherwise long simulations leak memory. Tested in SWARMLET-034
- **Color consistency in animations.** Auto vmin/vmax computed across all frames, not per-frame, to avoid color jitter. Tested in SWARMLET-031 and SWARMLET-034
- **Import boundary lint.** `tests/viz/test_import_boundary.py` runs on every CI build and fails if any viz file imports from forbidden modules. This is the mechanism that preserves the separation inside a single repo
- **Preset aesthetics.** Each preset must produce visually clean output for its target example. Manual review during SWARMLET-039

**Critical design gates:**

- **Layer composition rule.** Cells and fields are mutually exclusive as background. Agents are always overlay. Documented in SWARMLET-033 with rationale
- **Format dispatch by extension.** The CLI infers format from `--out` extension. No `--format` flag. Unix convention
- **Contact sheet as first-class output.** SWARMLET-037 is NOT an afterthought. Contact sheets are the most useful format for documentation and are produced via the same pipeline as videos

**After Phase 10 is merged,** Swarmlet has:
- Working interpreter (Stage 1 Phases 0-9)
- Working offline visualizer producing shareable videos, GIFs, frames, and contact sheets
- Five-example gallery with visual proof-of-work
- A proven snapshot contract that a future web viewer (Stage 2B, planned separately) will inherit
- Clean architectural separation inside a single repo, enforced by lint tests

**What Phase 10 is NOT:**
- Real-time playback (matplotlib is too slow for that — Stage 2B's purpose)
- Interactive (no zoom, pan, click)
- Browser-based (Stage 2B)
- A replacement for Stage 2B — it's a stepping stone

**What Stage 2B will add on top of Phase 10 (planned separately, outside this document):**
- Browser-based interactive playback
- Live parameter tuning with re-run
- Shareable URLs with seed and params
- Side-by-side comparison
- Fastify backend wrapping the swarmlet CLI
- Svelte 5 + TypeScript + Canvas frontend
- Server-Sent Events for real-time streaming
- Its own separate repo (`swarmlet-viz-web`)

Phase 10 deliberately delivers 80% of the visualization value with 20% of the effort, giving the project visible output fast and validating the snapshot contract before Stage 2B is designed.

---

## Note on Phase 11 renumbering

This addendum adds 14 issues numbered SWARMLET-027 through SWARMLET-040. As a result, the educational documentation issues from `SWARMLET_ISSUES_PHASE11.md` must be renumbered from SWARMLET-027..038 to **SWARMLET-041..052**. The content of Phase 11 remains unchanged; only the ID numbers shift.

The updated Phase 11 numbering:
- SWARMLET-041: Doc — how to think functionally (was 027)
- SWARMLET-042: Doc — pattern matching (was 028)
- SWARMLET-043: Doc — let-expressions vs assignments (was 029)
- SWARMLET-044: Doc — expression evaluator (was 030)
- SWARMLET-045: Doc — tick as snapshot transformation (was 031)
- SWARMLET-046: Doc — intent pattern (was 032)
- SWARMLET-047: Doc — recursion vs iteration (was 033)
- SWARMLET-048: Doc — purity and side effects (was 034)
- SWARMLET-049: Doc — algebraic data types (was 035)
- SWARMLET-050: Doc — from Swarmlet to Protelis (was 036)
- SWARMLET-051: Doc — Swarmlet and Codex axioms (was 037)
- SWARMLET-052: Cheatsheet — Swarmlet syntax one-pager (was 038)

Dependencies in Phase 11 documents that reference implementation issues (e.g. SWARMLET-006, SWARMLET-011) remain unchanged — only the Phase 11 doc IDs themselves shift. The "recommended reading schedule" table in `SWARMLET_ISSUES_PHASE11.md` also needs the doc IDs updated to the new numbering.

Apply the renumbering as a mechanical search-and-replace before starting Phase 11 work.
