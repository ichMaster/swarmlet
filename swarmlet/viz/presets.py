"""Built-in render presets for the reference examples.

Each entry is a :class:`FrameSpec` tuned for a specific example.
The CLI ``--preset NAME`` flag loads one of these as the base spec; individual
CLI flags then override specific fields on top.

Populated in SWARMLET-039.
"""

from __future__ import annotations

from typing import Dict

from swarmlet.viz.render.composite import FrameSpec

PRESETS: Dict[str, FrameSpec] = {}
