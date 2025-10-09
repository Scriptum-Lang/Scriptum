"""
Builders that convert regex ASTs into NFAs and DFAs for the Scriptum lexer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Set, Tuple

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
                kind=pattern.kind.name if hasattr(pattern.kind, "name") else str(pattern.kind),
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


@dataclass(frozen=True)
class _SpecPattern:
    name: str
    pattern: str
    priority: int
    ignore: bool
    kind: str


def _symbol_to_str(code: int) -> str:
    char = chr(code)
    # Preserve printable symbols; fallback to escaped hex for non-printable.
    if char.isprintable() or char in {"\n", "\t", " "}:
        return char
    return f"\\x{code:02x}"


def build_tables_from_specs(
    specs: Iterable[Tuple[str, str, int] | Tuple[str, str, int, bool] | Tuple[str, str, int, bool, str]],
    *,
    deterministic_order: bool = True,
) -> dict:
    """
    Build a minimised DFA from lexical specifications.

    Parameters
    ----------
    specs:
        Iterable of tuples describing each token (name, regex, priority, [ignore], [kind]).
    deterministic_order:
        When True, reindexes states using a BFS traversal to guarantee deterministic IDs.

    Returns
    -------
    dict
        Mapping containing DFA states, transitions, finals, alphabet and metadata.
    """

    normalized: list[_SpecPattern] = []
    for item in specs:
        if len(item) < 3:
            raise ValueError("Each specification must contain at least (name, regex, priority).")
        name, pattern, priority = item[:3]
        ignore = bool(item[3]) if len(item) >= 4 else False
        kind = item[4] if len(item) >= 5 else "TOKEN"
        normalized.append(_SpecPattern(name=name, pattern=pattern, priority=int(priority), ignore=ignore, kind=str(kind)))

    builder = AutomataBuilder()
    result = builder.build(normalized)

    states = result.dfa.states
    total_states = len(states)

    if deterministic_order:
        ordered_ids: list[int] = []
        seen = set()
        queue = [result.dfa.start_state]
        seen.add(result.dfa.start_state)
        while queue:
            current = queue.pop(0)
            ordered_ids.append(current)
            transitions = states[current].transitions
            for symbol in sorted(transitions.keys()):
                target = transitions[symbol]
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        for idx in range(total_states):
            if idx not in seen:
                ordered_ids.append(idx)
    else:
        ordered_ids = list(range(total_states))

    remap = {old: new for new, old in enumerate(ordered_ids)}

    trans: dict[str, dict[str, int]] = {}
    for old_state in ordered_ids:
        new_state = remap[old_state]
        edges: dict[str, int] = {}
        for symbol, target in sorted(states[old_state].transitions.items()):
            edges[_symbol_to_str(symbol)] = remap[target]
        trans[str(new_state)] = edges

    finals: list[int] = []
    final_labels: dict[str, str] = {}
    final_priority: dict[str, int] = {}
    final_ignore: dict[str, bool] = {}
    final_kind: dict[str, str] = {}
    final_index: dict[str, int] = {}

    for old_state in ordered_ids:
        accepting = states[old_state].accepting
        if accepting is not None:
            new_state = remap[old_state]
            finals.append(new_state)
            key = str(new_state)
            final_labels[key] = accepting.name
            final_priority[key] = accepting.priority
            final_ignore[key] = accepting.ignore
            final_kind[key] = accepting.kind
            final_index[key] = accepting.index

    alphabet = sorted(_symbol_to_str(code) for code in result.alphabet)

    return {
        "states": list(range(len(ordered_ids))),
        "start": remap[result.dfa.start_state],
        "finals": finals,
        "alphabet": alphabet,
        "trans": trans,
        "final_token_labels": final_labels,
        "final_token_priority": final_priority,
        "final_token_ignore": final_ignore,
        "final_token_kind": final_kind,
        "final_token_index": final_index,
    }
