from __future__ import annotations

from typing import Iterable, Optional

from ..ir.ir import (
    IrArrayLiteral,
    IrAssignment,
    IrBinary,
    IrCall,
    IrConditional,
    IrExpr,
    IrExpressionStatement,
    IrIdentifier,
    IrIf,
    IrLambda,
    IrLiteral,
    IrMemberAccess,
    IrObjectLiteral,
    IrObjectProperty,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
)


class LocalOptimizer:
    """Performs lightweight simplifications directly on the structural IR."""

    def optimize(self, module: ModuleIr) -> ModuleIr:
        for glob in module.globals:
            if glob.initializer is not None:
                glob.initializer = self._opt_expr(glob.initializer)
        for func in module.functions:
            func.body = [self._opt_statement(stmt) for stmt in func.body]
        return module

    # ------------------------------------------------------------------ statements

    def _opt_statement(self, stmt: IrStatement) -> IrStatement:
        if isinstance(stmt, IrVariableDeclaration):
            if stmt.initializer is not None:
                stmt.initializer = self._opt_expr(stmt.initializer)
            return stmt
        if isinstance(stmt, IrExpressionStatement):
            stmt.expression = self._opt_expr(stmt.expression)
            return stmt
        if isinstance(stmt, IrReturn):
            if stmt.value is not None:
                stmt.value = self._opt_expr(stmt.value)
            return stmt
        if isinstance(stmt, IrIf):
            stmt.condition = self._opt_expr(stmt.condition)
            stmt.then_branch = [self._opt_statement(inner) for inner in stmt.then_branch]
            stmt.else_branch = [self._opt_statement(inner) for inner in stmt.else_branch]
            literal = self._as_literal(stmt.condition)
            if literal is not None:
                branch = stmt.then_branch if self._truthy(literal.value) else stmt.else_branch
                return self._collapse_branch(branch, stmt)
            return stmt
        if isinstance(stmt, IrWhile):
            stmt.condition = self._opt_expr(stmt.condition)
            stmt.body = [self._opt_statement(inner) for inner in stmt.body]
            return stmt
        return stmt

    def _collapse_branch(self, statements: Iterable[IrStatement], fallback: IrIf) -> IrStatement:
        block = list(statements)
        if len(block) == 1:
            return block[0]
        # When multiple statements, keep the IrIf but clear the unused branch to preserve structure.
        fallback.then_branch = block
        fallback.else_branch = []
        fallback.condition = IrLiteral(span=fallback.span, value=True, raw="verum")
        return fallback

    # ------------------------------------------------------------------ expressions

    def _opt_expr(self, expr: Optional[IrExpr]) -> Optional[IrExpr]:
        if expr is None:
            return None
        if isinstance(expr, IrLiteral):
            return expr
        if isinstance(expr, IrIdentifier):
            return expr
        if isinstance(expr, IrUnary):
            expr.operand = self._opt_expr(expr.operand)
            literal = self._as_literal(expr.operand)
            if literal is not None:
                folded = self._fold_unary(expr.operator, literal.value)
                if folded is not None:
                    return self._literal(expr, folded)
            return expr
        if isinstance(expr, IrBinary):
            expr.left = self._opt_expr(expr.left)
            expr.right = self._opt_expr(expr.right)
            folded = self._fold_binary(expr)
            if folded is not None:
                return folded
            simplified = self._simplify_binary_identities(expr)
            if simplified is not None:
                return simplified
            return expr
        if isinstance(expr, IrAssignment):
            expr.value = self._opt_expr(expr.value)
            return expr
        if isinstance(expr, IrConditional):
            expr.condition = self._opt_expr(expr.condition)
            expr.consequent = self._opt_expr(expr.consequent)
            expr.alternate = self._opt_expr(expr.alternate)
            literal = self._as_literal(expr.condition)
            if literal is not None:
                return expr.consequent if self._truthy(literal.value) else expr.alternate
            return expr
        if isinstance(expr, IrCall):
            expr.callee = self._opt_expr(expr.callee)
            expr.arguments = [self._opt_expr(arg) for arg in expr.arguments]
            return expr
        if isinstance(expr, IrMemberAccess):
            expr.object = self._opt_expr(expr.object)
            return expr
        if isinstance(expr, IrArrayLiteral):
            expr.elements = [self._opt_expr(element) for element in expr.elements if element is not None]
            return expr
        if isinstance(expr, IrObjectLiteral):
            expr.properties = [
                IrObjectProperty(span=prop.span, key=prop.key, value=self._opt_expr(prop.value))
                for prop in expr.properties
            ]
            return expr
        if isinstance(expr, IrLambda):
            expr.body_statements = [self._opt_statement(stmt) for stmt in expr.body_statements]
            if expr.body_expression is not None:
                expr.body_expression = self._opt_expr(expr.body_expression)
            for param in expr.parameters:
                if param.default_value is not None:
                    param.default_value = self._opt_expr(param.default_value)
            return expr
        return expr

    # ------------------------------------------------------------------ helpers

    def _fold_unary(self, operator: str, value) -> Optional[object]:
        if operator in {"-", "NEGATE"}:
            if isinstance(value, (int, float)):
                return -value
        if operator in {"NOT", "!"}:
            return not self._truthy(value)
        if operator in {"+", "POSITIVE"}:
            if isinstance(value, (int, float)):
                return +value
        return None

    def _fold_binary(self, expr: IrBinary) -> Optional[IrExpr]:
        left = self._as_literal(expr.left)
        right = self._as_literal(expr.right)
        op = expr.operator
        if op in {"NULLISH", "??"} and left is not None:
            return expr.left if left.value is not None else expr.right
        if op in {"OR", "||"} and left is not None:
            return expr.left if self._truthy(left.value) else expr.right
        if op in {"AND", "&&"} and left is not None:
            return expr.right if self._truthy(left.value) else expr.left
        if left is None or right is None:
            return None

        value = self._eval_binary(op, left.value, right.value)
        if value is None:
            return None
        return self._literal(expr, value)

    def _simplify_binary_identities(self, expr: IrBinary) -> Optional[IrExpr]:
        right = self._as_literal(expr.right)
        left = self._as_literal(expr.left)
        op = expr.operator
        if op in {"+", "ADD"} and right and self._is_zero(right.value):
            return expr.left
        if op in {"+", "ADD"} and left and self._is_zero(left.value):
            return expr.right
        if op in {"-", "SUB"} and right and self._is_zero(right.value):
            return expr.left
        if op in {"*", "MUL"}:
            if right and self._is_one(right.value):
                return expr.left
            if left and self._is_one(left.value):
                return expr.right
            if right and self._is_zero(right.value):
                return self._literal(expr, 0)
            if left and self._is_zero(left.value):
                return self._literal(expr, 0)
        if op in {"/", "DIV"} and right and self._is_one(right.value):
            return expr.left
        return None

    def _literal(self, expr: IrExpr, value) -> IrLiteral:
        return IrLiteral(
            span=expr.span,
            value=value,
            raw=self._literal_raw(value),
            type_info=getattr(expr, "type_info", None),
        )

    def _literal_raw(self, value) -> str:
        if value is None:
            return "nullum"
        if value is True:
            return "verum"
        if value is False:
            return "falsum"
        return str(value)

    def _is_zero(self, value) -> bool:
        return isinstance(value, (int, float)) and value == 0

    def _is_one(self, value) -> bool:
        return isinstance(value, (int, float)) and value == 1

    def _as_literal(self, expr: Optional[IrExpr]) -> Optional[IrLiteral]:
        if isinstance(expr, IrLiteral):
            return expr
        return None

    def _truthy(self, value) -> bool:
        if value is None:
            return False
        return bool(value)

    def _eval_binary(self, operator: str, left, right):
        try:
            if operator in {"+", "ADD"}:
                return left + right
            if operator in {"-", "SUB"}:
                return left - right
            if operator in {"*", "MUL"}:
                return left * right
            if operator in {"/", "DIV"}:
                return left / right
            if operator in {"%", "MOD"}:
                return left % right
            if operator in {"==", "EQ"}:
                return left == right
            if operator in {"!=", "NE"}:
                return left != right
            if operator in {">", "GT"}:
                return left > right
            if operator in {"<", "LT"}:
                return left < right
            if operator in {">=", "GE"}:
                return left >= right
            if operator in {"<=", "LE"}:
                return left <= right
        except Exception:
            return None
        return None
