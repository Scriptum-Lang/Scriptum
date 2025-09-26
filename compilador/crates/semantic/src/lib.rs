#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Analisador semântico da linguagem Scriptum.

pub mod semantic_pass;
pub mod symbol_table;
pub mod type_system;

pub use semantic_pass::{analyze_module, SemanticError};
