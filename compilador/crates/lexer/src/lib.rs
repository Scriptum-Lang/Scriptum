#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Lexer de alto desempenho para Scriptum (.stm).

mod dfa;
pub mod keywords;
pub mod lexer;
pub mod operators;
pub mod tokens;

pub use lexer::{lex, Lexer};
pub use tokens::{Token, TokenKind};
