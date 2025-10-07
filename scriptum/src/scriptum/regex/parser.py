"""
Recursive-descent parser that converts regular expressions into AST nodes.

The grammar supported is intentionally tailored to the needs of the Scriptum
lexer. It understands alternation (`|`), concatenation, grouping, character
classes, quantifiers (`*`, `+`, `?`, `{m,n}`) and the constructs used within the
specification in `scriptum.lexer.spec`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from . import ast


ESCAPE_SEQUENCES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "f": "\f",
    "v": "\v",
    "b": "\b",
    "a": "\a",
    "\\": "\\",
    '"': '"',
    "'": "'",
}


class RegexSyntaxError(ValueError):
    """Raised when the regex parser encounters invalid syntax."""


@dataclass(slots=True)
class _Token:
    """Internal representation of a parsed atom and trailing quantifier."""

    node: ast.RegexNode
    minimum: int = 1
    maximum: Optional[int] = 1


class RegexParser:
    """Parse textual regex descriptions into AST nodes."""

    def __init__(self, alphabet_size: int = 128) -> None:
        self.alphabet_size = alphabet_size
        self._pattern = ""
        self._length = 0
        self._index = 0

    # Public API -----------------------------------------------------------------

    def parse(self, pattern: str) -> ast.RegexNode:
        self._pattern = pattern
        self._length = len(pattern)
        self._index = 0
        node = self._parse_expression()
        if not self._at_end():
            raise RegexSyntaxError(
                f"Unexpected trailing characters at position {self._index}: {self._pattern[self._index:]}"
            )
        return node

    def parse_many(self, patterns: Iterable[str]) -> list[ast.RegexNode]:
        return [self.parse(pattern) for pattern in patterns]

    # Parsing primitives ---------------------------------------------------------

    def _parse_expression(self) -> ast.RegexNode:
        parts = [self._parse_term()]
        while self._match("|"):
            parts.append(self._parse_term())
        if len(parts) == 1:
            return parts[0]
        return ast.Alternation(parts)

    def _parse_term(self) -> ast.RegexNode:
        elements: List[ast.RegexNode] = []
        while not self._at_end() and self._peek() not in "|)":
            token = self._parse_factor()
            elements.append(self._apply_quantifier(token))
        if not elements:
            return ast.Empty()
        if len(elements) == 1:
            return elements[0]
        return ast.Sequence(elements)

    def _parse_factor(self) -> _Token:
        char = self._peek()
        if char == "(":
            return _Token(self._parse_group())
        if char == "[":
            return _Token(self._parse_character_class())
        if char == ".":
            self._advance()
            return _Token(ast.AnyChar())
        if char == "\\":
            literal = self._parse_escape()
            return _Token(ast.Literal(ord(literal)))
        if char == "^" or char == "$":
            # Anchors are not used in the Scriptum lexer. Treat them as literals.
            self._advance()
            return _Token(ast.Literal(ord(char)))
        self._advance()
        return _Token(ast.Literal(ord(char)))

    def _parse_group(self) -> ast.RegexNode:
        self._expect("(")
        if self._match("?:"):
            pass  # Non-capturing group – same semantics for the parser.
        node = self._parse_expression()
        self._expect(")")
        return node

    def _parse_character_class(self) -> ast.RegexNode:
        self._expect("[")
        negated = self._match("^")
        ranges: List[tuple[int, int]] = []
        first = True
        while not self._at_end():
            if self._peek() == "]" and not first:
                break
            start_char = self._read_class_char()
            end_char = start_char
            if self._peek() == "-" and self._lookahead() not in {"]", ""}:
                self._advance()  # consume '-'
                end_char = self._read_class_char()
                if end_char < start_char:
                    start_char, end_char = end_char, start_char
            ranges.append((start_char, end_char))
            first = False
        self._expect("]")
        return ast.CharacterClass(tuple(ranges), negated=negated)

    def _read_class_char(self) -> int:
        if self._peek() == "\\":
            return ord(self._parse_escape())
        char = self._advance()
        return ord(char)

    def _apply_quantifier(self, token: _Token) -> ast.RegexNode:
        if self._at_end():
            return self._finalise_token(token)
        char = self._peek()
        if char in "*+?":
            self._advance()
            min_max = {
                "*": (0, None),
                "+": (1, None),
                "?": (0, 1),
            }[char]
            token.minimum, token.maximum = min_max
            if self._peek() == "?":  # non-greedy marker – ignored by the engine
                self._advance()
            return self._finalise_token(token)
        if char == "{":
            self._advance()
            min_count = self._read_number()
            max_count = min_count
            if self._match(","):
                if self._peek() == "}":
                    max_count = None
                else:
                    max_count = self._read_number()
            self._expect("}")
            if self._peek() == "?":
                self._advance()
            token.minimum = min_count
            token.maximum = max_count
            return self._finalise_token(token)
        return self._finalise_token(token)

    def _finalise_token(self, token: _Token) -> ast.RegexNode:
        if token.minimum == 1 and token.maximum == 1:
            return token.node
        return ast.Repeat(token.node, token.minimum, token.maximum)

    # Utility --------------------------------------------------------------------

    def _parse_escape(self) -> str:
        self._expect("\\")
        if self._at_end():
            raise RegexSyntaxError("Dangling escape at end of pattern")
        char = self._advance()
        if char in ESCAPE_SEQUENCES:
            return ESCAPE_SEQUENCES[char]
        if char == "x":
            return chr(self._read_hex_digits(2))
        if char == "u":
            return chr(self._read_hex_digits(4))
        # Unrecognised escapes map to the char itself (JS-style behaviour)
        return char

    def _read_hex_digits(self, count: int) -> int:
        if self._index + count > self._length:
            raise RegexSyntaxError("Incomplete hexadecimal escape sequence")
        value = 0
        for _ in range(count):
            char = self._advance()
            if char not in "0123456789abcdefABCDEF":
                raise RegexSyntaxError(f"Invalid hex digit in escape: {char!r}")
            value = (value << 4) + int(char, 16)
        return value

    def _read_number(self) -> int:
        start = self._index
        while not self._at_end() and self._peek().isdigit():
            self._advance()
        if start == self._index:
            raise RegexSyntaxError("Expected number in quantifier")
        return int(self._pattern[start:self._index])

    # Character/position helpers -------------------------------------------------

    def _at_end(self) -> bool:
        return self._index >= self._length

    def _peek(self) -> str:
        if self._at_end():
            return ""
        return self._pattern[self._index]

    def _lookahead(self) -> str:
        if self._index + 1 >= self._length:
            return ""
        return self._pattern[self._index + 1]

    def _advance(self) -> str:
        if self._at_end():
            raise RegexSyntaxError("Unexpected end of pattern")
        char = self._pattern[self._index]
        self._index += 1
        return char

    def _match(self, text: str) -> bool:
        if self._pattern.startswith(text, self._index):
            self._index += len(text)
            return True
        return False

    def _expect(self, text: str) -> None:
        if not self._match(text):
            raise RegexSyntaxError(
                f"Expected {text!r} at position {self._index} in {self._pattern!r}"
            )
