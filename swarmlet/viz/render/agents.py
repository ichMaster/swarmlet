"""Agent overlay renderer.

Draws agents as scatter points on top of an existing axes, optionally grouped
by ``type`` with one color per type and with heading arrows pointing along the
8 Moore directions (SPEC Appendix B: 0..7 clockwise from East, y-axis down).
"""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt

from swarmlet.viz.model import AgentRecord, Snapshot

HEADING_DELTAS = {
    0: (1, 0),     # E
    1: (1, 1),     # SE
    2: (0, 1),     # S
    3: (-1, 1),    # SW
    4: (-1, 0),    # W
    5: (-1, -1),   # NW
    6: (0, -1),    # N
    7: (1, -1),    # NE
}

_DEFAULT_PALETTE_ORDER = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#ffff33",
    "#a65628",
    "#f781bf",
]


def _agent_heading(agent: AgentRecord):
    for name, value in agent.fields:
        if name == "heading":
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


def _auto_marker_size(snap: Snapshot) -> float:
    dim = max(snap.world.w, snap.world.h)
    if dim <= 0:
        return 20.0
    return max(6.0, min(60.0, 2400.0 / dim))


def render_agents(
    snap: Snapshot,
    ax: plt.Axes,
    by_type: bool = True,
    type_palette: Optional[Dict[str, str]] = None,
    marker_size: Optional[float] = None,
    show_heading: bool = False,
    heading_arrow_length: float = 0.7,
    show_legend: bool = True,
) -> None:
    """Overlay agents onto *ax* as scatter points, optionally with heading arrows."""
    if not snap.agents:
        return

    size = marker_size if marker_size is not None else _auto_marker_size(snap)

    if by_type:
        groups: Dict[str, list] = {}
        for a in snap.agents:
            groups.setdefault(a.type, []).append(a)
    else:
        groups = {"*": list(snap.agents)}

    palette: Dict[str, str] = {}
    for i, type_name in enumerate(sorted(groups)):
        if type_palette and type_name in type_palette:
            palette[type_name] = type_palette[type_name]
        else:
            palette[type_name] = _DEFAULT_PALETTE_ORDER[i % len(_DEFAULT_PALETTE_ORDER)]

    for type_name, members in groups.items():
        xs = [a.x for a in members]
        ys = [a.y for a in members]
        ax.scatter(
            xs,
            ys,
            s=size,
            c=palette[type_name],
            edgecolors="black",
            linewidths=0.5,
            label=type_name if by_type else None,
            zorder=3,
        )

    if show_heading:
        for a in snap.agents:
            h = _agent_heading(a)
            if h is None or h not in HEADING_DELTAS:
                continue
            dx, dy = HEADING_DELTAS[h]
            color = palette[a.type if by_type else "*"]
            ax.arrow(
                a.x,
                a.y,
                dx * heading_arrow_length,
                dy * heading_arrow_length,
                head_width=0.25,
                head_length=0.2,
                fc=color,
                ec="black",
                linewidth=0.5,
                length_includes_head=True,
                zorder=4,
            )

    if by_type and show_legend and len(groups) > 1:
        ax.legend(
            loc="upper right",
            frameon=True,
            framealpha=0.8,
            markerscale=0.8,
            fontsize="small",
        )
