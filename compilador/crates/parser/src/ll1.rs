use std::sync::Arc;

use scriptum_lexer::{Token, TokenKind};
use scriptum_utils::Span;

use crate::ast_builder::ParseError;

/// Stream de tokens com suporte a lookahead de 1 símbolo.
#[derive(Clone)]
pub struct TokenStream {
    tokens: Arc<[Token]>,
    position: usize,
}

impl TokenStream {
    pub fn new(tokens: Arc<[Token]>) -> Self {
        Self {
            tokens,
            position: 0,
        }
    }

    pub fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.position)
    }

    pub fn next(&mut self) -> Option<Token> {
        let tok = self.tokens.get(self.position).copied();
        if tok.is_some() {
            self.position += 1;
        }
        tok
    }

    pub fn peek_kind(&self) -> Option<TokenKind> {
        self.peek().map(|t| t.kind)
    }

    pub fn peek_next_kind(&self) -> Option<TokenKind> {
        self.tokens.get(self.position + 1).map(|t| t.kind)
    }

    pub fn expect(&mut self, expected: TokenKind) -> Result<Span, ParseError> {
        let token = self
            .next()
            .ok_or_else(|| ParseError::new("fim inesperado de input", Span::default()))?;
        if token.kind == expected {
            Ok(token.span)
        } else {
            Err(ParseError::new(
                format!("esperado {:?}, encontrado {:?}", expected, token.kind),
                token.span,
            ))
        }
    }

    pub fn position(&self) -> usize {
        self.position
    }

    pub fn tokens(&self) -> Arc<[Token]> {
        self.tokens.clone()
    }
}
