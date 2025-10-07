"""
Symbol table primitives for Scriptum semantic analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class Symbol:
    name: str
    type_name: Optional[str] = None


@dataclass(slots=True)
class Scope:
    symbols: Dict[str, Symbol] = field(default_factory=dict)

    def declare(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise ValueError(f"Symbol already declared: {symbol.name}")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)


@dataclass(slots=True)
class SymbolTable:
    scopes: List[Scope] = field(default_factory=lambda: [Scope()])

    def push_scope(self) -> None:
        self.scopes.append(Scope())

    def pop_scope(self) -> None:
        if len(self.scopes) == 1:
            raise ValueError("Cannot pop the global scope.")
        self.scopes.pop()

    def declare(self, symbol: Symbol) -> None:
        self.scopes[-1].declare(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            candidate = scope.lookup(name)
            if candidate is not None:
                return candidate
        return None
