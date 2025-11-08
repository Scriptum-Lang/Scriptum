"""Recursive-descent + Pratt parser for Scriptum."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ll1calc.first_follow import EPSILON as LL1_EPSILON
from ll1calc.lexer import LexerError as LL1LexerError
from ll1calc.parser import LL1Parser, ParseError as LL1ParseError, ParseTreeNode as LL1ParseTreeNode

from .. import errors, text, tokens
from ..ast import nodes
from ..lexer.lexer import ScriptumLexer
from ..text import Span
from .precedence import binding_powers


TYPE_KEYWORDS = {
    "numerus",
    "textus",
    "booleanum",
    "vacuum",
    "quodlibet",
    "nullum",
    "indefinitum",
    "functio",
    "structura",
}


class ParseError(errors.CompilerError):
    """Raised when a syntactic error is encountered."""


@dataclass(slots=True)
class ParserConfig:
    allow_lambda_shortcut: bool = True
    max_depth: int = 2048


@dataclass(slots=True)
class ParserTraceNode:
    """Lightweight tree node used for parser instrumentation."""

    label: str
    span: Span
    lexeme: str | None = None
    children: List["ParserTraceNode"] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        label = self.label
        if self.lexeme:
            label += f" [{self.lexeme}]"
        lines = [" " * indent + label]
        for child in self.children:
            lines.append(child.pretty(indent + 2))
        return "\n".join(lines)


@dataclass(slots=True)
class ParserTrace:
    """Holds optional instrumentation results for ScriptumParser."""

    expression_trees: List[ParserTraceNode] = field(default_factory=list)
    productions: List[str] = field(default_factory=list)

    def add_expression(self, node: ParserTraceNode) -> None:
        self.expression_trees.append(node)

    def log(self, entry: str) -> None:
        self.productions.append(entry)


@dataclass(slots=True)
class _LL1Trace:
    tree: LL1ParseTreeNode
    derivations: List[str]


_LL1_ALLOWED_RE = re.compile(r"^[0-9+\-*/()\s]+$")


class ScriptumParser:
    """Parses Scriptum source code into an AST module."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()
        self._lexer = ScriptumLexer()
        self._tokens: List[tokens.Token] = []
        self._index: int = 0
        self._node_counter: int = 0
        self._source: Optional[text.SourceFile] = None
        self._depth: int = 0
        self._expr_call_depth: int = 0
        self._trace: ParserTrace | None = None
        self._ll1_traces: Dict[int, _LL1Trace] = {}
        self._ll1_parser: LL1Parser | None = None

    # Public API -----------------------------------------------------------------

    def parse(self, source: text.SourceFile, trace: ParserTrace | None = None) -> nodes.Module:
        self._source = source
        self._tokens = self._lexer.tokenize(source)
        self._index = 0
        self._node_counter = 0
        self._expr_call_depth = 0
        self._trace = trace
        self._ll1_traces = {}
        declarations: List[nodes.Declaration] = []
        try:
            while not self._is_at_end():
                declarations.append(self._parse_declaration(global_scope=True))
            module_span = Span(0, len(source.text))
            return nodes.Module(node_id=self._next_id(), span=module_span, declarations=declarations)
        finally:
            self._trace = None

    # Declaration parsing --------------------------------------------------------

    def _parse_declaration(self, global_scope: bool) -> nodes.Declaration:
        if self._check_keyword("functio"):
            return self._parse_function_declaration()
        if self._check_keyword("mutabilis") or self._check_keyword("constans"):
            return self._parse_variable_declaration(global_scope=global_scope)
        stmt = self._parse_statement()
        if isinstance(stmt, nodes.Declaration):
            return stmt
        raise ParseError("Unexpected top-level statement.")

    def _parse_function_declaration(self) -> nodes.FunctionDeclaration:
        start = self._consume_keyword("functio")
        name_token = self._consume(tokens.TokenKind.IDENTIFIER, "Expected function name.")

        self._consume_symbol("(", "Expected '(' after function name.")
        parameters = self._parse_parameters()
        self._consume_symbol(")", "Expected ')' after parameter list.")

        return_type = None
        if self._match_symbol("->"):
            return_type = self._parse_type_annotation()

        body = self._parse_block_statement()
        span = self._combine_spans(start.span, body.span)
        return nodes.FunctionDeclaration(
            node_id=self._next_id(),
            span=span,
            name=name_token.lexeme,
            parameters=parameters,
            return_type=return_type,
            body=body,
        )

    def _parse_variable_declaration(self, global_scope: bool) -> nodes.VariableDeclaration:
        keyword = self._advance()
        mutable = keyword.lexeme == "mutabilis"
        name_token, type_annotation, _ = self._parse_binding(
            allow_type_prefix=True,
            message="Expected identifier for variable declaration.",
        )

        initializer = None
        if self._match_symbol("="):
            initializer = self._parse_expression()

        semicolon = self._consume_symbol(";", "Expected ';' after variable declaration.")
        span = self._combine_spans(keyword.span, semicolon.span)
        return nodes.VariableDeclaration(
            node_id=self._next_id(),
            span=span,
            mutable=mutable,
            name=name_token.lexeme,
            type_annotation=type_annotation,
            initializer=initializer,
            is_global=global_scope,
        )

    def _parse_parameters(self) -> List[nodes.Parameter]:
        parameters: List[nodes.Parameter] = []
        if self._check_symbol(")"):
            return parameters
        while True:
            name_token, type_annotation, binding_span = self._parse_binding(
                allow_type_prefix=True,
                message="Expected parameter name.",
            )
            parameter_span = binding_span
            default_value = None
            if self._match_symbol("="):
                default_value = self._parse_expression()
                parameter_span = self._combine_spans(binding_span, default_value.span)
            parameters.append(
                nodes.Parameter(
                    node_id=self._next_id(),
                    span=parameter_span,
                    name=name_token.lexeme,
                    type_annotation=type_annotation,
                    default_value=default_value,
                )
            )
            if not self._match_symbol(","):
                break
        return parameters

    # Statement parsing ----------------------------------------------------------

    def _parse_statement(self) -> nodes.Statement:
        if self._match_symbol("{"):
            return self._parse_block_statement(already_open=True)
        if self._check_keyword("mutabilis") or self._check_keyword("constans"):
            return self._parse_variable_declaration(global_scope=False)
        if self._match_keyword("si"):
            return self._parse_if_statement()
        if self._match_keyword("dum"):
            return self._parse_while_statement()
        if self._match_keyword("pro"):
            return self._parse_for_statement()
        if self._match_keyword("redde"):
            return self._parse_return_statement()
        if self._match_keyword("frange"):
            keyword = self._previous()
            semicolon = self._consume_symbol(";", "Expected ';' after 'frange'.")
            return nodes.BreakStatement(
                node_id=self._next_id(),
                span=self._combine_spans(keyword.span, semicolon.span),
            )
        if self._match_keyword("perge"):
            keyword = self._previous()
            semicolon = self._consume_symbol(";", "Expected ';' after 'perge'.")
            return nodes.ContinueStatement(
                node_id=self._next_id(),
                span=self._combine_spans(keyword.span, semicolon.span),
            )
        return self._parse_expression_statement()

    def _parse_block_statement(self, already_open: bool = False) -> nodes.BlockStatement:
        if not already_open:
            open_token = self._consume_symbol("{", "Expected '{'.")
        else:
            open_token = self._previous()
        statements: List[nodes.Statement] = []
        while not self._check_symbol("}") and not self._is_at_end():
            statements.append(self._parse_statement())
        close_token = self._consume_symbol("}", "Expected '}' to close block.")
        span = self._combine_spans(open_token.span, close_token.span)
        return nodes.BlockStatement(node_id=self._next_id(), span=span, statements=statements)

    def _parse_expression_statement(self) -> nodes.ExpressionStatement:
        expression = self._parse_expression()
        semicolon = self._consume_symbol(";", "Expected ';' after expression.")
        span = self._combine_spans(expression.span, semicolon.span)
        return nodes.ExpressionStatement(node_id=self._next_id(), span=span, expression=expression)

    def _parse_if_statement(self) -> nodes.IfStatement:
        keyword = self._previous()
        condition = self._parse_expression()
        then_branch = self._parse_statement()
        else_branch = None
        if self._match_keyword("aliter"):
            else_branch = self._parse_statement()
        end_span = else_branch.span if else_branch else then_branch.span
        return nodes.IfStatement(
            node_id=self._next_id(),
            span=self._combine_spans(keyword.span, end_span),
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_while_statement(self) -> nodes.WhileStatement:
        keyword = self._previous()
        condition = self._parse_expression()
        body = self._parse_statement()
        return nodes.WhileStatement(
            node_id=self._next_id(),
            span=self._combine_spans(keyword.span, body.span),
            condition=condition,
            body=body,
        )

    def _parse_for_statement(self) -> nodes.ForStatement:
        keyword_token = self._previous()
        using_parentheses = self._match_symbol("(")

        mutable = False
        binding_keyword: Optional[tokens.Token] = None
        if self._check_keyword("mutabilis") or self._check_keyword("constans"):
            binding_keyword = self._advance()
            mutable = binding_keyword.lexeme == "mutabilis"

        name_token, type_annotation, binding_span = self._parse_binding(
            allow_type_prefix=True,
            message="Expected loop variable identifier.",
        )

        self._consume_keyword("in")
        iterable = self._parse_expression()
        if using_parentheses:
            self._consume_symbol(")", "Expected ')' after for binding.")
        body = self._parse_statement()

        target_span = self._combine_spans(binding_keyword.span, binding_span) if binding_keyword else binding_span
        target = nodes.ForTarget(
            node_id=self._next_id(),
            span=target_span,
            name=name_token.lexeme,
            mutable=mutable,
            type_annotation=type_annotation,
        )

        loop_span = self._combine_spans(keyword_token.span, body.span)
        return nodes.ForStatement(
            node_id=self._next_id(),
            span=loop_span,
            target=target,
            iterable=iterable,
            body=body,
        )

    def _parse_return_statement(self) -> nodes.ReturnStatement:
        keyword = self._previous()
        if self._check_symbol(";"):
            semicolon = self._advance()
            span = self._combine_spans(keyword.span, semicolon.span)
            return nodes.ReturnStatement(node_id=self._next_id(), span=span, value=None)
        value = self._parse_expression()
        semicolon = self._consume_symbol(";", "Expected ';' after return value.")
        span = self._combine_spans(keyword.span, semicolon.span)
        return nodes.ReturnStatement(node_id=self._next_id(), span=span, value=value)

    # Expression parsing ---------------------------------------------------------

    def _enter_depth(self) -> None:
        self._depth += 1
        if self._depth > self.config.max_depth:
            token = self._peek()
            raise ParseError(
                f"Parser depth limit exceeded ({self.config.max_depth}). "
                f"Last token: {token.lexeme!r} at {token.span}."
            )

    def _leave_depth(self) -> None:
        self._depth = max(0, self._depth - 1)

    def _parse_expression(self, min_bp: int = 0) -> nodes.Expression:
        self._enter_depth()
        self._expr_call_depth += 1
        try:
            expr = self._parse_prefix()

            while True:
                if self._is_at_end():
                    break

                if self._match_symbol("("):
                    expr = self._finish_call(expr)
                    if self._trace is not None:
                        self._trace.log(f"CALL {expr.span.start}:{expr.span.end}")
                    continue
                if self._match_symbol("["):
                    expr = self._finish_index(expr)
                    if self._trace is not None:
                        self._trace.log(f"INDEX {expr.span.start}:{expr.span.end}")
                    continue
                if self._match_symbol("."):
                    expr = self._finish_member(expr)
                    if self._trace is not None:
                        self._trace.log(f"MEMBER {expr.span.start}:{expr.span.end}")
                    continue

                token = self._peek()
                binding = binding_powers(token.lexeme)
                if binding is None or binding[0] < min_bp:
                    break

                operator_token = self._advance()
                if operator_token.lexeme == "?":
                    true_expr = self._parse_expression()
                    self._consume_symbol(":", "Expected ':' in conditional expression.")
                    # Allow lower-precedence operators (e.g. assignment) inside the alternate branch.
                    false_min_bp = binding[1] - 1 if binding[1] > 0 else 0
                    false_expr = self._parse_expression(false_min_bp)
                    expr = nodes.ConditionalExpression(
                        node_id=self._next_id(),
                        span=self._combine_spans(expr.span, false_expr.span),
                        condition=expr,
                        consequent=true_expr,
                        alternate=false_expr,
                    )
                    if self._trace is not None:
                        self._trace.log(f"TERNARY {expr.span.start}:{expr.span.end}")
                    continue

                right = self._parse_expression(binding[1])
                span = self._combine_spans(expr.span, right.span)
                if operator_token.lexeme == "=":
                    expr = nodes.AssignmentExpression(
                        node_id=self._next_id(),
                        span=span,
                        target=expr,
                        value=right,
                    )
                    if self._trace is not None:
                        self._trace.log(f"ASSIGN {span.start}:{span.end}")
                else:
                    expr = nodes.BinaryExpression(
                        node_id=self._next_id(),
                        span=span,
                        operator=self._binary_operator(operator_token.lexeme),
                        left=expr,
                        right=right,
                    )
                    if self._trace is not None:
                        self._trace.log(f"BINARY {operator_token.lexeme} {span.start}:{span.end}")

            expr = self._maybe_delegate_to_ll1(expr, min_bp)
            if self._trace is not None and self._expr_call_depth == 1:
                self._record_expression_trace(expr)
            return expr
        finally:
            self._expr_call_depth = max(0, self._expr_call_depth - 1)
            self._leave_depth()

    def _record_expression_trace(self, expr: nodes.Expression) -> None:
        if self._trace is None:
            return
        node = self._expression_to_trace(expr)
        self._trace.add_expression(node)
        ll1_info = self._ll1_traces.get(expr.node_id)
        if ll1_info:
            self._trace.productions.extend(ll1_info.derivations)
        else:
            self._trace.log(f"EXPR {type(expr).__name__} {expr.span.start}:{expr.span.end}")

    def _expression_to_trace(self, expr: nodes.Expression) -> ParserTraceNode:
        label = type(expr).__name__
        lexeme: str | None = None
        children: List[ParserTraceNode] = []

        if isinstance(expr, nodes.Literal):
            lexeme = expr.raw
        elif isinstance(expr, nodes.Identifier):
            lexeme = expr.name
        elif isinstance(expr, nodes.BinaryExpression):
            lexeme = self._binary_symbol(expr.operator) or str(expr.operator)
            children = [self._expression_to_trace(expr.left), self._expression_to_trace(expr.right)]
        elif isinstance(expr, nodes.AssignmentExpression):
            lexeme = "="
            children = [self._expression_to_trace(expr.target), self._expression_to_trace(expr.value)]
        elif isinstance(expr, nodes.ConditionalExpression):
            lexeme = "?:"
            children = [
                self._expression_to_trace(expr.condition),
                self._expression_to_trace(expr.consequent),
                self._expression_to_trace(expr.alternate),
            ]
        elif isinstance(expr, nodes.CallExpression):
            children = [self._expression_to_trace(expr.callee)] + [
                self._expression_to_trace(argument) for argument in expr.arguments
            ]
        elif isinstance(expr, nodes.MemberExpression):
            lexeme = expr.property
            children = [self._expression_to_trace(expr.object)]
        elif isinstance(expr, nodes.IndexExpression):
            children = [self._expression_to_trace(expr.collection), self._expression_to_trace(expr.index)]
        elif isinstance(expr, nodes.UnaryExpression):
            lexeme = expr.operator.name if isinstance(expr.operator, nodes.UnaryOperator) else str(expr.operator)
            children = [self._expression_to_trace(expr.operand)]
        elif isinstance(expr, nodes.ArrayLiteral):
            children = [self._expression_to_trace(element) for element in expr.elements]
        elif isinstance(expr, nodes.ObjectLiteral):
            for prop in expr.properties:
                prop_node = ParserTraceNode(
                    label="ObjectProperty",
                    span=prop.span,
                    lexeme=prop.key,
                    children=[self._expression_to_trace(prop.value)],
                )
                children.append(prop_node)
        return ParserTraceNode(label=label, span=expr.span, lexeme=lexeme, children=children)

    def _maybe_delegate_to_ll1(self, expr: nodes.Expression, min_bp: int) -> nodes.Expression:
        if self._source is None or not self._is_pure_arithmetic(expr):
            return expr
        snippet = self._source.slice(expr.span)
        if not snippet or not _LL1_ALLOWED_RE.fullmatch(snippet):
            return expr
        if self._ll1_parser is None:
            self._ll1_parser = LL1Parser()
        try:
            result = self._ll1_parser.parse(snippet)
            rebuilt = self._ll1_tree_to_ast(result.tree, expr.span.start)
        except (LL1LexerError, LL1ParseError, ParseError):
            return expr
        self._ll1_traces[rebuilt.node_id] = _LL1Trace(tree=result.tree, derivations=result.derivations)
        return rebuilt

    def _is_pure_arithmetic(self, expr: nodes.Expression) -> bool:
        if isinstance(expr, nodes.BinaryExpression):
            symbol = self._binary_symbol(expr.operator)
            if symbol not in {"+", "-", "*", "/"}:
                return False
            return self._is_pure_arithmetic(expr.left) and self._is_pure_arithmetic(expr.right)
        if isinstance(expr, nodes.Literal):
            if isinstance(expr.value, int) and expr.raw.isdigit():
                return True
            return False
        return False

    def _ll1_tree_to_ast(self, node: LL1ParseTreeNode, offset: int) -> nodes.Expression:
        if node.symbol != "E":
            raise ParseError("LL(1) tree root must be 'E'.")

        def build_e(current: LL1ParseTreeNode) -> nodes.Expression:
            left = build_t(current.children[0])
            return build_e_prime(current.children[1], left)

        def build_e_prime(current: LL1ParseTreeNode, acc: nodes.Expression) -> nodes.Expression:
            head = current.children[0]
            if head.symbol == LL1_EPSILON:
                return acc
            operator_node = head
            if operator_node.token is None:
                raise ParseError("Missing operator token in LL(1) tree.")
            right = build_t(current.children[1])
            combined = self._make_binary_node(operator_node.token.lexeme, acc, right)
            return build_e_prime(current.children[2], combined)

        def build_t(current: LL1ParseTreeNode) -> nodes.Expression:
            left = build_f(current.children[0])
            return build_t_prime(current.children[1], left)

        def build_t_prime(current: LL1ParseTreeNode, acc: nodes.Expression) -> nodes.Expression:
            head = current.children[0]
            if head.symbol == LL1_EPSILON:
                return acc
            operator_node = head
            if operator_node.token is None:
                raise ParseError("Missing operator token in LL(1) tree.")
            right = build_f(current.children[1])
            combined = self._make_binary_node(operator_node.token.lexeme, acc, right)
            return build_t_prime(current.children[2], combined)

        def build_f(current: LL1ParseTreeNode) -> nodes.Expression:
            child = current.children[0]
            if child.symbol == "(":
                return build_e(current.children[1])
            if child.symbol == "num":
                if child.token is None:
                    raise ParseError("Number node missing token.")
                start = offset + child.token.position
                end = start + len(child.token.lexeme)
                span = Span(start, end)
                value = int(child.token.lexeme)
                return nodes.Literal(node_id=self._next_id(), span=span, value=value, raw=child.token.lexeme)
            raise ParseError(f"Unexpected symbol {child.symbol!r} in LL(1) tree.")

        return build_e(node)

    def _make_binary_node(self, operator_symbol: str, left: nodes.Expression, right: nodes.Expression) -> nodes.BinaryExpression:
        span = self._combine_spans(left.span, right.span)
        return nodes.BinaryExpression(
            node_id=self._next_id(),
            span=span,
            operator=self._binary_operator(operator_symbol),
            left=left,
            right=right,
        )

    def _binary_symbol(self, operator: nodes.BinaryOperator | str) -> str | None:
        if isinstance(operator, nodes.BinaryOperator):
            mapping = {
                nodes.BinaryOperator.ADD: "+",
                nodes.BinaryOperator.SUB: "-",
                nodes.BinaryOperator.MUL: "*",
                nodes.BinaryOperator.DIV: "/",
                nodes.BinaryOperator.MOD: "%",
                nodes.BinaryOperator.POW: "**",
                nodes.BinaryOperator.GT: ">",
                nodes.BinaryOperator.LT: "<",
                nodes.BinaryOperator.GE: ">=",
                nodes.BinaryOperator.LE: "<=",
                nodes.BinaryOperator.EQ: "==",
                nodes.BinaryOperator.NE: "!=",
                nodes.BinaryOperator.STRICT_EQ: "===",
                nodes.BinaryOperator.STRICT_NE: "!==",
                nodes.BinaryOperator.AND: "&&",
                nodes.BinaryOperator.OR: "||",
                nodes.BinaryOperator.NULLISH: "??",
                nodes.BinaryOperator.ACCESS: ".",
            }
            return mapping.get(operator)
        if isinstance(operator, str):
            return operator
        return None

    def _parse_prefix(self) -> nodes.Expression:
        token = self._advance()

        if token.kind is tokens.TokenKind.IDENTIFIER:
            return nodes.Identifier(node_id=self._next_id(), span=token.span, name=token.lexeme)

        if token.kind is tokens.TokenKind.NUMBER_LITERAL:
            return nodes.Literal(node_id=self._next_id(), span=token.span, value=token.value, raw=token.lexeme)

        if token.kind is tokens.TokenKind.STRING_LITERAL:
            return nodes.Literal(node_id=self._next_id(), span=token.span, value=token.value, raw=token.lexeme)

        if token.kind is tokens.TokenKind.KEYWORD:
            if token.lexeme == "verum":
                return nodes.Literal(node_id=self._next_id(), span=token.span, value=True, raw=token.lexeme)
            if token.lexeme == "falsum":
                return nodes.Literal(node_id=self._next_id(), span=token.span, value=False, raw=token.lexeme)
            if token.lexeme == "nullum":
                return nodes.Literal(node_id=self._next_id(), span=token.span, value=None, raw=token.lexeme)
            if token.lexeme == "indefinitum":
                return nodes.Literal(node_id=self._next_id(), span=token.span, value="indefinitum", raw=token.lexeme)
            if token.lexeme == "structura":
                return self._parse_object_literal(token)
            if token.lexeme == "functio":
                return self._parse_lambda_expression(token)

        if token.lexeme == "(":
            expr = self._parse_expression()
            closing = self._consume_symbol(")", "Expected ')' after expression.")
            expr.span = self._combine_spans(token.span, closing.span)
            return expr

        if token.lexeme == "[":
            return self._parse_array_literal(token)

        if token.lexeme in {"!", "-", "+"}:
            operand = self._parse_expression(10)
            span = self._combine_spans(token.span, operand.span)
            return nodes.UnaryExpression(
                node_id=self._next_id(),
                span=span,
                operator=self._unary_operator(token.lexeme),
                operand=operand,
            )

        raise ParseError(f"Unexpected token {token.lexeme!r} at {token.span}.")

    def _finish_call(self, callee: nodes.Expression) -> nodes.Expression:
        arguments: List[nodes.Expression] = []
        if not self._check_symbol(")"):
            while True:
                arguments.append(self._parse_expression())
                if not self._match_symbol(","):
                    break
        closing = self._consume_symbol(")", "Expected ')' after arguments.")
        return nodes.CallExpression(
            node_id=self._next_id(),
            span=self._combine_spans(callee.span, closing.span),
            callee=callee,
            arguments=arguments,
        )

    def _finish_index(self, collection: nodes.Expression) -> nodes.Expression:
        index_expr = self._parse_expression()
        closing = self._consume_symbol("]", "Expected ']' after index expression.")
        return nodes.IndexExpression(
            node_id=self._next_id(),
            span=self._combine_spans(collection.span, closing.span),
            collection=collection,
            index=index_expr,
        )

    def _finish_member(self, obj: nodes.Expression) -> nodes.Expression:
        name_token = self._consume(tokens.TokenKind.IDENTIFIER, "Expected property name after '.'.")
        return nodes.MemberExpression(
            node_id=self._next_id(),
            span=self._combine_spans(obj.span, name_token.span),
            object=obj,
            property=name_token.lexeme,
        )

    def _parse_array_literal(self, start_token: tokens.Token) -> nodes.ArrayLiteral:
        elements: List[nodes.Expression] = []
        if not self._check_symbol("]"):
            while True:
                elements.append(self._parse_expression())
                if not self._match_symbol(","):
                    break
        closing = self._consume_symbol("]", "Expected ']' after array literal.")
        return nodes.ArrayLiteral(
            node_id=self._next_id(),
            span=self._combine_spans(start_token.span, closing.span),
            elements=elements,
        )

    def _parse_object_literal(self, start_token: tokens.Token) -> nodes.ObjectLiteral:
        open_brace = self._consume_symbol("{", "Expected '{' after 'structura'.")
        properties: List[nodes.ObjectProperty] = []
        if not self._check_symbol("}"):
            while True:
                key_token = self._consume(tokens.TokenKind.IDENTIFIER, "Expected property identifier.")
                self._consume_symbol(":", "Expected ':' after property name.")
                value_expr = self._parse_expression()
                prop_span = self._combine_spans(key_token.span, value_expr.span)
                properties.append(
                    nodes.ObjectProperty(
                        node_id=self._next_id(),
                        span=prop_span,
                        key=key_token.lexeme,
                        value=value_expr,
                    )
                )
                if not self._match_symbol(","):
                    break
        closing = self._consume_symbol("}", "Expected '}' after object literal.")
        return nodes.ObjectLiteral(
            node_id=self._next_id(),
            span=self._combine_spans(start_token.span, closing.span),
            properties=properties,
        )

    def _parse_lambda_expression(self, fun_token: tokens.Token) -> nodes.LambdaExpression:
        self._consume_symbol("(", "Expected '(' after 'functio'.")
        parameters = self._parse_parameters()
        self._consume_symbol(")", "Expected ')' after parameter list.")

        return_type = None
        if self._match_symbol("->"):
            return_type = self._parse_type_annotation()

        if self._match_symbol("=>"):
            body_expr = self._parse_expression()
            span = self._combine_spans(fun_token.span, body_expr.span)
            return nodes.LambdaExpression(
                node_id=self._next_id(),
                span=span,
                parameters=parameters,
                return_type=return_type,
                body=body_expr,
            )

        body_block = self._parse_block_statement()
        span = self._combine_spans(fun_token.span, body_block.span)
        return nodes.LambdaExpression(
            node_id=self._next_id(),
            span=span,
            parameters=parameters,
            return_type=return_type,
            body=body_block,
        )

    def _parse_type_annotation(self) -> nodes.TypeAnnotation:
        parts: List[str] = []
        start_span: Optional[Span] = None
        end_span: Optional[Span] = None
        while not self._is_at_end():
            token = self._peek()
            if token.kind is tokens.TokenKind.KEYWORD and token.lexeme in TYPE_KEYWORDS:
                parts.append(self._advance().lexeme)
            elif token.kind is tokens.TokenKind.IDENTIFIER:
                parts.append(self._advance().lexeme)
            elif token.lexeme in {"[", "]", "?", "->"}:
                parts.append(self._advance().lexeme)
            else:
                break
            start_span = start_span or token.span
            end_span = token.span
        if not parts or start_span is None or end_span is None:
            raise ParseError("Expected type annotation.")
        return nodes.TypeAnnotation(
            node_id=self._next_id(),
            span=self._combine_spans(start_span, end_span),
            name="".join(parts),
        )

    # Binding helpers -------------------------------------------------------------

    def _parse_binding(self, allow_type_prefix: bool, message: str) -> Tuple[tokens.Token, Optional[nodes.TypeAnnotation], Span]:
        type_annotation: Optional[nodes.TypeAnnotation] = None
        start_span: Optional[Span] = None
        if allow_type_prefix and self._is_type_prefix():
            type_token = self._advance()
            type_annotation = nodes.TypeAnnotation(
                node_id=self._next_id(),
                span=type_token.span,
                name=type_token.lexeme,
            )
            start_span = type_token.span
        name_token = self._consume(tokens.TokenKind.IDENTIFIER, message)
        if start_span is None:
            start_span = name_token.span
        if self._match_symbol(":"):
            type_annotation = self._parse_type_annotation()
        end_span = type_annotation.span if type_annotation else name_token.span
        return name_token, type_annotation, self._combine_spans(start_span, end_span)

    def _is_type_prefix(self) -> bool:
        if self._is_at_end():
            return False
        token = self._peek()
        if token.lexeme in {"mutabilis", "constans"}:
            return False
        if token.kind is tokens.TokenKind.KEYWORD:
            if token.lexeme not in TYPE_KEYWORDS:
                return False
        elif token.kind is not tokens.TokenKind.IDENTIFIER:
            return False
        next_token = self._peek_next()
        return next_token.kind is tokens.TokenKind.IDENTIFIER

    def _peek_next(self) -> tokens.Token:
        index = self._index + 1
        if index >= len(self._tokens):
            return self._tokens[-1]
        return self._tokens[index]

    # Helpers --------------------------------------------------------------------

    def _binary_operator(self, lexeme: str) -> nodes.BinaryOperator | str:
        mapping = {
            "+": nodes.BinaryOperator.ADD,
            "-": nodes.BinaryOperator.SUB,
            "*": nodes.BinaryOperator.MUL,
            "/": nodes.BinaryOperator.DIV,
            "%": nodes.BinaryOperator.MOD,
            "**": nodes.BinaryOperator.POW,
            "||": nodes.BinaryOperator.OR,
            "&&": nodes.BinaryOperator.AND,
            "??": nodes.BinaryOperator.NULLISH,
            "==": nodes.BinaryOperator.EQ,
            "!=": nodes.BinaryOperator.NE,
            "===": nodes.BinaryOperator.STRICT_EQ,
            "!==": nodes.BinaryOperator.STRICT_NE,
            ">": nodes.BinaryOperator.GT,
            "<": nodes.BinaryOperator.LT,
            ">=": nodes.BinaryOperator.GE,
            "<=": nodes.BinaryOperator.LE,
        }
        return mapping.get(lexeme, lexeme)

    def _unary_operator(self, lexeme: str) -> nodes.UnaryOperator:
        mapping = {
            "-": nodes.UnaryOperator.NEGATE,
            "+": nodes.UnaryOperator.POSITIVE,
            "!": nodes.UnaryOperator.NOT,
        }
        return mapping[lexeme]

    def _combine_spans(self, start: Span, end: Span) -> Span:
        return Span(start.start, end.end)

    def _consume(self, kind: tokens.TokenKind, message: str) -> tokens.Token:
        if self._check(kind):
            return self._advance()
        token = self._peek()
        raise ParseError(f"{message} Found {token.lexeme!r} at {token.span}.")

    def _consume_symbol(self, symbol: str, message: str) -> tokens.Token:
        if self._match_symbol(symbol):
            return self._previous()
        token = self._peek()
        raise ParseError(f"{message} Found {token.lexeme!r} at {token.span}.")

    def _consume_keyword(self, keyword: str) -> tokens.Token:
        if self._match_keyword(keyword):
            return self._previous()
        token = self._peek()
        raise ParseError(f"Expected keyword '{keyword}', found {token.lexeme!r}.")

    def _check(self, kind: tokens.TokenKind) -> bool:
        if self._is_at_end():
            return False
        return self._peek().kind is kind

    def _check_symbol(self, symbol: str) -> bool:
        if self._is_at_end():
            return False
        return self._peek().lexeme == symbol

    def _check_keyword(self, keyword: str) -> bool:
        if self._is_at_end():
            return False
        token = self._peek()
        return token.kind is tokens.TokenKind.KEYWORD and token.lexeme == keyword

    def _match_symbol(self, symbol: str) -> bool:
        if self._check_symbol(symbol):
            self._advance()
            return True
        if symbol == "=>" and not self._is_at_end():
            token = self._peek()
            if token.lexeme == "=>":
                self._advance()
                return True
        return False

    def _match_keyword(self, keyword: str) -> bool:
        if self._check_keyword(keyword):
            self._advance()
            return True
        return False

    def _match(self, kind: tokens.TokenKind) -> bool:
        if self._check(kind):
            self._advance()
            return True
        return False

    def _advance(self) -> tokens.Token:
        if not self._is_at_end():
            self._index += 1
        return self._tokens[self._index - 1]

    def _peek(self) -> tokens.Token:
        return self._tokens[self._index]

    def _previous(self) -> tokens.Token:
        return self._tokens[self._index - 1]

    def _is_at_end(self) -> bool:
        return self._peek().kind is tokens.TokenKind.EOF

    def _next_id(self) -> int:
        self._node_counter += 1
        return self._node_counter
