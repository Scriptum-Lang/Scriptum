"""
Lexical token definitions for the Scriptum compiler.

This module centralises the canonical list of keywords, operators, punctuation
and token kinds required by the lexer and parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from .text import Span


class TokenKind(Enum):
    """Kinds of tokens produced by the Scriptum lexer."""

    IDENTIFIER = auto()
    KEYWORD = auto()
    NUMBER_LITERAL = auto()
    STRING_LITERAL = auto()
    OPERATOR = auto()
    PUNCTUATION = auto()
    DELIMITER = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    EOF = auto()


KEYWORDS: Tuple[str, ...] = (
    "mutabilis",
    "constans",
    "functio",
    "structura",
    "si",
    "aliter",
    "dum",
    "pro",
    "in",
    "de",
    "redde",
    "frange",
    "perge",
    "verum",
    "falsum",
    "nullum",
    "indefinitum",
    "numerus",
    "textus",
    "booleanum",
    "vacuum",
    "quodlibet",
)


OPERATORS: Tuple[str, ...] = (
    "=",
    "?:",
    "??",
    "||",
    "&&",
    "===",
    "!==",
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "+",
    "-",
    "*",
    "/",
    "%",
    "**",
    "!",
    ".",
)


PUNCTUATION: Tuple[str, ...] = (",", ";", ":", "::", "->", "=>", "?")


DELIMITERS: Tuple[str, ...] = ("{", "}", "[", "]", "(", ")")


@dataclass(slots=True)
class Token:
    """Concrete token emitted by the lexer."""

    kind: TokenKind
    lexeme: str
    span: Span
    value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:  # pragma: no cover - human readable
        return f"Token(kind={self.kind.name}, lexeme={self.lexeme!r}, span={self.span!r})"


def is_keyword(lexeme: str) -> bool:
    """Check if *lexeme* is a reserved Scriptum keyword."""

    return lexeme in KEYWORDS


def all_literals() -> Iterable[str]:
    """Return the set of fixed literal lexemes (operators + punctuation + delimiters)."""

    seen: Set[str] = set()
    for collection in (OPERATORS, PUNCTUATION, DELIMITERS):
        for literal in collection:
            if literal not in seen:
                seen.add(literal)
                yield literal
