#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Geração de código Scriptum para bytecode simples.

pub mod emit;
pub mod ir;
pub mod lowering;
pub mod optimizer;

pub use emit::emit_module;
pub use ir::{FunctionIr, Instruction, ModuleIr, Operand};
pub use lowering::lower_module;
pub use optimizer::optimize_module;
