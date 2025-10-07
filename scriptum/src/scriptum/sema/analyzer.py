"""Semantic analysis for Scriptum modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..ast import nodes
from ..parser.parser import ScriptumParser
from ..text import SourceFile
from . import symbols, types


@dataclass(slots=True)
class SemanticDiagnostic:
    message: str
    span: Optional[object]


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.symbols = symbols.SymbolTable()
        self.diagnostics: List[SemanticDiagnostic] = []
        self.current_return_type: Optional[types.Type] = None

    def analyze(self, module: nodes.Module) -> List[SemanticDiagnostic]:
        self.diagnostics.clear()
        for declaration in module.declarations:
            if isinstance(declaration, nodes.FunctionDeclaration):
                self._analyze_function(declaration)
            elif isinstance(declaration, nodes.VariableDeclaration):
                self._analyze_variable(declaration)
        return list(self.diagnostics)

    def _analyze_function(self, func: nodes.FunctionDeclaration) -> None:
        self.symbols.push_scope()
        self.current_return_type = self._annotation_to_type(func.return_type) or types.type_from_annotation("vacuum")
        for param in func.parameters:
            param_type = self._annotation_to_type(param.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
            try:
                self.symbols.declare(symbols.Symbol(param.name, param_type, mutable=False, span=param.span))
            except ValueError as exc:
                self._error(str(exc), param.span)
        for stmt in func.body.statements:
            self._analyze_statement(stmt)
        self.symbols.pop_scope()

    def _analyze_variable(self, decl: nodes.VariableDeclaration) -> None:
        var_type = self._annotation_to_type(decl.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
        init_type = self._analyze_expression(decl.initializer) if decl.initializer else None
        if init_type and not var_type.is_assignable_from(init_type):
            self._error(
                f"Type mismatch: cannot initialise '{decl.name}' of type {var_type} with {init_type}",
                decl.span,
            )
        try:
            self.symbols.declare(symbols.Symbol(decl.name, var_type, mutable=decl.mutable, span=decl.span))
        except ValueError as exc:
            self._error(str(exc), decl.span)

    def _analyze_statement(self, stmt: nodes.Statement) -> None:
        if isinstance(stmt, nodes.VariableDeclaration):
            self._analyze_variable(stmt)
        elif isinstance(stmt, nodes.ExpressionStatement):
            self._analyze_expression(stmt.expression)
        elif isinstance(stmt, nodes.ReturnStatement):
            value_type = self._analyze_expression(stmt.value) if stmt.value else types.PRIMITIVE_TYPES["vacuum"]
            if self.current_return_type and not self.current_return_type.is_assignable_from(value_type):
                self._error(
                    f"Return type mismatch: expected {self.current_return_type}, got {value_type}",
                    stmt.span,
                )
        elif isinstance(stmt, nodes.BlockStatement):
            self.symbols.push_scope()
            for inner in stmt.statements:
                self._analyze_statement(inner)
            self.symbols.pop_scope()
        elif isinstance(stmt, nodes.IfStatement):
            self._analyze_expression(stmt.condition)
            self._analyze_statement(stmt.then_branch)
            if stmt.else_branch:
                self._analyze_statement(stmt.else_branch)
        elif isinstance(stmt, nodes.WhileStatement):
            self._analyze_expression(stmt.condition)
            self._analyze_statement(stmt.body)
        elif isinstance(stmt, nodes.ForStatement):
            iterable_type = self._analyze_expression(stmt.iterable)
            target_type = self._annotation_to_type(stmt.target.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
            if iterable_type and iterable_type.kind is types.TypeKind.ARRAY and iterable_type.element:
                element_type = iterable_type.element
            else:
                element_type = types.PRIMITIVE_TYPES["quodlibet"]
            if not target_type.is_assignable_from(element_type):
                self._error(
                    f"Loop variable '{stmt.target.name}' expects {target_type}, got {element_type}",
                    stmt.target.span,
                )
            self.symbols.push_scope()
            try:
                self.symbols.declare(
                    symbols.Symbol(stmt.target.name, target_type, mutable=stmt.target.mutable, span=stmt.target.span)
                )
            except ValueError as exc:
                self._error(str(exc), stmt.target.span)
            self._analyze_statement(stmt.body)
            self.symbols.pop_scope()

    def _analyze_expression(self, expr: Optional[nodes.Expression]) -> Optional[types.Type]:
        if expr is None:
            return None
        if isinstance(expr, nodes.Literal):
            return types.type_from_literal(expr.value, expr.raw)
        if isinstance(expr, nodes.Identifier):
            symbol = self.symbols.lookup(expr.name)
            if symbol is None:
                self._error(f"Undeclared identifier '{expr.name}'", expr.span)
                return types.PRIMITIVE_TYPES["quodlibet"]
            return symbol.type
        if isinstance(expr, nodes.AssignmentExpression):
            target_type = self._analyze_expression(expr.target)
            value_type = self._analyze_expression(expr.value)
            if isinstance(expr.target, nodes.Identifier) and target_type and value_type:
                message = self.symbols.assign(expr.target.name, value_type)
                if message:
                    self._error(message, expr.span)
            return target_type
        if isinstance(expr, nodes.BinaryExpression):
            left = self._analyze_expression(expr.left)
            right = self._analyze_expression(expr.right)
            if expr.operator in {nodes.BinaryOperator.ADD, nodes.BinaryOperator.SUB, nodes.BinaryOperator.MUL, nodes.BinaryOperator.DIV}:
                if left and right:
                    if left.kind is types.TypeKind.NUMERUS and right.kind is types.TypeKind.NUMERUS:
                        return types.PRIMITIVE_TYPES["numerus"]
                    self._error("Arithmetic operands must be numerus", expr.span)
                return types.PRIMITIVE_TYPES["quodlibet"]
            if expr.operator in {nodes.BinaryOperator.GT, nodes.BinaryOperator.GE, nodes.BinaryOperator.LT, nodes.BinaryOperator.LE}:
                return types.PRIMITIVE_TYPES["booleanum"]
            if expr.operator in {nodes.BinaryOperator.EQ, nodes.BinaryOperator.NE, nodes.BinaryOperator.STRICT_EQ, nodes.BinaryOperator.STRICT_NE}:
                return types.PRIMITIVE_TYPES["booleanum"]
            return left or right
        if isinstance(expr, nodes.CallExpression):
            for argument in expr.arguments:
                self._analyze_expression(argument)
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.MemberExpression):
            self._analyze_expression(expr.object)
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.IndexExpression):
            base_type = self._analyze_expression(expr.collection)
            if base_type and base_type.kind is types.TypeKind.ARRAY and base_type.element:
                return base_type.element
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.ConditionalExpression):
            self._analyze_expression(expr.condition)
            consequent = self._analyze_expression(expr.consequent)
            alternate = self._analyze_expression(expr.alternate)
            return types.least_restrictive([t for t in [consequent, alternate] if t])
        if isinstance(expr, nodes.LambdaExpression):
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.ArrayLiteral):
            element_types = [self._analyze_expression(element) for element in expr.elements]
            element_types = [t for t in element_types if t]
            element_type = types.least_restrictive(element_types) if element_types else types.PRIMITIVE_TYPES["quodlibet"]
            return types.Type(types.TypeKind.ARRAY, element=element_type)
        return types.PRIMITIVE_TYPES["quodlibet"]

    def _annotation_to_type(self, annotation: Optional[nodes.TypeAnnotation]) -> Optional[types.Type]:
        if annotation is None:
            return None
        return types.type_from_annotation(annotation.name)

    def _error(self, message: str, span: Optional[object]) -> None:
        self.diagnostics.append(SemanticDiagnostic(message=message, span=span))
