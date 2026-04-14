"""Snapshot serialization — JSONL and NPZ formats."""

from __future__ import annotations

import json
from typing import Callable, Optional

import numpy as np


def write_jsonl(world, path: str, ticks: int, every: int = 1,
                progress: Optional[Callable] = None):
    """Run simulation and write snapshots to line-delimited JSON file.

    Args:
        world: World instance
        path: output file path (.jsonl)
        ticks: number of ticks to simulate
        every: write every N-th tick (default 1)
        progress: optional callback(tick) for progress reporting
    """
    with open(path, "w") as f:
        # Write initial snapshot
        f.write(json.dumps(world.snapshot()) + "\n")

        for t in range(1, ticks + 1):
            world.step(1)
            if t % every == 0:
                f.write(json.dumps(world.snapshot()) + "\n")
            if progress:
                progress(t)


def write_npz(world, path: str, ticks: int, every: int = 1,
              progress: Optional[Callable] = None):
    """Run simulation and write snapshots to compressed numpy archive.

    The archive contains:
        - tick_N_states: state index array for tick N
        - tick_N_<fieldname>: field array for tick N
        - tick_N_agents: JSON string of agent data for tick N
        - metadata: JSON string with world dimensions, state names, etc.
    """
    data = {}
    # Metadata
    meta = {
        "width": world.width,
        "height": world.height,
        "topology": world.topology,
        "state_names": world.state_names,
        "field_names": world.field_names,
        "every": every,
        "ticks": ticks,
    }
    data["metadata"] = json.dumps(meta)

    # Initial snapshot
    _add_npz_snapshot(data, world, 0)

    for t in range(1, ticks + 1):
        world.step(1)
        if t % every == 0:
            _add_npz_snapshot(data, world, t)
        if progress:
            progress(t)

    np.savez_compressed(path, **data)


def _add_npz_snapshot(data: dict, world, tick: int):
    """Add a single snapshot to the NPZ data dict."""
    prefix = f"tick_{tick}"
    data[f"{prefix}_states"] = world.states.copy()
    for fname, arr in world.fields.items():
        data[f"{prefix}_{fname}"] = arr.copy()
    agents_json = json.dumps([
        {"id": a.id, "type": a.agent_type, "x": a.x, "y": a.y, "fields": a.fields}
        for a in world.agents if a.alive
    ])
    data[f"{prefix}_agents"] = agents_json


def read_jsonl(path: str) -> list:
    """Read snapshots from a JSONL file. Returns list of dicts."""
    snapshots = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                snapshots.append(json.loads(line))
    return snapshots
