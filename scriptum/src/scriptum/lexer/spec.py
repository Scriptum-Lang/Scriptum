"""
Token specification for the Scriptum lexer.

This module records keywords, operators and punctuation in a structured form so
the lexer can be generated or validated automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


KEYWORDS: Sequence[str] = (
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


OPERATORS: Sequence[str] = (
    "=",
    "?:",
    "??",
    "||",
    "&&",
    "==",
    "!=",
    "===",
    "!==",
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


PUNCTUATION: Sequence[str] = (
    ",",
    ";",
    ":",
    "::",
    "->",
    "=>",
    "?",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
)


@dataclass(slots=True)
class TokenSpec:
    """Definition of a token accepted by the lexer DFAs."""

    name: str
    pattern: str
    priority: int = 0


def build_default_spec() -> Dict[str, TokenSpec]:
    """Return the token specification used by the Scriptum lexer."""

    return {
        "identifier": TokenSpec(name="identifier", pattern=r"[A-Za-z_][A-Za-z0-9_$]*"),
        "number": TokenSpec(name="number", pattern=r"-?[0-9][0-9_]*(?:\\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?"),
        "string": TokenSpec(name="string", pattern=r'"([^"\\\\]|\\\\.)*"'),
        "whitespace": TokenSpec(name="whitespace", pattern=r"[ \\t\\n\\r]+", priority=-1),
        "comment_line": TokenSpec(name="comment_line", pattern=r"//.*", priority=-1),
        "comment_block": TokenSpec(name="comment_block", pattern=r"/\\*.*?\\*/", priority=-1),
    }
