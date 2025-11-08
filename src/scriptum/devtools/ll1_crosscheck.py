from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from ll1calc.first_follow import EPSILON
from ll1calc.lexer import LexerError
from ll1calc.parser import LL1Parser, ParseError as LL1ParseError, ParseTreeNode

from ..ast import nodes
from ..parser.parser import ParseError as ScriptumParseError, ParserTrace, ParserTraceNode, ScriptumParser
from ..text import SourceFile, Span

BinarySymbol = str
CanonicalExpr = tuple[str, str] | tuple[str, str, "CanonicalExpr", "CanonicalExpr"]

DEFAULT_EXPRESSIONS: list[str] = [
    "42",
    "1+2*3",
    "1+2+3",
    "4-2-1",
    "6/3/2",
    "(1+2)*3-4/2",
    "((2))",
    "7*(3+(2-1))",
    "(8/4)*(1+3)",
]

__all__ = ["ComparisonReport", "compare_expression", "run", "main"]

_BINARY_OPERATOR_SYMBOLS: dict[nodes.BinaryOperator, BinarySymbol] = {
    nodes.BinaryOperator.ADD: "+",
    nodes.BinaryOperator.SUB: "-",
    nodes.BinaryOperator.MUL: "*",
    nodes.BinaryOperator.DIV: "/",
}

_OPERATOR_SPACING_RE = re.compile(r"([()+\-*/])")


@dataclass(slots=True)
class ComparisonReport:
    expression: str
    success: bool
    message: str | None = None
    ll1_tree: ParseTreeNode | None = None
    scriptum_expr: nodes.Expression | None = None
    scriptum_trace: ParserTraceNode | None = None
    scriptum_trace_log: list[str] | None = None
    ll1_normalized: CanonicalExpr | None = None
    scriptum_normalized: CanonicalExpr | None = None
    derivations: list[str] | None = None


def compare_expression(expression: str) -> ComparisonReport:
    """Run both parsers, canonicalise their ASTs and compare results."""

    report = ComparisonReport(expression=expression, success=False)

    ll1_parser = LL1Parser()
    try:
        ll1_result = ll1_parser.parse(expression)
    except (LexerError, LL1ParseError) as exc:
        report.message = f"LL(1) parser error: {exc}"
        return report

    report.ll1_tree = ll1_result.tree
    report.derivations = ll1_result.derivations

    try:
        scriptum_expr, trace_node, trace_log = _parse_with_scriptum(expression)
    except (ScriptumParseError, ValueError) as exc:
        report.message = f"Scriptum parser error: {exc}"
        return report

    report.scriptum_expr = scriptum_expr
    report.scriptum_trace = trace_node
    report.scriptum_trace_log = trace_log
    report.ll1_normalized = _canonicalise_ll1(ll1_result.tree)
    report.scriptum_normalized = _canonicalise_scriptum(scriptum_expr)
    report.success = report.ll1_normalized == report.scriptum_normalized
    if not report.success:
        report.message = "Normalized ASTs differ."
    return report


def _parse_with_scriptum(expression: str) -> tuple[nodes.Expression, ParserTraceNode | None, list[str]]:
    parser = ScriptumParser()
    trace = ParserTrace()
    normalized = _normalise_expression_spacing(expression)
    source = SourceFile("<ll1-crosscheck>", f"mutabilis numerus tmp = {normalized};")
    module = parser.parse(source, trace=trace)
    if not module.declarations:
        raise ValueError("No declarations produced.")
    declaration = module.declarations[0]
    if not isinstance(declaration, nodes.VariableDeclaration):
        raise ValueError("Unexpected declaration kind.")
    if declaration.initializer is None:
        raise ValueError("Declaration missing initializer.")
    trace_node = _match_trace_node(trace, declaration.initializer.span)
    return declaration.initializer, trace_node, trace.productions.copy()


def _match_trace_node(trace: ParserTrace, span: Span) -> ParserTraceNode | None:
    for node in trace.expression_trees:
        if node.span.start == span.start and node.span.end == span.end:
            return node
    if trace.expression_trees:
        return trace.expression_trees[-1]
    return None


def _canonicalise_ll1(node: ParseTreeNode) -> CanonicalExpr:
    if node.symbol != "E":
        raise ValueError("LL(1) tree must start at 'E'.")
    return _canonicalise_E(node)


def _canonicalise_E(node: ParseTreeNode) -> CanonicalExpr:
    left = _canonicalise_T(node.children[0])
    return _canonicalise_E_prime(node.children[1], left)


def _canonicalise_E_prime(node: ParseTreeNode, acc: CanonicalExpr) -> CanonicalExpr:
    head = node.children[0]
    if head.symbol == EPSILON:
        return acc
    operator_node = head
    if operator_node.token is None:
        raise ValueError("Terminal node missing token.")
    right = _canonicalise_T(node.children[1])
    combined: CanonicalExpr = ("bin", operator_node.token.lexeme, acc, right)
    return _canonicalise_E_prime(node.children[2], combined)


def _canonicalise_T(node: ParseTreeNode) -> CanonicalExpr:
    left = _canonicalise_F(node.children[0])
    return _canonicalise_T_prime(node.children[1], left)


def _canonicalise_T_prime(node: ParseTreeNode, acc: CanonicalExpr) -> CanonicalExpr:
    head = node.children[0]
    if head.symbol == EPSILON:
        return acc
    operator_node = head
    if operator_node.token is None:
        raise ValueError("Terminal node missing token.")
    right = _canonicalise_F(node.children[1])
    combined: CanonicalExpr = ("bin", operator_node.token.lexeme, acc, right)
    return _canonicalise_T_prime(node.children[2], combined)


def _canonicalise_F(node: ParseTreeNode) -> CanonicalExpr:
    child = node.children[0]
    if child.symbol == "(":
        # Production: ( E )
        return _canonicalise_E(node.children[1])
    if child.symbol == "num":
        if child.token is None:
            raise ValueError("Number node missing token.")
        return ("num", child.token.lexeme)
    raise ValueError(f"Unexpected symbol inside F: {child.symbol}")


def _canonicalise_scriptum(expr: nodes.Expression) -> CanonicalExpr:
    if isinstance(expr, nodes.Literal):
        return ("num", str(expr.raw))
    if isinstance(expr, nodes.BinaryExpression):
        operator = expr.operator
        symbol = _BINARY_OPERATOR_SYMBOLS.get(operator)
        if symbol is None:
            if isinstance(operator, str) and operator in {"+", "-", "*", "/"}:
                symbol = operator
            else:
                raise ValueError(f"Unsupported binary operator {operator!r}.")
        left = _canonicalise_scriptum(expr.left)
        right = _canonicalise_scriptum(expr.right)
        return ("bin", symbol, left, right)
    raise ValueError(f"Unsupported Scriptum AST node: {type(expr).__name__}")


def _normalise_expression_spacing(expression: str) -> str:
    separated = _OPERATOR_SPACING_RE.sub(r" \1 ", expression)
    collapsed = " ".join(separated.split())
    return collapsed


def _format_canonical(expr: CanonicalExpr | None) -> str:
    if expr is None:
        return "<unavailable>"
    kind = expr[0]
    if kind == "num":
        return expr[1]
    if kind == "bin":
        _, op, left, right = expr
        return f"({_format_canonical(left)} {op} {_format_canonical(right)})"
    return repr(expr)


def run(expressions: Sequence[str]) -> list[ComparisonReport]:
    return [compare_expression(expr) for expr in expressions]


def _read_expressions(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf8").splitlines() if line.strip()]


def _collect_expressions(args: argparse.Namespace) -> list[str]:
    expressions: list[str] = []
    if args.file is not None:
        expressions.extend(_read_expressions(Path(args.file)))
    expressions.extend(expr for expr in args.expressions if expr.strip())
    if not expressions:
        expressions = DEFAULT_EXPRESSIONS.copy()
    return expressions


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Cross-check Scriptum's Pratt parser against the didactic LL(1) parser "
            "for arithmetic expressions involving + - * /."
        )
    )
    parser.add_argument("expressions", nargs="*", help="Inline expressions to compare.")
    parser.add_argument(
        "-f",
        "--file",
        help="Path to a file containing one expression per line to compare.",
    )
    parser.add_argument(
        "--show-derivations",
        action="store_true",
        help="Print LL(1) derivation steps when a mismatch occurs.",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop after the first mismatch.",
    )
    args = parser.parse_args(argv)

    expressions = _collect_expressions(args)
    reports: list[ComparisonReport] = []
    success_count = 0

    for expression in expressions:
        report = compare_expression(expression)
        reports.append(report)

        status = "OK" if report.success else "FAIL"
        print(f"[{status}] {report.expression}")
        if report.success:
            success_count += 1
            continue

        if report.message:
            print(f"  -> {report.message}")
        if report.ll1_tree is not None:
            print("  LL(1) parse tree:")
            print(report.ll1_tree.pretty(indent=4))
        if args.show_derivations and report.derivations:
            print("  LL(1) derivations:")
            for step in report.derivations:
                print(f"    {step}")
        if report.ll1_normalized is not None:
            print(f"  LL(1) canonical: {_format_canonical(report.ll1_normalized)}")
        if report.scriptum_normalized is not None:
            print(f"  Scriptum canonical: {_format_canonical(report.scriptum_normalized)}")
        if report.scriptum_trace is not None:
            print("  Scriptum trace tree:")
            print(report.scriptum_trace.pretty(indent=4))
        if report.scriptum_trace_log:
            print("  Scriptum trace log:")
            for entry in report.scriptum_trace_log:
                print(f"    {entry}")

        if args.stop_on_failure:
            break

    total = len(reports)
    print(f"{success_count}/{total} expressions matched.")
    return 0 if success_count == total else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
