"""
Abstract syntax tree node definitions for Scriptum.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from ..text import Span


class NodeKind(Enum):
    MODULE = auto()
    FUNCTION = auto()
    VARIABLE = auto()
    BLOCK = auto()
    STATEMENT = auto()
    EXPRESSION = auto()


@dataclass(slots=True)
class Node:
    """Base AST node containing a span and unique identifier."""

    node_id: int
    span: Span


@dataclass(slots=True)
class Module(Node):
    items: List["Item"] = field(default_factory=list)


@dataclass(slots=True)
class Item(Node):
    kind: NodeKind
    data: object


@dataclass(slots=True)
class Identifier(Node):
    symbol: str
