"""Trivial smoke test for the viz sub-package skeleton (SWARMLET-027)."""

import swarmlet.viz as viz


def test_viz_package_imports():
    assert hasattr(viz, "load_snapshots")
    assert hasattr(viz, "render_frame")
    assert hasattr(viz, "FrameSpec")
    assert hasattr(viz, "SnapshotError")


def test_snapshot_error_is_exception():
    assert issubclass(viz.SnapshotError, Exception)


def test_render_stubs_raise_not_implemented():
    """render_frame and FrameSpec are not yet implemented (SWARMLET-033)."""
    import pytest
    with pytest.raises(NotImplementedError):
        viz.render_frame(None)
    with pytest.raises(NotImplementedError):
        viz.FrameSpec()
