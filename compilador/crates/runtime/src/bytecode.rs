use thiserror::Error;

/// Bytecode carregado na memória.
#[derive(Debug, Clone)]
pub struct Chunk {
    pub functions: Vec<FunctionChunk>,
}

#[derive(Debug, Clone)]
pub struct FunctionChunk {
    pub name: u32,
    pub arity: u8,
    pub instructions: Vec<Instruction>,
}

/// Instruções interpretadas pela VM.
#[derive(Debug, Clone, Copy)]
pub enum Instruction {
    Const(f64),
    LoadLocal(u16),
    StoreLocal(u16),
    Add,
    Sub,
    Mul,
    Div,
    CmpEq,
    CmpNe,
    CmpLt,
    CmpLe,
    CmpGt,
    CmpGe,
    Jump(usize),
    JumpIfFalse(usize),
    Call { function: u32, args: u8 },
    Return,
}

#[derive(Debug, Error)]
pub enum BytecodeError {
    #[error("formato inválido do bytecode")]
    InvalidFormat,
    #[error("dados insuficientes")]
    UnexpectedEof,
}

impl Chunk {
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, BytecodeError> {
        if bytes.len() < 8 || &bytes[..4] != b"SBC0" {
            return Err(BytecodeError::InvalidFormat);
        }
        let mut offset = 4;
        let count = read_u32(bytes, &mut offset)? as usize;
        let mut functions = Vec::with_capacity(count);
        for _ in 0..count {
            functions.push(read_function(bytes, &mut offset)?);
        }
        Ok(Self { functions })
    }
}

fn read_function(bytes: &[u8], offset: &mut usize) -> Result<FunctionChunk, BytecodeError> {
    let name = read_u32(bytes, offset)?;
    let arity = read_u8(bytes, offset)?;
    let len = read_u32(bytes, offset)? as usize;
    let mut instructions = Vec::with_capacity(len);
    for _ in 0..len {
        instructions.push(read_instruction(bytes, offset)?);
    }
    Ok(FunctionChunk {
        name,
        arity,
        instructions,
    })
}

fn read_instruction(bytes: &[u8], offset: &mut usize) -> Result<Instruction, BytecodeError> {
    let opcode = read_u8(bytes, offset)?;
    Ok(match opcode {
        0x01 => Instruction::Const(read_f64(bytes, offset)?),
        0x02 => Instruction::LoadLocal(read_u16(bytes, offset)?),
        0x03 => Instruction::StoreLocal(read_u16(bytes, offset)?),
        0x10 => Instruction::Add,
        0x11 => Instruction::Sub,
        0x12 => Instruction::Mul,
        0x13 => Instruction::Div,
        0x20 => Instruction::CmpEq,
        0x21 => Instruction::CmpNe,
        0x22 => Instruction::CmpLt,
        0x23 => Instruction::CmpLe,
        0x24 => Instruction::CmpGt,
        0x25 => Instruction::CmpGe,
        0x30 => Instruction::Jump(read_u32(bytes, offset)? as usize),
        0x31 => Instruction::JumpIfFalse(read_u32(bytes, offset)? as usize),
        0x40 => Instruction::Call {
            function: read_u32(bytes, offset)?,
            args: read_u8(bytes, offset)?,
        },
        0x50 => Instruction::Return,
        _ => return Err(BytecodeError::InvalidFormat),
    })
}

fn read_u8(bytes: &[u8], offset: &mut usize) -> Result<u8, BytecodeError> {
    if *offset >= bytes.len() {
        return Err(BytecodeError::UnexpectedEof);
    }
    let value = bytes[*offset];
    *offset += 1;
    Ok(value)
}

fn read_u16(bytes: &[u8], offset: &mut usize) -> Result<u16, BytecodeError> {
    if *offset + 2 > bytes.len() {
        return Err(BytecodeError::UnexpectedEof);
    }
    let value = u16::from_le_bytes(bytes[*offset..*offset + 2].try_into().unwrap());
    *offset += 2;
    Ok(value)
}

fn read_u32(bytes: &[u8], offset: &mut usize) -> Result<u32, BytecodeError> {
    if *offset + 4 > bytes.len() {
        return Err(BytecodeError::UnexpectedEof);
    }
    let value = u32::from_le_bytes(bytes[*offset..*offset + 4].try_into().unwrap());
    *offset += 4;
    Ok(value)
}

fn read_f64(bytes: &[u8], offset: &mut usize) -> Result<f64, BytecodeError> {
    if *offset + 8 > bytes.len() {
        return Err(BytecodeError::UnexpectedEof);
    }
    let value = f64::from_le_bytes(bytes[*offset..*offset + 8].try_into().unwrap());
    *offset += 8;
    Ok(value)
}
