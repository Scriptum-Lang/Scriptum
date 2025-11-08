from __future__ import annotations

from typing import Dict, List, Sequence, Set, Tuple

EPSILON = "ε"
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
    """Propagates FOLLOW using FIRST(β) and FOLLOW(lhs) until convergence."""

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

__all__ = [
    "EPSILON",
    "FIRST_SETS",
    "FOLLOW_SETS",
    "GRAMMAR",
    "START_SYMBOL",
    "TERMINALS",
    "first_of_sequence",
]
