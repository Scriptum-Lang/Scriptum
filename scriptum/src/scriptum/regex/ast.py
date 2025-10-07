"""
Regex AST nodes used to build the Scriptum lexical automata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class RegexNode:
    """Base class for all regex AST nodes."""


@dataclass(slots=True)
class Literal(RegexNode):
    """Represents a literal character."""

    value: str


@dataclass(slots=True)
class Sequence(RegexNode):
    """Represents concatenation of regex nodes."""

    elements: List[RegexNode]


@dataclass(slots=True)
class Alternation(RegexNode):
    """Represents alternation (a|b)."""

    options: List[RegexNode]


@dataclass(slots=True)
class Repeat(RegexNode):
    """Kleene/star style repetition."""

    node: RegexNode
    min: int
    max: Optional[int]
