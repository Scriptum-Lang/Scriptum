"""
Visitor utilities for traversing Scriptum AST nodes.
"""

from __future__ import annotations

from typing import Protocol

from . import nodes


class Visitor(Protocol):
    """Protocol for AST visitors."""

    def visit(self, node: nodes.Node) -> None:
        ...


def walk(visitor: Visitor, node: nodes.Node) -> None:
    """
    Dispatch to `visitor.visit`.

    Real traversal logic will be added once the AST node hierarchy is fleshed
    out.
    """

    visitor.visit(node)
