"""Swarmlet — a small functional language for simulating cellular automata and agent-based swarms."""

__version__ = "0.1.4"

from swarmlet.errors import SwarmletError, SwarmletStaticError, SwarmletRuntimeError


def load(source: str):
    """Parse and analyze a Swarmlet program from source text. Returns a Program AST."""
    raise NotImplementedError("load() will be implemented in Phase 2")
