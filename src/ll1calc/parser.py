from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .first_follow import EPSILON, START_SYMBOL
from .lexer import Lexer, Token, TokenKind
from .ll1_table import PARSE_TABLE, TERMINALS, format_production


class ParseError(Exception):
    """Syntactic error detected by the LL(1) parser."""


@dataclass(slots=True)
class ParseTreeNode:
    symbol: str
    children: List["ParseTreeNode"] = field(default_factory=list)
    token: Token | None = None

    def to_tuple(self) -> Tuple:
        if not self.children:
            if self.token:
                return (self.symbol, self.token.lexeme)
            return (self.symbol,)
        return (self.symbol, tuple(child.to_tuple() for child in self.children))

    def pretty(self, indent: int = 0) -> str:
        label = self.symbol
        if self.token and self.symbol != EPSILON:
            label += f" [{self.token.lexeme}]"
        lines = [" " * indent + label]
        for child in self.children:
            lines.append(child.pretty(indent + 2))
        return "\n".join(lines)


@dataclass(slots=True)
class ParseResult:
    tree: ParseTreeNode
    derivations: List[str]


class LL1Parser:
    """Classic LL(1) parser with an explicit symbol×token stack and derivations."""

    def __init__(self) -> None:
        self._lexer = Lexer()

    def parse(self, text: str) -> ParseResult:
        tokens = self._lexer.tokenize(text)
        stack: List[str] = ["$", START_SYMBOL]
        root = ParseTreeNode(START_SYMBOL)
        node_stack: List[ParseTreeNode] = [ParseTreeNode("$"), root]
        derivations: List[str] = []
        index = 0

        while stack:
            top = stack.pop()
            node = node_stack.pop()
            current = tokens[index]
            lookahead = current.kind.value

            if top in TERMINALS:
                if top != lookahead:
                    raise ParseError(f"Expected terminal {top}, but found {lookahead}.")
                node.token = current
                index += 1
                continue

            production = PARSE_TABLE.get(top, {}).get(lookahead)
            if production is None:
                raise ParseError(f"No production available for ({top}, {lookahead}).")

            derivations.append(f"{top} -> {format_production(production)}")
            if production == (EPSILON,):
                node.children.append(ParseTreeNode(EPSILON))
                continue

            new_children = [ParseTreeNode(symbol) for symbol in production]
            node.children.extend(new_children)
            for child in reversed(new_children):
                stack.append(child.symbol)
                node_stack.append(child)

        if index != len(tokens):
            raise ParseError("Unexpected tokens remained after the stack emptied.")

        derivations.append("ACCEPT")
        return ParseResult(tree=root, derivations=derivations)


__all__ = ["LL1Parser", "ParseError", "ParseResult", "ParseTreeNode"]
