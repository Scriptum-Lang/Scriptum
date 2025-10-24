"""Structural intermediate representation for Scriptum."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from typing import Any, List, Optional

from ..text import Span


@dataclass(slots=True)
class IrNode:
    span: Span


@dataclass(slots=True)
class ModuleIr(IrNode):
    globals: List["IrVariable"]
    functions: List["IrFunction"]


# Backwards-compatible alias.
IrModule = ModuleIr


@dataclass(slots=True)
class IrVariable(IrNode):
    name: str
    mutable: bool
    type_annotation: Optional[str]
    initializer: Optional["IrExpr"]


@dataclass(slots=True)
class IrParameter(IrNode):
    name: str
    type_annotation: Optional[str]
    default_value: Optional["IrExpr"]


@dataclass(slots=True)
class IrFunction(IrNode):
    name: str
    parameters: List[IrParameter]
    return_annotation: Optional[str]
    body: List["IrStatement"]


@dataclass(slots=True)
class IrStatement(IrNode):
    pass


@dataclass(slots=True)
class IrExpressionStatement(IrStatement):
    expression: "IrExpr"


@dataclass(slots=True)
class IrVariableDeclaration(IrStatement):
    name: str
    mutable: bool
    type_annotation: Optional[str]
    initializer: Optional["IrExpr"]


@dataclass(slots=True)
class IrIf(IrStatement):
    condition: "IrExpr"
    then_branch: List[IrStatement]
    else_branch: List[IrStatement]


@dataclass(slots=True)
class IrWhile(IrStatement):
    condition: "IrExpr"
    body: List[IrStatement]


@dataclass(slots=True)
class IrForTarget(IrNode):
    name: str
    mutable: bool
    type_annotation: Optional[str]


@dataclass(slots=True)
class IrForIn(IrStatement):
    target: IrForTarget
    iterable: "IrExpr"
    body: List[IrStatement]


@dataclass(slots=True)
class IrReturn(IrStatement):
    value: Optional["IrExpr"]


@dataclass(slots=True)
class IrBreak(IrStatement):
    pass


@dataclass(slots=True)
class IrContinue(IrStatement):
    pass


@dataclass(slots=True)
class IrExpr(IrNode):
    pass


@dataclass(slots=True)
class IrIdentifier(IrExpr):
    name: str


@dataclass(slots=True)
class IrLiteral(IrExpr):
    value: Any
    raw: str


@dataclass(slots=True)
class IrUnary(IrExpr):
    operator: str
    operand: IrExpr


@dataclass(slots=True)
class IrBinary(IrExpr):
    operator: str
    left: IrExpr
    right: IrExpr


@dataclass(slots=True)
class IrAssignment(IrExpr):
    target: IrExpr
    value: IrExpr


@dataclass(slots=True)
class IrConditional(IrExpr):
    condition: IrExpr
    consequent: IrExpr
    alternate: IrExpr


@dataclass(slots=True)
class IrCall(IrExpr):
    callee: IrExpr
    arguments: List[IrExpr]


@dataclass(slots=True)
class IrMemberAccess(IrExpr):
    object: IrExpr
    property: str


@dataclass(slots=True)
class IrIndex(IrExpr):
    collection: IrExpr
    index: IrExpr


@dataclass(slots=True)
class IrArrayLiteral(IrExpr):
    elements: List[IrExpr]


@dataclass(slots=True)
class IrObjectProperty(IrNode):
    key: str
    value: IrExpr


@dataclass(slots=True)
class IrObjectLiteral(IrExpr):
    properties: List[IrObjectProperty]


@dataclass(slots=True)
class IrLambda(IrExpr):
    parameters: List[IrParameter]
    return_annotation: Optional[str]
    body_expression: Optional[IrExpr]
    body_statements: List[IrStatement]


def _serialize_span(span: Span) -> list[int]:
    return [span.start, span.end]


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Span):
        return _serialize_span(value)
    if isinstance(value, IrNode):
        return _serialize_node(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _serialize_node(node: IrNode) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": node.__class__.__name__,
        "span": _serialize_span(node.span),
    }
    for field in fields(node):
        if field.name == "span":
            continue
        value = getattr(node, field.name)
        result[field.name] = _serialize_value(value)
    return result


def format_module_ir(module: ModuleIr) -> str:
    """Return a stable JSON representation of the provided module IR."""

    payload = _serialize_node(module)
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
