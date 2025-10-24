"""
Code generation scaffolding for Scriptum.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..ir import (
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


class CodeEmitter:
    """Produces Scriptum source code from the lowered IR."""

    _INDENT = "    "

    def emit(self, module: ModuleIr) -> str:
        lines: List[str] = []
        for index, var in enumerate(module.globals):
            lines.append(self._emit_variable(var))
        if module.globals and module.functions:
            lines.append("")
        for index, func in enumerate(module.functions):
            lines.extend(self._emit_function(func))
            if index != len(module.functions) - 1:
                lines.append("")
        if not module.globals and not module.functions:
            formatted = ""
        else:
            formatted = "\n".join(lines) + "\n"
        return formatted

    # Top-level declarations -------------------------------------------------

    def _emit_variable(self, var: IrVariable) -> str:
        parts = ["mutabilis" if var.mutable else "constans"]
        if var.type_annotation:
            parts.append(var.type_annotation)
        parts.append(var.name)
        line = " ".join(parts)
        if var.initializer:
            line += f" = {self._emit_expression(var.initializer)}"
        return f"{line};"

    def _emit_function(self, func: IrFunction) -> List[str]:
        params = ", ".join(self._format_parameter(param) for param in func.parameters)
        header = f"functio {func.name}({params})"
        if func.return_annotation:
            header += f" -> {func.return_annotation}"
        header += " {"
        lines = [header]
        lines.extend(self._emit_statements(func.body, indent_level=1))
        lines.append("}")
        return lines

    def _format_parameter(self, param: IrParameter) -> str:
        pieces: List[str] = []
        if param.type_annotation:
            pieces.append(param.type_annotation)
        pieces.append(param.name)
        result = " ".join(pieces)
        if param.default_value:
            result += f" = {self._emit_expression(param.default_value)}"
        return result

    # Statements -------------------------------------------------------------

    def _emit_statements(self, statements: List[IrStatement], indent_level: int) -> List[str]:
        lines: List[str] = []
        for stmt in statements:
            lines.extend(self._emit_statement(stmt, indent_level))
        return lines

    def _emit_statement(self, stmt: IrStatement, indent_level: int) -> List[str]:
        indent = self._INDENT * indent_level

        if isinstance(stmt, IrVariableDeclaration):
            parts = ["mutabilis" if stmt.mutable else "constans"]
            if stmt.type_annotation:
                parts.append(stmt.type_annotation)
            parts.append(stmt.name)
            line = " ".join(parts)
            if stmt.initializer:
                line += f" = {self._emit_expression(stmt.initializer)}"
            return [f"{indent}{line};"]

        if isinstance(stmt, IrExpressionStatement):
            expr = self._emit_expression(stmt.expression)
            return [f"{indent}{expr};"]

        if isinstance(stmt, IrReturn):
            if stmt.value:
                return [f"{indent}redde {self._emit_expression(stmt.value)};"]
            return [f"{indent}redde;"]

        if isinstance(stmt, IrIf):
            lines: List[str] = []
            condition = self._emit_expression(stmt.condition)
            lines.append(f"{indent}si ({condition}) {{")
            lines.extend(self._emit_statements(stmt.then_branch, indent_level + 1))
            if stmt.else_branch:
                lines.append(f"{indent}}} aliter {{")
                lines.extend(self._emit_statements(stmt.else_branch, indent_level + 1))
                lines.append(f"{indent}}}")
            else:
                lines.append(f"{indent}}}")
            return lines

        if isinstance(stmt, IrWhile):
            condition = self._emit_expression(stmt.condition)
            lines = [f"{indent}dum ({condition}) {{"]  # while body
            lines.extend(self._emit_statements(stmt.body, indent_level + 1))
            lines.append(f"{indent}}}")
            return lines

        if isinstance(stmt, IrForIn):
            target = self._format_for_target(stmt.target)
            iterable = self._emit_expression(stmt.iterable)
            lines = [f"{indent}pro {target} in {iterable} {{"]
            lines.extend(self._emit_statements(stmt.body, indent_level + 1))
            lines.append(f"{indent}}}")
            return lines

        if isinstance(stmt, IrBreak):
            return [f"{indent}frange;"]

        if isinstance(stmt, IrContinue):
            return [f"{indent}perge;"]

        raise TypeError(f"Unsupported statement type: {type(stmt)!r}")

    def _format_for_target(self, target: IrForTarget) -> str:
        parts: List[str] = []
        if target.mutable:
            parts.append("mutabilis")
        if target.type_annotation:
            parts.append(target.type_annotation)
        parts.append(target.name)
        return " ".join(parts)

    # Expressions ------------------------------------------------------------

    def _emit_expression(
        self,
        expr: IrExpr,
        parent_prec: int = 0,
        position: str = "any",
        indent_level: int = 0,
    ) -> str:
        if isinstance(expr, IrIdentifier):
            return expr.name

        if isinstance(expr, IrLiteral):
            return expr.raw

        if isinstance(expr, IrUnary):
            operator = self._unary_symbol(expr.operator)
            operand = self._emit_expression(expr.operand, self._precedence_unary(), "right", indent_level)
            text = f"{operator}{operand}"
            return self._maybe_parenthesize(text, self._precedence_unary(), parent_prec, "right", position)

        if isinstance(expr, IrBinary):
            symbol, prec, assoc = self._binary_metadata(expr.operator)
            left = self._emit_expression(expr.left, prec, "left", indent_level)
            right = self._emit_expression(expr.right, prec, "right", indent_level)
            text = f"{left} {symbol} {right}"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrAssignment):
            prec, assoc = 1, "right"
            target = self._emit_expression(expr.target, prec, "left", indent_level)
            value = self._emit_expression(expr.value, prec, "right", indent_level)
            text = f"{target} = {value}"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrConditional):
            prec, assoc = 2, "right"
            condition = self._emit_expression(expr.condition, prec, "left", indent_level)
            consequent = self._emit_expression(expr.consequent, prec, "right", indent_level)
            alternate = self._emit_expression(expr.alternate, prec, "right", indent_level)
            text = f"{condition} ? {consequent} : {alternate}"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrCall):
            prec, assoc = 14, "left"
            callee = self._emit_expression(expr.callee, prec, "left", indent_level)
            arguments = ", ".join(self._emit_expression(arg, 0, "any", indent_level) for arg in expr.arguments)
            text = f"{callee}({arguments})"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrMemberAccess):
            prec, assoc = 15, "left"
            obj = self._emit_expression(expr.object, prec, "left", indent_level)
            text = f"{obj}.{expr.property}"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrIndex):
            prec, assoc = 15, "left"
            collection = self._emit_expression(expr.collection, prec, "left", indent_level)
            index = self._emit_expression(expr.index, 0, "any", indent_level)
            text = f"{collection}[{index}]"
            return self._maybe_parenthesize(text, prec, parent_prec, assoc, position)

        if isinstance(expr, IrArrayLiteral):
            elements = ", ".join(self._emit_expression(elem, 0, "any", indent_level) for elem in expr.elements)
            return f"[{elements}]"

        if isinstance(expr, IrObjectLiteral):
            props = ", ".join(self._format_object_property(prop, indent_level) for prop in expr.properties)
            return f"structura {{ {props} }}"

        if isinstance(expr, IrLambda):
            params = ", ".join(self._format_parameter(param) for param in expr.parameters)
            if expr.body_expression is not None:
                body = self._emit_expression(expr.body_expression, 0, "any", indent_level)
                text = f"functio ({params}) => {body}"
                return self._maybe_parenthesize(text, 3, parent_prec, "right", position)

            statements = self._emit_statements(expr.body_statements, indent_level + 1)
            if statements:
                body = "\n".join(statements)
                closing = self._INDENT * indent_level + "}"
                opening = f"functio ({params}) {{"
                text = "\n".join([self._INDENT * indent_level + opening] + statements + [closing])
            else:
                opening = f"functio ({params}) {{"
                closing = self._INDENT * indent_level + "}"
                text = "\n".join([self._INDENT * indent_level + opening, closing])
            return text

        raise TypeError(f"Unsupported expression type: {type(expr)!r}")

    def _format_object_property(self, prop: IrObjectProperty, indent_level: int) -> str:
        value = self._emit_expression(prop.value, 0, "any", indent_level)
        return f"{prop.key}: {value}"

    # Operator metadata ------------------------------------------------------

    def _binary_metadata(self, operator: str) -> Tuple[str, int, str]:
        mapping = {
            "ADD": ("+", 8, "left"),
            "SUB": ("-", 8, "left"),
            "MUL": ("*", 9, "left"),
            "DIV": ("/", 9, "left"),
            "MOD": ("%", 9, "left"),
            "POW": ("**", 10, "right"),
            "OR": ("||", 4, "left"),
            "AND": ("&&", 5, "left"),
            "NULLISH": ("??", 3, "left"),
            "EQ": ("==", 6, "left"),
            "NE": ("!=", 6, "left"),
            "STRICT_EQ": ("===", 6, "left"),
            "STRICT_NE": ("!==", 6, "left"),
            "GT": (">", 7, "left"),
            "GE": (">=", 7, "left"),
            "LT": ("<", 7, "left"),
            "LE": ("<=", 7, "left"),
        }
        if operator in mapping:
            return mapping[operator]
        # Fallback for literal operators such as "??" that may already be present.
        symbol = operator
        precedence = {
            "??": 3,
            "||": 4,
            "&&": 5,
            "==": 6,
            "!=": 6,
            "===": 6,
            "!==": 6,
            ">": 7,
            ">=": 7,
            "<": 7,
            "<=": 7,
            "+": 8,
            "-": 8,
            "*": 9,
            "/": 9,
            "%": 9,
            "**": 10,
        }.get(symbol, 8)
        assoc = "right" if symbol == "**" else "left"
        return symbol, precedence, assoc

    def _unary_symbol(self, operator: str) -> str:
        mapping = {
            "NEGATE": "-",
            "POSITIVE": "+",
            "NOT": "!",
        }
        return mapping.get(operator, operator)

    def _precedence_unary(self) -> int:
        return 11

    def _maybe_parenthesize(self, text: str, prec: int, parent_prec: int, assoc: str, position: str) -> str:
        need = False
        if prec < parent_prec:
            need = True
        elif prec == parent_prec:
            if assoc == "left" and position == "right":
                need = True
            elif assoc == "right" and position == "left":
                need = True
        return f"({text})" if need else text
