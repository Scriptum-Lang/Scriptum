use std::iter::Peekable;
use std::str::CharIndices;

use thiserror::Error;

use scriptum_utils::Span;

use crate::keywords::KEYWORDS;
use crate::tokens::{Delimiter, Keyword, Operator, Punctuation, Token, TokenKind};

/// Resultado da análise léxica.
pub type LexResult<T> = Result<T, LexError>;

/// Erros produzidos pelo lexer.
#[derive(Debug, Error)]
#[error("{message}")]
pub struct LexError {
    pub message: String,
    pub span: Span,
}

impl LexError {
    fn new(message: impl Into<String>, span: Span) -> Self {
        Self {
            message: message.into(),
            span,
        }
    }
}

/// Lexer baseado em DFA manual simples.
pub struct Lexer<'a> {
    source: &'a str,
    chars: Peekable<CharIndices<'a>>,
    current: usize,
    tokens: Vec<Token>,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self {
            source,
            chars: source.char_indices().peekable(),
            current: 0,
            tokens: Vec::new(),
        }
    }

    pub fn run(mut self) -> LexResult<Vec<Token>> {
        while let Some((idx, ch)) = self.bump() {
            if ch.is_whitespace() {
                self.skip_whitespace(idx, ch);
                continue;
            }
            if ch == '/' {
                if self.consume_comment(idx)? {
                    continue;
                }
            }
            match ch {
                'a'..='z' | 'A'..='Z' | '_' => self.lex_identifier(idx, ch)?,
                '0'..='9' => self.lex_number(idx, ch)?,
                '"' => self.lex_string(idx)?,
                '(' => self.push_token(
                    TokenKind::Delimiter(Delimiter::LParen),
                    idx,
                    idx + ch.len_utf8(),
                ),
                ')' => self.push_token(
                    TokenKind::Delimiter(Delimiter::RParen),
                    idx,
                    idx + ch.len_utf8(),
                ),
                '{' => self.push_token(
                    TokenKind::Delimiter(Delimiter::LBrace),
                    idx,
                    idx + ch.len_utf8(),
                ),
                '}' => self.push_token(
                    TokenKind::Delimiter(Delimiter::RBrace),
                    idx,
                    idx + ch.len_utf8(),
                ),
                '[' => self.push_token(
                    TokenKind::Delimiter(Delimiter::LBracket),
                    idx,
                    idx + ch.len_utf8(),
                ),
                ']' => self.push_token(
                    TokenKind::Delimiter(Delimiter::RBracket),
                    idx,
                    idx + ch.len_utf8(),
                ),
                ',' => self.push_token(
                    TokenKind::Punctuation(Punctuation::Comma),
                    idx,
                    idx + ch.len_utf8(),
                ),
                ';' => self.push_token(
                    TokenKind::Punctuation(Punctuation::Semicolon),
                    idx,
                    idx + ch.len_utf8(),
                ),
                ':' => {
                    if self.peek_match('=') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::Assign), idx, end);
                    } else if self.peek_match(':') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Punctuation(Punctuation::DoubleColon), idx, end);
                    } else {
                        self.push_token(TokenKind::Punctuation(Punctuation::Colon), idx, idx + 1);
                    }
                }
                '?' => {
                    if self.peek_match('?') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::NullishCoalesce), idx, end);
                    } else if self.peek_match('.') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::QuestionDot), idx, end);
                    } else {
                        self.push_token(
                            TokenKind::Punctuation(Punctuation::Question),
                            idx,
                            idx + 1,
                        );
                    }
                }
                '.' => self.push_token(TokenKind::Punctuation(Punctuation::Dot), idx, idx + 1),
                '-' => {
                    if self.peek_match('>') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Punctuation(Punctuation::Arrow), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Sub), idx, idx + 1);
                    }
                }
                '=' => {
                    if self.peek_match('=') {
                        let after = self.bump().unwrap().0 + 1;
                        if self.peek_match('=') {
                            let end = self.bump().unwrap().0 + 1;
                            self.push_token(TokenKind::Operator(Operator::StrictEqual), idx, end);
                        } else {
                            self.push_token(TokenKind::Operator(Operator::Equal), idx, after);
                        }
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Assign), idx, idx + 1);
                    }
                }
                '!' => {
                    if self.peek_match('=') {
                        let after = self.bump().unwrap().0 + 1;
                        if self.peek_match('=') {
                            let end = self.bump().unwrap().0 + 1;
                            self.push_token(
                                TokenKind::Operator(Operator::StrictNotEqual),
                                idx,
                                end,
                            );
                        } else {
                            self.push_token(TokenKind::Operator(Operator::NotEqual), idx, after);
                        }
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Not), idx, idx + 1);
                    }
                }
                '+' => self.push_token(TokenKind::Operator(Operator::Add), idx, idx + 1),
                '*' => {
                    if self.peek_match('*') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::Pow), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Mul), idx, idx + 1);
                    }
                }
                '/' => self.push_token(TokenKind::Operator(Operator::Div), idx, idx + 1),
                '%' => self.push_token(TokenKind::Operator(Operator::Mod), idx, idx + 1),
                '&' => {
                    if self.peek_match('&') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::AndAnd), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::BitAnd), idx, idx + 1);
                    }
                }
                '|' => {
                    if self.peek_match('|') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::OrOr), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::BitOr), idx, idx + 1);
                    }
                }
                '^' => self.push_token(TokenKind::Operator(Operator::BitXor), idx, idx + 1),
                '<' => {
                    if self.peek_match('<') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::ShiftLeft), idx, end);
                    } else if self.peek_match('=') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::LessEqual), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Less), idx, idx + 1);
                    }
                }
                '>' => {
                    if self.peek_match('>') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::ShiftRight), idx, end);
                    } else if self.peek_match('=') {
                        let end = self.bump().unwrap().0 + 1;
                        self.push_token(TokenKind::Operator(Operator::GreaterEqual), idx, end);
                    } else {
                        self.push_token(TokenKind::Operator(Operator::Greater), idx, idx + 1);
                    }
                }
                _ => {
                    return Err(LexError::new(
                        format!("caractere inválido: {ch:?}"),
                        Span::new(idx, idx + ch.len_utf8()),
                    ));
                }
            }
        }

        let eof_span = Span::new(self.source.len(), self.source.len());
        self.tokens.push(Token::new(TokenKind::EOF, eof_span));
        Ok(self.tokens)
    }

    fn bump(&mut self) -> Option<(usize, char)> {
        if let Some(&(idx, ch)) = self.chars.peek() {
            self.chars.next();
            self.current = idx + ch.len_utf8();
            Some((idx, ch))
        } else {
            None
        }
    }

    fn peek(&mut self) -> Option<char> {
        self.chars.peek().map(|(_, ch)| *ch)
    }

    fn peek_match(&mut self, expected: char) -> bool {
        match self.chars.peek() {
            Some(&(_, ch)) if ch == expected => true,
            _ => false,
        }
    }

    fn push_token(&mut self, kind: TokenKind, start: usize, end: usize) {
        self.tokens.push(Token::new(kind, Span::new(start, end)));
    }

    fn skip_whitespace(&mut self, idx: usize, first: char) {
        let mut last = idx + first.len_utf8();
        while let Some(&(next_idx, ch)) = self.chars.peek() {
            if ch.is_whitespace() {
                self.chars.next();
                last = next_idx + ch.len_utf8();
            } else {
                break;
            }
        }
        self.current = last;
    }

    fn consume_comment(&mut self, start_idx: usize) -> LexResult<bool> {
        if self.peek_match('/') {
            self.chars.next();
            while let Some(&(idx, ch)) = self.chars.peek() {
                if ch == '\n' {
                    self.current = idx;
                    break;
                }
                self.chars.next();
            }
            Ok(true)
        } else if self.peek_match('*') {
            self.chars.next();
            while let Some((idx, ch)) = self.bump() {
                if ch == '*' && self.peek_match('/') {
                    let end = self.bump().unwrap().0 + 1;
                    self.current = end;
                    return Ok(true);
                }
            }
            Err(LexError::new(
                "comentário multiline não finalizado",
                Span::new(start_idx, self.source.len()),
            ))
        } else {
            // Não era comentário; trate como operador.
            self.push_token(TokenKind::Operator(Operator::Div), start_idx, start_idx + 1);
            Ok(true)
        }
    }

    fn lex_identifier(&mut self, start_idx: usize, first: char) -> LexResult<()> {
        let mut end = start_idx + first.len_utf8();
        while let Some(&(idx, ch)) = self.chars.peek() {
            if is_ident_continue(ch) {
                self.chars.next();
                end = idx + ch.len_utf8();
            } else {
                break;
            }
        }
        end = end.max(start_idx + first.len_utf8());
        let text = &self.source[start_idx..end];
        if let Some(keyword) = KEYWORDS.get(text) {
            self.tokens.push(Token::new(
                TokenKind::Keyword(*keyword),
                Span::new(start_idx, end),
            ));
        } else {
            self.tokens
                .push(Token::new(TokenKind::Identifier, Span::new(start_idx, end)));
        }
        Ok(())
    }

    fn lex_number(&mut self, start_idx: usize, first: char) -> LexResult<()> {
        let mut end = start_idx + first.len_utf8();
        while let Some(&(idx, ch)) = self.chars.peek() {
            if ch.is_ascii_digit() || ch == '_' {
                self.chars.next();
                end = idx + ch.len_utf8();
            } else {
                break;
            }
        }
        if self.peek_match('.') {
            self.chars.next();
            end += 1;
            while let Some(&(idx, ch)) = self.chars.peek() {
                if ch.is_ascii_digit() || ch == '_' {
                    self.chars.next();
                    end = idx + ch.len_utf8();
                } else {
                    break;
                }
            }
        }
        if let Some(&(_, ch)) = self.chars.peek() {
            if ch == 'e' || ch == 'E' {
                self.chars.next();
                end += 1;
                if let Some(&(_, sign)) = self.chars.peek() {
                    if sign == '+' || sign == '-' {
                        self.chars.next();
                        end += 1;
                    }
                }
                let mut has_digit = false;
                while let Some(&(idx, ch)) = self.chars.peek() {
                    if ch.is_ascii_digit() {
                        self.chars.next();
                        end = idx + ch.len_utf8();
                        has_digit = true;
                    } else {
                        break;
                    }
                }
                if !has_digit {
                    return Err(LexError::new(
                        "expoente sem dígitos",
                        Span::new(start_idx, end),
                    ));
                }
            }
        }
        end = end.max(start_idx + first.len_utf8());
        self.tokens.push(Token::new(
            TokenKind::NumeroLiteral,
            Span::new(start_idx, end),
        ));
        Ok(())
    }

    fn lex_string(&mut self, start_idx: usize) -> LexResult<()> {
        let mut escaped = false;
        let mut end = start_idx + 1;
        while let Some((idx, ch)) = self.bump() {
            end = idx + ch.len_utf8();
            if escaped {
                escaped = false;
                continue;
            }
            match ch {
                '\\' => escaped = true,
                '"' => {
                    end += 0; // já inclui o caractere atual
                    self.tokens.push(Token::new(
                        TokenKind::TextoLiteral,
                        Span::new(start_idx, end),
                    ));
                    return Ok(());
                }
                _ => {}
            }
        }
        Err(LexError::new(
            "string não finalizada",
            Span::new(start_idx, self.source.len()),
        ))
    }
}

fn is_ident_continue(ch: char) -> bool {
    ch.is_ascii_alphanumeric() || ch == '_' || ch == '$'
}

/// Executa o lexer e retorna os tokens.
pub fn lex(source: &str) -> LexResult<Vec<Token>> {
    Lexer::new(source).run()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn token_kinds(source: &str) -> Vec<TokenKind> {
        lex(source)
            .expect("lex bem-sucedido")
            .into_iter()
            .map(|token| token.kind)
            .collect()
    }

    #[test]
    fn lex_identifiers() {
        let kinds = token_kinds("mutabilis foo_bar ident123");
        assert_eq!(kinds[0], TokenKind::Keyword(Keyword::Mutabilis));
        assert_eq!(kinds[1], TokenKind::Identifier);
        assert_eq!(kinds[2], TokenKind::Identifier);
    }

    #[test]
    fn lex_numbers_with_exponent() {
        let tokens = lex("42 3.14 2.5e+10 1e-3").expect("ok");
        assert_eq!(
            tokens
                .iter()
                .filter(|t| t.kind == TokenKind::NumeroLiteral)
                .count(),
            4
        );
    }

    #[test]
    fn lex_strings_with_escapes() {
        let tokens = lex("\"ola\\nmundus\"").expect("ok");
        assert_eq!(tokens[0].kind, TokenKind::TextoLiteral);
    }
}
