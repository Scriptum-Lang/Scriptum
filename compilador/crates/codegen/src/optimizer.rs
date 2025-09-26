use crate::ir::{Instruction, ModuleIr};

/// Otimiza o módulo com passes leves (const-fold, eliminação simples).
pub fn optimize_module(module: &mut ModuleIr) {
    for function in &mut module.functions {
        let mut optimized = Vec::with_capacity(function.instructions.len());
        let mut stack: Vec<f64> = Vec::new();
        for instr in function.instructions.drain(..) {
            match instr {
                Instruction::Const(value) => {
                    stack.push(value);
                    optimized.push(Instruction::Const(value));
                }
                Instruction::Add | Instruction::Sub | Instruction::Mul | Instruction::Div => {
                    if let (Some(rhs), Some(lhs)) = (stack.pop(), stack.pop()) {
                        let value = match instr {
                            Instruction::Add => lhs + rhs,
                            Instruction::Sub => lhs - rhs,
                            Instruction::Mul => lhs * rhs,
                            Instruction::Div => lhs / rhs,
                            _ => unreachable!(),
                        };
                        stack.push(value);
                        optimized.pop();
                        optimized.pop();
                        optimized.push(Instruction::Const(value));
                    } else {
                        optimized.push(instr);
                    }
                }
                other => {
                    stack.clear();
                    optimized.push(other);
                }
            }
        }
        function.instructions = optimized;
    }
}
