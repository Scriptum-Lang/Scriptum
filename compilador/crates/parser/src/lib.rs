#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Parser LL(1) para Scriptum.

pub mod ast_builder;
pub mod grammar;
pub mod ll1;

pub use ast_builder::{parse_module, Parser};
