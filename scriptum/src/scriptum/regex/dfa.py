"""
Deterministic finite automata generated from Scriptum regex NFAs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

StateId = int


@dataclass(slots=True)
class DFAState:
    """State in a deterministic automaton."""

    transitions: Dict[str, StateId]
    accepting: bool = False
    token: Optional[str] = None


@dataclass(slots=True)
class DFA:
    """Deterministic automaton used by the lexer."""

    states: Dict[StateId, DFAState]
    start: StateId
