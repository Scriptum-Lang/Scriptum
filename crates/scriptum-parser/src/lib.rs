#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Parser Pratt/LR híbrido para a linguagem Scriptum.

use serde::Serialize;
use smallvec::SmallVec;
use thiserror::Error;

use scriptum_ast::{
    BinaryOp, Block, Expression, ExpressionKind, Function, Item, ItemKind, LambdaBody,
    LambdaExpression, Literal, LogicalOp, Module, NodeIdGenerator, ObjectField, Parameter,
    Statement, StatementKind, StringInterner, Symbol, TypeExpr, TypeExprKind, TypeField,
    TypeParameter, UnaryOp, VarDecl,
};
use scriptum_lexer::lex;
use scriptum_lexer::tokens::{Delimiter, Keyword, Operator, Punctuation, Token, TokenKind};
use scriptum_utils::Span;

/// Resultado completo do parser.
#[derive(Debug, Serialize)]
pub struct ParseOutput {
    pub module: Module,
    pub diagnostics: Vec<ParseError>,
}

/// Erros recuperáveis reportados durante o parsing.
#[derive(Debug, Clone, Error, Serialize)]
#[error("{message}")]
pub struct ParseError {
    pub message: String,
    pub span: Span,
}

impl ParseError {
    fn new(message: impl Into<String>, span: Span) -> Self {
        Self {
            message: message.into(),
            span,
        }
    }
}

/// Entrypoint principal do parser.
pub fn parse_module(source: &str) -> Result<ParseOutput, ParseError> {
    let tokens = lex(source).map_err(|err| ParseError::new(err.message, err.span))?;
    let mut parser = Parser::new(source, tokens.into());
    let module = parser.parse_module();
    Ok(ParseOutput {
        module,
        diagnostics: parser.errors,
    })
}

struct Parser<'src> {
    source: &'src str,
    tokens: SmallVec<[Token; 256]>,
    pos: usize,
    errors: Vec<ParseError>,
    interner: StringInterner,
    ids: NodeIdGenerator,
    fuel: usize,
}

impl<'src> Parser<'src> {
    fn new(source: &'src str, tokens: Vec<Token>) -> Self {
        let fuel = tokens.len().saturating_mul(4).max(32);
        let tokens = tokens.into();
        Self {
            source,
            tokens,
            pos: 0,
            errors: Vec::new(),
            interner: StringInterner::new(),
            ids: NodeIdGenerator::new(),
            fuel,
        }
    }

    fn parse_module(&mut self) -> Module {
        let start = self.current_span().map(|span| span.start()).unwrap_or(0);
        let mut items = Vec::new();
        while !self.is_at_end() {
            let before = self.pos;
            if self.matches(TokenKind::EOF) {
                break;
            }
            if let Some(item) = self.parse_item() {
                items.push(item);
            } else {
                self.synchronize(&[TokenKind::Punctuation(Punctuation::Semicolon)]);
            }
            if !self.guard_progress(before, "módulo") {
                break;
            }
        }
        let end = self
            .tokens
            .last()
            .map(|token| token.span.end())
            .unwrap_or(self.source.len());
        Module::new(
            self.ids.fresh(),
            Span::new(start, end),
            self.interner.clone(),
            items,
        )
    }

    fn parse_item(&mut self) -> Option<Item> {
        let token = self.peek_token()?;
        match token.kind {
            TokenKind::Keyword(Keyword::Functio) => self.parse_function_item(),
            TokenKind::Keyword(Keyword::Mutabilis) | TokenKind::Keyword(Keyword::Constans) => {
                let decl = self.parse_variable_decl(true)?;
                let span = decl
                    .initializer
                    .as_ref()
                    .map(|expr| expr.span)
                    .unwrap_or_else(|| self.previous_span());
                Some(Item {
                    id: self.ids.fresh(),
                    span,
                    kind: ItemKind::Let(decl),
                })
            }
            _ => {
                let span = token.span;
                self.error("esperado 'functio', 'mutabilis' ou 'constans'", span);
                None
            }
        }
    }

    fn parse_function_item(&mut self) -> Option<Item> {
        let keyword = self.advance();
        let name_token = self.expect_identifier("nome de função esperado")?;
        let name = self.symbol_from(name_token.span);
        let generics = if self.matches(TokenKind::Operator(Operator::Less)) {
            self.parse_generic_params()
        } else {
            Vec::new()
        };
        self.expect_delimiter(Delimiter::LParen, "esperado '(' após nome da função")?;
        let params = self.parse_parameter_list();
        self.expect_delimiter(Delimiter::RParen, "esperado ')' após parâmetros")?;
        let return_type = if self.matches(TokenKind::Punctuation(Punctuation::Arrow)) {
            Some(self.parse_type_expr())
        } else {
            None
        };
        let body = self.parse_block();
        let span = Span::new(keyword.span.start(), body.span.end());
        Some(Item {
            id: self.ids.fresh(),
            span,
            kind: ItemKind::Function(Function {
                name,
                generics,
                params,
                return_type,
                body,
            }),
        })
    }

    fn parse_generic_params(&mut self) -> Vec<TypeParameter> {
        let params = self.parse_list(
            TokenKind::Punctuation(Punctuation::Comma),
            TokenKind::Operator(Operator::Greater),
            false,
            "parâmetros genéricos",
            |parser| {
                let ident = parser.expect_identifier("nome de parâmetro de tipo esperado")?;
                Some(TypeParameter {
                    name: parser.symbol_from(ident.span),
                })
            },
        );
        self.expect(
            TokenKind::Operator(Operator::Greater),
            "esperado '>' em parâmetros genéricos".into(),
        );
        params
    }

    fn parse_parameter_list(&mut self) -> Vec<Parameter> {
        self.parse_list(
            TokenKind::Punctuation(Punctuation::Comma),
            TokenKind::Delimiter(Delimiter::RParen),
            true,
            "lista de parâmetros",
            |parser| {
                if parser.peek_is_type_keyword() {
                    let ty = parser.parse_simple_type().expect("tipo prefixado válido");
                    let name_tok =
                        parser.expect_identifier("nome de parâmetro esperado após tipo")?;
                    let name = parser.symbol_from(name_tok.span);
                    let span = Span::new(ty.span.start(), name_tok.span.end());
                    return Some(Parameter {
                        id: parser.ids.fresh(),
                        span,
                        name,
                        ty: Some(ty),
                    });
                }
                let name_tok = parser.expect_identifier("nome de parâmetro esperado")?;
                let name = parser.symbol_from(name_tok.span);
                let mut span_end = name_tok.span.end();
                let ty = if parser.matches(TokenKind::Punctuation(Punctuation::Colon)) {
                    let ty = parser.parse_type_expr();
                    span_end = ty.span.end();
                    Some(ty)
                } else {
                    None
                };
                let span = Span::new(name_tok.span.start(), span_end);
                Some(Parameter {
                    id: parser.ids.fresh(),
                    span,
                    name,
                    ty,
                })
            },
        )
    }

    fn parse_block(&mut self) -> Block {
        let lbrace = self.expect_delimiter(Delimiter::LBrace, "esperado '{'");
        let lbrace = match lbrace {
            Some(tok) => tok,
            None => {
                let id = self.ids.fresh();
                return Block::new(
                    id,
                    Span::new(self.previous_span().start(), self.previous_span().end()),
                    Vec::new(),
                );
            }
        };
        let mut statements = Vec::new();
        while !self.check(TokenKind::Delimiter(Delimiter::RBrace)) && !self.is_at_end() {
            let before = self.pos;
            if let Some(stmt) = self.parse_statement() {
                statements.push(stmt);
            } else {
                self.synchronize(&[
                    TokenKind::Punctuation(Punctuation::Semicolon),
                    TokenKind::Delimiter(Delimiter::RBrace),
                ]);
            }
            if !self.guard_progress(before, "bloco") {
                break;
            }
        }
        let rbrace = self.expect_delimiter(Delimiter::RBrace, "esperado '}'");
        let end = rbrace
            .as_ref()
            .map(|tok| tok.span.end())
            .unwrap_or(lbrace.span.end());
        Block::new(
            self.ids.fresh(),
            Span::new(lbrace.span.start(), end),
            statements,
        )
    }

    fn parse_statement(&mut self) -> Option<Statement> {
        if self.matches(TokenKind::Keyword(Keyword::Mutabilis)) {
            return Some(self.finish_var_statement(true));
        }
        if self.matches(TokenKind::Keyword(Keyword::Constans)) {
            return Some(self.finish_var_statement(false));
        }
        if self.matches(TokenKind::Keyword(Keyword::Redde)) {
            let start = self.previous_span().start();
            let value = if self.check_statement_end() {
                None
            } else {
                Some(self.parse_expression())
            };
            self.consume_semicolon("esperado ';' após retorno");
            return Some(Statement {
                id: self.ids.fresh(),
                span: Span::new(start, self.previous_span().end()),
                kind: StatementKind::Return(value),
            });
        }
        if self.matches(TokenKind::Keyword(Keyword::Si)) {
            return Some(self.parse_if_statement());
        }
        if self.matches(TokenKind::Keyword(Keyword::Dum)) {
            return Some(self.parse_while_statement());
        }
        if self.matches(TokenKind::Keyword(Keyword::Pro)) {
            return Some(self.parse_for_statement());
        }
        if self.matches(TokenKind::Keyword(Keyword::Frange)) {
            let span = self.previous_span();
            self.consume_semicolon("esperado ';' após 'frange'");
            return Some(Statement {
                id: self.ids.fresh(),
                span,
                kind: StatementKind::Break(None),
            });
        }
        if self.matches(TokenKind::Keyword(Keyword::Perge)) {
            let span = self.previous_span();
            self.consume_semicolon("esperado ';' após 'perge'");
            return Some(Statement {
                id: self.ids.fresh(),
                span,
                kind: StatementKind::Continue(None),
            });
        }
        if self.matches(TokenKind::Delimiter(Delimiter::LBrace)) {
            self.rewind();
            let block = self.parse_block();
            return Some(Statement {
                id: self.ids.fresh(),
                span: block.span,
                kind: StatementKind::Block(block),
            });
        }
        let expr = self.parse_expression();
        self.consume_semicolon("esperado ';' após expressão");
        Some(Statement {
            id: self.ids.fresh(),
            span: expr.span,
            kind: StatementKind::Expr(expr),
        })
    }

    fn finish_var_statement(&mut self, mutable: bool) -> Statement {
        let start = self.previous_span().start();
        let decl = self.finish_variable_decl(mutable);
        Statement {
            id: self.ids.fresh(),
            span: Span::new(start, self.previous_span().end()),
            kind: if mutable {
                StatementKind::Let(decl)
            } else {
                StatementKind::Const(decl)
            },
        }
    }

    fn parse_variable_decl(&mut self, allow_top_level: bool) -> Option<VarDecl> {
        let mutable = if self.previous_kind() == Some(TokenKind::Keyword(Keyword::Mutabilis)) {
            true
        } else if self.previous_kind() == Some(TokenKind::Keyword(Keyword::Constans)) {
            false
        } else if allow_top_level {
            match self.peek_token()?.kind {
                TokenKind::Keyword(Keyword::Mutabilis) => {
                    self.advance();
                    true
                }
                TokenKind::Keyword(Keyword::Constans) => {
                    self.advance();
                    false
                }
                _ => {
                    self.error("esperado 'mutabilis' ou 'constans'", self.peek_span());
                    return None;
                }
            }
        } else {
            self.error("declaração de variável inválida", self.peek_span());
            return None;
        };
        Some(self.finish_variable_decl(mutable))
    }

    fn finish_variable_decl(&mut self, mutable: bool) -> VarDecl {
        let (name_tok, type_annotation) = if self.peek_is_type_keyword() {
            let ty = self.parse_simple_type().expect("tipo prefixado válido");
            let name_tok = match self.expect_identifier("nome de variável esperado após tipo") {
                Some(tok) => tok,
                None => {
                    return VarDecl {
                        name: self.symbol_from(self.previous_span()),
                        mutable,
                        type_annotation: Some(ty),
                        initializer: None,
                    };
                }
            };
            (name_tok, Some(ty))
        } else {
            let name_tok = match self.expect_identifier("nome de variável esperado") {
                Some(tok) => tok,
                None => {
                    return VarDecl {
                        name: self.symbol_from(self.previous_span()),
                        mutable,
                        type_annotation: None,
                        initializer: None,
                    };
                }
            };
            let ty = if self.matches(TokenKind::Punctuation(Punctuation::Colon)) {
                Some(self.parse_type_expr())
            } else {
                None
            };
            (name_tok, ty)
        };
        let name = self.symbol_from(name_tok.span);
        let initializer = if self.matches(TokenKind::Operator(Operator::Assign)) {
            Some(self.parse_expression())
        } else {
            None
        };
        self.consume_semicolon("esperado ';' após declaração");
        VarDecl {
            name,
            mutable,
            type_annotation,
            initializer,
        }
    }

    fn parse_if_statement(&mut self) -> Statement {
        let start = self.previous_span().start();
        let condition = self.parse_expression();
        let then_branch = self.parse_embedded_statement();
        let else_branch = if self.matches(TokenKind::Keyword(Keyword::Aliter)) {
            Some(Box::new(self.parse_embedded_statement()))
        } else {
            None
        };
        Statement {
            id: self.ids.fresh(),
            span: Span::new(start, then_branch.span.end()),
            kind: StatementKind::If {
                condition,
                then_branch: Box::new(then_branch),
                else_branch,
            },
        }
    }

    fn parse_embedded_statement(&mut self) -> Statement {
        if self.matches(TokenKind::Delimiter(Delimiter::LBrace)) {
            self.rewind();
            let block = self.parse_block();
            Statement {
                id: self.ids.fresh(),
                span: block.span,
                kind: StatementKind::Block(block),
            }
        } else {
            let stmt = self.parse_statement();
            stmt.unwrap_or_else(|| Statement {
                id: self.ids.fresh(),
                span: self.previous_span(),
                kind: StatementKind::Expr(self.empty_expr()),
            })
        }
    }

    fn parse_while_statement(&mut self) -> Statement {
        let start = self.previous_span().start();
        let condition = self.parse_expression();
        let body = self.parse_embedded_statement();
        Statement {
            id: self.ids.fresh(),
            span: Span::new(start, body.span.end()),
            kind: StatementKind::While {
                condition,
                body: Box::new(body),
            },
        }
    }

    fn parse_for_statement(&mut self) -> Statement {
        let start = self.previous_span().start();
        let binding_tok = self.expect_identifier("identificador após 'pro' esperado");
        let binding_tok = match binding_tok {
            Some(tok) => tok,
            None => {
                return Statement {
                    id: self.ids.fresh(),
                    span: self.previous_span(),
                    kind: StatementKind::Expr(self.empty_expr()),
                }
            }
        };
        self.expect_keyword(Keyword::In, "esperado 'in' em laço 'pro'");
        let iterator = self.parse_expression();
        let body = self.parse_embedded_statement();
        Statement {
            id: self.ids.fresh(),
            span: Span::new(start, body.span.end()),
            kind: StatementKind::For {
                binding: self.symbol_from(binding_tok.span),
                iterator,
                body: Box::new(body),
            },
        }
    }

    fn parse_expression(&mut self) -> Expression {
        self.parse_assignment()
    }

    fn parse_assignment(&mut self) -> Expression {
        let expr = self.parse_ternary();
        if self.matches(TokenKind::Operator(Operator::Assign)) {
            let value = self.parse_assignment();
            let span = Span::new(expr.span.start(), value.span.end());
            Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Assignment {
                    target: Box::new(expr),
                    value: Box::new(value),
                },
            }
        } else {
            expr
        }
    }

    fn parse_ternary(&mut self) -> Expression {
        let mut expr = self.parse_nullish();
        if self.matches(TokenKind::Punctuation(Punctuation::Question)) {
            let then_expr = self.parse_expression();
            self.expect(
                TokenKind::Punctuation(Punctuation::Colon),
                "esperado ':' no operador ternário".into(),
            );
            let else_expr = self.parse_expression();
            let span = Span::new(expr.span.start(), else_expr.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Conditional {
                    condition: Box::new(expr),
                    then_branch: Box::new(then_expr),
                    else_branch: Box::new(else_expr),
                },
            };
        }
        expr
    }

    fn parse_nullish(&mut self) -> Expression {
        let mut expr = self.parse_logical_or();
        while self.matches(TokenKind::Operator(Operator::NullishCoalesce)) {
            let right = self.parse_logical_or();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::NullishCoalesce {
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn parse_logical_or(&mut self) -> Expression {
        let mut expr = self.parse_logical_and();
        while self.matches(TokenKind::Operator(Operator::OrOr)) {
            let right = self.parse_logical_and();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Logical {
                    op: LogicalOp::Or,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn parse_logical_and(&mut self) -> Expression {
        let mut expr = self.parse_equality();
        while self.matches(TokenKind::Operator(Operator::AndAnd)) {
            let right = self.parse_equality();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Logical {
                    op: LogicalOp::And,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn parse_equality(&mut self) -> Expression {
        let mut expr = self.parse_comparison();
        while let Some(op) = self.match_equality_operator() {
            let right = self.parse_comparison();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn match_equality_operator(&mut self) -> Option<BinaryOp> {
        if self.matches(TokenKind::Operator(Operator::Equal)) {
            Some(BinaryOp::Equal)
        } else if self.matches(TokenKind::Operator(Operator::NotEqual)) {
            Some(BinaryOp::NotEqual)
        } else if self.matches(TokenKind::Operator(Operator::StrictEqual)) {
            Some(BinaryOp::StrictEqual)
        } else if self.matches(TokenKind::Operator(Operator::StrictNotEqual)) {
            Some(BinaryOp::StrictNotEqual)
        } else {
            None
        }
    }

    fn parse_comparison(&mut self) -> Expression {
        let mut expr = self.parse_term();
        while let Some(op) = self.match_comparison_operator() {
            let right = self.parse_term();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn match_comparison_operator(&mut self) -> Option<BinaryOp> {
        if self.matches(TokenKind::Operator(Operator::Greater)) {
            Some(BinaryOp::Greater)
        } else if self.matches(TokenKind::Operator(Operator::GreaterEqual)) {
            Some(BinaryOp::GreaterEqual)
        } else if self.matches(TokenKind::Operator(Operator::Less)) {
            Some(BinaryOp::Less)
        } else if self.matches(TokenKind::Operator(Operator::LessEqual)) {
            Some(BinaryOp::LessEqual)
        } else {
            None
        }
    }

    fn parse_term(&mut self) -> Expression {
        let mut expr = self.parse_factor();
        while let Some(op) = self.match_term_operator() {
            let right = self.parse_factor();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn match_term_operator(&mut self) -> Option<BinaryOp> {
        if self.matches(TokenKind::Operator(Operator::Add)) {
            Some(BinaryOp::Add)
        } else if self.matches(TokenKind::Operator(Operator::Sub)) {
            Some(BinaryOp::Sub)
        } else {
            None
        }
    }

    fn parse_factor(&mut self) -> Expression {
        let mut expr = self.parse_power();
        while let Some(op) = self.match_factor_operator() {
            let right = self.parse_power();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn match_factor_operator(&mut self) -> Option<BinaryOp> {
        if self.matches(TokenKind::Operator(Operator::Mul)) {
            Some(BinaryOp::Mul)
        } else if self.matches(TokenKind::Operator(Operator::Div)) {
            Some(BinaryOp::Div)
        } else if self.matches(TokenKind::Operator(Operator::Mod)) {
            Some(BinaryOp::Mod)
        } else {
            None
        }
    }

    fn parse_power(&mut self) -> Expression {
        let mut expr = self.parse_unary();
        if self.matches(TokenKind::Operator(Operator::Pow)) {
            let right = self.parse_power();
            let span = Span::new(expr.span.start(), right.span.end());
            expr = Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op: BinaryOp::Power,
                    left: Box::new(expr),
                    right: Box::new(right),
                },
            };
        }
        expr
    }

    fn parse_unary(&mut self) -> Expression {
        if self.matches(TokenKind::Operator(Operator::Sub)) {
            let op_span = self.previous_span();
            let expr = self.parse_unary();
            let zero = Expression {
                id: self.ids.fresh(),
                span: op_span,
                kind: ExpressionKind::Literal(Literal::Numerus(0.0)),
            };
            let span = Span::new(op_span.start(), expr.span.end());
            return Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Binary {
                    op: BinaryOp::Sub,
                    left: Box::new(zero),
                    right: Box::new(expr),
                },
            };
        }
        if self.matches(TokenKind::Operator(Operator::Add)) {
            let expr = self.parse_unary();
            return expr;
        }
        if self.matches(TokenKind::Operator(Operator::Not)) {
            let op_span = self.previous_span();
            let expr = self.parse_unary();
            let span = Span::new(op_span.start(), expr.span.end());
            return Expression {
                id: self.ids.fresh(),
                span,
                kind: ExpressionKind::Unary {
                    op: UnaryOp::Not,
                    expr: Box::new(expr),
                },
            };
        }
        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> Expression {
        let mut expr = self.parse_primary();
        loop {
            if self.matches(TokenKind::Delimiter(Delimiter::LParen)) {
                let args = self.parse_argument_list();
                let end = self
                    .expect_delimiter(Delimiter::RParen, "esperado ')'")
                    .map(|tok| tok.span.end())
                    .unwrap_or_else(|| self.previous_span().end());
                let span = Span::new(expr.span.start(), end);
                expr = Expression {
                    id: self.ids.fresh(),
                    span,
                    kind: ExpressionKind::Call {
                        callee: Box::new(expr),
                        arguments: args,
                    },
                };
                continue;
            }
            if self.matches(TokenKind::Delimiter(Delimiter::LBracket)) {
                let index = self.parse_expression();
                let end = self
                    .expect_delimiter(Delimiter::RBracket, "esperado ']' para indexação")
                    .map(|tok| tok.span.end())
                    .unwrap_or_else(|| self.previous_span().end());
                let span = Span::new(expr.span.start(), end);
                expr = Expression {
                    id: self.ids.fresh(),
                    span,
                    kind: ExpressionKind::Index {
                        target: Box::new(expr),
                        index: Box::new(index),
                    },
                };
                continue;
            }
            if self.matches(TokenKind::Punctuation(Punctuation::Dot)) {
                let ident = match self.expect_identifier("nome de membro esperado") {
                    Some(tok) => tok,
                    None => break,
                };
                let span = Span::new(expr.span.start(), ident.span.end());
                expr = Expression {
                    id: self.ids.fresh(),
                    span,
                    kind: ExpressionKind::Member {
                        target: Box::new(expr),
                        property: self.symbol_from(ident.span),
                    },
                };
                continue;
            }
            break;
        }
        expr
    }

    fn parse_argument_list(&mut self) -> Vec<Expression> {
        self.parse_list(
            TokenKind::Punctuation(Punctuation::Comma),
            TokenKind::Delimiter(Delimiter::RParen),
            true,
            "lista de argumentos",
            |parser| Some(parser.parse_expression()),
        )
    }

    fn parse_primary(&mut self) -> Expression {
        let token = self.advance();
        match token.kind {
            TokenKind::NumeroLiteral => self.number_literal(token),
            TokenKind::TextoLiteral => self.string_literal(token),
            TokenKind::Identifier => self.identifier_expr(token),
            TokenKind::Keyword(Keyword::Verum) => Expression {
                id: self.ids.fresh(),
                span: token.span,
                kind: ExpressionKind::Literal(Literal::Booleanum(true)),
            },
            TokenKind::Keyword(Keyword::Falsum) => Expression {
                id: self.ids.fresh(),
                span: token.span,
                kind: ExpressionKind::Literal(Literal::Booleanum(false)),
            },
            TokenKind::Keyword(Keyword::Nullum) => Expression {
                id: self.ids.fresh(),
                span: token.span,
                kind: ExpressionKind::Literal(Literal::Nullum),
            },
            TokenKind::Keyword(Keyword::Indefinitum) => Expression {
                id: self.ids.fresh(),
                span: token.span,
                kind: ExpressionKind::Literal(Literal::Indefinitum),
            },
            TokenKind::Delimiter(Delimiter::LParen) => {
                let expr = self.parse_expression();
                self.expect_delimiter(Delimiter::RParen, "esperado ')' após expressão");
                expr
            }
            TokenKind::Delimiter(Delimiter::LBracket) => {
                self.parse_array_literal(token.span.start())
            }
            TokenKind::Keyword(Keyword::Structura) => self.parse_object_literal(token.span.start()),
            TokenKind::Keyword(Keyword::Functio) => self.parse_lambda(token.span.start()),
            _ => {
                self.error("expressão inesperada", token.span);
                self.empty_expr_with_span(token.span)
            }
        }
    }

    fn number_literal(&mut self, token: Token) -> Expression {
        let text = &self.source[token.span.start()..token.span.end()];
        let value = text.replace('_', "").parse::<f64>().unwrap_or(0.0);
        Expression {
            id: self.ids.fresh(),
            span: token.span,
            kind: ExpressionKind::Literal(Literal::Numerus(value)),
        }
    }

    fn string_literal(&mut self, token: Token) -> Expression {
        let raw = &self.source[token.span.start() + 1..token.span.end() - 1];
        let mut chars = raw.chars();
        let mut result = String::new();
        while let Some(ch) = chars.next() {
            if ch == '\\' {
                if let Some(escape) = chars.next() {
                    match escape {
                        'n' => result.push('\n'),
                        't' => result.push('\t'),
                        'r' => result.push('\r'),
                        '"' => result.push('"'),
                        '\\' => result.push('\\'),
                        other => {
                            self.error(format!("escape desconhecido: \\{other}"), token.span);
                            result.push(other);
                        }
                    }
                }
            } else {
                result.push(ch);
            }
        }
        Expression {
            id: self.ids.fresh(),
            span: token.span,
            kind: ExpressionKind::Literal(Literal::Textus(result)),
        }
    }

    fn identifier_expr(&mut self, token: Token) -> Expression {
        Expression {
            id: self.ids.fresh(),
            span: token.span,
            kind: ExpressionKind::Identifier(self.symbol_from(token.span)),
        }
    }

    fn parse_array_literal(&mut self, start: usize) -> Expression {
        let elements = self.parse_list(
            TokenKind::Punctuation(Punctuation::Comma),
            TokenKind::Delimiter(Delimiter::RBracket),
            true,
            "literal de array",
            |parser| Some(parser.parse_expression()),
        );
        let end = self
            .expect_delimiter(Delimiter::RBracket, "esperado ']' no literal de array")
            .map(|tok| tok.span.end())
            .unwrap_or_else(|| self.previous_span().end());
        Expression {
            id: self.ids.fresh(),
            span: Span::new(start, end),
            kind: ExpressionKind::ArrayLiteral(elements),
        }
    }

    fn parse_object_literal(&mut self, start: usize) -> Expression {
        self.expect_delimiter(Delimiter::LBrace, "esperado '{' após 'structura'");
        let fields = self.parse_list(
            TokenKind::Punctuation(Punctuation::Comma),
            TokenKind::Delimiter(Delimiter::RBrace),
            true,
            "literal de objeto",
            |parser| {
                let name_tok = parser.expect_identifier("nome de campo esperado")?;
                parser.expect(
                    TokenKind::Punctuation(Punctuation::Colon),
                    "esperado ':' em literal de objeto".into(),
                )?;
                let value = parser.parse_expression();
                Some(ObjectField {
                    key: parser.symbol_from(name_tok.span),
                    value,
                })
            },
        );
        let end = self
            .expect_delimiter(Delimiter::RBrace, "esperado '}' em literal de objeto")
            .map(|tok| tok.span.end())
            .unwrap_or_else(|| self.previous_span().end());
        Expression {
            id: self.ids.fresh(),
            span: Span::new(start, end),
            kind: ExpressionKind::ObjectLiteral(fields),
        }
    }

    fn parse_lambda(&mut self, start: usize) -> Expression {
        let generics = if self.matches(TokenKind::Operator(Operator::Less)) {
            self.parse_generic_params()
        } else {
            Vec::new()
        };
        self.expect_delimiter(Delimiter::LParen, "esperado '(' em lambda");
        let params = self.parse_parameter_list();
        self.expect_delimiter(Delimiter::RParen, "esperado ')' em lambda");
        let return_type = if self.matches(TokenKind::Punctuation(Punctuation::Arrow)) {
            Some(self.parse_type_expr())
        } else {
            None
        };
        let body = if self.matches(TokenKind::Delimiter(Delimiter::LBrace)) {
            self.rewind();
            LambdaBody::Block(self.parse_block())
        } else {
            let expr = self.parse_expression();
            LambdaBody::Expression(Box::new(expr))
        };
        let end = match &body {
            LambdaBody::Block(block) => block.span.end(),
            LambdaBody::Expression(expr) => expr.span.end(),
        };
        Expression {
            id: self.ids.fresh(),
            span: Span::new(start, end),
            kind: ExpressionKind::Lambda(Box::new(LambdaExpression {
                id: self.ids.fresh(),
                span: Span::new(start, end),
                generics,
                params,
                return_type,
                body,
            })),
        }
    }

    fn parse_type_expr(&mut self) -> TypeExpr {
        let mut ty = self.parse_type_primary();
        while self.matches(TokenKind::Punctuation(Punctuation::Question)) {
            let span = Span::new(ty.span.start(), self.previous_span().end());
            ty = TypeExpr {
                id: self.ids.fresh(),
                span,
                kind: TypeExprKind::Optional(Box::new(ty)),
            };
        }
        ty
    }

    fn parse_type_primary(&mut self) -> TypeExpr {
        let start = self.peek_span().start();
        if self.matches(TokenKind::Delimiter(Delimiter::LBracket)) {
            let inner = self.parse_type_expr();
            self.expect_delimiter(Delimiter::RBracket, "esperado ']' em tipo array");
            let span = Span::new(start, self.previous_span().end());
            return TypeExpr {
                id: self.ids.fresh(),
                span,
                kind: TypeExprKind::Array(Box::new(inner)),
            };
        }
        if self.matches(TokenKind::Delimiter(Delimiter::LBrace)) {
            let fields = self.parse_list(
                TokenKind::Punctuation(Punctuation::Comma),
                TokenKind::Delimiter(Delimiter::RBrace),
                true,
                "campos de tipo de objeto",
                |parser| {
                    let name_tok = parser.expect_identifier("nome do campo de tipo esperado")?;
                    parser.expect(
                        TokenKind::Punctuation(Punctuation::Colon),
                        "esperado ':' em tipo de objeto".into(),
                    )?;
                    let ty = parser.parse_type_expr();
                    Some(TypeField {
                        name: parser.symbol_from(name_tok.span),
                        ty,
                    })
                },
            );
            self.expect_delimiter(Delimiter::RBrace, "esperado '}' em tipo de objeto");
            let span = Span::new(start, self.previous_span().end());
            return TypeExpr {
                id: self.ids.fresh(),
                span,
                kind: TypeExprKind::Object(fields),
            };
        }
        if self.matches(TokenKind::Keyword(Keyword::Functio)) {
            let generics = if self.matches(TokenKind::Operator(Operator::Less)) {
                self.parse_generic_params()
            } else {
                Vec::new()
            };
            self.expect_delimiter(Delimiter::LParen, "esperado '(' em tipo de função");
            let params = self.parse_list(
                TokenKind::Punctuation(Punctuation::Comma),
                TokenKind::Delimiter(Delimiter::RParen),
                true,
                "parâmetros de tipo de função",
                |parser| Some(parser.parse_type_expr()),
            );
            self.expect_delimiter(Delimiter::RParen, "esperado ')' em tipo de função");
            self.expect(
                TokenKind::Punctuation(Punctuation::Arrow),
                "esperado '->' em tipo de função".into(),
            );
            let ret = self.parse_type_expr();
            let span = Span::new(start, self.previous_span().end());
            return TypeExpr {
                id: self.ids.fresh(),
                span,
                kind: TypeExprKind::Function {
                    generics,
                    params,
                    ret: Box::new(ret),
                },
            };
        }
        if let Some(simple) = self.parse_simple_type() {
            return simple;
        }
        self.error("tipo inválido", self.peek_span());
        TypeExpr {
            id: self.ids.fresh(),
            span: Span::new(start, start),
            kind: TypeExprKind::Simple(self.symbol_from(Span::new(start, start))),
        }
    }
    fn expect(&mut self, expected: TokenKind, message: String) -> Option<Token> {
        if self.check(expected.clone()) {
            Some(self.advance())
        } else {
            self.error(message, self.peek_span());
            None
        }
    }

    fn expect_identifier(&mut self, message: &str) -> Option<Token> {
        if self.check(TokenKind::Identifier) {
            Some(self.advance())
        } else {
            self.error(message, self.peek_span());
            None
        }
    }

    fn expect_keyword(&mut self, keyword: Keyword, message: &str) -> Option<Token> {
        if self.check(TokenKind::Keyword(keyword)) {
            Some(self.advance())
        } else {
            self.error(message, self.peek_span());
            None
        }
    }

    fn expect_delimiter(&mut self, delim: Delimiter, message: &str) -> Option<Token> {
        if self.check(TokenKind::Delimiter(delim)) {
            Some(self.advance())
        } else {
            self.error(message, self.peek_span());
            None
        }
    }

    fn advance(&mut self) -> Token {
        if self.pos >= self.tokens.len() {
            return *self.tokens.last().expect("lista de tokens vazia");
        }
        if self.fuel == 0 {
            let span = self.peek_span();
            self.error("parser paralisado: combustível esgotado", span);
        } else {
            self.fuel -= 1;
        }
        let token = self.tokens[self.pos];
        self.pos = (self.pos + 1).min(self.tokens.len());
        token
    }

    fn rewind(&mut self) {
        if self.pos > 0 {
            self.pos -= 1;
        }
    }

    fn guard_progress(&mut self, before: usize, context: &str) -> bool {
        if self.pos == before {
            let span = self.peek_span();
            self.error(format!("nenhum progresso ao analisar {}", context), span);
            if !self.is_at_end() {
                self.advance();
            }
            false
        } else {
            true
        }
    }

    fn parse_list<T, F>(
        &mut self,
        separator: TokenKind,
        terminator: TokenKind,
        allow_trailing: bool,
        context: &str,
        mut parse_element: F,
    ) -> Vec<T>
    where
        F: FnMut(&mut Parser<'src>) -> Option<T>,
    {
        let mut items = Vec::new();
        while !self.check(terminator.clone()) && !self.is_at_end() {
            let before = self.pos;
            let mut progressed = false;
            if let Some(item) = parse_element(self) {
                items.push(item);
                progressed = true;
            }
            if !self.guard_progress(before, context) {
                break;
            }
            if !progressed {
                break;
            }
            if self.matches(separator.clone()) {
                if allow_trailing && self.check(terminator.clone()) {
                    break;
                }
                continue;
            }
            break;
        }
        items
    }
    fn parse_simple_type(&mut self) -> Option<TypeExpr> {
        let token = self.peek_token()?;
        let keyword_ty = matches!(
            token.kind,
            TokenKind::Keyword(Keyword::Numerus)
                | TokenKind::Keyword(Keyword::Textus)
                | TokenKind::Keyword(Keyword::Booleanum)
                | TokenKind::Keyword(Keyword::Nullum)
                | TokenKind::Keyword(Keyword::Indefinitum)
                | TokenKind::Keyword(Keyword::Vacuum)
                | TokenKind::Keyword(Keyword::Quodlibet)
        );
        if token.kind == TokenKind::Identifier || keyword_ty {
            let tok = self.advance();
            return Some(TypeExpr {
                id: self.ids.fresh(),
                span: tok.span,
                kind: TypeExprKind::Simple(self.symbol_from(tok.span)),
            });
        }
        None
    }

    fn peek_is_type_keyword(&self) -> bool {
        matches!(
            self.peek_token().map(|tok| tok.kind),
            Some(
                TokenKind::Keyword(Keyword::Numerus)
                    | TokenKind::Keyword(Keyword::Textus)
                    | TokenKind::Keyword(Keyword::Booleanum)
                    | TokenKind::Keyword(Keyword::Nullum)
                    | TokenKind::Keyword(Keyword::Indefinitum)
                    | TokenKind::Keyword(Keyword::Vacuum)
                    | TokenKind::Keyword(Keyword::Quodlibet)
            )
        )
    }

    fn matches(&mut self, kind: TokenKind) -> bool {
        if self.check(kind.clone()) {
            self.advance();
            true
        } else {
            false
        }
    }

    fn check(&self, kind: TokenKind) -> bool {
        self.peek_token().map_or(false, |token| token.kind == kind)
    }

    fn previous_kind(&self) -> Option<TokenKind> {
        if self.pos == 0 {
            None
        } else {
            Some(self.tokens[self.pos - 1].kind)
        }
    }

    fn previous_span(&self) -> Span {
        if self.pos == 0 {
            Span::new(0, 0)
        } else {
            self.tokens[self.pos - 1].span
        }
    }

    fn peek_token(&self) -> Option<Token> {
        self.tokens.get(self.pos).copied()
    }

    fn peek_span(&self) -> Span {
        self.peek_token()
            .map(|token| token.span)
            .unwrap_or_else(|| Span::new(self.source.len(), self.source.len()))
    }

    fn current_span(&self) -> Option<Span> {
        self.tokens.get(self.pos).map(|token| token.span)
    }

    fn is_at_end(&self) -> bool {
        matches!(
            self.peek_token().map(|tok| tok.kind),
            Some(TokenKind::EOF) | None
        )
    }

    fn consume_semicolon(&mut self, message: &str) {
        if !self.matches(TokenKind::Punctuation(Punctuation::Semicolon)) {
            self.error(message, self.peek_span());
        }
    }

    fn check_statement_end(&self) -> bool {
        matches!(
            self.peek_token().map(|tok| tok.kind),
            Some(TokenKind::Punctuation(Punctuation::Semicolon))
                | Some(TokenKind::Delimiter(Delimiter::RBrace))
        )
    }

    fn synchronize(&mut self, kinds: &[TokenKind]) {
        while !self.is_at_end() {
            if kinds.iter().any(|kind| self.check(kind.clone())) {
                return;
            }
            self.advance();
        }
    }

    fn error(&mut self, message: impl Into<String>, span: Span) {
        self.errors.push(ParseError::new(message, span));
    }

    fn empty_expr(&mut self) -> Expression {
        self.empty_expr_with_span(Span::new(self.source.len(), self.source.len()))
    }

    fn empty_expr_with_span(&mut self, span: Span) -> Expression {
        Expression {
            id: self.ids.fresh(),
            span,
            kind: ExpressionKind::Literal(Literal::Nullum),
        }
    }

    fn symbol_from(&mut self, span: Span) -> Symbol {
        let text = &self.source[span.start()..span.end()];
        self.interner.intern(text)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_simple_function() {
        let source = "functio add(numerus a, numerus b) -> numerus { redde a + b; }";
        let output = parse_module(source).expect("parse");
        assert!(output.diagnostics.is_empty());
        assert_eq!(output.module.items.len(), 1);
    }

    #[test]
    fn parse_dangling_else() {
        let source = "functio f() { si verum si falsum redde 1; aliter redde 2; aliter redde 3; }";
        let output = parse_module(source).expect("parse");
        assert!(output.diagnostics.is_empty());
    }
}
