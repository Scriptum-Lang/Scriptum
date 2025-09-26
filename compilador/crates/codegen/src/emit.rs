use crate::ir::{FunctionIr, Instruction, ModuleIr};

/// Serializa o IR em bytecode Scriptum (`.sbc`).
pub fn emit_module(module: &ModuleIr) -> Vec<u8> {
    let mut bytes = Vec::new();
    bytes.extend_from_slice(b"SBC0");
    bytes.extend_from_slice(&(module.functions.len() as u32).to_le_bytes());
    for function in &module.functions {
        emit_function(function, &mut bytes);
    }
    bytes
}

fn emit_function(function: &FunctionIr, out: &mut Vec<u8>) {
    out.extend_from_slice(&function.name.as_u32().to_le_bytes());
    out.push(function.arity);
    out.extend_from_slice(&(function.instructions.len() as u32).to_le_bytes());
    for instr in &function.instructions {
        emit_instruction(instr, out);
    }
}

fn emit_instruction(instr: &Instruction, out: &mut Vec<u8>) {
    match instr {
        Instruction::Const(value) => {
            out.push(0x01);
            out.extend_from_slice(&value.to_le_bytes());
        }
        Instruction::LoadLocal(idx) => {
            out.push(0x02);
            out.extend_from_slice(&idx.to_le_bytes());
        }
        Instruction::StoreLocal(idx) => {
            out.push(0x03);
            out.extend_from_slice(&idx.to_le_bytes());
        }
        Instruction::Add => out.push(0x10),
        Instruction::Sub => out.push(0x11),
        Instruction::Mul => out.push(0x12),
        Instruction::Div => out.push(0x13),
        Instruction::CmpEq => out.push(0x20),
        Instruction::CmpNe => out.push(0x21),
        Instruction::CmpLt => out.push(0x22),
        Instruction::CmpLe => out.push(0x23),
        Instruction::CmpGt => out.push(0x24),
        Instruction::CmpGe => out.push(0x25),
        Instruction::Jump(target) => {
            out.push(0x30);
            out.extend_from_slice(&(*target as u32).to_le_bytes());
        }
        Instruction::JumpIfFalse(target) => {
            out.push(0x31);
            out.extend_from_slice(&(*target as u32).to_le_bytes());
        }
        Instruction::Call { function, args } => {
            out.push(0x40);
            out.extend_from_slice(&function.as_u32().to_le_bytes());
            out.push(*args);
        }
        Instruction::Return => out.push(0x50),
    }
}
