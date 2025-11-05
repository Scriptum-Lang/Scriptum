"""Recursive-descent + Pratt parser for Scriptum."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

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

    # Public API -----------------------------------------------------------------

    def parse(self, source: text.SourceFile) -> nodes.Module:
        self._source = source
        self._tokens = self._lexer.tokenize(source)
        self._index = 0
        self._node_counter = 0
        declarations: List[nodes.Declaration] = []
        while not self._is_at_end():
            declarations.append(self._parse_declaration(global_scope=True))
        module_span = Span(0, len(source.text))
        return nodes.Module(node_id=self._next_id(), span=module_span, declarations=declarations)

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
        try:
            expr = self._parse_prefix()

            while True:
                if self._is_at_end():
                    break

                if self._match_symbol("("):
                    expr = self._finish_call(expr)
                    continue
                if self._match_symbol("["):
                    expr = self._finish_index(expr)
                    continue
                if self._match_symbol("."):
                    expr = self._finish_member(expr)
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
                else:
                    expr = nodes.BinaryExpression(
                        node_id=self._next_id(),
                        span=span,
                        operator=self._binary_operator(operator_token.lexeme),
                        left=expr,
                        right=right,
                    )
            return expr
        finally:
            self._leave_depth()

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
