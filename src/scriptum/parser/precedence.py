"""
Operator precedence and associativity tables for the Scriptum parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Tuple


class Associativity(Enum):
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class PrecedenceRule:
    precedence: int
    associativity: Associativity


PRECEDENCE_TABLE: Dict[str, PrecedenceRule] = {
    "=": PrecedenceRule(1, Associativity.RIGHT),
    "?": PrecedenceRule(2, Associativity.RIGHT),
    "??": PrecedenceRule(3, Associativity.LEFT),
    "||": PrecedenceRule(4, Associativity.LEFT),
    "&&": PrecedenceRule(5, Associativity.LEFT),
    "==": PrecedenceRule(6, Associativity.LEFT),
    "!=": PrecedenceRule(6, Associativity.LEFT),
    "===": PrecedenceRule(6, Associativity.LEFT),
    "!==": PrecedenceRule(6, Associativity.LEFT),
    ">": PrecedenceRule(7, Associativity.LEFT),
    ">=": PrecedenceRule(7, Associativity.LEFT),
    "<": PrecedenceRule(7, Associativity.LEFT),
    "<=": PrecedenceRule(7, Associativity.LEFT),
    "+": PrecedenceRule(8, Associativity.LEFT),
    "-": PrecedenceRule(8, Associativity.LEFT),
    "*": PrecedenceRule(9, Associativity.LEFT),
    "/": PrecedenceRule(9, Associativity.LEFT),
    "%": PrecedenceRule(9, Associativity.LEFT),
    "**": PrecedenceRule(10, Associativity.RIGHT),
}


def binding_powers(operator: str) -> Optional[Tuple[int, int]]:
    rule = PRECEDENCE_TABLE.get(operator)
    if rule is None:
        return None
    if rule.associativity is Associativity.LEFT:
        return (rule.precedence, rule.precedence + 1)
    return (rule.precedence, rule.precedence)
