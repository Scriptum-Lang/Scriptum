#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Utilidades compartilhadas entre as crates do compilador Scriptum.

pub mod diagnostics;
pub mod errors;
pub mod source_map;
pub mod span;

pub use diagnostics::{Diagnostic, DiagnosticBuilder};
pub use errors::{Error, ErrorKind, Result};
pub use source_map::{SourceFile, SourceMap};
pub use span::Span;
