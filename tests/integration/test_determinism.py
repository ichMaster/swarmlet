"""Determinism harness: two World instances with same seed must produce
identical snapshot sequences. Different seeds must differ."""

import hashlib
import json
import os
from swarmlet.parser import parse
from swarmlet.engine import World

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "swarmlet", "examples")

# Use fewer ticks for examples with agents (they're slower)
EXAMPLE_TICKS = {
    "forest_fire.swl": 20,
    "ants.swl": 10,
    "boids.swl": 10,
    "wolf_sheep.swl": 10,
    "gray_scott.swl": 5,
}


def _snapshot_hash(world):
    """Hash the current snapshot for comparison."""
    snap = world.snapshot()
    return hashlib.sha256(json.dumps(snap, sort_keys=True).encode()).hexdigest()


def _run_and_hash(source, seed, ticks):
    """Run a program and return list of snapshot hashes."""
    prog = parse(source)
    w = World(prog, seed=seed)
    hashes = [_snapshot_hash(w)]
    for _ in range(ticks):
        w.step(1)
        hashes.append(_snapshot_hash(w))
    return hashes


def test_forest_fire_determinism():
    _check_determinism("forest_fire.swl")


def test_ants_determinism():
    _check_determinism("ants.swl")


def test_boids_determinism():
    _check_determinism("boids.swl")


def test_wolf_sheep_determinism():
    _check_determinism("wolf_sheep.swl")


def test_gray_scott_determinism():
    _check_determinism("gray_scott.swl")


def _check_determinism(filename):
    path = os.path.join(EXAMPLES_DIR, filename)
    with open(path) as f:
        source = f.read()

    ticks = EXAMPLE_TICKS[filename]

    # Two runs with same seed must be identical
    hashes1 = _run_and_hash(source, seed=42, ticks=ticks)
    hashes2 = _run_and_hash(source, seed=42, ticks=ticks)
    assert hashes1 == hashes2, f"{filename}: same seed produced different hashes"

    # Different seed must differ (skip for purely deterministic models with no RNG calls)
    if filename != "gray_scott.swl":
        hashes3 = _run_and_hash(source, seed=43, ticks=ticks)
        assert hashes1 != hashes3, f"{filename}: different seeds produced same hashes"
