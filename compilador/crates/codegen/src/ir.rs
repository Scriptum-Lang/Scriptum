use serde::{Deserialize, Serialize};

use scriptum_ast::Symbol;

/// Operando genérico utilizado por algumas instruções.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum Operand {
    Local(u16),
    Constant(f64),
    Function(Symbol),
}

/// Instruções de bytecode simples.
#[derive(Debug, Clone, Serialize, Deserialize)]
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
    Call { function: Symbol, args: u8 },
    Return,
}

/// IR de um módulo Scriptum.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleIr {
    pub functions: Vec<FunctionIr>,
}

/// Função em IR.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionIr {
    pub name: Symbol,
    pub arity: u8,
    pub instructions: Vec<Instruction>,
}

impl ModuleIr {
    pub fn new(functions: Vec<FunctionIr>) -> Self {
        Self { functions }
    }
}

impl FunctionIr {
    pub fn new(name: Symbol, arity: u8, instructions: Vec<Instruction>) -> Self {
        Self {
            name,
            arity,
            instructions,
        }
    }
}
