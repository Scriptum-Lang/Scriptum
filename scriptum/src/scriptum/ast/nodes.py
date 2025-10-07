"""
Canonical AST structures for the Scriptum language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from ..text import Span


class BinaryOperator(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    POW = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
    EQ = auto()
    NE = auto()
    STRICT_EQ = auto()
    STRICT_NE = auto()
    AND = auto()
    OR = auto()
    NULLISH = auto()
    ACCESS = auto()


class UnaryOperator(Enum):
    NEGATE = auto()
    POSITIVE = auto()
    NOT = auto()


@dataclass(slots=True)
class Node:
    node_id: int
    span: Span


@dataclass(slots=True)
class Statement(Node):
    pass


@dataclass(slots=True)
class Declaration(Statement):
    pass


@dataclass(slots=True)
class Module(Node):
    declarations: List[Declaration] = field(default_factory=list)


@dataclass(slots=True)
class TypeAnnotation(Node):
    name: str


@dataclass(slots=True)
class Parameter(Node):
    name: str
    type_annotation: Optional[TypeAnnotation]
    default_value: Optional["Expression"]


@dataclass(slots=True)
class FunctionDeclaration(Declaration):
    name: str
    parameters: List[Parameter]
    return_type: Optional[TypeAnnotation]
    body: "BlockStatement"


@dataclass(slots=True)
class VariableDeclaration(Declaration):
    mutable: bool
    name: str
    type_annotation: Optional[TypeAnnotation]
    initializer: Optional["Expression"]
    is_global: bool = False


@dataclass(slots=True)
class BlockStatement(Statement):
    statements: List[Statement]


@dataclass(slots=True)
class ExpressionStatement(Statement):
    expression: "Expression"


@dataclass(slots=True)
class IfStatement(Statement):
    condition: "Expression"
    then_branch: Statement
    else_branch: Optional[Statement]


@dataclass(slots=True)
class WhileStatement(Statement):
    condition: "Expression"
    body: Statement


@dataclass(slots=True)
class ForTarget(Node):
    name: str
    mutable: bool
    type_annotation: Optional[TypeAnnotation]


@dataclass(slots=True)
class ForStatement(Statement):
    target: ForTarget
    iterable: "Expression"
    body: Statement


@dataclass(slots=True)
class ReturnStatement(Statement):
    value: Optional["Expression"]


@dataclass(slots=True)
class BreakStatement(Statement):
    pass


@dataclass(slots=True)
class ContinueStatement(Statement):
    pass


@dataclass(slots=True)
class Expression(Node):
    pass


@dataclass(slots=True)
class Identifier(Expression):
    name: str


@dataclass(slots=True)
class Literal(Expression):
    value: object
    raw: str


@dataclass(slots=True)
class UnaryExpression(Expression):
    operator: UnaryOperator
    operand: Expression


@dataclass(slots=True)
class BinaryExpression(Expression):
    operator: BinaryOperator | str
    left: Expression
    right: Expression


@dataclass(slots=True)
class AssignmentExpression(Expression):
    target: Expression
    value: Expression


@dataclass(slots=True)
class ConditionalExpression(Expression):
    condition: Expression
    consequent: Expression
    alternate: Expression


@dataclass(slots=True)
class CallExpression(Expression):
    callee: Expression
    arguments: List[Expression]


@dataclass(slots=True)
class MemberExpression(Expression):
    object: Expression
    property: str


@dataclass(slots=True)
class IndexExpression(Expression):
    collection: Expression
    index: Expression


@dataclass(slots=True)
class ArrayLiteral(Expression):
    elements: List[Expression]


@dataclass(slots=True)
class ObjectProperty(Node):
    key: str
    value: Expression


@dataclass(slots=True)
class ObjectLiteral(Expression):
    properties: List[ObjectProperty]


@dataclass(slots=True)
class LambdaExpression(Expression):
    parameters: List[Parameter]
    return_type: Optional[TypeAnnotation]
    body: Statement | Expression
