"""Snapshot file loaders: JSONL and NPZ → list of dict snapshots.

Returns dicts in the SPEC.md section 9.1 format:
    {
        "t": int,
        "world": {"w": int, "h": int, "wrap": bool},
        "states": np.ndarray[H, W] (int8, indices into states_legend),
        "states_legend": list[str],
        "fields": dict[str, np.ndarray[H, W]] (float32),
        "agents": list[dict],
    }

The on-disk JSONL format produced by `swarmlet run --out` stores cell states
as name strings; this loader normalizes them into integer indices plus a
sorted legend of unique state names found across the file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Union

import numpy as np


def load_jsonl(path: Union[str, Path]) -> List[dict]:
    """Stream a JSONL snapshot file line by line, return list of normalized dicts.

    Each line is parsed individually rather than reading the whole file into
    one string, so memory use stays proportional to one snapshot at a time
    during parsing.
    """
    path = Path(path)
    raw: List[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw.append(json.loads(line))
    legend = _build_legend(raw)
    return [_normalize_jsonl_snapshot(d, legend) for d in raw]


def load_npz(path: Union[str, Path]) -> List[dict]:
    """Read a compressed numpy archive, return list of normalized dicts."""
    path = Path(path)
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["metadata"]))
        legend = list(meta["state_names"])
        field_names = list(meta["field_names"])
        every = int(meta["every"])
        ticks = int(meta["ticks"])
        wrap = meta.get("topology", "wrap") == "wrap"
        w = int(meta["width"])
        h = int(meta["height"])

        snapshots: List[dict] = []
        tick_values = [0] + [t for t in range(every, ticks + 1, every) if t != 0]
        for t in tick_values:
            states_key = f"tick_{t}_states"
            if states_key not in data.files:
                continue
            states = np.asarray(data[states_key], dtype=np.int8)
            fields = {
                fn: np.asarray(data[f"tick_{t}_{fn}"], dtype=np.float32)
                for fn in field_names
                if f"tick_{t}_{fn}" in data.files
            }
            agents = json.loads(str(data[f"tick_{t}_agents"]))
            snapshots.append({
                "t": t,
                "world": {"w": w, "h": h, "wrap": wrap},
                "states": states,
                "states_legend": legend,
                "fields": fields,
                "agents": agents,
            })
        return snapshots


def load_file(path: Union[str, Path]) -> List[dict]:
    """Dispatch to the right loader based on file extension."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".jsonl":
        return load_jsonl(p)
    if suffix == ".npz":
        return load_npz(p)
    raise ValueError(
        f"Unsupported snapshot file extension: '{suffix}' "
        f"(expected '.jsonl' or '.npz')"
    )


def _build_legend(raw_snapshots: List[dict]) -> List[str]:
    """Collect sorted unique state names found across all snapshots."""
    names: set = set()
    for d in raw_snapshots:
        for row in d.get("states", []):
            for cell in row:
                names.add(cell)
    return sorted(names)


def _normalize_jsonl_snapshot(d: dict, legend: List[str]) -> dict:
    """Convert raw on-disk JSONL dict into a SPEC.md section 9.1 dict."""
    legend_idx = {n: i for i, n in enumerate(legend)}
    states_grid = d.get("states", [])
    if states_grid:
        states = np.array(
            [[legend_idx[name] for name in row] for row in states_grid],
            dtype=np.int8,
        )
    else:
        states = np.zeros((int(d["height"]), int(d["width"])), dtype=np.int8)
    fields = {
        name: np.asarray(arr, dtype=np.float32)
        for name, arr in d.get("fields", {}).items()
    }
    return {
        "t": int(d["tick"]),
        "world": {
            "w": int(d["width"]),
            "h": int(d["height"]),
            "wrap": d.get("topology", "wrap") == "wrap",
        },
        "states": states,
        "states_legend": legend,
        "fields": fields,
        "agents": list(d.get("agents", [])),
    }
