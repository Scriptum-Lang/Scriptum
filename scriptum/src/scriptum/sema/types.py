"""
Type system representation for Scriptum semantic analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional


class TypeKind(Enum):
    NUMERUS = auto()
    TEXTUS = auto()
    BOOLEANUM = auto()
    VACUUM = auto()
    NULLUM = auto()
    INDEFINITUM = auto()
    QUODLIBET = auto()
    ARRAY = auto()
    OBJECT = auto()
    FUNCTION = auto()
    OPTIONAL = auto()


@dataclass(frozen=True)
class Type:
    kind: TypeKind
    element: Optional["Type"] = None
    fields: Optional[Dict[str, "Type"]] = None
    params: Optional[List["Type"]] = None
    ret: Optional["Type"] = None

    def is_assignable_from(self, other: "Type") -> bool:
        """Placeholder check mirroring eventual semantic rules."""

        if self.kind is TypeKind.QUODLIBET:
            return True
        return self == other
