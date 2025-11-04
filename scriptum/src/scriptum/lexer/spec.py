"""
Declarative lexical specification for the Scriptum lexer.

Each token is represented by a regular expression along with metadata that the
`build_afd.py` script serialises into `tables.json`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from .. import tokens


@dataclass(frozen=True, slots=True)
class TokenPattern:
    """Single token rule used by the lexer generator."""

    name: str
    kind: tokens.TokenKind
    pattern: str
    priority: int = 0
    ignore: bool = False

    def as_json(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind.name,
            "pattern": self.pattern,
            "priority": self.priority,
            "ignore": self.ignore,
        }


def literal_regex(literal: str) -> str:
    """Return a regex that matches a literal exactly."""

    return re.escape(literal)


_LITERAL_NAMES = {
    "!": "BANG",
    '"': "DQUOTE",
    "$": "DOLLAR",
    "%": "PERCENT",
    "&": "AMP",
    "'": "SQUOTE",
    "(": "LPAREN",
    ")": "RPAREN",
    "*": "STAR",
    "+": "PLUS",
    ",": "COMMA",
    "-": "MINUS",
    ".": "DOT",
    "/": "SLASH",
    ":": "COLON",
    ";": "SEMI",
    "<": "LT",
    "=": "EQ",
    ">": "GT",
    "?": "QMARK",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "{": "LBRACE",
    "|": "BAR",
    "}": "RBRACE",
}


def literal_name(prefix: str, literal: str) -> str:
    """Produce a stable name for literal token entries."""

    parts = [_LITERAL_NAMES.get(ch, f"U{ord(ch):04X}") for ch in literal]
    return f"{prefix}_{'_'.join(parts)}"


TOKEN_PATTERNS: List[TokenPattern] = [
    TokenPattern(
        name="WHITESPACE",
        kind=tokens.TokenKind.WHITESPACE,
        pattern=r"[ \t\r\n\f\v]+",
        priority=100,
        ignore=True,
    ),
    TokenPattern(
        name="COMMENT_LINE",
        kind=tokens.TokenKind.COMMENT,
        pattern=r"//[^\r\n]*",
        priority=90,
        ignore=True,
    ),
    TokenPattern(
        name="COMMENT_BLOCK",
        kind=tokens.TokenKind.COMMENT,
        pattern=r"/\*(?:.|\r|\n)*?\*/",
        priority=90,
        ignore=True,
    ),
    TokenPattern(
        name="NUMBER_LITERAL",
        kind=tokens.TokenKind.NUMBER_LITERAL,
        pattern=r"-?(?:0|[1-9][0-9_]*)(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?",
        priority=70,
    ),
    TokenPattern(
        name="STRING_LITERAL",
        kind=tokens.TokenKind.STRING_LITERAL,
        pattern=r'"(?:[^"\\]|\\["\\\/bfnrt]|\\u[0-9a-fA-F]{4})*"',
        priority=70,
    ),
    TokenPattern(
        name="IDENTIFIER",
        kind=tokens.TokenKind.IDENTIFIER,
        pattern=r"[A-Za-z_][A-Za-z0-9_$]*",
        priority=60,
    ),
]

# Literal tokens (operators first by length, then punctuation, then delimiters).

_OPERATOR_ORDER = {literal: index for index, literal in enumerate(tokens.OPERATORS)}
_PUNCTUATION_ORDER = {literal: index for index, literal in enumerate(tokens.PUNCTUATION)}
_DELIMITER_ORDER = {literal: index for index, literal in enumerate(tokens.DELIMITERS)}


def _literal_sort_key(order: dict[str, int]):
    def key(literal: str) -> tuple[int, int, str]:
        return (-len(literal), order[literal], literal)

    return key


for literal in sorted(tokens.OPERATORS, key=_literal_sort_key(_OPERATOR_ORDER)):
    TOKEN_PATTERNS.append(
        TokenPattern(
            name=literal_name("OP", literal),
            kind=tokens.TokenKind.OPERATOR,
            pattern=literal_regex(literal),
            priority=50,
        )
    )

for literal in sorted(tokens.PUNCTUATION, key=_literal_sort_key(_PUNCTUATION_ORDER)):
    TOKEN_PATTERNS.append(
        TokenPattern(
            name=literal_name("PUNC", literal),
            kind=tokens.TokenKind.PUNCTUATION,
            pattern=literal_regex(literal),
            priority=40,
        )
    )

for literal in sorted(tokens.DELIMITERS, key=_literal_sort_key(_DELIMITER_ORDER)):
    TOKEN_PATTERNS.append(
        TokenPattern(
            name=literal_name("DELIM", literal),
            kind=tokens.TokenKind.DELIMITER,
            pattern=literal_regex(literal),
            priority=40,
        )
    )


ALPHABET = {
    "letters": "A-Z a-z _",
    "digits": "0-9",
    "symbols": sorted(
        {
            ch
            for literal in tokens.all_literals()
            for ch in literal
        }
        | {"$", '"', "'", "_"}
    ),
}


def to_json() -> dict:
    """Return a serialisable representation consumed by the DFA builder."""

    return {
        "version": 1,
        "alphabet": ALPHABET,
        "keywords": list(tokens.KEYWORDS),
        "token_patterns": [pattern.as_json() for pattern in TOKEN_PATTERNS],
    }


TOKEN_SPECS = [
    (pattern.name, pattern.pattern, pattern.priority, pattern.ignore, pattern.kind.name)
    for pattern in TOKEN_PATTERNS
]
