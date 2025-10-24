"""Semantic analysis for Scriptum modules."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Dict, List, Optional, Tuple

from ..ast import nodes
from ..text import Span
from . import symbols, types


@dataclass(slots=True)
class SemanticDiagnostic:
    code: str
    message: str
    span: Optional[Span]


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.symbols = symbols.SymbolTable()
        self.diagnostics: List[SemanticDiagnostic] = []
        self.current_return_type: Optional[types.Type] = None
        self.loop_depth: int = 0
        self.function_signatures: Dict[str, Tuple[List[types.Type], Optional[types.Type]]] = {}

    def analyze(self, module: nodes.Module) -> List[SemanticDiagnostic]:
        self.diagnostics.clear()
        self.symbols = symbols.SymbolTable()
        self.function_signatures = {}
        self.current_return_type = None
        self.loop_depth = 0

        for declaration in module.declarations:
            if isinstance(declaration, nodes.FunctionDeclaration):
                self._register_function(declaration)

        for declaration in module.declarations:
            if isinstance(declaration, nodes.FunctionDeclaration):
                self._analyze_function(declaration)
            elif isinstance(declaration, nodes.VariableDeclaration):
                self._analyze_variable(declaration)
        return list(self.diagnostics)

    def _register_function(self, func: nodes.FunctionDeclaration) -> None:
        param_types = [
            self._annotation_to_type(param.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
            for param in func.parameters
        ]
        return_annotation = self._annotation_to_type(func.return_type)
        function_type = types.function_type(param_types, return_annotation or types.PRIMITIVE_TYPES["quodlibet"])
        if not self.symbols.declare(symbols.Symbol(func.name, function_type, mutable=False, span=func.span)):
            self._error("S110", f"Symbol '{func.name}' already declared in this scope", func.span)
        self.function_signatures[func.name] = (param_types, return_annotation)

    def _analyze_function(self, func: nodes.FunctionDeclaration) -> None:
        signature = self.function_signatures.get(func.name)
        param_types = signature[0] if signature else [
            self._annotation_to_type(param.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
            for param in func.parameters
        ]
        return_annotation = signature[1] if signature else self._annotation_to_type(func.return_type)

        previous_return = self.current_return_type
        previous_loop_depth = self.loop_depth
        self.current_return_type = return_annotation
        self.loop_depth = 0

        self.symbols.push_scope()
        for index, param in enumerate(func.parameters):
            param_type = param_types[index] if index < len(param_types) else (
                self._annotation_to_type(param.type_annotation) or types.PRIMITIVE_TYPES["quodlibet"]
            )
            if not self.symbols.declare(symbols.Symbol(param.name, param_type, mutable=False, span=param.span)):
                self._error("S110", f"Parameter '{param.name}' already declared in this scope", param.span)
        for stmt in func.body.statements:
            self._analyze_statement(stmt)
        self.symbols.pop_scope()

        self.current_return_type = previous_return
        self.loop_depth = previous_loop_depth

    def _analyze_variable(self, decl: nodes.VariableDeclaration) -> None:
        init_type = self._analyze_expression(decl.initializer) if decl.initializer else None
        annotated_type = self._annotation_to_type(decl.type_annotation)
        var_type = annotated_type or init_type or types.PRIMITIVE_TYPES["quodlibet"]

        if annotated_type and init_type and not annotated_type.is_assignable_from(init_type):
            self._error(
                "T200",
                f"Type mismatch: cannot initialise '{decl.name}' of type {annotated_type} with {init_type}",
                decl.span,
            )
        if not self.symbols.declare(symbols.Symbol(decl.name, var_type, mutable=decl.mutable, span=decl.span)):
            self._error("S110", f"Symbol '{decl.name}' already declared in this scope", decl.span)

    def _analyze_statement(self, stmt: nodes.Statement) -> None:
        if isinstance(stmt, nodes.VariableDeclaration):
            self._analyze_variable(stmt)
        elif isinstance(stmt, nodes.ExpressionStatement):
            self._analyze_expression(stmt.expression)
        elif isinstance(stmt, nodes.ReturnStatement):
            value_type = self._analyze_expression(stmt.value) if stmt.value else types.PRIMITIVE_TYPES["vacuum"]
            if self.current_return_type and value_type and not self.current_return_type.is_assignable_from(value_type):
                self._error(
                    "T010",
                    f"Return type mismatch: expected {self.current_return_type}, got {value_type}",
                    stmt.span,
                )
        elif isinstance(stmt, nodes.BlockStatement):
            self.symbols.push_scope()
            for inner in stmt.statements:
                self._analyze_statement(inner)
            self.symbols.pop_scope()
        elif isinstance(stmt, nodes.IfStatement):
            condition_type = self._analyze_expression(stmt.condition)
            self._expect_boolean(condition_type, stmt.condition.span, "T020", "Condition for 'si' must be booleanum")
            self._analyze_statement(stmt.then_branch)
            if stmt.else_branch:
                self._analyze_statement(stmt.else_branch)
        elif isinstance(stmt, nodes.WhileStatement):
            condition_type = self._analyze_expression(stmt.condition)
            self._expect_boolean(condition_type, stmt.condition.span, "T021", "Condition for 'dum' must be booleanum")
            self.loop_depth += 1
            self._analyze_statement(stmt.body)
            self.loop_depth -= 1
        elif isinstance(stmt, nodes.ForStatement):
            iterable_type = self._analyze_expression(stmt.iterable)
            element_type = self._iterable_element_type(iterable_type, stmt.iterable.span)
            target_annotation = self._annotation_to_type(stmt.target.type_annotation)
            target_type = target_annotation or element_type
            if target_annotation and not target_annotation.is_assignable_from(element_type):
                self._error(
                    "T031",
                    f"Loop variable '{stmt.target.name}' expects {target_annotation}, got {element_type}",
                    stmt.target.span,
                )
            self.symbols.push_scope()
            if not self.symbols.declare(
                symbols.Symbol(stmt.target.name, target_type, mutable=stmt.target.mutable, span=stmt.target.span)
            ):
                self._error("S110", f"Symbol '{stmt.target.name}' already declared in this scope", stmt.target.span)
            self.loop_depth += 1
            self._analyze_statement(stmt.body)
            self.loop_depth -= 1
            self.symbols.pop_scope()
        elif isinstance(stmt, nodes.BreakStatement):
            if self.loop_depth == 0:
                self._error("T040", "'frange' can only be used inside loops", stmt.span)
        elif isinstance(stmt, nodes.ContinueStatement):
            if self.loop_depth == 0:
                self._error("T041", "'perge' can only be used inside loops", stmt.span)

    def _analyze_expression(self, expr: Optional[nodes.Expression]) -> Optional[types.Type]:
        if expr is None:
            return None
        if isinstance(expr, nodes.Literal):
            return types.type_from_literal(expr.value, expr.raw)
        if isinstance(expr, nodes.Identifier):
            symbol = self.symbols.lookup(expr.name)
            if symbol is None:
                self._error("S100", f"Undeclared identifier '{expr.name}'", expr.span)
                return types.PRIMITIVE_TYPES["quodlibet"]
            return symbol.type
        if isinstance(expr, nodes.UnaryExpression):
            return self._analyze_unary(expr)
        if isinstance(expr, nodes.AssignmentExpression):
            return self._analyze_assignment(expr)
        if isinstance(expr, nodes.BinaryExpression):
            return self._analyze_binary(expr)
        if isinstance(expr, nodes.CallExpression):
            return self._analyze_call(expr)
        if isinstance(expr, nodes.MemberExpression):
            self._analyze_expression(expr.object)
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.IndexExpression):
            collection_type = self._analyze_expression(expr.collection)
            self._analyze_expression(expr.index)
            if collection_type and collection_type.kind is types.TypeKind.ARRAY and collection_type.element:
                return collection_type.element
            return types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.ConditionalExpression):
            condition_type = self._analyze_expression(expr.condition)
            self._expect_boolean(condition_type, expr.condition.span, "T130", "Condition for '?:' must be booleanum")
            consequent = self._analyze_expression(expr.consequent)
            alternate = self._analyze_expression(expr.alternate)
            filtered = [t for t in (consequent, alternate) if t]
            return types.least_restrictive(filtered) if filtered else types.PRIMITIVE_TYPES["quodlibet"]
        if isinstance(expr, nodes.ArrayLiteral):
            element_types = [self._analyze_expression(element) for element in expr.elements]
            filtered = [t for t in element_types if t]
            element_type = types.least_restrictive(filtered) if filtered else types.PRIMITIVE_TYPES["quodlibet"]
            return types.Type(types.TypeKind.ARRAY, element=element_type)
        if isinstance(expr, nodes.ObjectLiteral):
            value_types = {
                prop.key: self._analyze_expression(prop.value) or types.PRIMITIVE_TYPES["quodlibet"]
                for prop in expr.properties
            }
            return types.Type(types.TypeKind.OBJECT, fields=value_types)
        if isinstance(expr, nodes.LambdaExpression):
            return types.PRIMITIVE_TYPES["quodlibet"]
        return types.PRIMITIVE_TYPES["quodlibet"]

    def _analyze_unary(self, expr: nodes.UnaryExpression) -> types.Type:
        operand_type = self._analyze_expression(expr.operand)
        if expr.operator is nodes.UnaryOperator.NOT:
            self._expect_boolean(operand_type, expr.span, "T110", "Logical negation requires booleanum")
            return types.PRIMITIVE_TYPES["booleanum"]
        if expr.operator in {nodes.UnaryOperator.NEGATE, nodes.UnaryOperator.POSITIVE}:
            if operand_type and operand_type.kind not in {types.TypeKind.NUMERUS, types.TypeKind.QUODLIBET}:
                self._error("T100", "Unary arithmetic operands must be numerus", expr.span)
            return types.PRIMITIVE_TYPES["numerus"]
        return operand_type or types.PRIMITIVE_TYPES["quodlibet"]

    def _analyze_assignment(self, expr: nodes.AssignmentExpression) -> types.Type:
        if isinstance(expr.target, nodes.Identifier):
            symbol = self.symbols.lookup(expr.target.name)
            if symbol is None:
                self._error("S100", f"Undeclared identifier '{expr.target.name}'", expr.target.span)
                target_type: Optional[types.Type] = types.PRIMITIVE_TYPES["quodlibet"]
            else:
                target_type = symbol.type
                if not symbol.mutable:
                    self._error("S120", f"Cannot assign to immutable symbol '{expr.target.name}'", expr.span)
        else:
            target_type = self._analyze_expression(expr.target)
        value_type = self._analyze_expression(expr.value)
        if target_type and value_type and not target_type.is_assignable_from(value_type):
            self._error("T200", f"Type mismatch: cannot assign {value_type} to {target_type}", expr.span)
        return target_type or value_type or types.PRIMITIVE_TYPES["quodlibet"]

    def _analyze_binary(self, expr: nodes.BinaryExpression) -> types.Type:
        left = self._analyze_expression(expr.left)
        right = self._analyze_expression(expr.right)
        op = expr.operator

        arithmetic_ops = {
            nodes.BinaryOperator.ADD,
            nodes.BinaryOperator.SUB,
            nodes.BinaryOperator.MUL,
            nodes.BinaryOperator.DIV,
            nodes.BinaryOperator.MOD,
            nodes.BinaryOperator.POW,
        }
        if op in arithmetic_ops:
            if (left and left.kind not in {types.TypeKind.NUMERUS, types.TypeKind.QUODLIBET}) or (
                right and right.kind not in {types.TypeKind.NUMERUS, types.TypeKind.QUODLIBET}
            ):
                self._error("T100", "Arithmetic operands must be numerus", expr.span)
                return types.PRIMITIVE_TYPES["quodlibet"]
            return types.PRIMITIVE_TYPES["numerus"]

        if op in {
            nodes.BinaryOperator.GT,
            nodes.BinaryOperator.GE,
            nodes.BinaryOperator.LT,
            nodes.BinaryOperator.LE,
        }:
            if (left and left.kind not in {types.TypeKind.NUMERUS, types.TypeKind.QUODLIBET}) or (
                right and right.kind not in {types.TypeKind.NUMERUS, types.TypeKind.QUODLIBET}
            ):
                self._error("T102", "Comparison operands must be numerus", expr.span)
            return types.PRIMITIVE_TYPES["booleanum"]

        if op in {
            nodes.BinaryOperator.EQ,
            nodes.BinaryOperator.NE,
            nodes.BinaryOperator.STRICT_EQ,
            nodes.BinaryOperator.STRICT_NE,
        }:
            return types.PRIMITIVE_TYPES["booleanum"]

        if op in {nodes.BinaryOperator.AND, nodes.BinaryOperator.OR}:
            if (left and left.kind not in {types.TypeKind.BOOLEANUM, types.TypeKind.QUODLIBET}) or (
                right and right.kind not in {types.TypeKind.BOOLEANUM, types.TypeKind.QUODLIBET}
            ):
                self._error("T110", "Logical operands must be booleanum", expr.span)
            return types.PRIMITIVE_TYPES["booleanum"]

        if op is nodes.BinaryOperator.NULLISH:
            return self._analyze_nullish(expr, left, right)

        return left or right or types.PRIMITIVE_TYPES["quodlibet"]

    def _analyze_nullish(
        self,
        expr: nodes.BinaryExpression,
        left: Optional[types.Type],
        right: Optional[types.Type],
    ) -> types.Type:
        if left and left.kind not in {
            types.TypeKind.OPTIONAL,
            types.TypeKind.NULLUM,
            types.TypeKind.QUODLIBET,
        }:
            self._error("T120", "Left operand of '??' must be optional, nullum or quodlibet", expr.span)

        if left and left.kind is types.TypeKind.OPTIONAL and left.element and right:
            if not left.element.is_assignable_from(right):
                self._error(
                    "T121",
                    f"Right operand of '??' must be assignable to {left.element}",
                    expr.right.span,
                )

        result_candidates: List[types.Type] = []
        if left:
            if left.kind is types.TypeKind.OPTIONAL and left.element:
                result_candidates.append(left.element)
            else:
                result_candidates.append(left)
        if right:
            result_candidates.append(right)
        return types.least_restrictive(result_candidates) if result_candidates else types.PRIMITIVE_TYPES["quodlibet"]

    def _analyze_call(self, expr: nodes.CallExpression) -> types.Type:
        callee_type = self._analyze_expression(expr.callee)
        argument_types = [self._analyze_expression(argument) for argument in expr.arguments]
        if callee_type and callee_type.kind is types.TypeKind.FUNCTION:
            param_types = callee_type.params or []
            if len(param_types) != len(argument_types):
                self._error(
                    "T300",
                    f"Expected {len(param_types)} arguments, got {len(argument_types)}",
                    expr.span,
                )
            for index, (param_type, arg_type, arg_expr) in enumerate(
                zip_longest(param_types, argument_types, expr.arguments, fillvalue=None),
                start=1,
            ):
                if param_type is None or arg_type is None:
                    continue
                if not param_type.is_assignable_from(arg_type):
                    self._error(
                        "T301",
                        f"Argument {index} type mismatch: expected {param_type}, got {arg_type}",
                        arg_expr.span,
                    )
            return callee_type.ret or types.PRIMITIVE_TYPES["quodlibet"]

        if callee_type is not None:
            self._error("T302", "Expression is not callable", expr.callee.span)
        else:
            self._error("T302", "Expression is not callable", expr.span)
        return types.PRIMITIVE_TYPES["quodlibet"]

    def _annotation_to_type(self, annotation: Optional[nodes.TypeAnnotation]) -> Optional[types.Type]:
        if annotation is None:
            return None
        return types.type_from_annotation(annotation.name)

    def _expect_boolean(self, type_obj: Optional[types.Type], span: Optional[object], code: str, message: str) -> None:
        if type_obj is None:
            return
        if type_obj.kind not in {types.TypeKind.BOOLEANUM, types.TypeKind.QUODLIBET}:
            self._error(code, message, span)

    def _iterable_element_type(self, iterable_type: Optional[types.Type], span: Optional[object]) -> types.Type:
        if iterable_type is None:
            return types.PRIMITIVE_TYPES["quodlibet"]
        if iterable_type.kind is types.TypeKind.ARRAY and iterable_type.element:
            return iterable_type.element
        if iterable_type.kind is types.TypeKind.QUODLIBET:
            return types.PRIMITIVE_TYPES["quodlibet"]
        self._error("T030", "Expression in 'pro' must be iterable", span)
        return types.PRIMITIVE_TYPES["quodlibet"]

    def _error(self, code: str, message: str, span: Optional[object]) -> None:
        self.diagnostics.append(SemanticDiagnostic(code=code, message=message, span=span))
