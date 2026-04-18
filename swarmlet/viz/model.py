"""Typed Snapshot dataclasses and validation.

Wraps the raw dicts produced by `swarmlet.viz.loader` in immutable, validated
objects. All downstream renderers depend on `Snapshot`, never on raw dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np

from swarmlet.viz import SnapshotError


@dataclass(frozen=True)
class WorldInfo:
    w: int
    h: int
    wrap: bool


@dataclass(frozen=True)
class AgentRecord:
    type: str
    id: int
    x: int
    y: int
    fields: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, d: dict) -> "AgentRecord":
        known = {"type", "id", "x", "y", "fields"}
        nested = d.get("fields") or {}
        extras = {k: v for k, v in d.items() if k not in known}
        merged: Dict[str, Any] = {**nested, **extras}
        return cls(
            type=str(d["type"]),
            id=int(d["id"]),
            x=int(d["x"]),
            y=int(d["y"]),
            fields=tuple(sorted(merged.items())),
        )


@dataclass(frozen=True, eq=False)
class Snapshot:
    t: int
    world: WorldInfo
    states: np.ndarray
    states_legend: Tuple[str, ...]
    fields: Tuple[Tuple[str, np.ndarray], ...]
    agents: Tuple[AgentRecord, ...]

    def __post_init__(self):
        self.states.setflags(write=False)
        for _, arr in self.fields:
            arr.setflags(write=False)

    def _signature(self):
        return (
            self.t,
            self.world,
            self.states.shape,
            self.states.dtype.str,
            self.states.tobytes(),
            self.states_legend,
            tuple((n, a.shape, a.dtype.str, a.tobytes()) for n, a in self.fields),
            self.agents,
        )

    def __eq__(self, other):
        if not isinstance(other, Snapshot):
            return NotImplemented
        return self._signature() == other._signature()

    def __hash__(self):
        return hash(self._signature())

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        try:
            t = int(d["t"])
            world_dict = d["world"]
            world = WorldInfo(
                w=int(world_dict["w"]),
                h=int(world_dict["h"]),
                wrap=bool(world_dict["wrap"]),
            )
            states = np.asarray(d["states"])
            legend = tuple(d["states_legend"])
            fields_dict = d.get("fields") or {}
            agents_list = d.get("agents") or []
        except KeyError as exc:
            raise SnapshotError(f"missing required key in snapshot: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise SnapshotError(f"invalid snapshot value: {exc}") from exc

        h, w = world.h, world.w

        if states.shape != (h, w):
            raise SnapshotError(
                f"states.shape {states.shape} does not match world (h, w) = ({h}, {w})"
            )
        if not np.issubdtype(states.dtype, np.integer):
            raise SnapshotError(
                f"states.dtype must be integer, got {states.dtype}"
            )
        if states.size > 0:
            if int(states.min()) < 0:
                raise SnapshotError(
                    f"states contains negative index {int(states.min())}"
                )
            if int(states.max()) >= len(legend):
                raise SnapshotError(
                    f"states max index {int(states.max())} out of legend "
                    f"range (size {len(legend)})"
                )

        validated_fields: List[Tuple[str, np.ndarray]] = []
        for fname, arr in fields_dict.items():
            arr_np = np.asarray(arr)
            if arr_np.shape != (h, w):
                raise SnapshotError(
                    f"field '{fname}' shape {arr_np.shape} does not match "
                    f"world (h, w) = ({h}, {w})"
                )
            if not np.issubdtype(arr_np.dtype, np.floating):
                raise SnapshotError(
                    f"field '{fname}' dtype must be floating point, got {arr_np.dtype}"
                )
            validated_fields.append((fname, arr_np))

        seen_ids: set = set()
        agents: List[AgentRecord] = []
        for raw in agents_list:
            ax = int(raw["x"])
            ay = int(raw["y"])
            if not (0 <= ax < w):
                raise SnapshotError(
                    f"agent id={raw.get('id')} x={ax} out of bounds [0, {w})"
                )
            if not (0 <= ay < h):
                raise SnapshotError(
                    f"agent id={raw.get('id')} y={ay} out of bounds [0, {h})"
                )
            aid = int(raw["id"])
            if aid in seen_ids:
                raise SnapshotError(f"duplicate agent id: {aid}")
            seen_ids.add(aid)
            agents.append(AgentRecord.from_dict(raw))

        return cls(
            t=t,
            world=world,
            states=states,
            states_legend=legend,
            fields=tuple(validated_fields),
            agents=tuple(agents),
        )


def load_snapshots(path: Union[str, Path]) -> List[Snapshot]:
    """Load and validate snapshots from a JSONL or NPZ file."""
    from swarmlet.viz.loader import load_file
    return [Snapshot.from_dict(d) for d in load_file(path)]
