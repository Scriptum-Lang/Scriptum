"""Self-contained LL(1) arithmetic parser reused by the Scriptum parser.

The implementation mirrors the standalone ll1calc package but lives inside the
parser package so that the Pratt parser can delegate to it without depending on
an external helper module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Sequence, Set, Tuple

# ------------------------------------------------------------------------------
# Grammar and FIRST/FOLLOW computation

EPSILON = "\u03b5"
START_SYMBOL = "E"

Grammar = Dict[str, List[Tuple[str, ...]]]

# LL(1) grammar already free of left recursion.
GRAMMAR: Grammar = {
    "E": [("T", "E'")],
    "E'": [("+", "T", "E'"), ("-", "T", "E'"), (EPSILON,)],
    "T": [("F", "T'")],
    "T'": [("*", "F", "T'"), ("/", "F", "T'"), (EPSILON,)],
    "F": [("(", "E", ")"), ("num",)],
}

TERMINALS: Set[str] = {"+", "-", "*", "/", "(", ")", "num", "$"}


def first_of_sequence(sequence: Sequence[str], first_sets: Dict[str, Set[str]]) -> Set[str]:
    """Computes FIRST for an arbitrary symbol sequence using accumulated results."""

    result: Set[str] = set()
    if not sequence:
        result.add(EPSILON)
        return result
    for symbol in sequence:
        if symbol in GRAMMAR:
            result.update(first_sets[symbol] - {EPSILON})
            if EPSILON in first_sets[symbol]:
                continue
            break
        result.add(symbol)
        break
    else:
        result.add(EPSILON)
    return result


def compute_first_sets(grammar: Grammar) -> Dict[str, Set[str]]:
    """Iterates to a fixed point, propagating terminals into each FIRST set."""

    first_sets: Dict[str, Set[str]] = {nt: set() for nt in grammar}
    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                idx = 0
                add_epsilon = True
                while idx < len(production):
                    symbol = production[idx]
                    if symbol in grammar:
                        additions = first_sets[symbol] - {EPSILON}
                        if not additions.issubset(first_sets[lhs]):
                            first_sets[lhs].update(additions)
                            changed = True
                        if EPSILON in first_sets[symbol]:
                            idx += 1
                            continue
                        add_epsilon = False
                        break
                    else:
                        if symbol not in first_sets[lhs]:
                            first_sets[lhs].add(symbol)
                            changed = True
                        add_epsilon = False
                        break
                if add_epsilon and EPSILON not in first_sets[lhs]:
                    first_sets[lhs].add(EPSILON)
                    changed = True
    return first_sets


def compute_follow_sets(grammar: Grammar, first_sets: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Propagates FOLLOW using FIRST(��) and FOLLOW(lhs) until convergence."""

    follow_sets: Dict[str, Set[str]] = {nt: set() for nt in grammar}
    follow_sets[START_SYMBOL].add("$")
    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                for index, symbol in enumerate(production):
                    if symbol not in grammar:
                        continue
                    beta = production[index + 1 :]
                    beta_first = first_of_sequence(beta, first_sets)
                    before = len(follow_sets[symbol])
                    follow_sets[symbol].update(beta_first - {EPSILON})
                    if len(follow_sets[symbol]) != before:
                        changed = True
                    if EPSILON in beta_first:
                        before = len(follow_sets[symbol])
                        follow_sets[symbol].update(follow_sets[lhs])
                        if len(follow_sets[symbol]) != before:
                            changed = True
    return follow_sets


FIRST_SETS = compute_first_sets(GRAMMAR)
FOLLOW_SETS = compute_follow_sets(GRAMMAR, FIRST_SETS)


# ------------------------------------------------------------------------------
# LL(1) table construction

ParseTable = Dict[str, Dict[str, Tuple[str, ...]]]


class TableConflictError(Exception):
    """Signals a collision while populating the LL(1) parse table."""


def format_production(production: Tuple[str, ...]) -> str:
    if production == (EPSILON,):
        return EPSILON
    return " ".join(production)


def build_ll1_table() -> ParseTable:
    """Builds the LL(1) parse table and raises on duplicated cells."""

    table: ParseTable = {nt: {} for nt in GRAMMAR}
    for lhs, productions in GRAMMAR.items():
        for production in productions:
            first = first_of_sequence(production, FIRST_SETS)
            for terminal in first - {EPSILON}:
                if terminal in table[lhs]:
                    raise TableConflictError(f"Conflict at ({lhs}, {terminal}).")
                table[lhs][terminal] = production
            if EPSILON in first:
                for terminal in FOLLOW_SETS[lhs]:
                    if terminal in table[lhs]:
                        raise TableConflictError(f"Conflict at ({lhs}, {terminal}).")
                    table[lhs][terminal] = production
    return table


PARSE_TABLE = build_ll1_table()


# ------------------------------------------------------------------------------
# Lexer


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


# ------------------------------------------------------------------------------
# Parser


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
    """Classic LL(1) parser with an explicit symbol-token stack and derivations."""

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


__all__ = [
    "EPSILON",
    "LL1Parser",
    "Lexer",
    "LexerError",
    "ParseError",
    "ParseResult",
    "ParseTreeNode",
]
