from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...sema import types as sema_types


@dataclass(slots=True)
class LLVMTypeInfo:
    """Description of a lowered LLVM type."""

    ir: str
    kind: sema_types.TypeKind
    category: str  # e.g., numeric, boolean, pointer, variant, void
    optional: bool = False
    element: Optional["LLVMTypeInfo"] = None

    @property
    def is_numeric(self) -> bool:
        return self.kind is sema_types.TypeKind.NUMERUS

    @property
    def is_boolean(self) -> bool:
        return self.kind is sema_types.TypeKind.BOOLEANUM

    @property
    def is_pointer(self) -> bool:
        return self.category == "pointer"

    @property
    def is_variant(self) -> bool:
        return self.category == "variant"


class TypeLowerer:
    """Map Scriptum semantic types into LLVM textual representations."""

    def __init__(self) -> None:
        value_ir = "%scriptum.value"
        self._numeric = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.NUMERUS, category="value")
        self._boolean = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.BOOLEANUM, category="value")
        self._void = LLVMTypeInfo(ir="void", kind=sema_types.TypeKind.VACUUM, category="void")
        self._variant = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.QUODLIBET, category="value")
        self._text = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.TEXTUS, category="value")
        self._array = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.ARRAY, category="value")
        self._object = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.OBJECT, category="value")
        self._lambda = LLVMTypeInfo(ir=value_ir, kind=sema_types.TypeKind.FUNCTION, category="value")

    def lower(self, scriptum_type: Optional[sema_types.Type]) -> LLVMTypeInfo:
        if scriptum_type is None:
            return self._numeric

        kind = scriptum_type.kind
        if kind is sema_types.TypeKind.NUMERUS:
            return self._numeric
        if kind is sema_types.TypeKind.BOOLEANUM:
            return self._boolean
        if kind is sema_types.TypeKind.TEXTUS:
            return self._text
        if kind is sema_types.TypeKind.ARRAY:
            return self._array
        if kind is sema_types.TypeKind.OBJECT:
            return self._object
        if kind is sema_types.TypeKind.FUNCTION:
            return self._lambda
        if kind is sema_types.TypeKind.VACUUM:
            return self._void
        if kind is sema_types.TypeKind.OPTIONAL:
            element = self.lower(scriptum_type.element)
            return LLVMTypeInfo(
                ir=self._variant.ir,
                kind=kind,
                category="value",
                optional=True,
                element=element,
            )
        if kind is sema_types.TypeKind.QUODLIBET:
            return self._variant
        if kind in {sema_types.TypeKind.NULLUM, sema_types.TypeKind.INDEFINITUM}:
            return self._variant
        return self._variant
