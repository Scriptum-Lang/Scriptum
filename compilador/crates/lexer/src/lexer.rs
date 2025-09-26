use crate::dfa::{identifier_end, number_end, skip_ignorable};
use crate::keywords::lookup_keyword;
use crate::operators::match_operator;
use crate::tokens::{KeywordKind, OperatorKind, Token, TokenKind};
use scriptum_utils::Span;
use thiserror::Error;

/// Erro emitido pelo lexer.
#[derive(Debug, Error)]
#[error("erro léxico: {message}")]
pub struct LexError {
    pub message: String,
    pub span: Span,
}

/// Lexer streaming sem alocação no fast-path.
pub struct Lexer<'a> {
    source: &'a str,
    offset: usize,
    finished: bool,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self {
            source,
            offset: 0,
            finished: false,
        }
    }

    fn bump(&mut self, amount: usize) {
        self.offset += amount;
    }

    fn remaining(&self) -> &'a str {
        &self.source[self.offset..]
    }

    fn make_span(&self, start: usize, end: usize) -> Span {
        Span::new(start, end)
    }

    fn read_number(&mut self) -> Result<Token, LexError> {
        let rest = self.remaining();
        let len = number_end(rest);
        let span = self.make_span(self.offset, self.offset + len);
        let literal = &rest[..len];
        if literal.is_empty() {
            return Err(LexError {
                message: "número inválido".into(),
                span,
            });
        }
        self.bump(len);
        Ok(Token::new(TokenKind::Number, span))
    }

    fn read_identifier(&mut self) -> Token {
        let rest = self.remaining();
        let len = identifier_end(rest);
        let span = self.make_span(self.offset, self.offset + len);
        let lexeme = &rest[..len];
        self.bump(len);
        if let Some(kind) = lookup_keyword(lexeme) {
            match kind {
                TokenKind::Keyword(KeywordKind::Verum) => return Token::new(TokenKind::Bool, span),
                TokenKind::Keyword(KeywordKind::Falsum) => {
                    return Token::new(TokenKind::Bool, span)
                }
                _ => return Token::new(kind, span),
            }
        }
        Token::new(TokenKind::Identifier, span)
    }

    fn read_operator(&mut self) -> Result<Token, LexError> {
        let rest = self.remaining();
        let candidates = [2usize, 1usize];
        for len in candidates {
            if rest.len() >= len {
                let slice = &rest[..len];
                if let Some(op) = match_operator(slice) {
                    let span = self.make_span(self.offset, self.offset + len);
                    self.bump(len);
                    return Ok(Token::new(TokenKind::Operator(op), span));
                }
            }
        }
        Err(LexError {
            message: "operador desconhecido".into(),
            span: self.make_span(self.offset, self.offset + 1),
        })
    }

    fn read_punct(&mut self, kind: TokenKind, len: usize) -> Token {
        let span = self.make_span(self.offset, self.offset + len);
        self.bump(len);
        Token::new(kind, span)
    }
}

impl<'a> Iterator for Lexer<'a> {
    type Item = Result<Token, LexError>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.finished {
            return None;
        }

        let rest = self.remaining();
        if rest.is_empty() {
            self.finished = true;
            let span = self.make_span(self.offset, self.offset);
            return Some(Ok(Token::new(TokenKind::EOF, span)));
        }

        let skipped = skip_ignorable(rest);
        if skipped > 0 {
            self.bump(skipped);
            return self.next();
        }

        let rest = self.remaining();
        let first = rest.as_bytes()[0];
        let token = match first {
            b'a'..=b'z' | b'A'..=b'Z' | b'_' => Ok(self.read_identifier()),
            b'0'..=b'9' => self.read_number(),
            b'(' => Ok(self.read_punct(TokenKind::LParen, 1)),
            b')' => Ok(self.read_punct(TokenKind::RParen, 1)),
            b'{' => Ok(self.read_punct(TokenKind::LBrace, 1)),
            b'}' => Ok(self.read_punct(TokenKind::RBrace, 1)),
            b';' => Ok(self.read_punct(TokenKind::Semicolon, 1)),
            b',' => Ok(self.read_punct(TokenKind::Comma, 1)),
            b'=' | b'!' | b'<' | b'>' | b'+' | b'-' | b'*' | b'/' => self.read_operator(),
            _ => {
                let span = self.make_span(self.offset, self.offset + 1);
                self.bump(1);
                Err(LexError {
                    message: format!("caractere inesperado: {}", first as char),
                    span,
                })
            }
        };

        Some(token)
    }
}

/// Realiza a tokenização completa em memória.
pub fn lex(source: &str) -> Result<Vec<Token>, LexError> {
    let mut tokens = Vec::new();
    let mut lexer = Lexer::new(source);
    while let Some(token) = lexer.next() {
        let token = token?;
        tokens.push(token);
        if token.kind == TokenKind::EOF {
            break;
        }
    }
    Ok(tokens)
}
