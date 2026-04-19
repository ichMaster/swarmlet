"""Built-in render presets for the five reference examples.

Each entry is a :class:`FrameSpec` tuned for a specific example. The CLI
``--preset NAME`` flag loads one of these as the base spec; individual flags
then override specific fields on top.
"""

from __future__ import annotations

from typing import Dict

from swarmlet.viz.render.composite import FrameSpec


PRESETS: Dict[str, FrameSpec] = {
    "forest_fire": FrameSpec(
        show_cells=True,
        cells_palette={
            "Empty": "#d2b48c",        # tan
            "Tree": "#1f7a3a",         # forest green
            "Fire": "#e4572e",         # orange-red
            "Ash": "#3a3a3a",          # dark gray
        },
        show_field=None,
        show_agents=False,
        title_template="Forest Fire — t = {t}",
        figsize=(7.0, 7.0),
    ),
    "ants": FrameSpec(
        show_cells=False,
        show_field="pheromone",
        field_cmap="YlOrRd",
        field_colorbar=True,
        show_agents=True,
        agents_palette={"Ant": "#000000"},
        agent_marker_size=6.0,
        show_agent_heading=False,
        title_template="Ant Foraging — t = {t}",
        figsize=(7.0, 7.0),
    ),
    "boids": FrameSpec(
        show_cells=True,
        cells_palette={"Empty": "#eeeeee"},
        show_field=None,
        show_agents=True,
        agents_palette={"Bird": "#1f5fb4"},
        show_agent_heading=True,
        title_template="Boids — t = {t}",
        figsize=(7.0, 7.0),
    ),
    "wolf_sheep": FrameSpec(
        show_cells=True,
        cells_palette={
            "Empty": "#8b5a2b",        # brown earth
            "Grass": "#38b000",        # bright green
        },
        show_field=None,
        show_agents=True,
        agents_palette={
            "Sheep": "#ffffff",
            "Wolf": "#111111",
        },
        show_agent_heading=False,
        title_template="Wolf-Sheep — t = {t}",
        figsize=(7.0, 7.0),
    ),
    "gray_scott": FrameSpec(
        show_cells=False,
        show_field="v",
        field_cmap="inferno",
        field_vmin=0.0,
        field_vmax=0.5,
        field_colorbar=True,
        show_agents=False,
        title_template="Gray-Scott — t = {t}",
        figsize=(7.0, 7.0),
    ),
}
