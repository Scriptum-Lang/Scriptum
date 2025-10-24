"""Lower Scriptum AST nodes into the structural IR."""

from __future__ import annotations

from typing import Iterable, List, Optional

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


def lower_module(module: nodes.Module) -> ModuleIr:
    globals_ir: List[IrVariable] = []
    functions_ir: List[IrFunction] = []

    for declaration in module.declarations:
        if isinstance(declaration, nodes.FunctionDeclaration):
            functions_ir.append(_lower_function(declaration))
        elif isinstance(declaration, nodes.VariableDeclaration):
            globals_ir.append(_lower_global_variable(declaration))

    return IrModule(span=module.span, globals=globals_ir, functions=functions_ir)


def _lower_global_variable(decl: nodes.VariableDeclaration) -> IrVariable:
    initializer = _lower_expression(decl.initializer) if decl.initializer else None
    annotation = _annotation_name(decl.type_annotation)
    return IrVariable(
        span=decl.span,
        name=decl.name,
        mutable=decl.mutable,
        type_annotation=annotation,
        initializer=initializer,
    )


def _lower_function(func: nodes.FunctionDeclaration) -> IrFunction:
    parameters = [_lower_parameter(param) for param in func.parameters]
    return_annotation = _annotation_name(func.return_type)
    body_statements = _lower_block(func.body.statements)
    return IrFunction(
        span=func.span,
        name=func.name,
        parameters=parameters,
        return_annotation=return_annotation,
        body=body_statements,
    )


def _lower_parameter(param: nodes.Parameter) -> IrParameter:
    annotation = _annotation_name(param.type_annotation)
    default_value = _lower_expression(param.default_value) if param.default_value else None
    return IrParameter(
        span=param.span,
        name=param.name,
        type_annotation=annotation,
        default_value=default_value,
    )


def _lower_block(statements: Iterable[nodes.Statement]) -> List[IrStatement]:
    result: List[IrStatement] = []
    for stmt in statements:
        result.extend(_lower_statement(stmt))
    return result


def _lower_statement(stmt: nodes.Statement) -> List[IrStatement]:
    if isinstance(stmt, nodes.BlockStatement):
        return _lower_block(stmt.statements)

    lowered = _lower_single_statement(stmt)
    return [lowered]


def _lower_single_statement(stmt: nodes.Statement) -> IrStatement:
    if isinstance(stmt, nodes.VariableDeclaration):
        initializer = _lower_expression(stmt.initializer) if stmt.initializer else None
        annotation = _annotation_name(stmt.type_annotation)
        return IrVariableDeclaration(
            span=stmt.span,
            name=stmt.name,
            mutable=stmt.mutable,
            type_annotation=annotation,
            initializer=initializer,
        )
    if isinstance(stmt, nodes.ExpressionStatement):
        expr = _lower_expression(stmt.expression)
        return IrExpressionStatement(span=stmt.span, expression=expr)
    if isinstance(stmt, nodes.ReturnStatement):
        value = _lower_expression(stmt.value) if stmt.value else None
        return IrReturn(span=stmt.span, value=value)
    if isinstance(stmt, nodes.IfStatement):
        condition = _lower_expression(stmt.condition)
        then_branch = _lower_statement(stmt.then_branch)
        else_branch = _lower_statement(stmt.else_branch) if stmt.else_branch else []
        return IrIf(
            span=stmt.span,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )
    if isinstance(stmt, nodes.WhileStatement):
        condition = _lower_expression(stmt.condition)
        body = _lower_statement(stmt.body)
        return IrWhile(span=stmt.span, condition=condition, body=body)
    if isinstance(stmt, nodes.ForStatement):
        iterable = _lower_expression(stmt.iterable)
        target_annotation = _annotation_name(stmt.target.type_annotation)
        target = IrForTarget(
            span=stmt.target.span,
            name=stmt.target.name,
            mutable=stmt.target.mutable,
            type_annotation=target_annotation,
        )
        body = _lower_statement(stmt.body)
        return IrForIn(span=stmt.span, target=target, iterable=iterable, body=body)
    if isinstance(stmt, nodes.BreakStatement):
        return IrBreak(span=stmt.span)
    if isinstance(stmt, nodes.ContinueStatement):
        return IrContinue(span=stmt.span)
    raise TypeError(f"Unsupported statement type: {type(stmt)!r}")


def _lower_expression(expr: Optional[nodes.Expression]) -> Optional[IrExpr]:
    if expr is None:
        return None
    if isinstance(expr, nodes.Identifier):
        return IrIdentifier(span=expr.span, name=expr.name)
    if isinstance(expr, nodes.Literal):
        return IrLiteral(span=expr.span, value=expr.value, raw=expr.raw)
    if isinstance(expr, nodes.UnaryExpression):
        operand = _lower_expression(expr.operand)
        operator = expr.operator.name if isinstance(expr.operator, nodes.UnaryOperator) else str(expr.operator)
        return IrUnary(span=expr.span, operator=operator, operand=operand)
    if isinstance(expr, nodes.BinaryExpression):
        left = _lower_expression(expr.left)
        right = _lower_expression(expr.right)
        operator = expr.operator.name if hasattr(expr.operator, "name") else str(expr.operator)
        return IrBinary(span=expr.span, operator=operator, left=left, right=right)
    if isinstance(expr, nodes.AssignmentExpression):
        target = _lower_expression(expr.target)
        value = _lower_expression(expr.value)
        return IrAssignment(span=expr.span, target=target, value=value)
    if isinstance(expr, nodes.ConditionalExpression):
        condition = _lower_expression(expr.condition)
        consequent = _lower_expression(expr.consequent)
        alternate = _lower_expression(expr.alternate)
        return IrConditional(
            span=expr.span,
            condition=condition,
            consequent=consequent,
            alternate=alternate,
        )
    if isinstance(expr, nodes.CallExpression):
        callee = _lower_expression(expr.callee)
        arguments = [_lower_expression(arg) for arg in expr.arguments]
        return IrCall(span=expr.span, callee=callee, arguments=arguments)
    if isinstance(expr, nodes.MemberExpression):
        obj = _lower_expression(expr.object)
        return IrMemberAccess(span=expr.span, object=obj, property=expr.property)
    if isinstance(expr, nodes.IndexExpression):
        collection = _lower_expression(expr.collection)
        index = _lower_expression(expr.index)
        return IrIndex(span=expr.span, collection=collection, index=index)
    if isinstance(expr, nodes.ArrayLiteral):
        elements = [_lower_expression(element) for element in expr.elements]
        return IrArrayLiteral(span=expr.span, elements=elements)
    if isinstance(expr, nodes.ObjectLiteral):
        properties = [
            IrObjectProperty(span=prop.span, key=prop.key, value=_lower_expression(prop.value))
            for prop in expr.properties
        ]
        return IrObjectLiteral(span=expr.span, properties=properties)
    if isinstance(expr, nodes.LambdaExpression):
        parameters = [_lower_parameter(param) for param in expr.parameters]
        return_annotation = _annotation_name(expr.return_type)
        if isinstance(expr.body, nodes.Statement):
            body_statements = _lower_statement(expr.body)
            body_expression = None
        else:
            body_statements = []
            body_expression = _lower_expression(expr.body)
        return IrLambda(
            span=expr.span,
            parameters=parameters,
            return_annotation=return_annotation,
            body_expression=body_expression,
            body_statements=body_statements,
        )
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def _annotation_name(annotation: Optional[nodes.TypeAnnotation]) -> Optional[str]:
    if annotation is None:
        return None
    return annotation.name
