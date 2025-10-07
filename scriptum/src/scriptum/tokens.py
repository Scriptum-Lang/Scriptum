"""
Token definitions used by the Scriptum lexer and parser.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional

from .text import Span


class TokenKind(enum.Enum):
    """Enumeration of all tokens recognized by the Scriptum lexer."""

    IDENTIFIER = "identifier"
    NUMBER = "number"
    STRING = "string"
    KEYWORD = "keyword"
    OPERATOR = "operator"
    DELIMITER = "delimiter"
    PUNCTUATION = "punctuation"
    EOF = "eof"


@dataclass(slots=True)
class Token:
    """A single token emitted by the lexer."""

    kind: TokenKind
    lexeme: str
    span: Span
    value: Optional[Any] = None

    def __repr__(self) -> str:  # pragma: no cover - human friendly representation
        return f"Token(kind={self.kind!s}, lexeme={self.lexeme!r}, span={self.span!r})"
