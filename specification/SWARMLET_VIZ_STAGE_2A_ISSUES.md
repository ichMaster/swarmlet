# Swarmlet Visualizer Stage 2A — Offline Matplotlib Renderer

**Status:** Plan
**Audience:** language designer (Vitalii), Claude Code (implementation)
**Scope:** Stage 2A — offline matplotlib-based renderer that consumes snapshots and produces video, GIF, PNG, and contact-sheet outputs. This is the intermediate version before Stage 2B (web-based interactive viewer).
**Companion documents:** `SPEC.md` (Swarmlet language spec), `SWARMLET_ISSUES.md` (Stage 1 implementation), `SWARMLET_ISSUES_PHASE11.md` (educational documentation)

---

## Why Stage 2A exists

Stage 1 (the Swarmlet interpreter) deliberately ships **without any visualization** — the engine produces snapshots, and visualization is the consumer's job. This decision is correct architecturally (sim2real, multiple consumers, clean separation), but it leaves the project without any visible output until somebody writes a renderer.

Stage 2A is that renderer. It is intentionally **simple, offline, Python-based**, and built on the same stack as the engine (numpy, matplotlib, imageio). It does one thing well: take a snapshot file produced by Stage 1, produce a video file you can play, embed in a slide, or post on social media.

Stage 2B (the web-based interactive viewer with Fastify + Svelte + TypeScript) is planned separately and starts only after Stage 2A is working. The reason for this split:

1. **Stage 2A delivers immediate value** with 20% of the effort. After ~5 days of work, you have shareable videos of all five reference examples
2. **Stage 2A validates the snapshot contract** — if matplotlib can render snapshots correctly, then the snapshot format is right, and the eventual web viewer will inherit the same proven contract
3. **Stage 2A informs Stage 2B design** — after rendering Boids, ants, predator-prey, and Gray-Scott as videos, you will know exactly what UI controls and visualization options matter. The web version will be designed by experience, not speculation
4. **Stage 2A is dependency-free** — no Node.js, no npm, no TypeScript build pipeline, no two-language stack. One language, one virtualenv, one CLI command

The architectural relationship between the three pieces:

```
┌──────────────────────────────────────────┐
│  Stage 1: swarmlet (Python)              │
│  produces snapshots.jsonl / snapshots.npz│
└────────────────┬─────────────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
       ▼                   ▼
┌───────────────┐   ┌──────────────────┐
│  Stage 2A:    │   │  Stage 2B:       │
│  swarmlet-viz │   │  swarmlet-viz-web│
│  (Python +    │   │  (Fastify+Svelte │
│   matplotlib) │   │   + TypeScript)  │
│               │   │                  │
│  → mp4/gif/   │   │  → interactive   │
│    png/sheet  │   │    browser UI    │
└───────────────┘   └──────────────────┘
```

Both Stage 2A and Stage 2B consume the same snapshot format. Both are independent of Stage 1. Both can evolve at their own pace.

---

## Issues Summary Table — Stage 2A

| # | ID | Title | Size | Phase | Dependencies |
|---|---|---|---|---|---|
| 1 | VIZ-A-001 | Repository skeleton and packaging | S | 1 — Foundation | -- |
| 2 | VIZ-A-002 | Snapshot loader (JSONL and NPZ) | S | 1 — Foundation | VIZ-A-001 |
| 3 | VIZ-A-003 | Snapshot data model and validation | S | 1 — Foundation | VIZ-A-002 |
| 4 | VIZ-A-004 | Cell state renderer with categorical colormap | M | 2 — Core rendering | VIZ-A-003 |
| 5 | VIZ-A-005 | Cell field renderer with continuous colormap | M | 2 — Core rendering | VIZ-A-003 |
| 6 | VIZ-A-006 | Agent overlay renderer | M | 2 — Core rendering | VIZ-A-003 |
| 7 | VIZ-A-007 | Composite frame renderer | M | 2 — Core rendering | VIZ-A-004, VIZ-A-005, VIZ-A-006 |
| 8 | VIZ-A-008 | MP4 video export via imageio-ffmpeg | M | 3 — Output formats | VIZ-A-007 |
| 9 | VIZ-A-009 | GIF export | S | 3 — Output formats | VIZ-A-007 |
| 10 | VIZ-A-010 | Single-frame PNG export | S | 3 — Output formats | VIZ-A-007 |
| 11 | VIZ-A-011 | Contact sheet export | S | 3 — Output formats | VIZ-A-007 |
| 12 | VIZ-A-012 | CLI: render command with all options | M | 4 — CLI and presets | VIZ-A-008..011 |
| 13 | VIZ-A-013 | Per-example presets for the five Stage 1 references | M | 4 — CLI and presets | VIZ-A-012 |
| 14 | VIZ-A-014 | README, gallery, usage examples | S | 5 — Documentation | VIZ-A-013 |

**Size legend:** S = ≤ 0.5 day, M = 0.5–1 day, L = 1–2 days

**Total Stage 2A effort:** 14 issues, ~5–7 working days for one author working alone, or ~3–4 days with Claude Code drafting and author review.

---

## Dependency Tree

```
                     VIZ-A-001 (skeleton)
                            |
                            v
                     VIZ-A-002 (snapshot loader)
                            |
                            v
                     VIZ-A-003 (data model)
                            |
            +---------------+----------------+
            v               v                v
      VIZ-A-004       VIZ-A-005        VIZ-A-006
      (cell states)   (cell fields)    (agents)
            |               |                |
            +-------+-------+--------+-------+
                    v                v
              VIZ-A-007 (composite frame)
                    |
       +------------+------------+---------+
       v            v            v         v
  VIZ-A-008    VIZ-A-009    VIZ-A-010  VIZ-A-011
  (mp4)        (gif)        (png)      (contact sheet)
       |            |            |         |
       +------------+-----+------+---------+
                          v
                    VIZ-A-012 (CLI)
                          |
                          v
                    VIZ-A-013 (presets)
                          |
                          v
                    VIZ-A-014 (docs)
```

**Parallelization hints:**

- VIZ-A-004, VIZ-A-005, VIZ-A-006 can run in parallel after VIZ-A-003 (three independent renderers)
- VIZ-A-008, VIZ-A-009, VIZ-A-010, VIZ-A-011 can run in parallel after VIZ-A-007 (four independent output formats)
- Documentation (VIZ-A-014) is sequential at the end

---

## External dependency on Stage 1

Stage 2A depends on Stage 1 (the swarmlet interpreter) being **at minimum at SWARMLET-018 complete** — that is, snapshot serialization to JSONL and NPZ must work. Without this, there is nothing to render.

The recommended Stage 1 progress before starting Stage 2A:

- SWARMLET-001 through SWARMLET-018: must be done. This gives you a working interpreter that can write snapshots
- SWARMLET-020 (forest fire example) should also be done so you have a real test input

After that, Stage 2A can proceed in parallel with the rest of Stage 1 (SWARMLET-019 CLI, SWARMLET-021..024 other examples, SWARMLET-025 determinism, SWARMLET-026 docs) without conflicts.

---

## Phase 1 — Foundation

### VIZ-A-001 — Repository skeleton and packaging

**Description:**
Create the `swarmlet-viz` Python project as a separate repository with its own packaging, dependencies, and tooling. This is intentionally a separate repo from `swarmlet` to enforce the architectural boundary: visualizer consumes snapshots, never the other way around.

**What needs to be done:**

- Create new repository `swarmlet-viz` (location: `/Users/Vitalii_Bondarenko2/Documents/GoogleDrive/projects/swarmlet-viz/` per personal convention)
- Create `pyproject.toml` for Python 3.11+ with entry point `swarmlet-viz = swarmlet_viz.cli:main`
- Runtime dependencies: `numpy`, `matplotlib`, `imageio[ffmpeg]`, `pillow`
- Dev dependencies: `pytest`, `pytest-cov`
- **Do NOT depend on `swarmlet` package itself.** The viz tool reads snapshot files, which are a stable contract — it does not import any swarmlet Python code. This keeps the dependency graph one-way and lets viz evolve independently
- Create package layout:
  ```
  swarmlet_viz/
  ├── __init__.py
  ├── loader.py        # snapshot file readers (jsonl, npz)
  ├── model.py         # snapshot dataclasses
  ├── render/
  │   ├── __init__.py
  │   ├── cells.py     # cell state renderer
  │   ├── fields.py    # cell field renderer
  │   ├── agents.py    # agent overlay
  │   └── composite.py # combined frame
  ├── output/
  │   ├── __init__.py
  │   ├── mp4.py
  │   ├── gif.py
  │   ├── png.py
  │   └── sheet.py     # contact sheet
  ├── presets.py       # per-example settings
  └── cli.py
  ```
- Create `tests/` with `__init__.py` and one trivial passing test
- Create `README.md` skeleton with project name and one-paragraph description
- Create `.gitignore` for Python projects, plus `*.mp4`, `*.gif`, `*.png` (we don't commit generated outputs except in `examples/gallery/`)
- Ensure `pip install -e .` succeeds and `swarmlet-viz --help` runs

**Dependencies:** None. Stage 1 swarmlet does not need to be installed for this issue — we only need the snapshot file format spec, which is documented in SPEC.md section 9.1

**Expected result:**
A clean Python project skeleton that installs correctly and has a working placeholder CLI. No actual rendering yet — that's the next phases

**Acceptance criteria:**
- [ ] `pip install -e .` exits 0
- [ ] `python -c "import swarmlet_viz"` succeeds
- [ ] `swarmlet-viz --help` prints something
- [ ] Directory layout matches the structure above
- [ ] Repository is independent from swarmlet (no import of `swarmlet`)
- [ ] `pytest` runs and finds the trivial test

---

### VIZ-A-002 — Snapshot loader (JSONL and NPZ)

**Description:**
Implement the loader that reads snapshot files produced by Stage 1's `swarmlet run --out`. Two formats supported: JSONL (one snapshot per line) and NPZ (compressed numpy archive). Both must produce the same in-memory representation so downstream renderers don't care about the source format.

**What needs to be done:**

- In `swarmlet_viz/loader.py`, implement two functions:
  - `load_jsonl(path: Path) -> List[dict]` — reads a JSONL file, parses each line as a JSON object, returns a list of snapshot dicts
  - `load_npz(path: Path) -> List[dict]` — reads a `.npz` archive, reconstructs the snapshot list. The NPZ archive contains entries `t000000`, `t000001`, ... for the states arrays, plus `<field_name>_t000000`, ... for each field, plus `agents_t000000`, ... for the JSON-serialized agent lists. Reconstruct each snapshot dict by combining these
- Implement a unified entry point `load(path: Path) -> List[dict]` that dispatches by extension (`.jsonl` → load_jsonl, `.npz` → load_npz, otherwise raise ValueError)
- Each snapshot dict in the returned list must match the structure from SPEC.md section 9.1:
  ```python
  {
      "t": int,
      "world": {"w": int, "h": int, "wrap": bool},
      "states": ndarray[H, W],          # int8
      "states_legend": List[str],
      "fields": {name: ndarray[H, W]},  # float32
      "agents": List[dict],
  }
  ```
- The loader is responsible for converting JSON list-of-lists back into numpy arrays (since JSONL stores arrays as nested lists)
- Handle large files efficiently: stream JSONL line by line, do not load the whole file into memory at once when it exceeds ~100 MB. For NPZ this is automatic since `np.load` is lazy
- Write ≥6 unit tests in `tests/test_loader.py`:
  - JSONL with one snapshot
  - JSONL with 100 snapshots
  - NPZ with one snapshot
  - NPZ with 100 snapshots and multiple fields
  - Round-trip: a snapshot written to JSONL then loaded equals the original (use a hand-built snapshot)
  - Error on unknown extension

**Dependencies:** VIZ-A-001

**Expected result:**
A loader that consumes any valid snapshot file produced by Stage 1's `--out` flag and exposes a clean Python API for downstream code

**Acceptance criteria:**
- [ ] 6+ unit tests passing
- [ ] `load("snapshots.jsonl")` returns a list of dicts matching SPEC.md section 9.1 structure
- [ ] `load("snapshots.npz")` returns the same structure
- [ ] `load("snapshots.txt")` raises ValueError with a clear message
- [ ] Round-trip test: hand-built snapshot → write JSONL → load → equals original
- [ ] Memory test: a 100 MB JSONL file does not load fully into memory at once

---

### VIZ-A-003 — Snapshot data model and validation

**Description:**
Wrap the raw dict-based snapshots in a typed dataclass for downstream code, and add a validation function that checks structural integrity. This is the only place where viz code touches the raw dict shape — all downstream code uses the dataclass.

**What needs to be done:**

- In `swarmlet_viz/model.py`, define dataclasses:
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
- Implement `Snapshot.from_dict(d: dict) -> Snapshot` that constructs a `Snapshot` from the raw loader output. This is where validation happens
- Validation rules (raise `SnapshotError` with a clear message on violation):
  - `states.shape == (h, w)`
  - `states.dtype` is integer
  - `min(states) >= 0` and `max(states) < len(states_legend)`
  - Each field has `shape == (h, w)` and is float
  - Each agent has `0 <= x < w` and `0 <= y < h`
  - Agent IDs are unique across the agents list
- Define `SnapshotError(Exception)` in `swarmlet_viz/__init__.py`
- Implement `load_snapshots(path: Path) -> List[Snapshot]` as a convenience that combines `loader.load` with `Snapshot.from_dict` for each item
- Write ≥6 unit tests in `tests/test_model.py` covering valid snapshots and each validation error category

**Dependencies:** VIZ-A-002

**Expected result:**
A typed, validated model that downstream renderers can depend on without worrying about malformed input

**Acceptance criteria:**
- [ ] 6+ unit tests passing
- [ ] `Snapshot.from_dict(valid_dict)` returns a frozen Snapshot
- [ ] Each validation rule has a test that triggers the corresponding error
- [ ] `load_snapshots("forest_fire.jsonl")` returns `List[Snapshot]` ready to render
- [ ] Snapshot is hashable and immutable (frozen dataclass)

---

## Phase 2 — Core rendering

### VIZ-A-004 — Cell state renderer with categorical colormap

**Description:**
Render the cell state grid as a categorical heatmap: each state value maps to a fixed color, the result is a 2D image. This is the most basic visualization layer and the only one needed for pure CA examples like forest fire.

**What needs to be done:**

- In `swarmlet_viz/render/cells.py`, implement `render_cell_states(snap: Snapshot, ax: plt.Axes, cmap: Optional[str] = None, palette: Optional[Dict[str, str]] = None)` that:
  - Takes a Snapshot and a matplotlib Axes
  - Builds a categorical colormap from the snapshot's `states_legend` — either from a named matplotlib categorical cmap (`cmap="tab10"`, `"Set2"`, etc.) or from an explicit palette dict mapping state names to colors
  - If neither is provided, use a sensible default: `tab10` for ≤10 states, `tab20` otherwise
  - Renders `snap.states` as an `imshow` with the categorical colormap
  - Adds a legend mapping state names to colors (positioned outside the axes by default)
  - Sets correct extent so the grid is drawn pixel-perfect
  - Removes default axis ticks and labels
  - Returns nothing (mutates `ax`)
- Provide a higher-level convenience: `make_cell_figure(snap: Snapshot, **kwargs) -> plt.Figure` that creates a fresh figure with one axes and renders into it. Used by the PNG single-frame export
- Write ≥4 unit tests in `tests/test_render_cells.py`:
  - Renders a 5x5 hand-built snapshot to a figure and saves to a temp PNG; asserts file is non-empty
  - Custom palette is respected
  - Default cmap chosen based on legend length
  - Legend shows correct labels

**Dependencies:** VIZ-A-003

**Expected result:**
A categorical heatmap renderer that handles any cell state declaration from a Swarmlet program

**Acceptance criteria:**
- [ ] 4+ unit tests passing
- [ ] Forest fire snapshot renders with 4 distinct colors for Empty/Tree/Fire/Ash
- [ ] Custom palette `{"Tree": "green", "Fire": "red", "Ash": "gray", "Empty": "white"}` is used when provided
- [ ] Legend appears with correct state labels
- [ ] Output PNG is visually correct (manual check on first run, automated check on file size > 0)

---

### VIZ-A-005 — Cell field renderer with continuous colormap

**Description:**
Render a cell field as a continuous heatmap with optional colorbar, log scale, and clipping. This is what shows pheromone gradients in ants, U/V concentrations in Gray-Scott, and any other scalar field.

**What needs to be done:**

- In `swarmlet_viz/render/fields.py`, implement `render_cell_field(snap: Snapshot, field_name: str, ax: plt.Axes, cmap: str = "viridis", vmin: Optional[float] = None, vmax: Optional[float] = None, log_scale: bool = False, colorbar: bool = True)` that:
  - Looks up `snap.fields[field_name]`, raising KeyError if absent
  - Renders as `imshow` with the specified cmap
  - If `vmin`/`vmax` are not provided, uses min/max of the field. If provided, uses them (allows fixed scale across frames for animations)
  - If `log_scale=True`, uses `LogNorm` (clipping zero values)
  - Adds a colorbar if `colorbar=True`
  - Removes axis ticks
- Provide convenience `make_field_figure(snap, field_name, **kwargs) -> plt.Figure`
- Auto-vmin/vmax for animations: provide a helper `compute_field_range(snapshots: List[Snapshot], field_name: str) -> Tuple[float, float]` that returns `(min, max)` across all frames. This lets animations have a fixed color scale instead of jittering frame-to-frame
- Write ≥5 unit tests in `tests/test_render_fields.py`:
  - Renders a small field with default settings
  - Custom vmin/vmax
  - Log scale
  - Colorbar on/off
  - `compute_field_range` returns correct values across multiple snapshots

**Dependencies:** VIZ-A-003

**Expected result:**
A continuous field renderer with the right defaults for typical use cases (Gray-Scott, ant pheromone)

**Acceptance criteria:**
- [ ] 5+ unit tests passing
- [ ] Pheromone field from a hand-built ant simulation snapshot renders with viridis colormap and visible gradient
- [ ] Log scale handles zero values without crashing
- [ ] `compute_field_range` is monotonic across a series

---

### VIZ-A-006 — Agent overlay renderer

**Description:**
Render agents as points (or small markers) on top of an existing axes that already has a cell state or field rendered. Optionally show heading as an arrow, optionally color by type, optionally show a small legend.

**What needs to be done:**

- In `swarmlet_viz/render/agents.py`, implement `render_agents(snap: Snapshot, ax: plt.Axes, by_type: bool = True, type_palette: Optional[Dict[str, str]] = None, marker_size: float = 20.0, show_heading: bool = False, heading_arrow_length: float = 0.7)` that:
  - Iterates over `snap.agents`
  - If `by_type=True`, groups agents by `type` and renders each group as a separate scatter with its own color (from `type_palette` or auto-assigned)
  - If `show_heading=True` AND the agent has a `heading` field, draws a small arrow from the agent position in the direction of its heading. Use the direction encoding from SPEC.md Appendix B (0..7 clockwise from East)
  - Adds a small legend in the top-right corner if `by_type=True`
- Auto-pick a default marker size based on grid dimensions: smaller markers for larger grids, so they don't overlap visually
- Default type palette: high-contrast colors that work over dark-ish backgrounds (since fields are often colorful)
- Write ≥5 unit tests in `tests/test_render_agents.py`:
  - Single agent type, no heading
  - Multiple agent types with auto colors
  - Heading arrows correctly point in one of 8 directions
  - Custom palette
  - Empty agent list does not crash

**Dependencies:** VIZ-A-003

**Expected result:**
An overlay renderer that draws agents on top of any base map. Used for ants, boids, and predator-prey

**Acceptance criteria:**
- [ ] 5+ unit tests passing
- [ ] Wolf-sheep snapshot renders Wolves and Sheep in different colors
- [ ] Boids snapshot with `show_heading=True` shows visible arrows pointing in the right directions
- [ ] Empty agent list (e.g. forest fire snapshot) does not crash the renderer

---

### VIZ-A-007 — Composite frame renderer

**Description:**
Combine cell, field, and agent renderers into a single function that produces a complete frame from a snapshot. This is the main entry point used by all four output formats. Configurable layer stacking: which fields to show, in which order, with which agents on top.

**What needs to be done:**

- In `swarmlet_viz/render/composite.py`, define `FrameSpec` dataclass:
  ```python
  @dataclass
  class FrameSpec:
      show_cells: bool = True
      cells_palette: Optional[Dict[str, str]] = None
      cells_cmap: Optional[str] = None
      show_field: Optional[str] = None     # field name to show as background, or None
      field_cmap: str = "viridis"
      field_vmin: Optional[float] = None
      field_vmax: Optional[float] = None
      field_log_scale: bool = False
      field_colorbar: bool = True
      show_agents: bool = True
      agents_by_type: bool = True
      agents_palette: Optional[Dict[str, str]] = None
      show_agent_heading: bool = False
      title_template: str = "t = {t}"      # format string for figure title
      figsize: Tuple[float, float] = (8.0, 8.0)
      dpi: int = 100
  ```
- Implement `render_frame(snap: Snapshot, spec: FrameSpec) -> plt.Figure` that creates a figure, applies the spec, calls the underlying renderers in the right order:
  1. If `show_cells=True` AND `show_field=None`, render cells as background
  2. If `show_field` is set, render the field as background (cells are NOT shown — fields override cells visually)
  3. If `show_agents=True`, overlay agents
  4. Set figure title from `title_template.format(t=snap.t, **other_vars)`
  5. Return the figure (caller is responsible for `plt.close(fig)` after use)
- The reason `show_cells` and `show_field` are mutually exclusive: putting a categorical heatmap under a continuous heatmap creates visual noise. If the user wants both, they should run two renders (one for cells, one for fields). For the typical case (Gray-Scott — only field; forest fire — only cells; ants — field + agents) the spec is correct
- Implement helper `render_frames(snapshots: List[Snapshot], spec: FrameSpec) -> Generator[plt.Figure, None, None]` that yields figures one by one. The video/gif exporters consume this generator to avoid loading all frames into memory at once
- Write ≥4 unit tests in `tests/test_render_composite.py`

**Dependencies:** VIZ-A-004, VIZ-A-005, VIZ-A-006

**Expected result:**
A single function that turns a snapshot + spec into a matplotlib figure ready to be saved or composed into a video

**Acceptance criteria:**
- [ ] 4+ unit tests passing
- [ ] `render_frame(forest_fire_snap, FrameSpec())` returns a figure with cells visible
- [ ] `render_frame(gray_scott_snap, FrameSpec(show_cells=False, show_field="v"))` returns a figure with field visible
- [ ] `render_frame(ants_snap, FrameSpec(show_field="pheromone", show_agents=True))` returns a figure with field + agents visible
- [ ] `render_frames` generator yields figures one at a time without loading all into memory

---

## Phase 3 — Output formats

### VIZ-A-008 — MP4 video export via imageio-ffmpeg

**Description:**
Implement video export: take a list of snapshots and a frame spec, render each frame, encode the result as an MP4 file. Uses `imageio` with the `ffmpeg` plugin so users do not need a separate ffmpeg installation (it's bundled by `imageio-ffmpeg`).

**What needs to be done:**

- In `swarmlet_viz/output/mp4.py`, implement `write_mp4(snapshots: List[Snapshot], spec: FrameSpec, path: Path, fps: int = 30, quality: int = 7)` that:
  - Computes auto vmin/vmax across all snapshots if `spec.field_vmin` and `spec.field_vmax` are None and a field is being shown — this prevents color jitter from frame to frame
  - Opens an `imageio.get_writer(path, fps=fps, quality=quality)` context
  - For each snapshot, calls `render_frame(snap, spec)` to get a matplotlib figure, converts the figure to a numpy RGB array, appends to the writer
  - Closes each figure after use (`plt.close(fig)`) to release memory
  - Reports progress via an optional `progress_callback: Callable[[int, int], None]` argument that's called as `(current_frame, total_frames)`
- Conversion from matplotlib figure to numpy array:
  ```python
  fig.canvas.draw()
  rgba = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
  rgba = rgba.reshape(fig.canvas.get_width_height()[::-1] + (4,))
  rgb = rgba[:, :, 1:4]  # drop alpha
  ```
  Or use the modern `fig.canvas.buffer_rgba()` if available
- Default fps=30 is good for smooth playback. For long simulations user can set `--every N` upstream in `swarmlet run` to reduce snapshot count first
- Default quality=7 is a balance between file size and visual quality (1-10 scale)
- Write ≥3 unit tests in `tests/test_output_mp4.py`:
  - Small simulation produces a valid MP4 file
  - Auto vmin/vmax is computed when not provided
  - Progress callback is called the expected number of times

**Dependencies:** VIZ-A-007, plus `imageio-ffmpeg` runtime dependency (already in pyproject.toml from VIZ-A-001)

**Expected result:**
Working MP4 export that produces a playable video file from any snapshot sequence

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_mp4(forest_fire_snaps, FrameSpec(), "fire.mp4")` produces a valid MP4
- [ ] The MP4 file plays in a standard video player (verified manually on first run, then by file size > 0 and ffprobe metadata in tests)
- [ ] Memory does not grow unboundedly during long runs (figures are closed after each frame)
- [ ] Progress callback fires once per frame

---

### VIZ-A-009 — GIF export

**Description:**
Implement GIF export. Same pattern as MP4 but with `.gif` output. Useful for embedding in markdown documentation, social posts, slack messages.

**What needs to be done:**

- In `swarmlet_viz/output/gif.py`, implement `write_gif(snapshots: List[Snapshot], spec: FrameSpec, path: Path, fps: int = 15, loop: int = 0)` that:
  - Mirrors the structure of `write_mp4` but uses `imageio.mimsave` or the GIF writer
  - Default fps=15 (lower than MP4 because GIFs are larger per frame)
  - `loop=0` means infinite loop (standard for GIF)
  - Optional `max_colors=256` parameter for palette quantization (default 256)
  - Optional `subsample=1` parameter to reduce frame count by N (e.g. `subsample=2` keeps every other frame). GIFs get big fast; this is a quick way to manage size
- Same figure-to-numpy conversion as MP4
- Same memory management (close figures)
- Same progress callback
- Write ≥3 unit tests

**Dependencies:** VIZ-A-007

**Expected result:**
Working GIF export that produces playable, embeddable GIF files

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_gif(snaps, spec, "fire.gif")` produces a valid GIF
- [ ] GIF loops by default
- [ ] `subsample=2` produces a GIF with half the frames

---

### VIZ-A-010 — Single-frame PNG export

**Description:**
Implement single-frame PNG export. Takes one snapshot (chosen by tick number) and saves it as a PNG. Useful for static documentation, README hero images, slide decks.

**What needs to be done:**

- In `swarmlet_viz/output/png.py`, implement `write_png(snap: Snapshot, spec: FrameSpec, path: Path, dpi: int = 150)` that:
  - Calls `render_frame(snap, spec)` to get the figure
  - Saves with `fig.savefig(path, dpi=dpi, bbox_inches="tight")`
  - Closes the figure
- Convenience: `write_png_from_snapshots(snapshots: List[Snapshot], tick: int, spec: FrameSpec, path: Path, dpi: int = 150)` that finds the snapshot with `t == tick` (or the closest one) and renders it
- Write ≥3 unit tests

**Dependencies:** VIZ-A-007

**Expected result:**
PNG export that produces high-quality static images

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_png(snap, FrameSpec(), "frame.png")` produces a valid PNG
- [ ] DPI parameter is respected
- [ ] `bbox_inches="tight"` removes unnecessary whitespace around the figure

---

### VIZ-A-011 — Contact sheet export

**Description:**
Implement contact sheet export: a single PNG showing N evenly-spaced frames from a simulation as a grid. This is **the most useful format for documentation**: one image showing the entire arc of a simulation from start to finish, ideal for README files, papers, slide decks, and the eventual web gallery.

**What needs to be done:**

- In `swarmlet_viz/output/sheet.py`, implement `write_contact_sheet(snapshots: List[Snapshot], spec: FrameSpec, path: Path, n_frames: int = 12, cols: int = 4, dpi: int = 150, title: Optional[str] = None)` that:
  - Picks `n_frames` evenly-spaced snapshots from the input list (e.g. for 1000 snapshots and `n_frames=12`, picks indices 0, 90, 181, ..., 999)
  - Computes grid dimensions: `cols` columns, `ceil(n_frames / cols)` rows
  - Creates a single matplotlib figure with subplots in a grid
  - For each picked snapshot, calls a stripped-down version of `render_frame` that draws into a subplot axes (without colorbar, without legend, with smaller title showing just `t = N`)
  - Adds an optional overall title via `fig.suptitle(title)` if provided
  - Saves the figure as a single PNG
- Auto vmin/vmax across all picked frames (so the colors are consistent across the contact sheet)
- The result is one image that tells the whole story of a run. For Gray-Scott this shows pattern formation. For forest fire this shows ignition + burn + recovery. For predator-prey this shows oscillation
- Write ≥3 unit tests

**Dependencies:** VIZ-A-007

**Expected result:**
Contact sheet export that produces a gallery image showing the full arc of a simulation in one PNG

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] `write_contact_sheet(snaps, spec, "fire_sheet.png", n_frames=12)` produces one PNG with 12 sub-frames in a 4×3 grid
- [ ] Frames are evenly spaced from the snapshot list
- [ ] All sub-frames share the same color scale (auto-computed across them)
- [ ] Optional title appears at the top

---

## Phase 4 — CLI and presets

### VIZ-A-012 — CLI: render command with all options

**Description:**
Implement the `swarmlet-viz render` command-line interface that ties everything together. Single command, multiple output formats, sensible defaults, full control via flags for power users.

**What needs to be done:**

- In `swarmlet_viz/cli.py`, implement `main()` using `argparse`
- Subcommands:
  - `swarmlet-viz render <snapshots_file> [options]`
  - `swarmlet-viz info <snapshots_file>` — prints metadata about a snapshot file (number of snapshots, world size, agent counts, fields present) without rendering anything
  - `swarmlet-viz version`
- `render` options:
  - `--out PATH` — output file path. Format dispatched by extension: `.mp4`, `.gif`, `.png`, `_sheet.png` (any path ending in `_sheet.png` triggers contact sheet mode). Required
  - `--preset NAME` — apply a built-in preset (forest_fire, ants, boids, wolf_sheep, gray_scott). Optional. If provided, overrides defaults for cells palette, field, agents, etc.
  - `--field NAME` — show this field as background instead of cell states
  - `--cells-cmap NAME` — categorical colormap name (e.g. tab10, Set2)
  - `--field-cmap NAME` — continuous colormap name (e.g. viridis, plasma, magma)
  - `--field-vmin FLOAT`, `--field-vmax FLOAT` — fixed color scale range
  - `--no-cells`, `--no-agents` — disable layers
  - `--show-heading` — draw heading arrows on agents
  - `--fps N` — frame rate for video/gif (default 30 for mp4, 15 for gif)
  - `--quality N` — video quality 1-10 (default 7)
  - `--every N` — only use every Nth snapshot (subsample for speed/size)
  - `--frames N` — for contact sheet: number of frames in the grid (default 12)
  - `--cols N` — for contact sheet: number of columns (default 4)
  - `--tick N` — for single PNG: which tick to render (default: last)
  - `--title TEXT` — optional title for the output
  - `--dpi N` — DPI for raster outputs (default 150)
  - `--figsize WxH` — figure size in inches (e.g. `8x8`)
- Print summary at the end: input file, output file, frame count, elapsed seconds
- Catch errors and print human-readable messages (no Python tracebacks for normal users)
- Write ≥4 integration tests in `tests/test_cli.py`

**Dependencies:** VIZ-A-008, VIZ-A-009, VIZ-A-010, VIZ-A-011

**Expected result:**
A working CLI that handles all four output formats with sensible defaults and full power-user options

**Acceptance criteria:**
- [ ] 4+ integration tests passing
- [ ] `swarmlet-viz render snapshots.jsonl --out fire.mp4` produces a valid MP4
- [ ] `swarmlet-viz render snapshots.jsonl --out fire.gif --every 5` produces a GIF with 1/5 the frames
- [ ] `swarmlet-viz render snapshots.jsonl --out frame.png --tick 100` produces a PNG of tick 100
- [ ] `swarmlet-viz render snapshots.jsonl --out fire_sheet.png --frames 16 --cols 4` produces a contact sheet
- [ ] `swarmlet-viz info snapshots.jsonl` prints metadata
- [ ] Errors print human-readable messages, not Python tracebacks

---

### VIZ-A-013 — Per-example presets for the five Stage 1 references

**Description:**
Define presets for each of the five reference examples in Stage 1. Each preset is a `FrameSpec` instance with the optimal settings for that example: which colormap, which field to show, whether to draw agents, custom title template. Selecting a preset via `--preset NAME` makes "render this example" a one-line command.

**What needs to be done:**

- In `swarmlet_viz/presets.py`, define `PRESETS: Dict[str, FrameSpec]` with one entry per reference example
- **Forest fire preset** (`forest_fire`):
  ```python
  FrameSpec(
      show_cells=True,
      cells_palette={
          "Empty": "#d4c4a0",   # tan
          "Tree": "#2d7a3e",    # forest green
          "Fire": "#ff4500",    # orange-red
          "Ash": "#3d3d3d",     # dark gray
      },
      show_field=None,
      show_agents=False,
      title_template="Forest Fire — t = {t}",
      figsize=(8.0, 8.0),
  )
  ```
- **Ants preset** (`ants`):
  ```python
  FrameSpec(
      show_cells=False,
      show_field="pheromone",
      field_cmap="YlOrRd",
      field_log_scale=False,
      show_agents=True,
      agents_by_type=True,
      agents_palette={"Ant": "#1a1a1a"},  # black ants on warm field
      show_agent_heading=False,
      title_template="Ant Foraging — t = {t}",
      figsize=(8.0, 8.0),
  )
  ```
- **Boids preset** (`boids`):
  ```python
  FrameSpec(
      show_cells=True,  # just one state Empty, renders as flat background
      cells_palette={"Empty": "#f0f0f0"},  # very light gray
      show_field=None,
      show_agents=True,
      agents_by_type=True,
      agents_palette={"Bird": "#1f77b4"},  # blue
      show_agent_heading=True,  # arrows are essential for boids
      title_template="Boids — t = {t}",
      figsize=(8.0, 8.0),
  )
  ```
- **Wolf-sheep preset** (`wolf_sheep`):
  ```python
  FrameSpec(
      show_cells=True,
      cells_palette={
          "Empty": "#c4a574",   # brown earth
          "Grass": "#5cb85c",   # bright green
      },
      show_field=None,
      show_agents=True,
      agents_by_type=True,
      agents_palette={
          "Sheep": "#ffffff",   # white
          "Wolf": "#1a1a1a",    # black
      },
      show_agent_heading=False,
      title_template="Wolf-Sheep — t = {t}",
      figsize=(8.0, 8.0),
  )
  ```
- **Gray-Scott preset** (`gray_scott`):
  ```python
  FrameSpec(
      show_cells=False,
      show_field="v",
      field_cmap="inferno",
      field_vmin=0.0,
      field_vmax=0.5,
      field_log_scale=False,
      field_colorbar=True,
      show_agents=False,
      title_template="Gray-Scott — t = {t}",
      figsize=(8.0, 8.0),
  )
  ```
- Each preset produces visually appealing output with no further configuration. The user runs:
  ```
  swarmlet run forest_fire.swl --ticks 1000 --seed 42 --out fire.jsonl
  swarmlet-viz render fire.jsonl --preset forest_fire --out fire.mp4
  ```
  and gets a beautiful video
- The CLI's `--preset` flag loads the matching FrameSpec, then individual `--field`, `--cells-cmap`, etc. flags can override specific fields of the preset (so the user can take a preset and tweak it)
- Write ≥3 unit tests verifying that each preset is a valid FrameSpec and produces non-empty output when applied to a tiny hand-built snapshot of the corresponding type

**Dependencies:** VIZ-A-012

**Expected result:**
Five working presets that turn rendering into a one-flag operation for any of the reference examples

**Acceptance criteria:**
- [ ] 3+ unit tests passing
- [ ] All five presets defined in `PRESETS`
- [ ] `swarmlet-viz render fire.jsonl --preset forest_fire --out fire.mp4` produces a visually correct video
- [ ] `--preset` combined with individual flags allows overriding (e.g. `--preset gray_scott --field-cmap viridis` overrides the inferno colormap)
- [ ] Each preset color choice is at least defensible aesthetically (manual review on first run)

---

## Phase 5 — Documentation

### VIZ-A-014 — README, gallery, usage examples

**Description:**
Write the user-facing documentation for swarmlet-viz: a README with installation and quickstart, a gallery of pre-rendered examples committed to the repo, and a brief usage guide.

**What needs to be done:**

- Expand `README.md` with:
  - One-paragraph project description: "Offline matplotlib renderer for Swarmlet snapshot files. Produces MP4 videos, GIFs, PNG frames, and contact sheets."
  - Architectural diagram showing swarmlet (Stage 1) → snapshot file → swarmlet-viz → output
  - Installation: `pip install -e .`
  - Quickstart: 4-line example showing the typical workflow:
    ```
    # 1. Install both packages
    pip install -e ../swarmlet
    pip install -e .

    # 2. Run a Swarmlet simulation
    swarmlet run ../swarmlet/examples/forest_fire.swl --ticks 1000 --seed 42 --out fire.jsonl

    # 3. Render to video
    swarmlet-viz render fire.jsonl --preset forest_fire --out fire.mp4
    ```
  - Gallery section embedding pre-rendered images of all five reference examples
  - Link to the planned Stage 2B (web viewer) as future work
- Create `examples/gallery/` directory and commit:
  - `forest_fire_sheet.png` — a contact sheet showing forest fire arc
  - `ants_sheet.png` — ant colony forming pheromone trails
  - `boids_sheet.png` — boids flocking
  - `wolf_sheep_sheet.png` — predator-prey oscillation
  - `gray_scott_sheet.png` — Gray-Scott pattern formation
- Each gallery image is generated by running:
  ```
  swarmlet run examples/<name>.swl --ticks N --seed 42 --out tmp.jsonl
  swarmlet-viz render tmp.jsonl --preset <name> --out gallery/<name>_sheet.png --frames 12 --cols 4
  ```
- These gallery images are the **proof that the project works** and serve as the visual table of contents
- Add a brief `docs/usage.md` (not a tutorial, just a reference) with:
  - All CLI flags and their meanings
  - Available presets
  - Tips: how to choose fps, when to use --every, how to fix color jitter
  - Common workflows: short video for sharing, long video for analysis, contact sheet for documentation
- Write nothing about Stage 2B beyond a one-liner pointing to the planned future work

**Dependencies:** VIZ-A-013, plus working Stage 1 examples (SWARMLET-020..024)

**Expected result:**
A complete user-facing documentation pack: README that converts a curious visitor into a user in 5 minutes, a gallery that proves the project works, a usage reference that answers most questions

**Acceptance criteria:**
- [ ] `README.md` includes installation, quickstart, gallery, link to Stage 2B
- [ ] Five gallery images exist in `examples/gallery/` and are committed to the repo
- [ ] Quickstart in the README runs successfully as written (verified by manual run)
- [ ] `docs/usage.md` covers all CLI flags and presets
- [ ] All gallery images render without errors
- [ ] Gallery images are visually meaningful (not just noise) — manual aesthetic check

---

## Stage 2A scope notes

**Total Stage 2A effort:** 14 issues, ~5–7 working days for one author working alone, or ~3–4 days with Claude Code drafting and author review.

**Hard prerequisites for Stage 2A:**
- Stage 1 (swarmlet) at minimum at SWARMLET-018 complete (snapshot serialization works)
- Python 3.11+
- `numpy`, `matplotlib`, `imageio[ffmpeg]`, `pillow`
- Reading SPEC.md section 9.1 (snapshot structure) before starting VIZ-A-002

**Files created by Stage 2A:**
- `swarmlet-viz/` separate repository
- Package `swarmlet_viz/` with submodules `loader`, `model`, `render/{cells,fields,agents,composite}`, `output/{mp4,gif,png,sheet}`, `presets`, `cli`
- `tests/` with one test file per module (~14 test files)
- `examples/gallery/` with 5 pre-rendered contact sheets
- `README.md`, `docs/usage.md`

**Files NOT touched by Stage 2A:**
- Anything in the `swarmlet/` repo. Stage 2A does NOT modify Stage 1. This is a strict architectural boundary
- Anything related to Node.js, browser, web. That is Stage 2B and a separate plan

**Critical correctness gates:**

- **Snapshot contract:** the loader must accept any valid output of `swarmlet run --out`. Any bug in the loader that mis-parses a Stage 1 output is a critical regression. The round-trip test in VIZ-A-002 guards this
- **Memory management:** rendering must close matplotlib figures after each frame. Otherwise long simulations leak memory and crash. Tested in VIZ-A-008
- **Color consistency in animations:** auto vmin/vmax must be computed across all frames, not per-frame, to avoid color jitter. Tested in VIZ-A-005 and VIZ-A-008
- **Preset aesthetics:** each preset must produce visually clean output for its target example. Manual review during VIZ-A-013

**Critical design gates:**

- **One-way dependency:** swarmlet-viz depends on the snapshot file format, NOT on the swarmlet Python package. This keeps the visualizer working even if Stage 1 internals change, as long as the snapshot format stays stable
- **Layer composition rules:** cells and fields are mutually exclusive as background. Agents are always overlay. Documented in VIZ-A-007
- **Format dispatch by extension:** the CLI infers format from `--out` extension. No `--format` flag needed. This matches Unix convention

**After Stage 2A is merged,** the Swarmlet ecosystem has:
- Working interpreter (Stage 1)
- Working offline visualizer that produces shareable videos, GIFs, frames, and contact sheets
- A gallery of 5 reference examples ready for documentation, presentations, and social media
- A proven snapshot contract that the future web viewer will inherit
- All architectural decisions for Stage 2B can now be made by **looking at real videos** and asking "what would I want from an interactive version of this?", instead of speculating

**What Stage 2B will add on top of Stage 2A:**
- Browser-based interactive playback (not offline rendering)
- Live parameter tuning with re-run
- Shareable URLs with seed and params
- Side-by-side comparison
- Fastify backend that wraps swarmlet CLI
- Svelte 5 + TypeScript + Canvas frontend
- Server-Sent Events for real-time streaming

**What Stage 2A is NOT:**
- Real-time playback (matplotlib is too slow for that — that's Stage 2B's purpose)
- Interactive (no zoom, pan, click)
- Browser-based (Stage 2B)
- A replacement for Stage 2B (it's a stepping stone)

The decision to do Stage 2A first is deliberate and pragmatic. After Stage 2A, the Swarmlet project has visible output, the snapshot contract is battle-tested, and Stage 2B can be designed by experience instead of by speculation.
