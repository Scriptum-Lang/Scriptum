use std::fs;
use std::path::Path;

use crate::bytecode::{BytecodeError, Chunk};

/// Carrega um módulo `.sbc` do disco.
pub fn load_module(path: impl AsRef<Path>) -> Result<Chunk, BytecodeError> {
    let bytes = fs::read(path).map_err(|_| BytecodeError::InvalidFormat)?;
    Chunk::from_bytes(&bytes)
}
