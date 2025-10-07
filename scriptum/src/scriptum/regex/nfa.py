"""
Non-deterministic finite automata (NFA) primitives for Scriptum regex support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from . import ast

StateId = int
ASCII_LIMIT = 128


@dataclass(slots=True)
class NFAState:
    """Represents a node in the Thompson NFA."""

    epsilon: Set[StateId] = field(default_factory=set)
    transitions: Dict[int, Set[StateId]] = field(default_factory=dict)

    def add_transition(self, symbol: int, target: StateId) -> None:
        self.transitions.setdefault(symbol, set()).add(target)


@dataclass(slots=True)
class Fragment:
    """Helper structure used during Thompson construction."""

    start: StateId
    accepts: Set[StateId]


@dataclass(slots=True)
class NFA:
    """Full non-deterministic automaton."""

    states: Dict[StateId, NFAState]
    start_state: StateId
    accepting: Dict[StateId, Any]
    alphabet: Set[int]
    alphabet_size: int = ASCII_LIMIT

    def epsilon_closure(self, states: Iterable[StateId]) -> Set[StateId]:
        """Return the epsilon-closure of *states*."""

        stack = list(states)
        closure = set(stack)
        while stack:
            state_id = stack.pop()
            state = self.states[state_id]
            for target in state.epsilon:
                if target not in closure:
                    closure.add(target)
                    stack.append(target)
        return closure


class ThompsonBuilder:
    """Constructs NFAs from regex AST nodes via Thompson's algorithm."""

    def __init__(self, alphabet_size: int = ASCII_LIMIT) -> None:
        self.alphabet_size = alphabet_size
        self.states: Dict[StateId, NFAState] = {}
        self.start_state = self._new_state()
        self.accepting: Dict[StateId, Any] = {}
        self.alphabet: Set[int] = set()

    # Public API -----------------------------------------------------------------

    def add_pattern(self, node: ast.RegexNode, payload: Any) -> None:
        fragment = self._build(node)
        accept_state = self._new_state()
        for accept in fragment.accepts:
            self.states[accept].epsilon.add(accept_state)
        self.states[self.start_state].epsilon.add(fragment.start)
        self.accepting[accept_state] = payload

    def to_nfa(self) -> NFA:
        return NFA(
            states=self.states,
            start_state=self.start_state,
            accepting=self.accepting,
            alphabet=self.alphabet,
            alphabet_size=self.alphabet_size,
        )

    # Thompson construction ------------------------------------------------------

    def _build(self, node: ast.RegexNode) -> Fragment:
        if isinstance(node, ast.Empty):
            state = self._new_state()
            return Fragment(state, {state})
        if isinstance(node, ast.Literal):
            return self._literal_fragment({node.value})
        if isinstance(node, ast.AnyChar):
            chars = {c for c in range(self.alphabet_size) if c != ord("\n")}
            return self._literal_fragment(chars)
        if isinstance(node, ast.CharacterClass):
            chars = self._expand_character_class(node)
            return self._literal_fragment(chars)
        if isinstance(node, ast.Sequence):
            return self._build_sequence(node.elements)
        if isinstance(node, ast.Alternation):
            return self._build_alternation(node.options)
        if isinstance(node, ast.Repeat):
            return self._build_repetition(node)
        raise TypeError(f"Unsupported regex node: {type(node).__name__}")

    def _build_sequence(self, elements: Iterable[ast.RegexNode]) -> Fragment:
        fragments = [self._build(element) for element in elements]
        if not fragments:
            return self._build(ast.Empty())
        head = fragments[0]
        for tail in fragments[1:]:
            for accept in head.accepts:
                self.states[accept].epsilon.add(tail.start)
            head = Fragment(head.start, tail.accepts)
        return head

    def _build_alternation(self, options: Iterable[ast.RegexNode]) -> Fragment:
        options = list(options)
        if not options:
            return self._build(ast.Empty())
        start = self._new_state()
        accept = self._new_state()
        for option in options:
            fragment = self._build(option)
            self.states[start].epsilon.add(fragment.start)
            for state in fragment.accepts:
                self.states[state].epsilon.add(accept)
        return Fragment(start, {accept})

    def _build_repetition(self, node: ast.Repeat) -> Fragment:
        min_times = node.minimum
        max_times = node.maximum

        # Build the mandatory part.
        fragment: Optional[Fragment] = None
        for _ in range(min_times):
            part_fragment = self._build(self._clone(node.node))
            fragment = self._concat(fragment, part_fragment)

        if max_times is None:
            # Unlimited repetitions after the mandatory part.
            star_fragment = self._make_star(self._clone(node.node))
            fragment = self._concat(fragment, star_fragment)
        else:
            optional_count = max_times - min_times
            for _ in range(optional_count):
                optional = self._make_optional(self._clone(node.node))
                fragment = self._concat(fragment, optional)

        return fragment or self._build(ast.Empty())

    # Fragment helpers -----------------------------------------------------------

    def _concat(self, left: Optional[Fragment], right: Fragment) -> Fragment:
        if left is None:
            return right
        for accept in left.accepts:
            self.states[accept].epsilon.add(right.start)
        return Fragment(left.start, right.accepts)

    def _make_optional(self, node: ast.RegexNode) -> Fragment:
        fragment = self._build(node)
        start = self._new_state()
        accept = self._new_state()
        self.states[start].epsilon.update({fragment.start, accept})
        for state in fragment.accepts:
            self.states[state].epsilon.add(accept)
        return Fragment(start, {accept})

    def _make_star(self, node: ast.RegexNode) -> Fragment:
        fragment = self._build(node)
        start = self._new_state()
        accept = self._new_state()
        self.states[start].epsilon.update({fragment.start, accept})
        for state in fragment.accepts:
            self.states[state].epsilon.update({fragment.start, accept})
        return Fragment(start, {accept})

    def _literal_fragment(self, chars: Set[int]) -> Fragment:
        start = self._new_state()
        end = self._new_state()
        for char in chars:
            if char >= self.alphabet_size:
                continue  # Ignore characters outside the configured alphabet.
            self.states[start].add_transition(char, end)
            self.alphabet.add(char)
        return Fragment(start, {end})

    def _expand_character_class(self, node: ast.CharacterClass) -> Set[int]:
        chars: Set[int] = set()
        for start, end in node.ranges:
            start = max(0, start)
            end = min(self.alphabet_size - 1, end)
            chars.update(range(start, end + 1))
        if node.negated:
            return {c for c in range(self.alphabet_size) if c not in chars}
        return chars

    def _clone(self, node: ast.RegexNode) -> ast.RegexNode:
        # Regex nodes are immutable dataclasses; we can safely reuse them.
        return node

    # State management -----------------------------------------------------------

    def _new_state(self) -> StateId:
        state_id = len(self.states)
        self.states[state_id] = NFAState()
        return state_id
