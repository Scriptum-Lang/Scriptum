from __future__ import annotations

from scriptum.ast import nodes
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile


def _parse_expression_snippet(snippet: str) -> nodes.Expression:
    parser = ScriptumParser()
    source = SourceFile("<test>", f"mutabilis numerus tmp = {snippet};")
    module = parser.parse(source)
    declaration = module.declarations[0]
    assert isinstance(declaration, nodes.VariableDeclaration)
    assert declaration.initializer is not None
    return declaration.initializer


def test_exponentiation_is_right_associative() -> None:
    expr = _parse_expression_snippet("a ** b ** c")
    assert isinstance(expr, nodes.BinaryExpression)
    assert expr.operator is nodes.BinaryOperator.POW
    assert isinstance(expr.right, nodes.BinaryExpression)
    assert expr.right.operator is nodes.BinaryOperator.POW


def test_assignment_is_right_associative() -> None:
    expr = _parse_expression_snippet("a = b = c")
    assert isinstance(expr, nodes.AssignmentExpression)
    assert isinstance(expr.value, nodes.AssignmentExpression)
    assert isinstance(expr.value.value, nodes.Identifier)


def test_nullish_precedes_ternary() -> None:
    expr = _parse_expression_snippet("a ?? b ? c : d")
    assert isinstance(expr, nodes.ConditionalExpression)
    assert isinstance(expr.condition, nodes.BinaryExpression)
    assert expr.condition.operator is nodes.BinaryOperator.NULLISH


def test_ternary_allows_assignment_in_alternate() -> None:
    expr = _parse_expression_snippet("a ? b : c = d")
    assert isinstance(expr, nodes.ConditionalExpression)
    assert isinstance(expr.alternate, nodes.AssignmentExpression)
    assert isinstance(expr.alternate.value, nodes.Identifier)


def test_nullish_ternary_assignment_chain() -> None:
    expr = _parse_expression_snippet("a ?? b ? c : d = e")
    assert isinstance(expr, nodes.ConditionalExpression)
    assert isinstance(expr.alternate, nodes.AssignmentExpression)
    assert isinstance(expr.condition, nodes.BinaryExpression)
    assert expr.condition.operator is nodes.BinaryOperator.NULLISH


def test_nested_ternary_is_right_associative() -> None:
    expr = _parse_expression_snippet("a ? b : c ? d : e")
    assert isinstance(expr, nodes.ConditionalExpression)
    assert isinstance(expr.alternate, nodes.ConditionalExpression)
    inner = expr.alternate
    assert isinstance(inner.alternate, nodes.Identifier)
