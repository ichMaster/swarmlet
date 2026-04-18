"""Swarmlet offline visualizer — consumes snapshot files and renders frames/videos.

This sub-package depends only on the snapshot file format documented in SPEC.md
section 9.1. It does not import from the interpreter (lexer/parser/eval/engine).
The boundary is enforced by tests/viz/test_import_boundary.py.
"""


class SnapshotError(Exception):
    """Raised when a loaded snapshot violates the documented format contract."""


def load_snapshots(path):
    """Load snapshots from a JSONL or NPZ file as validated Snapshot objects."""
    from swarmlet.viz.model import load_snapshots as _impl
    return _impl(path)


def render_frame(snapshot, spec=None):
    """Render a single snapshot to a matplotlib Figure according to spec."""
    raise NotImplementedError("render_frame() will be implemented in SWARMLET-033")


class FrameSpec:
    """Declarative specification for how to render a frame (layers, colormaps, overlays)."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("FrameSpec will be implemented in SWARMLET-033")
