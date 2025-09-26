use indexmap::IndexMap;

use scriptum_ast::{
    Block, Expression, ExpressionKind, Function, Module, Statement, StatementKind, Symbol,
};

use crate::ir::{FunctionIr, Instruction, ModuleIr};

/// Converte a AST em IR intermediário.
pub fn lower_module(module: &Module) -> ModuleIr {
    let mut functions = Vec::new();
    for function in &module.functions {
        functions.push(lower_function(function));
    }
    ModuleIr::new(functions)
}

struct LoweringContext {
    instructions: Vec<Instruction>,
    locals: IndexMap<Symbol, u16>,
    next_local: u16,
}

impl LoweringContext {
    fn new() -> Self {
        Self {
            instructions: Vec::new(),
            locals: IndexMap::new(),
            next_local: 0,
        }
    }

    fn emit(&mut self, instr: Instruction) -> usize {
        let idx = self.instructions.len();
        self.instructions.push(instr);
        idx
    }

    fn patch(&mut self, pos: usize, target: usize) {
        match self
            .instructions
            .get_mut(pos)
            .expect("posição de jump inválida")
        {
            Instruction::Jump(dest) | Instruction::JumpIfFalse(dest) => {
                *dest = target;
            }
            instr => panic!("não é instrução de salto: {instr:?}"),
        }
    }

    fn alloc_local(&mut self, symbol: Symbol) -> u16 {
        if let Some(local) = self.locals.get(&symbol) {
            *local
        } else {
            let idx = self.next_local;
            self.locals.insert(symbol, idx);
            self.next_local += 1;
            idx
        }
    }

    fn local(&self, symbol: Symbol) -> Option<u16> {
        self.locals.get(&symbol).copied()
    }
}

fn lower_function(function: &Function) -> FunctionIr {
    let mut ctx = LoweringContext::new();
    for (idx, param) in function.params.iter().enumerate() {
        ctx.locals.insert(*param, idx as u16);
        ctx.next_local = (idx + 1) as u16;
    }
    lower_block(&function.body, &mut ctx);
    if !matches!(ctx.instructions.last(), Some(Instruction::Return)) {
        ctx.emit(Instruction::Const(0.0));
        ctx.emit(Instruction::Return);
    }
    FunctionIr::new(function.name, function.params.len() as u8, ctx.instructions)
}

fn lower_block(block: &Block, ctx: &mut LoweringContext) {
    for statement in &block.statements {
        lower_statement(statement, ctx);
    }
}

fn lower_statement(statement: &Statement, ctx: &mut LoweringContext) {
    match &statement.kind {
        StatementKind::Let { name, value } => {
            lower_expression(value, ctx);
            let local = ctx.alloc_local(*name);
            ctx.emit(Instruction::StoreLocal(local));
        }
        StatementKind::Assign { target, value } => {
            lower_expression(value, ctx);
            let local = ctx
                .local(*target)
                .expect("variável deve ter sido declarada");
            ctx.emit(Instruction::StoreLocal(local));
        }
        StatementKind::If {
            cond,
            then_branch,
            else_branch,
        } => {
            lower_expression(cond, ctx);
            let jump_false = ctx.emit(Instruction::JumpIfFalse(usize::MAX));
            lower_block(then_branch, ctx);
            if let Some(else_branch) = else_branch {
                let jump_end = ctx.emit(Instruction::Jump(usize::MAX));
                let else_start = ctx.instructions.len();
                ctx.patch(jump_false, else_start);
                lower_block(else_branch, ctx);
                let end = ctx.instructions.len();
                ctx.patch(jump_end, end);
            } else {
                let end = ctx.instructions.len();
                ctx.patch(jump_false, end);
            }
        }
        StatementKind::While { cond, body } => {
            let loop_start = ctx.instructions.len();
            lower_expression(cond, ctx);
            let jump_exit = ctx.emit(Instruction::JumpIfFalse(usize::MAX));
            lower_block(body, ctx);
            ctx.emit(Instruction::Jump(loop_start));
            let end = ctx.instructions.len();
            ctx.patch(jump_exit, end);
        }
        StatementKind::Return { value } => {
            lower_expression(value, ctx);
            ctx.emit(Instruction::Return);
        }
        StatementKind::Expr(expr) => {
            lower_expression(expr, ctx);
            // Drop resultado implícito
        }
    }
}

fn lower_expression(expr: &Expression, ctx: &mut LoweringContext) {
    match &expr.kind {
        ExpressionKind::Number(value) => {
            ctx.emit(Instruction::Const(*value));
        }
        ExpressionKind::Bool(value) => {
            ctx.emit(Instruction::Const(if *value { 1.0 } else { 0.0 }));
        }
        ExpressionKind::Symbol(sym) => {
            let local = ctx.local(*sym).expect("símbolo não declarado");
            ctx.emit(Instruction::LoadLocal(local));
        }
        ExpressionKind::Binary { op, left, right } => {
            lower_expression(left, ctx);
            lower_expression(right, ctx);
            use scriptum_ast::BinaryOp::*;
            match op {
                Add => ctx.emit(Instruction::Add),
                Sub => ctx.emit(Instruction::Sub),
                Mul => ctx.emit(Instruction::Mul),
                Div => ctx.emit(Instruction::Div),
                Eq => ctx.emit(Instruction::CmpEq),
                Ne => ctx.emit(Instruction::CmpNe),
                Lt => ctx.emit(Instruction::CmpLt),
                Le => ctx.emit(Instruction::CmpLe),
                Gt => ctx.emit(Instruction::CmpGt),
                Ge => ctx.emit(Instruction::CmpGe),
            };
        }
        ExpressionKind::Call { callee, args } => {
            for arg in args {
                lower_expression(arg, ctx);
            }
            ctx.emit(Instruction::Call {
                function: *callee,
                args: args.len() as u8,
            });
        }
    }
}
