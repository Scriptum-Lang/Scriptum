use std::collections::HashMap;

use thiserror::Error;

use crate::bytecode::{Chunk, FunctionChunk, Instruction};

#[derive(Debug, Error)]
pub enum VmError {
    #[error("função de entrada não encontrada")]
    UnknownEntry,
}

#[derive(Debug)]
pub struct ExecutionResult {
    pub value: f64,
}

/// Máquina virtual interpretativa simples.
pub struct VirtualMachine<'a> {
    chunk: &'a Chunk,
    index: HashMap<u32, &'a FunctionChunk>,
}

impl<'a> VirtualMachine<'a> {
    pub fn new(chunk: &'a Chunk) -> Self {
        let mut index = HashMap::new();
        for function in &chunk.functions {
            index.insert(function.name, function);
        }
        Self { chunk, index }
    }

    pub fn run(&self, entry: u32, args: &[f64]) -> Result<ExecutionResult, VmError> {
        let function = self.index.get(&entry).ok_or(VmError::UnknownEntry)?;
        let mut stack: Vec<f64> = Vec::new();
        let mut frames = Vec::new();
        frames.push(Frame::new(function, args));

        while let Some(frame) = frames.last_mut() {
            if frame.ip >= frame.function.instructions.len() {
                break;
            }
            match frame.function.instructions[frame.ip] {
                Instruction::Const(value) => {
                    stack.push(value);
                    frame.ip += 1;
                }
                Instruction::LoadLocal(idx) => {
                    let value = frame.locals[idx as usize];
                    stack.push(value);
                    frame.ip += 1;
                }
                Instruction::StoreLocal(idx) => {
                    let value = stack.pop().unwrap_or(0.0);
                    frame.locals[idx as usize] = value;
                    frame.ip += 1;
                }
                Instruction::Add => binary_op(&mut stack, f64::add, frame),
                Instruction::Sub => binary_op(&mut stack, f64::sub, frame),
                Instruction::Mul => binary_op(&mut stack, f64::mul, frame),
                Instruction::Div => binary_op(&mut stack, f64::div, frame),
                Instruction::CmpEq => compare(&mut stack, |a, b| a == b, frame),
                Instruction::CmpNe => compare(&mut stack, |a, b| a != b, frame),
                Instruction::CmpLt => compare(&mut stack, |a, b| a < b, frame),
                Instruction::CmpLe => compare(&mut stack, |a, b| a <= b, frame),
                Instruction::CmpGt => compare(&mut stack, |a, b| a > b, frame),
                Instruction::CmpGe => compare(&mut stack, |a, b| a >= b, frame),
                Instruction::Jump(target) => {
                    frame.ip = target;
                }
                Instruction::JumpIfFalse(target) => {
                    let cond = stack.pop().unwrap_or(0.0);
                    if cond == 0.0 {
                        frame.ip = target;
                    } else {
                        frame.ip += 1;
                    }
                }
                Instruction::Call {
                    function,
                    args: nargs,
                } => {
                    let callee = self.index.get(&function).ok_or(VmError::UnknownEntry)?;
                    let mut call_args = Vec::with_capacity(nargs as usize);
                    for _ in 0..nargs {
                        call_args.push(stack.pop().unwrap_or(0.0));
                    }
                    call_args.reverse();
                    frames.push(Frame::new(callee, &call_args));
                }
                Instruction::Return => {
                    let value = stack.pop().unwrap_or(0.0);
                    frames.pop();
                    if let Some(prev) = frames.last_mut() {
                        stack.push(value);
                        prev.ip += 1;
                    } else {
                        return Ok(ExecutionResult { value });
                    }
                }
            }
        }

        Ok(ExecutionResult {
            value: stack.pop().unwrap_or(0.0),
        })
    }
}

struct Frame<'a> {
    function: &'a FunctionChunk,
    ip: usize,
    locals: Vec<f64>,
}

impl<'a> Frame<'a> {
    fn new(function: &'a FunctionChunk, args: &[f64]) -> Self {
        let mut locals = vec![0.0; local_count(function)];
        for (i, value) in args.iter().enumerate() {
            if i < locals.len() {
                locals[i] = *value;
            }
        }
        Self {
            function,
            ip: 0,
            locals,
        }
    }
}

fn local_count(function: &FunctionChunk) -> usize {
    let mut max = function.arity as u16;
    for instr in &function.instructions {
        match instr {
            Instruction::LoadLocal(idx) | Instruction::StoreLocal(idx) => {
                max = max.max(*idx + 1);
            }
            _ => {}
        }
    }
    max as usize
}

fn binary_op(stack: &mut Vec<f64>, op: fn(f64, f64) -> f64, frame: &mut Frame<'_>) {
    let rhs = stack.pop().unwrap_or(0.0);
    let lhs = stack.pop().unwrap_or(0.0);
    stack.push(op(lhs, rhs));
    frame.ip += 1;
}

fn compare(stack: &mut Vec<f64>, cmp: impl Fn(f64, f64) -> bool, frame: &mut Frame<'_>) {
    let rhs = stack.pop().unwrap_or(0.0);
    let lhs = stack.pop().unwrap_or(0.0);
    stack.push(if cmp(lhs, rhs) { 1.0 } else { 0.0 });
    frame.ip += 1;
}
