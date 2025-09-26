use serde::{Deserialize, Serialize};

use scriptum_utils::Span;

/// Tipos de token suportados pela linguagem Scriptum.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenKind {
    Identifier,
    Number,
    Bool,
    Keyword(KeywordKind),
    Operator(OperatorKind),
    Comma,
    Semicolon,
    LParen,
    RParen,
    LBrace,
    RBrace,
    EOF,
}

/// Palavras-chave reconhecidas.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum KeywordKind {
    Definire,
    Finis,
    Si,
    Alioqui,
    Dum,
    Verum,
    Falsum,
    Reditus,
}

/// Operadores.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OperatorKind {
    Assign,
    Plus,
    Minus,
    Star,
    Slash,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

/// Token com span.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Token {
    pub kind: TokenKind,
    pub span: Span,
}

impl Token {
    pub fn new(kind: TokenKind, span: Span) -> Self {
        Self { kind, span }
    }
}
