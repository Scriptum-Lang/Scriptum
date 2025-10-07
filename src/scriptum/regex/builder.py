"""
Builders that convert regex ASTs into NFAs and DFAs for the Scriptum lexer.
"""

from __future__ import annotations

from . import ast, dfa, nfa


class AutomataBuilder:
    """Transforms regex AST nodes into executable automata."""

    def to_nfa(self, pattern: ast.RegexNode) -> nfa.NFA:
        raise NotImplementedError("Regex to NFA conversion not implemented yet.")

    def to_dfa(self, automaton: nfa.NFA) -> dfa.DFA:
        raise NotImplementedError("NFA to DFA conversion not implemented yet.")
