"""Symbol table utilities for Scriptum semantic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .types import Type


@dataclass(slots=True)
class Symbol:
    name: str
    type: Type
    mutable: bool
    span: Optional[object] = None


@dataclass(slots=True)
class Scope:
    symbols: Dict[str, Symbol] = field(default_factory=dict)

    def declare(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)


class SymbolTable:
    def __init__(self) -> None:
        self._scopes: List[Scope] = [Scope()]

    def push_scope(self) -> None:
        self._scopes.append(Scope())

    def pop_scope(self) -> None:
        if len(self._scopes) == 1:
            raise ValueError("Cannot pop global scope")
        self._scopes.pop()

    def declare(self, symbol: Symbol) -> bool:
        return self._scopes[-1].declare(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self._scopes):
            symbol = scope.lookup(name)
            if symbol is not None:
                return symbol
        return None

    def is_declared_in_current_scope(self, name: str) -> bool:
        return name in self._scopes[-1].symbols

    def assign(self, name: str, value_type: Type) -> Optional[tuple[str, str]]:
        symbol = self.lookup(name)
        if symbol is None:
            return ("S100", f"Undeclared identifier '{name}'")
        if not symbol.mutable:
            return ("S120", f"Cannot assign to immutable symbol '{name}'")
        if not symbol.type.is_assignable_from(value_type):
            return ("T200", f"Type mismatch: cannot assign {value_type} to {symbol.type}")
        return None
