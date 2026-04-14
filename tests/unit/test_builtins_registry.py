"""Tests for built-in name registry and direction encoding."""

from swarmlet.builtins import (
    BUILTIN_NAMES, CELL_CONTEXT_ONLY, AGENT_CONTEXT_ONLY, HEADING_REQUIRED,
    DIRECTIONS, STAY, dir_offset, rotate_dir,
)


def test_sets_are_frozen_and_nonempty():
    assert isinstance(BUILTIN_NAMES, frozenset)
    assert isinstance(CELL_CONTEXT_ONLY, frozenset)
    assert isinstance(AGENT_CONTEXT_ONLY, frozenset)
    assert isinstance(HEADING_REQUIRED, frozenset)
    assert len(BUILTIN_NAMES) > 0
    assert len(CELL_CONTEXT_ONLY) > 0
    assert len(AGENT_CONTEXT_ONLY) > 0
    assert len(HEADING_REQUIRED) > 0


def test_dir_offset_east():
    assert dir_offset(0) == (1, 0)


def test_dir_offset_south():
    assert dir_offset(2) == (0, 1)


def test_dir_offset_stay():
    assert dir_offset(STAY) == (0, 0)


def test_all_eight_directions():
    expected = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    for i, exp in enumerate(expected):
        assert dir_offset(i) == exp, f"dir_offset({i}) should be {exp}"


def test_rotate_dir_180():
    assert rotate_dir(0, 4) == 4  # E -> W


def test_rotate_dir_wrap():
    assert rotate_dir(6, 4) == 2  # N -> S


def test_rotate_stay():
    assert rotate_dir(STAY, 3) == STAY


def test_forward_back_left_right_directions():
    """Verify the SPEC: forward=H, back=(H+4)%8, right=(H+2)%8, left=(H+6)%8."""
    for heading in range(8):
        assert rotate_dir(heading, 0) == heading          # forward
        assert rotate_dir(heading, 4) == (heading + 4) % 8  # back
        assert rotate_dir(heading, 2) == (heading + 2) % 8  # right
        assert rotate_dir(heading, 6) == (heading + 6) % 8  # left


def test_heading_required_subset():
    assert HEADING_REQUIRED == {"forward", "back", "left", "right"}
    assert HEADING_REQUIRED.issubset(BUILTIN_NAMES)
