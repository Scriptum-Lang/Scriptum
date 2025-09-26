use std::sync::Arc;

use scriptum_ast::{
    BinaryOp, Block, Expression, ExpressionKind, Function, Module, Statement, StatementKind,
    StringInterner, Symbol,
};
use scriptum_lexer::tokens::{KeywordKind, OperatorKind};
use scriptum_lexer::{lex, Token, TokenKind};
use scriptum_utils::Span;
use smallvec::SmallVec;
use thiserror::Error;

use crate::ll1::TokenStream;

/// Erro sintático estruturado.
#[derive(Debug, Error)]
#[error("erro sintático: {message}")]
pub struct ParseError {
    pub message: String,
    pub span: Span,
}

impl ParseError {
    pub fn new(message: impl Into<String>, span: Span) -> Self {
        Self {
            message: message.into(),
            span,
        }
    }
}

/// Parser LL(1) responsável por construir a AST.
pub struct Parser<'a> {
    source: &'a str,
    interner: StringInterner,
    stream: TokenStream,
}

pub fn parse_module(source: &str) -> Result<Module, ParseError> {
    let tokens = lex(source).map_err(|err| ParseError::new(err.message, err.span))?;
    let mut parser = Parser::new(source, tokens.into());
    parser.parse_module()
}

impl<'a> Parser<'a> {
    pub fn new(source: &'a str, tokens: Arc<[Token]>) -> Self {
        let stream = TokenStream::new(tokens);
        Self {
            source,
            interner: StringInterner::new(),
            stream,
        }
    }

    fn parse_module(&mut self) -> Result<Module, ParseError> {
        let mut functions = Vec::new();
        while let Some(kind) = self.stream.peek_kind() {
            if kind == TokenKind::EOF {
                break;
            }
            functions.push(self.parse_function()?);
        }
        Ok(Module::new(functions))
    }

    fn parse_function(&mut self) -> Result<Function, ParseError> {
        let start = self
            .expect_kind(TokenKind::Keyword(KeywordKind::Definire))?
            .span
            .start();
        let name_tok = self.expect_identifier()?;
        let name = self.symbol_from_span(name_tok.span);
        self.expect_kind(TokenKind::LParen)?;
        let params = self.parse_param_list()?;
        self.expect_kind(TokenKind::RParen)?;
        let body = self.parse_block()?;
        let span = Span::new(start, body.span.end());
        Ok(Function::new(name, params, body, span))
    }

    fn parse_param_list(&mut self) -> Result<SmallVec<[Symbol; 4]>, ParseError> {
        let mut params = SmallVec::new();
        if self.stream.peek_kind() == Some(TokenKind::RParen) {
            return Ok(params);
        }
        loop {
            let ident = self.expect_identifier()?;
            params.push(self.symbol_from_span(ident.span));
            if self.stream.peek_kind() == Some(TokenKind::Comma) {
                self.stream.next();
                continue;
            }
            break;
        }
        Ok(params)
    }

    fn parse_block(&mut self) -> Result<Block, ParseError> {
        let start_token = self.expect_kind(TokenKind::LBrace)?;
        let mut statements = Vec::new();
        while let Some(kind) = self.stream.peek_kind() {
            if kind == TokenKind::RBrace {
                break;
            }
            statements.push(self.parse_statement()?);
        }
        let end_token = self.expect_kind(TokenKind::RBrace)?;
        Ok(Block::new(
            statements,
            Span::new(start_token.span.start(), end_token.span.end()),
        ))
    }

    fn parse_statement(&mut self) -> Result<Statement, ParseError> {
        let token = self.stream.peek().copied().ok_or_else(|| {
            ParseError::new("declaração inesperada no fim do arquivo", Span::default())
        })?;
        match token.kind {
            TokenKind::Keyword(KeywordKind::Definire) => self.parse_let_statement(),
            TokenKind::Keyword(KeywordKind::Si) => self.parse_if_statement(),
            TokenKind::Keyword(KeywordKind::Dum) => self.parse_while_statement(),
            TokenKind::Keyword(KeywordKind::Reditus) => self.parse_return_statement(),
            TokenKind::Identifier => {
                if self.stream.peek_next_kind() == Some(TokenKind::Operator(OperatorKind::Assign)) {
                    self.parse_assignment()
                } else {
                    let expr = self.parse_expression()?;
                    let semi = self.expect_kind(TokenKind::Semicolon)?;
                    Ok(Statement::new(StatementKind::Expr(expr), semi.span))
                }
            }
            _ => {
                let expr = self.parse_expression()?;
                let semi = self.expect_kind(TokenKind::Semicolon)?;
                Ok(Statement::new(StatementKind::Expr(expr), semi.span))
            }
        }
    }

    fn parse_let_statement(&mut self) -> Result<Statement, ParseError> {
        let start = self
            .expect_kind(TokenKind::Keyword(KeywordKind::Definire))?
            .span
            .start();
        let ident = self.expect_identifier()?;
        self.expect_kind(TokenKind::Operator(OperatorKind::Assign))?;
        let value = self.parse_expression()?;
        let semi = self.expect_kind(TokenKind::Semicolon)?;
        Ok(Statement::new(
            StatementKind::Let {
                name: self.symbol_from_span(ident.span),
                value,
            },
            Span::new(start, semi.span.end()),
        ))
    }

    fn parse_assignment(&mut self) -> Result<Statement, ParseError> {
        let ident = self.expect_identifier()?;
        let start = ident.span.start();
        self.expect_kind(TokenKind::Operator(OperatorKind::Assign))?;
        let value = self.parse_expression()?;
        let semi = self.expect_kind(TokenKind::Semicolon)?;
        Ok(Statement::new(
            StatementKind::Assign {
                target: self.symbol_from_span(ident.span),
                value,
            },
            Span::new(start, semi.span.end()),
        ))
    }

    fn parse_if_statement(&mut self) -> Result<Statement, ParseError> {
        let start = self
            .expect_kind(TokenKind::Keyword(KeywordKind::Si))?
            .span
            .start();
        let cond = self.parse_expression()?;
        let then_branch = self.parse_block()?;
        let else_branch =
            if self.stream.peek_kind() == Some(TokenKind::Keyword(KeywordKind::Alioqui)) {
                self.stream.next();
                Some(self.parse_block()?)
            } else {
                None
            };
        let end = else_branch
            .as_ref()
            .map(|block| block.span.end())
            .unwrap_or(then_branch.span.end());
        Ok(Statement::new(
            StatementKind::If {
                cond,
                then_branch,
                else_branch,
            },
            Span::new(start, end),
        ))
    }

    fn parse_while_statement(&mut self) -> Result<Statement, ParseError> {
        let start = self
            .expect_kind(TokenKind::Keyword(KeywordKind::Dum))?
            .span
            .start();
        let cond = self.parse_expression()?;
        let body = self.parse_block()?;
        let span = Span::new(start, body.span.end());
        Ok(Statement::new(StatementKind::While { cond, body }, span))
    }

    fn parse_return_statement(&mut self) -> Result<Statement, ParseError> {
        let start = self
            .expect_kind(TokenKind::Keyword(KeywordKind::Reditus))?
            .span
            .start();
        let value = self.parse_expression()?;
        let semi = self.expect_kind(TokenKind::Semicolon)?;
        Ok(Statement::new(
            StatementKind::Return { value },
            Span::new(start, semi.span.end()),
        ))
    }

    fn parse_expression(&mut self) -> Result<Expression, ParseError> {
        self.parse_equality()
    }

    fn parse_equality(&mut self) -> Result<Expression, ParseError> {
        let mut expr = self.parse_comparison()?;
        while let Some(kind) = self.stream.peek_kind() {
            let op = match kind {
                TokenKind::Operator(OperatorKind::Eq) => BinaryOp::Eq,
                TokenKind::Operator(OperatorKind::Ne) => BinaryOp::Ne,
                _ => break,
            };
            self.stream.next();
            let right = self.parse_comparison()?;
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression::new(
                ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
                span,
            );
        }
        Ok(expr)
    }

    fn parse_comparison(&mut self) -> Result<Expression, ParseError> {
        let mut expr = self.parse_term()?;
        while let Some(kind) = self.stream.peek_kind() {
            let op = match kind {
                TokenKind::Operator(OperatorKind::Lt) => BinaryOp::Lt,
                TokenKind::Operator(OperatorKind::Le) => BinaryOp::Le,
                TokenKind::Operator(OperatorKind::Gt) => BinaryOp::Gt,
                TokenKind::Operator(OperatorKind::Ge) => BinaryOp::Ge,
                _ => break,
            };
            self.stream.next();
            let right = self.parse_term()?;
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression::new(
                ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
                span,
            );
        }
        Ok(expr)
    }

    fn parse_term(&mut self) -> Result<Expression, ParseError> {
        let mut expr = self.parse_factor()?;
        while let Some(kind) = self.stream.peek_kind() {
            let op = match kind {
                TokenKind::Operator(OperatorKind::Plus) => BinaryOp::Add,
                TokenKind::Operator(OperatorKind::Minus) => BinaryOp::Sub,
                _ => break,
            };
            self.stream.next();
            let right = self.parse_factor()?;
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression::new(
                ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
                span,
            );
        }
        Ok(expr)
    }

    fn parse_factor(&mut self) -> Result<Expression, ParseError> {
        let mut expr = self.parse_unary()?;
        while let Some(kind) = self.stream.peek_kind() {
            let op = match kind {
                TokenKind::Operator(OperatorKind::Star) => BinaryOp::Mul,
                TokenKind::Operator(OperatorKind::Slash) => BinaryOp::Div,
                _ => break,
            };
            self.stream.next();
            let right = self.parse_unary()?;
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression::new(
                ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
                span,
            );
        }
        Ok(expr)
    }

    fn parse_unary(&mut self) -> Result<Expression, ParseError> {
        if let Some(kind) = self.stream.peek_kind() {
            if kind == TokenKind::Operator(OperatorKind::Minus) {
                let op_token = self.stream.next().unwrap();
                let rhs = self.parse_unary()?;
                let rhs_span_end = rhs.span.end();
                let zero = Expression::new(ExpressionKind::Number(0.0), op_token.span);
                return Ok(Expression::new(
                    ExpressionKind::Binary {
                        op: BinaryOp::Sub,
                        left: Box::new(zero),
                        right: Box::new(rhs),
                    },
                    Span::new(op_token.span.start(), rhs_span_end),
                ));
            }
        }
        self.parse_primary()
    }

    fn parse_primary(&mut self) -> Result<Expression, ParseError> {
        let token = self
            .stream
            .next()
            .ok_or_else(|| ParseError::new("expressão incompleta", Span::default()))?;
        match token.kind {
            TokenKind::Number => {
                let value = self
                    .slice(token.span)
                    .parse::<f64>()
                    .map_err(|_| ParseError::new("literal numérico inválido", token.span))?;
                Ok(Expression::new(ExpressionKind::Number(value), token.span))
            }
            TokenKind::Bool => {
                let value = match self.slice(token.span) {
                    "verum" => true,
                    "falsum" => false,
                    other => {
                        return Err(ParseError::new(
                            format!("literal booleano desconhecido: {}", other),
                            token.span,
                        ))
                    }
                };
                Ok(Expression::new(ExpressionKind::Bool(value), token.span))
            }
            TokenKind::Identifier => {
                if self.stream.peek_kind() == Some(TokenKind::LParen) {
                    self.stream.next();
                    let mut args = Vec::new();
                    if self.stream.peek_kind() != Some(TokenKind::RParen) {
                        loop {
                            args.push(self.parse_expression()?);
                            if self.stream.peek_kind() == Some(TokenKind::Comma) {
                                self.stream.next();
                                continue;
                            }
                            break;
                        }
                    }
                    let end = self.expect_kind(TokenKind::RParen)?.span.end();
                    Ok(Expression::new(
                        ExpressionKind::Call {
                            callee: self.symbol_from_span(token.span),
                            args,
                        },
                        Span::new(token.span.start(), end),
                    ))
                } else {
                    Ok(Expression::new(
                        ExpressionKind::Symbol(self.symbol_from_span(token.span)),
                        token.span,
                    ))
                }
            }
            TokenKind::LParen => {
                let expr = self.parse_expression()?;
                self.expect_kind(TokenKind::RParen)?;
                Ok(expr)
            }
            other => Err(ParseError::new(
                format!("token inesperado em expressão: {:?}", other),
                token.span,
            )),
        }
    }

    fn expect_kind(&mut self, expected: TokenKind) -> Result<Token, ParseError> {
        let token = self
            .stream
            .next()
            .ok_or_else(|| ParseError::new(format!("esperado {:?}", expected), Span::default()))?;
        if token.kind == expected {
            Ok(token)
        } else {
            Err(ParseError::new(
                format!("esperado {:?}, encontrado {:?}", expected, token.kind),
                token.span,
            ))
        }
    }

    fn expect_identifier(&mut self) -> Result<Token, ParseError> {
        let token = self
            .stream
            .next()
            .ok_or_else(|| ParseError::new("identificador esperado", Span::default()))?;
        if token.kind == TokenKind::Identifier {
            Ok(token)
        } else {
            Err(ParseError::new(
                format!("identificador esperado, mas encontrou {:?}", token.kind),
                token.span,
            ))
        }
    }

    fn symbol_from_span(&mut self, span: Span) -> Symbol {
        let start = span.start();
        let end = span.end();
        let text = &self.source[start..end];
        self.interner.intern(text)
    }

    fn slice(&self, span: Span) -> &str {
        &self.source[span.start()..span.end()]
    }
}
