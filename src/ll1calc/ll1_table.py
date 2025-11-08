from __future__ import annotations

from typing import Dict, Tuple

from .first_follow import EPSILON, FIRST_SETS, FOLLOW_SETS, GRAMMAR, TERMINALS, first_of_sequence

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

__all__ = ["PARSE_TABLE", "TERMINALS", "TableConflictError", "format_production"]
