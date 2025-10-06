use serde::{Deserialize, Serialize};

use scriptum_utils::Span;

/// Tokens reconhecidos pelo lexer de Scriptum.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Token {
    pub kind: TokenKind,
    pub span: Span,
}

impl Token {
    pub fn new(kind: TokenKind, span: Span) -> Self {
        Self { kind, span }
    }
}

/// Tipos de token.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenKind {
    Identifier,
    NumeroLiteral,
    TextoLiteral,
    Keyword(Keyword),
    Operator(Operator),
    Delimiter(Delimiter),
    Punctuation(Punctuation),
    EOF,
}

/// Palavras-chave reservadas (latim!).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Keyword {
    Mutabilis,
    Constans,
    Functio,
    Structura,
    Si,
    Aliter,
    Dum,
    Pro,
    In,
    De,
    Redde,
    Frange,
    Perge,
    Verum,
    Falsum,
    Nullum,
    Indefinitum,
    Numerus,
    Textus,
    Booleanum,
    Vacuum,
    Quodlibet,
}

/// Delimitadores balanceados.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Delimiter {
    LParen,
    RParen,
    LBrace,
    RBrace,
    LBracket,
    RBracket,
}

/// Pontuação simples.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Punctuation {
    Colon,
    DoubleColon,
    Comma,
    Semicolon,
    Dot,
    Arrow,
    FatArrow,
    Question,
}

/// Operadores compostos.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Operator {
    Assign,
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Pow,
    BitAnd,
    BitOr,
    BitXor,
    ShiftLeft,
    ShiftRight,
    Equal,
    StrictEqual,
    NotEqual,
    StrictNotEqual,
    Greater,
    GreaterEqual,
    Less,
    LessEqual,
    NullishCoalesce,
    AndAnd,
    OrOr,
    QuestionDot,
    Not,
}
