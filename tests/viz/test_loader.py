"""Tests for swarmlet.viz.loader (SWARMLET-028)."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from swarmlet.viz.loader import load_file, load_jsonl, load_npz


def _write_jsonl(tmp_path: Path, snapshots):
    p = tmp_path / "snaps.jsonl"
    with p.open("w") as f:
        for snap in snapshots:
            f.write(json.dumps(snap) + "\n")
    return p


def _make_raw_snapshot(tick: int, w: int = 3, h: int = 2, fill: str = "Empty"):
    return {
        "tick": tick,
        "width": w,
        "height": h,
        "topology": "wrap",
        "states": [[fill] * w for _ in range(h)],
        "fields": {"heat": [[float(tick)] * w for _ in range(h)]},
        "agents": [],
    }


def test_load_jsonl_one_snapshot(tmp_path):
    p = _write_jsonl(tmp_path, [_make_raw_snapshot(0)])
    snaps = load_jsonl(p)
    assert len(snaps) == 1
    s = snaps[0]
    assert s["t"] == 0
    assert s["world"] == {"w": 3, "h": 2, "wrap": True}
    assert s["states"].shape == (2, 3)
    assert s["states_legend"] == ["Empty"]
    assert "heat" in s["fields"]
    assert s["fields"]["heat"].shape == (2, 3)


def test_load_jsonl_100_snapshots(tmp_path):
    raw = [_make_raw_snapshot(t) for t in range(100)]
    p = _write_jsonl(tmp_path, raw)
    snaps = load_jsonl(p)
    assert len(snaps) == 100
    assert [s["t"] for s in snaps] == list(range(100))
    assert all(s["states"].dtype == np.int8 for s in snaps)


def test_load_jsonl_legend_unions_across_snapshots(tmp_path):
    s0 = _make_raw_snapshot(0, fill="Empty")
    s1 = _make_raw_snapshot(1, fill="Tree")
    s2 = _make_raw_snapshot(2, fill="Fire")
    p = _write_jsonl(tmp_path, [s0, s1, s2])
    snaps = load_jsonl(p)
    assert snaps[0]["states_legend"] == ["Empty", "Fire", "Tree"]
    for s in snaps:
        assert s["states_legend"] == snaps[0]["states_legend"]


def _write_synthetic_npz(path: Path, ticks: int, w: int, h: int,
                         state_names, field_names, every: int = 1):
    """Build an NPZ file matching swarmlet.snapshot.write_npz's on-disk layout."""
    data = {}
    meta = {
        "width": w, "height": h, "topology": "wrap",
        "state_names": state_names, "field_names": field_names,
        "every": every, "ticks": ticks,
    }
    data["metadata"] = json.dumps(meta)
    for t in [0] + list(range(every, ticks + 1, every)):
        prefix = f"tick_{t}"
        data[f"{prefix}_states"] = np.zeros((h, w), dtype=np.int32)
        for fn in field_names:
            data[f"{prefix}_{fn}"] = np.full((h, w), float(t), dtype=np.float64)
        data[f"{prefix}_agents"] = json.dumps([])
    np.savez_compressed(path, **data)


def test_load_npz_one_snapshot(tmp_path):
    states_legend = ["Empty", "Tree"]
    out = tmp_path / "snaps.npz"
    _write_synthetic_npz(out, ticks=0, w=3, h=2,
                         state_names=states_legend, field_names=["heat"])
    snaps = load_npz(out)
    assert len(snaps) == 1
    s = snaps[0]
    assert s["t"] == 0
    assert s["world"]["w"] == 3 and s["world"]["h"] == 2
    assert s["states"].shape == (2, 3)
    assert s["states"].dtype == np.int8
    assert s["states_legend"] == states_legend
    assert s["fields"]["heat"].shape == (2, 3)


def test_load_npz_100_snapshots_multiple_fields(tmp_path):
    out = tmp_path / "snaps.npz"
    _write_synthetic_npz(out, ticks=99, w=4, h=3,
                         state_names=["A", "B"], field_names=["f1", "f2"])
    snaps = load_npz(out)
    assert len(snaps) == 100
    assert [s["t"] for s in snaps] == list(range(100))
    for s in snaps:
        assert "f1" in s["fields"]
        assert "f2" in s["fields"]
        assert s["fields"]["f1"].shape == (3, 4)
        assert s["fields"]["f2"].dtype == np.float32


def test_load_file_dispatches_jsonl(tmp_path):
    p = _write_jsonl(tmp_path, [_make_raw_snapshot(7)])
    snaps = load_file(p)
    assert len(snaps) == 1
    assert snaps[0]["t"] == 7


def test_load_file_dispatches_npz(tmp_path):
    out = tmp_path / "snaps.npz"
    _write_synthetic_npz(out, ticks=2, w=2, h=2,
                         state_names=["X"], field_names=[])
    snaps = load_file(out)
    assert len(snaps) == 3


def test_load_file_unknown_extension_raises(tmp_path):
    p = tmp_path / "snaps.txt"
    p.write_text("garbage")
    with pytest.raises(ValueError, match="Unsupported snapshot file extension"):
        load_file(p)


def test_round_trip_forest_fire(tmp_path):
    """End-to-end: run forest_fire.swl, then load the JSONL output."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    example = repo_root / "swarmlet" / "examples" / "forest_fire.swl"
    out = tmp_path / "ff.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "swarmlet", "run", str(example),
         "--ticks", "5", "--seed", "1", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"swarmlet run failed: {result.stderr}"
    assert out.exists()
    snaps = load_file(out)
    assert len(snaps) == 6  # ticks 0..5 inclusive
    assert all("t" in s and "world" in s for s in snaps)
    assert all(isinstance(s["states"], np.ndarray) for s in snaps)
    assert snaps[0]["world"]["w"] > 0 and snaps[0]["world"]["h"] > 0


def test_jsonl_streams_line_by_line(tmp_path, monkeypatch):
    """Confirm JSONL parsing iterates per line rather than reading whole file."""
    raw = [_make_raw_snapshot(t) for t in range(10)]
    p = _write_jsonl(tmp_path, raw)

    real_open = Path.open
    read_calls = {"n": 0}

    def tracking_open(self, *args, **kwargs):
        f = real_open(self, *args, **kwargs)
        original_read = f.read

        def counted_read(*a, **kw):
            read_calls["n"] += 1
            return original_read(*a, **kw)

        f.read = counted_read
        return f

    monkeypatch.setattr(Path, "open", tracking_open)
    snaps = load_jsonl(p)
    assert len(snaps) == 10
    assert read_calls["n"] == 0, "loader should iterate, not call .read()"
