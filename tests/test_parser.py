from __future__ import annotations

import pytest

from ll1calc.lexer import LexerError
from ll1calc.parser import LL1Parser, ParseError, ParseTreeNode


def _evaluate(tree: ParseTreeNode) -> int:
    def eval_e(node: ParseTreeNode) -> int:
        left = eval_t(node.children[0])
        return eval_e_prime(node.children[1], left)

    def eval_e_prime(node: ParseTreeNode, acc: int) -> int:
        head = node.children[0]
        if head.symbol == "ε":
            return acc
        op = head.token.lexeme
        right = eval_t(node.children[1])
        updated = acc + right if op == "+" else acc - right
        return eval_e_prime(node.children[2], updated)

    def eval_t(node: ParseTreeNode) -> int:
        left = eval_f(node.children[0])
        return eval_t_prime(node.children[1], left)

    def eval_t_prime(node: ParseTreeNode, acc: int) -> int:
        head = node.children[0]
        if head.symbol == "ε":
            return acc
        op = head.token.lexeme
        right = eval_f(node.children[1])
        updated = acc * right if op == "*" else acc // right
        return eval_t_prime(node.children[2], updated)

    def eval_f(node: ParseTreeNode) -> int:
        child = node.children[0]
        if child.symbol == "(":
            return eval_e(node.children[1])
        return int(child.token.lexeme)

    return eval_e(tree)


def test_literal_number() -> None:
    parser = LL1Parser()
    result = parser.parse("42")
    assert _evaluate(result.tree) == 42
    assert result.derivations[0] == "E -> T E'"
    assert result.derivations[-1] == "ACCEPT"


def test_precedence_and_derivations() -> None:
    parser = LL1Parser()
    result = parser.parse("1+2*3")
    assert _evaluate(result.tree) == 7
    assert any(step.startswith("T' -> * F") for step in result.derivations)


def test_parentheses_and_subtraction() -> None:
    parser = LL1Parser()
    result = parser.parse("(1+2)*3-4/2")
    assert _evaluate(result.tree) == 7
    assert any("E' -> - T" in step for step in result.derivations)


def test_nested_parentheses() -> None:
    parser = LL1Parser()
    result = parser.parse("((2))")
    assert _evaluate(result.tree) == 2


def test_invalid_character_raises() -> None:
    parser = LL1Parser()
    with pytest.raises(LexerError):
        parser.parse("1+a")


def test_trailing_operator_errors() -> None:
    parser = LL1Parser()
    with pytest.raises(ParseError):
        parser.parse("1+")
