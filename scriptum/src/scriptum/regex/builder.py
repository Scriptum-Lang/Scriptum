"""
Builders that convert regex ASTs into NFAs and DFAs for the Scriptum lexer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Set

from . import dfa, nfa, parser


@dataclass(frozen=True)
class AcceptInfo:
    """Metadata associated with accepting DFA states."""

    index: int
    name: str
    kind: str
    priority: int
    ignore: bool
    order: int


@dataclass(frozen=True)
class BuildOutput:
    """Result of building the combined automaton."""

    dfa: dfa.DFA
    alphabet: Set[int]
    accept_entries: Sequence[AcceptInfo]


class AutomataBuilder:
    """Transforms regular expressions into deterministic, minimised automata."""

    def __init__(self, alphabet_size: int = nfa.ASCII_LIMIT) -> None:
        self.alphabet_size = alphabet_size
        self._parser = parser.RegexParser(alphabet_size)

    def build(self, patterns: Sequence) -> BuildOutput:
        thompson = nfa.ThompsonBuilder(self.alphabet_size)
        accept_entries: list[AcceptInfo] = []

        for index, pattern in enumerate(patterns):
            node = self._parser.parse(pattern.pattern)
            info = AcceptInfo(
                index=index,
                name=pattern.name,
                kind=pattern.kind.name,
                priority=pattern.priority,
                ignore=pattern.ignore,
                order=index,
            )
            accept_entries.append(info)
            thompson.add_pattern(node, info)

        machine = thompson.to_nfa()
        deterministic = dfa.determinize(machine)
        deterministic.make_total()
        minimized = deterministic.minimize()
        return BuildOutput(dfa=minimized, alphabet=thompson.alphabet, accept_entries=accept_entries)
