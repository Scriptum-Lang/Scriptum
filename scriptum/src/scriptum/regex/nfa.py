"""
Non-deterministic finite automata (NFA) primitives for Scriptum regex support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


StateId = int


@dataclass(slots=True)
class Transition:
    """Represents an edge in the NFA."""

    symbol: Optional[str]
    target: StateId


@dataclass(slots=True)
class State:
    """Node within the NFA graph."""

    transitions: List[Transition] = field(default_factory=list)
    accepting: bool = False


@dataclass(slots=True)
class NFA:
    """Full non-deterministic automaton."""

    states: Dict[StateId, State]
    start: StateId
    accepting: Set[StateId]
