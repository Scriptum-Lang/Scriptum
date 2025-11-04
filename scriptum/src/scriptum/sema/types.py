"""Type system utilities for Scriptum semantic analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Iterable, List, Optional


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
        if self.kind is TypeKind.QUODLIBET:
            return True
        if self == other:
            return True
        if self.kind is TypeKind.OPTIONAL:
            if other.kind in {TypeKind.NULLUM, TypeKind.VACUUM}:
                return True
            if self.element:
                if other.kind is TypeKind.OPTIONAL and other.element:
                    return self.element.is_assignable_from(other.element)
                return self.element.is_assignable_from(other)
            return True
        if self.kind is TypeKind.OPTIONAL and other.kind is TypeKind.OPTIONAL:
            return self.element.is_assignable_from(other.element) if self.element and other.element else True
        if self.kind is TypeKind.NUMERUS and other.kind is TypeKind.NUMERUS:
            return True
        if self.kind is TypeKind.BOOLEANUM and other.kind is TypeKind.BOOLEANUM:
            return True
        if self.kind is TypeKind.TEXTUS and other.kind is TypeKind.TEXTUS:
            return True
        if self.kind is TypeKind.FUNCTION and other.kind is TypeKind.FUNCTION:
            if (self.params is None) or (other.params is None):
                return True
            if len(self.params) != len(other.params):
                return False
            return all(
                param_self.is_assignable_from(param_other)
                for param_self, param_other in zip(self.params, other.params)
            ) and (self.ret is None or other.ret is None or self.ret.is_assignable_from(other.ret))
        return False

    def with_optional(self) -> "Type":
        if self.kind is TypeKind.OPTIONAL:
            return self
        return Type(TypeKind.OPTIONAL, element=self)

    def unwrap_optional(self) -> "Type":
        if self.kind is TypeKind.OPTIONAL and self.element:
            return self.element
        return self

    def is_optional(self) -> bool:
        return self.kind is TypeKind.OPTIONAL

    def __str__(self) -> str:
        if self.kind is TypeKind.ARRAY:
            return f"[{self.element}]"
        if self.kind is TypeKind.OPTIONAL:
            return f"{self.element}?"
        if self.kind is TypeKind.OBJECT:
            return "{" + ", ".join(f"{k}: {v}" for k, v in (self.fields or {}).items()) + "}"
        if self.kind is TypeKind.FUNCTION:
            params = ", ".join(str(p) for p in (self.params or []))
            return f"functio({params}) -> {self.ret}"
        return self.kind.name.lower()


PRIMITIVE_TYPES: Dict[str, Type] = {
    "numerus": Type(TypeKind.NUMERUS),
    "textus": Type(TypeKind.TEXTUS),
    "booleanum": Type(TypeKind.BOOLEANUM),
    "vacuum": Type(TypeKind.VACUUM),
    "nullum": Type(TypeKind.NULLUM),
    "indefinitum": Type(TypeKind.INDEFINITUM),
    "quodlibet": Type(TypeKind.QUODLIBET),
}


def normalize_type_name(name: str) -> str:
    return name.strip().lower()


def type_from_annotation(name: str) -> Optional[Type]:
    name = normalize_type_name(name)
    if name.endswith("?"):
        inner = type_from_annotation(name[:-1])
        return inner.with_optional() if inner else None
    return PRIMITIVE_TYPES.get(name)


def type_from_literal(value: object, raw: str) -> Type:
    if isinstance(value, bool):
        return PRIMITIVE_TYPES["booleanum"]
    if isinstance(value, (int, float)):
        return PRIMITIVE_TYPES["numerus"]
    if isinstance(value, str):
        if raw == "indefinitum":
            return PRIMITIVE_TYPES["indefinitum"]
        if raw == "nullum":
            return PRIMITIVE_TYPES["nullum"]
        return PRIMITIVE_TYPES["textus"]
    if value is None:
        return PRIMITIVE_TYPES["nullum"]
    return PRIMITIVE_TYPES["quodlibet"]


def least_restrictive(types: Iterable[Type]) -> Type:
    result: Optional[Type] = None
    for t in types:
        if result is None:
            result = t
        elif t.is_assignable_from(result):
            continue
        elif result.is_assignable_from(t):
            result = t
        else:
            return PRIMITIVE_TYPES["quodlibet"]
    return result or PRIMITIVE_TYPES["quodlibet"]


def function_type(param_types: List[Type], return_type: Type) -> Type:
    return Type(TypeKind.FUNCTION, params=param_types, ret=return_type)
