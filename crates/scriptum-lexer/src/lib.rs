#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Lexer oficial da linguagem Scriptum.

mod keywords;
mod lexer;
pub mod tokens;

pub use lexer::{lex, LexError, LexResult, Lexer};
