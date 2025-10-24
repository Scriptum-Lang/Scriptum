"""
Utilities for working with Scriptum source text.

This module hosts lightweight data structures that describe locations within
source files and hold raw text. Later stages (lexer, parser, diagnostics) rely
on these primitives to track spans accurately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(slots=True)
class Span:
    """Half-open interval pointing into a source file."""

    start: int
    end: int

    def slice(self, text: str) -> str:
        """Return the substring denoted by this span."""

        return text[self.start : self.end]

    def line_col(self, text: str) -> Tuple[int, int]:
        """Return 1-based (line, column) for span.start within *text*."""

        line = text.count("\n", 0, self.start) + 1
        line_start = text.rfind("\n", 0, self.start)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1
        column = self.start - line_start + 1
        return line, column

    def highlight(self, text: str) -> str:
        """Return a short two-line string with the line and caret markers."""

        line_start = text.rfind("\n", 0, self.start)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1

        line_end = text.find("\n", self.end)
        if line_end == -1:
            line_end = len(text)

        line_text = text[line_start:line_end]
        caret_offset = max(0, self.start - line_start)
        caret_length = max(1, min(self.end - self.start, len(line_text) - caret_offset))
        caret_line = " " * caret_offset + "^" * caret_length
        return f"{line_text}\n{caret_line}"


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

    def line_col(self, span: Span) -> Tuple[int, int]:
        return span.line_col(self.text)

    def highlight(self, span: Span) -> str:
        return span.highlight(self.text)


def line_col(text: str, span: Span) -> Tuple[int, int]:
    return span.line_col(text)


def highlight_span(text: str, span: Span) -> str:
    return span.highlight(text)
