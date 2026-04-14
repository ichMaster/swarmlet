"""Integration tests for the CLI."""

import json
import os
import subprocess
import sys
import tempfile

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples")
FOREST_FIRE = os.path.join(EXAMPLES, "forest_fire.swl")
BROKEN = os.path.join(EXAMPLES, "broken.swl")


def run_cli(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "swarmlet"] + list(args),
        capture_output=True, text=True, timeout=30,
    )


def test_check_valid():
    """swarmlet check forest_fire.swl exits 0."""
    result = run_cli("check", FOREST_FIRE)
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_check_broken():
    """swarmlet check broken.swl exits 1 with error."""
    result = run_cli("check", BROKEN)
    assert result.returncode == 1
    assert "Error" in result.stderr or "error" in result.stderr.lower()


def test_run_jsonl():
    """swarmlet run forest_fire.swl produces valid JSONL."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        result = run_cli("run", FOREST_FIRE, "--ticks", "10", "--seed", "42", "--out", path)
        assert result.returncode == 0

        with open(path) as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 11  # initial + 10 ticks

        # Verify each line is valid JSON
        for line in lines:
            snap = json.loads(line)
            assert "tick" in snap
            assert "states" in snap
    finally:
        os.unlink(path)


def test_param_override():
    """--param should override param values."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        result = run_cli("run", FOREST_FIRE, "--ticks", "5", "--seed", "42",
                         "--out", path, "--param", "p_grow=0.5", "--param", "p_fire=0.0")
        assert result.returncode == 0

        with open(path) as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 6
    finally:
        os.unlink(path)


def test_run_no_output():
    """Run without --out should print summary."""
    result = run_cli("run", FOREST_FIRE, "--ticks", "5", "--seed", "42")
    assert result.returncode == 0
    assert "Ticks: 5" in result.stdout
