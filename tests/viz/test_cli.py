"""Integration tests for swarmlet-viz CLI (SWARMLET-038)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

from swarmlet.viz.cli import _dispatch_format, main


def _write_jsonl(path: Path, n_ticks: int = 6):
    h = w = 5
    names = ["Empty", "Tree", "Fire"]
    with open(path, "w") as f:
        for t in range(n_ticks):
            grid = [[names[(y * w + x + t) % 3] for x in range(w)] for y in range(h)]
            snap = {
                "tick": t,
                "width": w,
                "height": h,
                "topology": "wrap",
                "states": grid,
                "fields": {"heat": [[t * 0.1] * w for _ in range(h)]},
                "agents": [
                    {"type": "Bird", "id": 1, "x": 1, "y": 1, "heading": t % 8},
                ],
            }
            f.write(json.dumps(snap) + "\n")


def test_dispatch_format():
    assert _dispatch_format(Path("a.mp4")) == "mp4"
    assert _dispatch_format(Path("a.gif")) == "gif"
    assert _dispatch_format(Path("a.png")) == "png"
    assert _dispatch_format(Path("a_sheet.png")) == "sheet"
    with pytest.raises(ValueError):
        _dispatch_format(Path("a.txt"))


def test_render_mp4(tmp_path: Path, capsys):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps)
    out = tmp_path / "out.mp4"
    rc = main([
        "render",
        str(snaps),
        "--out",
        str(out),
        "--fps",
        "5",
        "--figsize",
        "2x2",
        "--dpi",
        "80",
    ])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0
    assert "rendered" in capsys.readouterr().out


def test_render_gif_with_every(tmp_path: Path):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps, n_ticks=10)
    out = tmp_path / "out.gif"
    rc = main([
        "render",
        str(snaps),
        "--out",
        str(out),
        "--every",
        "2",
        "--fps",
        "5",
        "--figsize",
        "2x2",
        "--dpi",
        "80",
    ])
    assert rc == 0 and out.exists()


def test_render_png_at_tick(tmp_path: Path):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps)
    out = tmp_path / "frame.png"
    rc = main([
        "render",
        str(snaps),
        "--out",
        str(out),
        "--tick",
        "3",
        "--figsize",
        "2x2",
        "--dpi",
        "80",
    ])
    assert rc == 0 and out.exists()


def test_render_contact_sheet(tmp_path: Path):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps, n_ticks=12)
    out = tmp_path / "out_sheet.png"
    rc = main([
        "render",
        str(snaps),
        "--out",
        str(out),
        "--frames",
        "4",
        "--cols",
        "2",
        "--dpi",
        "80",
    ])
    assert rc == 0 and out.exists()


def test_info_prints_metadata(tmp_path: Path, capsys):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps)
    rc = main(["info", str(snaps)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "snapshots: 6" in out
    assert "world: 5 x 5" in out
    assert "heat" in out


def test_missing_file_reports_error(tmp_path: Path, capsys):
    rc = main(["render", str(tmp_path / "nope.jsonl"), "--out", str(tmp_path / "o.mp4")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "snapshot file not found" in err


def test_bad_extension_reports_error(tmp_path: Path, capsys):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps)
    rc = main(["render", str(snaps), "--out", str(tmp_path / "x.txt")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "unsupported output extension" in err


def test_unknown_preset_reports_error(tmp_path: Path, capsys):
    snaps = tmp_path / "snaps.jsonl"
    _write_jsonl(snaps)
    rc = main([
        "render",
        str(snaps),
        "--out",
        str(tmp_path / "x.mp4"),
        "--preset",
        "does_not_exist",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown preset" in err


def test_version_subcommand(capsys):
    rc = main(["version"])
    assert rc == 0
    assert "swarmlet-viz" in capsys.readouterr().out
