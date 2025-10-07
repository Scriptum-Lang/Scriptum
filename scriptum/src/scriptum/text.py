"""
Utilities for working with Scriptum source text.

This module hosts lightweight data structures that describe locations within
source files and hold raw text. Later stages (lexer, parser, diagnostics) rely
on these primitives to track spans accurately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Span:
    """Half-open interval pointing into a source file."""

    start: int
    end: int

    def slice(self, text: str) -> str:
        """Return the substring denoted by this span."""

        return text[self.start : self.end]


@dataclass(slots=True)
class SourceFile:
    """Wrapper for Scriptum source code and its origin."""

    path: Optional[str]
    text: str

    def __post_init__(self) -> None:
        if "\r\n" in self.text:
            # Normalize Windows newlines to simplify span calculations.
            self.text = self.text.replace("\r\n", "\n")

    def slice(self, span: Span) -> str:
        """Return the substring represented by *span*."""

        return span.slice(self.text)
