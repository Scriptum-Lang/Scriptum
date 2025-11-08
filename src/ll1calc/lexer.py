from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class LexerError(Exception):
    """Lexical error raised when the source contains invalid characters."""


class TokenKind(str, Enum):
    NUM = "num"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    LPAREN = "("
    RPAREN = ")"
    EOF = "$"


@dataclass(slots=True)
class Token:
    kind: TokenKind
    lexeme: str
    position: int


_SINGLE_CHAR_TOKENS: Dict[str, TokenKind] = {
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
}


class Lexer:
    """Tokenizes arithmetic expressions while preserving character positions."""

    def tokenize(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        index = 0
        while index < len(text):
            char = text[index]
            if char.isspace():
                index += 1
                continue
            if char.isdigit():
                start = index
                while index < len(text) and text[index].isdigit():
                    index += 1
                tokens.append(Token(TokenKind.NUM, text[start:index], start))
                continue
            kind = _SINGLE_CHAR_TOKENS.get(char)
            if kind is not None:
                tokens.append(Token(kind, char, index))
                index += 1
                continue
            raise LexerError(f"Invalid character {char!r} at position {index}.")
        tokens.append(Token(TokenKind.EOF, "$", len(text)))
        return tokens


__all__ = ["Lexer", "LexerError", "Token", "TokenKind"]
