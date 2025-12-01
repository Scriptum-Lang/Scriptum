"""Lower Scriptum AST nodes into the structural IR."""

from __future__ import annotations

from typing import Iterable, List, Optional, Mapping, TYPE_CHECKING

from ..ast import nodes
from .ir import (
    IrArrayLiteral,
    IrAssignment,
    IrBinary,
    IrBreak,
    IrCall,
    IrConditional,
    IrContinue,
    IrExpr,
    IrExpressionStatement,
    IrForIn,
    IrForTarget,
    IrFunction,
    IrIdentifier,
    IrIf,
    IrIndex,
    IrLambda,
    IrLiteral,
    IrMemberAccess,
    IrModule,
    IrObjectLiteral,
    IrObjectProperty,
    IrParameter,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariable,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
)
from .ir import IrNode  # re-exported for type checking

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    from ..sema.types import Type
    from ..builtins import MethodBinding


class _LoweringContext:
    def __init__(
        self,
        type_info: Optional[Mapping[int, "Type"]] = None,
        member_bindings: Optional[Mapping[int, "MethodBinding"]] = None,
    ) -> None:
        self._type_info = dict(type_info or {})
        self._member_bindings = dict(member_bindings or {})

    def type_of(self, node: Optional[nodes.Node]) -> Optional["Type"]:
        if node is None:
            return None
        return self._type_info.get(node.node_id)

    def binding_of(self, node: Optional[nodes.Node]) -> Optional["MethodBinding"]:
        if node is None:
            return None
        return self._member_bindings.get(node.node_id)


def lower_module(
    module: nodes.Module,
    *,
    type_info: Optional[Mapping[int, "Type"]] = None,
    member_bindings: Optional[Mapping[int, "MethodBinding"]] = None,
) -> ModuleIr:
    ctx = _LoweringContext(type_info=type_info, member_bindings=member_bindings)
    globals_ir: List[IrVariable] = []
    functions_ir: List[IrFunction] = []

    for declaration in module.declarations:
        if isinstance(declaration, nodes.FunctionDeclaration):
            functions_ir.append(_lower_function(declaration, ctx))
        elif isinstance(declaration, nodes.VariableDeclaration):
            globals_ir.append(_lower_global_variable(declaration, ctx))

    return IrModule(span=module.span, globals=globals_ir, functions=functions_ir)


def _lower_global_variable(decl: nodes.VariableDeclaration, ctx: _LoweringContext) -> IrVariable:
    initializer = _lower_expression(decl.initializer, ctx) if decl.initializer else None
    annotation = _annotation_name(decl.type_annotation)
    return IrVariable(
        span=decl.span,
        name=decl.name,
        mutable=decl.mutable,
        type_annotation=annotation,
        initializer=initializer,
        type_info=ctx.type_of(decl),
    )


def _lower_function(func: nodes.FunctionDeclaration, ctx: _LoweringContext) -> IrFunction:
    parameters = [_lower_parameter(param, ctx) for param in func.parameters]
    return_annotation = _annotation_name(func.return_type)
    body_statements = _lower_block(func.body.statements, ctx)
    return IrFunction(
        span=func.span,
        name=func.name,
        parameters=parameters,
        return_annotation=return_annotation,
        body=body_statements,
    )


def _lower_parameter(param: nodes.Parameter, ctx: _LoweringContext) -> IrParameter:
    annotation = _annotation_name(param.type_annotation)
    default_value = _lower_expression(param.default_value, ctx) if param.default_value else None
    return IrParameter(
        span=param.span,
        name=param.name,
        type_annotation=annotation,
        default_value=default_value,
        type_info=ctx.type_of(param),
    )


def _lower_block(statements: Iterable[nodes.Statement], ctx: _LoweringContext) -> List[IrStatement]:
    result: List[IrStatement] = []
    for stmt in statements:
        result.extend(_lower_statement(stmt, ctx))
    return result


def _lower_statement(stmt: nodes.Statement, ctx: _LoweringContext) -> List[IrStatement]:
    if isinstance(stmt, nodes.BlockStatement):
        return _lower_block(stmt.statements, ctx)

    lowered = _lower_single_statement(stmt, ctx)
    return [lowered]


def _lower_single_statement(stmt: nodes.Statement, ctx: _LoweringContext) -> IrStatement:
    if isinstance(stmt, nodes.VariableDeclaration):
        initializer = _lower_expression(stmt.initializer, ctx) if stmt.initializer else None
        annotation = _annotation_name(stmt.type_annotation)
        return IrVariableDeclaration(
            span=stmt.span,
            name=stmt.name,
            mutable=stmt.mutable,
            type_annotation=annotation,
            initializer=initializer,
            type_info=ctx.type_of(stmt),
        )
    if isinstance(stmt, nodes.ExpressionStatement):
        expr = _lower_expression(stmt.expression, ctx)
        return IrExpressionStatement(span=stmt.span, expression=expr)
    if isinstance(stmt, nodes.ReturnStatement):
        value = _lower_expression(stmt.value, ctx) if stmt.value else None
        return IrReturn(span=stmt.span, value=value)
    if isinstance(stmt, nodes.IfStatement):
        condition = _lower_expression(stmt.condition, ctx)
        then_branch = _lower_statement(stmt.then_branch, ctx)
        else_branch = _lower_statement(stmt.else_branch, ctx) if stmt.else_branch else []
        return IrIf(
            span=stmt.span,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )
    if isinstance(stmt, nodes.WhileStatement):
        condition = _lower_expression(stmt.condition, ctx)
        body = _lower_statement(stmt.body, ctx)
        return IrWhile(span=stmt.span, condition=condition, body=body)
    if isinstance(stmt, nodes.ForStatement):
        iterable = _lower_expression(stmt.iterable, ctx)
        target_annotation = _annotation_name(stmt.target.type_annotation)
        target = IrForTarget(
            span=stmt.target.span,
            name=stmt.target.name,
            mutable=stmt.target.mutable,
            type_annotation=target_annotation,
            type_info=ctx.type_of(stmt.target),
        )
        body = _lower_statement(stmt.body, ctx)
        return IrForIn(span=stmt.span, target=target, iterable=iterable, body=body)
    if isinstance(stmt, nodes.BreakStatement):
        return IrBreak(span=stmt.span)
    if isinstance(stmt, nodes.ContinueStatement):
        return IrContinue(span=stmt.span)
    raise TypeError(f"Unsupported statement type: {type(stmt)!r}")


def _lower_expression(expr: Optional[nodes.Expression], ctx: _LoweringContext) -> Optional[IrExpr]:
    if expr is None:
        return None
    if isinstance(expr, nodes.Identifier):
        return IrIdentifier(span=expr.span, name=expr.name, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.Literal):
        return IrLiteral(span=expr.span, value=expr.value, raw=expr.raw, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.UnaryExpression):
        operand = _lower_expression(expr.operand, ctx)
        operator = expr.operator.name if isinstance(expr.operator, nodes.UnaryOperator) else str(expr.operator)
        return IrUnary(span=expr.span, operator=operator, operand=operand, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.BinaryExpression):
        left = _lower_expression(expr.left, ctx)
        right = _lower_expression(expr.right, ctx)
        operator = expr.operator.name if hasattr(expr.operator, "name") else str(expr.operator)
        return IrBinary(span=expr.span, operator=operator, left=left, right=right, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.AssignmentExpression):
        target = _lower_expression(expr.target, ctx)
        value = _lower_expression(expr.value, ctx)
        return IrAssignment(span=expr.span, target=target, value=value, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.ConditionalExpression):
        condition = _lower_expression(expr.condition, ctx)
        consequent = _lower_expression(expr.consequent, ctx)
        alternate = _lower_expression(expr.alternate, ctx)
        return IrConditional(
            span=expr.span,
            condition=condition,
            consequent=consequent,
            alternate=alternate,
            type_info=ctx.type_of(expr),
        )
    if isinstance(expr, nodes.CallExpression):
        callee = _lower_expression(expr.callee, ctx)
        arguments = [_lower_expression(arg, ctx) for arg in expr.arguments]
        return IrCall(span=expr.span, callee=callee, arguments=arguments, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.MemberExpression):
        obj = _lower_expression(expr.object, ctx)
        return IrMemberAccess(
            span=expr.span,
            object=obj,
            property=expr.property,
            binding=ctx.binding_of(expr),
            type_info=ctx.type_of(expr),
        )
    if isinstance(expr, nodes.IndexExpression):
        collection = _lower_expression(expr.collection, ctx)
        index = _lower_expression(expr.index, ctx)
        return IrIndex(span=expr.span, collection=collection, index=index, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.ArrayLiteral):
        elements = [_lower_expression(element, ctx) for element in expr.elements]
        return IrArrayLiteral(span=expr.span, elements=elements, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.ObjectLiteral):
        properties = [
            IrObjectProperty(span=prop.span, key=prop.key, value=_lower_expression(prop.value, ctx))
            for prop in expr.properties
        ]
        return IrObjectLiteral(span=expr.span, properties=properties, type_info=ctx.type_of(expr))
    if isinstance(expr, nodes.LambdaExpression):
        parameters = [_lower_parameter(param, ctx) for param in expr.parameters]
        return_annotation = _annotation_name(expr.return_type)
        if isinstance(expr.body, nodes.Statement):
            body_statements = _lower_statement(expr.body, ctx)
            body_expression = None
        else:
            body_statements = []
            body_expression = _lower_expression(expr.body, ctx)
        return IrLambda(
            span=expr.span,
            parameters=parameters,
            return_annotation=return_annotation,
            body_expression=body_expression,
            body_statements=body_statements,
            type_info=ctx.type_of(expr),
        )
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def _annotation_name(annotation: Optional[nodes.TypeAnnotation]) -> Optional[str]:
    if annotation is None:
        return None
    return annotation.name
