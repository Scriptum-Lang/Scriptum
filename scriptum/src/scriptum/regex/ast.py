"""
Regex AST nodes used to build the Scriptum lexical automata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


class RegexNode:
    """Base class for all regex AST nodes."""


@dataclass(slots=True)
class Empty(RegexNode):
    """Represents the empty string."""


@dataclass(slots=True)
class Literal(RegexNode):
    """Represents a literal character."""

    value: int  # Unicode code point


@dataclass(slots=True)
class AnyChar(RegexNode):
    """Matches any character except newline."""


@dataclass(slots=True)
class CharacterClass(RegexNode):
    """Character class with optional negation."""

    ranges: Sequence[Tuple[int, int]]
    negated: bool = False


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
    """General repetition."""

    node: RegexNode
    minimum: int
    maximum: Optional[int]
