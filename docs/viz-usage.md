# swarmlet-viz — CLI reference

`swarmlet-viz` is the offline renderer shipped with Swarmlet. It consumes snapshot files produced by `swarmlet run --out` and writes videos, GIFs, single frames, or contact sheets.

Install with the `[viz]` extras:

```bash
pip install -e ".[viz]"
```

## Commands

```
swarmlet-viz render <snapshots_file> --out <path> [options]
swarmlet-viz info   <snapshots_file>
swarmlet-viz version
```

Output format is inferred from the `--out` extension:

| Extension             | Format                          |
|-----------------------|---------------------------------|
| `.mp4`                | MP4 video                       |
| `.gif`                | Animated GIF                    |
| `*_sheet.png`         | Contact sheet (grid of frames)  |
| `.png`                | Single-frame PNG                |

## `render` flags

Input selection:

| Flag | Description |
|---|---|
| `--every N`          | Keep every Nth snapshot (thins the stream before rendering). |
| `--tick N`           | For `.png` output: render the snapshot with tick N (closest wins). |

Preset + layer control:

| Flag | Description |
|---|---|
| `--preset NAME`      | Apply a built-in preset. Individual flags below still override. |
| `--field NAME`       | Show this field as background (replaces cells). |
| `--no-cells`         | Do not draw the cell-state background. |
| `--no-agents`        | Do not draw the agent overlay. |
| `--show-heading`     | Draw heading arrows on agents (Boids-style). |

Color and scale:

| Flag | Description |
|---|---|
| `--cells-cmap NAME`  | Categorical colormap for cell states (e.g. `tab10`, `Set2`). |
| `--field-cmap NAME`  | Continuous colormap for the field layer (e.g. `viridis`, `inferno`). |
| `--field-vmin FLOAT` | Fixed minimum of the field color scale. |
| `--field-vmax FLOAT` | Fixed maximum of the field color scale. |
| `--field-log-scale`  | Use `LogNorm` for the field (clips zero/negative cells). |

Figure and timing:

| Flag | Description |
|---|---|
| `--fps N`            | Frames per second. Default: 30 for MP4, 15 for GIF. |
| `--quality N`        | MP4 quality 1-10 (default 7). |
| `--figsize WxH`      | Figure size in inches, e.g. `8x6`. |
| `--dpi N`            | Raster DPI (default 150). |
| `--title TEXT`       | Title text, or a template containing `{t}` that expands to the tick. |

Contact sheet:

| Flag | Description |
|---|---|
| `--frames N`         | Number of frames in the sheet (default 12). |
| `--cols N`           | Number of columns in the sheet (default 4). |

## Presets

Five presets are bundled for the reference examples. Each is a tuned `FrameSpec`.

| Name          | Highlights |
|---------------|-----------|
| `forest_fire` | Warm categorical palette (Empty / Tree / Fire / Ash), no agents. |
| `ants`        | `pheromone` field on `YlOrRd`, black ant dots. |
| `boids`       | Light-gray background, blue Bird agents with heading arrows. |
| `wolf_sheep`  | Earth/grass cells, white sheep on black wolves. |
| `gray_scott`  | `v` field on `inferno`, pinned to `[0.0, 0.5]`, with colorbar. |

Load a preset with `--preset <name>`; individual flags override specific fields on top.

## Recipes

### Short shareable clip

```bash
swarmlet run examples/forest_fire.swl --ticks 400 --seed 42 --out fire.jsonl
swarmlet-viz render fire.jsonl --preset forest_fire --out fire.gif --every 4 --fps 15
```

### Long analysis video

```bash
swarmlet run examples/gray_scott.swl --ticks 5000 --seed 7 --out gs.jsonl
swarmlet-viz render gs.jsonl --preset gray_scott --out gs.mp4 --fps 60 --quality 9
```

### Documentation image (single frame at a specific tick)

```bash
swarmlet-viz render gs.jsonl --preset gray_scott --out gs_t1000.png --tick 1000 --dpi 200
```

### Contact sheet of the run's arc

```bash
swarmlet-viz render gs.jsonl --preset gray_scott --out gs_sheet.png --frames 16 --cols 4
```

### Avoiding color flicker

For field-heavy videos, pre-compute the color range:

```bash
swarmlet-viz render gs.jsonl --preset gray_scott --field-vmin 0 --field-vmax 0.5 --out gs.mp4
```

Without `--field-vmin`/`--field-vmax`, the renderer auto-ranges across all frames, which also avoids flicker but pays a pre-pass over the snapshots.

## Tips

- **Subsample first, interpolate never.** If a long run produces a 50 MB JSONL, `--every 10` before rendering is almost always the right move. The visualizer does not interpolate between frames — dropping ticks is how you shorten videos.
- **Pick a backend deliberately.** MP4 is best for sharing and scrubbing; GIF is best for embedding in markdown and chat; PNG is best for slides; contact sheets beat all three for documentation.
- **Check `info` before you render.** `swarmlet-viz info snapshots.jsonl` tells you the tick count, grid size, available fields, and agent types — saves time when the snapshot file is unfamiliar.
