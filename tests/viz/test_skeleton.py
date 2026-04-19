"""Trivial smoke test for the viz sub-package skeleton (SWARMLET-027)."""

import swarmlet.viz as viz


def test_viz_package_imports():
    assert hasattr(viz, "load_snapshots")
    assert hasattr(viz, "render_frame")
    assert hasattr(viz, "FrameSpec")
    assert hasattr(viz, "SnapshotError")


def test_snapshot_error_is_exception():
    assert issubclass(viz.SnapshotError, Exception)


def test_render_entry_points_are_callable():
    """After SWARMLET-033, render_frame and FrameSpec return concrete objects."""
    spec = viz.FrameSpec()
    assert hasattr(spec, "show_cells")
    assert hasattr(spec, "show_agents")
