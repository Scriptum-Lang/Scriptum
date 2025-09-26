#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Runtime/VM simples para bytecode Scriptum.

pub mod bytecode;
pub mod loader;
pub mod vm;

pub use bytecode::{Chunk, Instruction};
pub use loader::load_module;
pub use vm::{ExecutionResult, VirtualMachine};
