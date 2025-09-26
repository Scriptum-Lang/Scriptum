#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Estruturas da AST da linguagem Scriptum.

use bumpalo::Bump;
use indexmap::IndexSet;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

use scriptum_utils::Span;

/// Identificador internado.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize, Debug)]
pub struct Symbol(u32);

impl Symbol {
    pub fn as_u32(self) -> u32 {
        self.0
    }
}

/// Interner compacto para strings.
#[derive(Default, Clone)]
pub struct StringInterner {
    arena: Bump,
    map: IndexSet<&'static str>,
}

impl StringInterner {
    pub fn new() -> Self {
        Self {
            arena: Bump::new(),
            map: IndexSet::new(),
        }
    }

    pub fn intern(&mut self, text: &str) -> Symbol {
        if let Some(idx) = self.map.get_index_of(text) {
            return Symbol(idx as u32);
        }
        let stored: &mut str = self.arena.alloc_str(text);
        let leaked: &'static str = unsafe { &*(stored as *const str) };
        let (idx, _) = self.map.insert_full(leaked);
        Symbol(idx as u32)
    }

    pub fn resolve(&self, sym: Symbol) -> &str {
        self.map
            .get_index(sym.0 as usize)
            .expect("símbolo inválido")
    }
}

/// Módulo Scriptum (arquivo inteiro).
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Module {
    pub functions: Vec<Function>,
}

impl Module {
    pub fn new(functions: Vec<Function>) -> Self {
        Self { functions }
    }
}

/// Função Scriptum.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Function {
    pub name: Symbol,
    pub params: SmallVec<[Symbol; 4]>,
    pub body: Block,
    pub span: Span,
}

/// Bloco `{ ... }`.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Block {
    pub statements: Vec<Statement>,
    pub span: Span,
}

/// Tipos de declaração.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum StatementKind {
    Let {
        name: Symbol,
        value: Expression,
    },
    Assign {
        target: Symbol,
        value: Expression,
    },
    If {
        cond: Expression,
        then_branch: Block,
        else_branch: Option<Block>,
    },
    While {
        cond: Expression,
        body: Block,
    },
    Return {
        value: Expression,
    },
    Expr(Expression),
}

/// Declaração com span.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Statement {
    pub kind: StatementKind,
    pub span: Span,
}

/// Expressões.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum ExpressionKind {
    Number(f64),
    Bool(bool),
    Symbol(Symbol),
    Binary {
        op: BinaryOp,
        left: Box<Expression>,
        right: Box<Expression>,
    },
    Call {
        callee: Symbol,
        args: Vec<Expression>,
    },
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Expression {
    pub kind: ExpressionKind,
    pub span: Span,
}

#[derive(Clone, Copy, Serialize, Deserialize, Debug, PartialEq, Eq)]
pub enum BinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

/// Trait para percorrer a AST.
pub trait Visitor {
    fn visit_module(&mut self, module: &Module) {
        for func in &module.functions {
            self.visit_function(func);
        }
    }

    fn visit_function(&mut self, function: &Function) {
        self.visit_block(&function.body);
    }

    fn visit_block(&mut self, block: &Block) {
        for stmt in &block.statements {
            self.visit_statement(stmt);
        }
    }

    fn visit_statement(&mut self, statement: &Statement) {
        match &statement.kind {
            StatementKind::Let { value, .. }
            | StatementKind::Assign { value, .. }
            | StatementKind::Return { value }
            | StatementKind::Expr(value) => self.visit_expression(value),
            StatementKind::If {
                cond,
                then_branch,
                else_branch,
            } => {
                self.visit_expression(cond);
                self.visit_block(then_branch);
                if let Some(else_branch) = else_branch {
                    self.visit_block(else_branch);
                }
            }
            StatementKind::While { cond, body } => {
                self.visit_expression(cond);
                self.visit_block(body);
            }
        }
    }

    fn visit_expression(&mut self, expr: &Expression) {
        match &expr.kind {
            ExpressionKind::Binary { left, right, .. } => {
                self.visit_expression(left);
                self.visit_expression(right);
            }
            ExpressionKind::Call { args, .. } => {
                for arg in args {
                    self.visit_expression(arg);
                }
            }
            ExpressionKind::Number(_) | ExpressionKind::Bool(_) | ExpressionKind::Symbol(_) => {}
        }
    }
}

impl Default for Module {
    fn default() -> Self {
        Self {
            functions: Vec::new(),
        }
    }
}

impl Block {
    pub fn new(statements: Vec<Statement>, span: Span) -> Self {
        Self { statements, span }
    }
}

impl Function {
    pub fn new(name: Symbol, params: SmallVec<[Symbol; 4]>, body: Block, span: Span) -> Self {
        Self {
            name,
            params,
            body,
            span,
        }
    }
}

impl Statement {
    pub fn new(kind: StatementKind, span: Span) -> Self {
        Self { kind, span }
    }
}

impl Expression {
    pub fn new(kind: ExpressionKind, span: Span) -> Self {
        Self { kind, span }
    }
}
