"""
Lightweight parser that converts regular expressions into regex AST nodes.

The implementation is deliberately incomplete; it documents the intended API so
future work can focus on the actual parsing logic.
"""

from __future__ import annotations

from typing import Iterable

from . import ast


class RegexParser:
    """Parse textual regex descriptions into AST nodes."""

    def parse(self, pattern: str) -> ast.RegexNode:
        raise NotImplementedError("Regex parsing not implemented yet.")

    def parse_many(self, patterns: Iterable[str]) -> list[ast.RegexNode]:
        """Parse multiple regex patterns, keeping the call consistent."""

        return [self.parse(pattern) for pattern in patterns]
