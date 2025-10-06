#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Definição canônica das estruturas de AST da linguagem Scriptum.

use std::fmt;
use std::sync::Arc;

use indexmap::IndexSet;
use serde::{Deserialize, Serialize};

use scriptum_utils::Span;

/// Identificador internado.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize, Debug)]
pub struct Symbol(u32);

impl Symbol {
    pub fn as_u32(self) -> u32 {
        self.0
    }

    pub fn from_u32(value: u32) -> Self {
        Self(value)
    }
}

/// Estrutura responsável por internar strings de forma estável.
#[derive(Default, Clone, Serialize, Deserialize)]
pub struct StringInterner {
    entries: IndexSet<Arc<str>>,
}

impl StringInterner {
    pub fn new() -> Self {
        Self {
            entries: IndexSet::new(),
        }
    }

    pub fn intern(&mut self, text: &str) -> Symbol {
        if let Some(index) = self.entries.get_index_of(text) {
            return Symbol(index as u32);
        }
        let owned: Arc<str> = Arc::from(text);
        let (index, _) = self.entries.insert_full(owned);
        Symbol(index as u32)
    }

    pub fn resolve(&self, symbol: Symbol) -> &str {
        self.entries
            .get_index(symbol.0 as usize)
            .map(|arc| arc.as_ref())
            .expect("símbolo inválido")
    }
}

/// Identificador único de nó da AST.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NodeId(u32);

impl NodeId {
    pub const fn new(id: u32) -> Self {
        Self(id)
    }

    pub fn as_u32(self) -> u32 {
        self.0
    }
}

impl fmt::Debug for NodeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "@{}", self.0)
    }
}

/// Gerador incremental de `NodeId`.
#[derive(Default, Clone, Debug)]
pub struct NodeIdGenerator {
    next: u32,
}

impl NodeIdGenerator {
    pub fn new() -> Self {
        Self { next: 0 }
    }

    pub fn fresh(&mut self) -> NodeId {
        let id = self.next;
        self.next = self.next.wrapping_add(1);
        NodeId::new(id)
    }
}

/// Módulo Scriptum (arquivo).
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Module {
    pub id: NodeId,
    pub span: Span,
    pub interner: StringInterner,
    pub items: Vec<Item>,
}

impl Module {
    pub fn new(id: NodeId, span: Span, interner: StringInterner, items: Vec<Item>) -> Self {
        Self {
            id,
            span,
            interner,
            items,
        }
    }
}

/// Itens de um módulo.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Item {
    pub id: NodeId,
    pub span: Span,
    pub kind: ItemKind,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum ItemKind {
    Function(Function),
    Let(VarDecl),
}

/// Declaração de variável no nível superior ou local.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct VarDecl {
    pub name: Symbol,
    pub mutable: bool,
    pub type_annotation: Option<TypeExpr>,
    pub initializer: Option<Expression>,
}

/// Declaração de função.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Function {
    pub name: Symbol,
    pub generics: Vec<TypeParameter>,
    pub params: Vec<Parameter>,
    pub return_type: Option<TypeExpr>,
    pub body: Block,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct TypeParameter {
    pub name: Symbol,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Parameter {
    pub id: NodeId,
    pub span: Span,
    pub name: Symbol,
    pub ty: Option<TypeExpr>,
}

/// Bloco `{ ... }` de declarações.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Block {
    pub id: NodeId,
    pub span: Span,
    pub statements: Vec<Statement>,
}

impl Block {
    pub fn new(id: NodeId, span: Span, statements: Vec<Statement>) -> Self {
        Self {
            id,
            span,
            statements,
        }
    }
}

/// Declarações dentro de blocos.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Statement {
    pub id: NodeId,
    pub span: Span,
    pub kind: StatementKind,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum StatementKind {
    Let(VarDecl),
    Const(VarDecl),
    Expr(Expression),
    Return(Option<Expression>),
    Block(Block),
    If {
        condition: Expression,
        then_branch: Box<Statement>,
        else_branch: Option<Box<Statement>>,
    },
    While {
        condition: Expression,
        body: Box<Statement>,
    },
    For {
        binding: Symbol,
        iterator: Expression,
        body: Box<Statement>,
    },
    Break(Option<Symbol>),
    Continue(Option<Symbol>),
}

/// Expressões Scriptum.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Expression {
    pub id: NodeId,
    pub span: Span,
    pub kind: ExpressionKind,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum ExpressionKind {
    Identifier(Symbol),
    Literal(Literal),
    Unary {
        op: UnaryOp,
        expr: Box<Expression>,
    },
    Binary {
        op: BinaryOp,
        left: Box<Expression>,
        right: Box<Expression>,
    },
    Logical {
        op: LogicalOp,
        left: Box<Expression>,
        right: Box<Expression>,
    },
    NullishCoalesce {
        left: Box<Expression>,
        right: Box<Expression>,
    },
    Conditional {
        condition: Box<Expression>,
        then_branch: Box<Expression>,
        else_branch: Box<Expression>,
    },
    Assignment {
        target: Box<Expression>,
        value: Box<Expression>,
    },
    Call {
        callee: Box<Expression>,
        arguments: Vec<Expression>,
    },
    Index {
        target: Box<Expression>,
        index: Box<Expression>,
    },
    Member {
        target: Box<Expression>,
        property: Symbol,
    },
    ArrayLiteral(Vec<Expression>),
    ObjectLiteral(Vec<ObjectField>),
    Lambda(LambdaExpression),
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct ObjectField {
    pub key: Symbol,
    pub value: Expression,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct LambdaExpression {
    pub id: NodeId,
    pub span: Span,
    pub generics: Vec<TypeParameter>,
    pub params: Vec<Parameter>,
    pub return_type: Option<TypeExpr>,
    pub body: LambdaBody,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum LambdaBody {
    Expression(Expression),
    Block(Block),
}

/// Literais da linguagem.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum Literal {
    Numerus(f64),
    Textus(String),
    Booleanum(bool),
    Nullum,
    Indefinitum,
}

#[derive(Clone, Copy, Serialize, Deserialize, Debug, PartialEq, Eq)]
pub enum UnaryOp {
    Pos,
    Neg,
    Not,
}

#[derive(Clone, Copy, Serialize, Deserialize, Debug, PartialEq, Eq)]
pub enum BinaryOp {
    Power,
    Mul,
    Div,
    Mod,
    Add,
    Sub,
    BitAnd,
    BitOr,
    BitXor,
    ShiftLeft,
    ShiftRight,
    Equal,
    NotEqual,
    StrictEqual,
    StrictNotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
    Range,
}

#[derive(Clone, Copy, Serialize, Deserialize, Debug, PartialEq, Eq)]
pub enum LogicalOp {
    And,
    Or,
}

/// Expressões de tipo sintáticas.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct TypeExpr {
    pub id: NodeId,
    pub span: Span,
    pub kind: TypeExprKind,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub enum TypeExprKind {
    Simple(Symbol),
    Array(Box<TypeExpr>),
    Object(Vec<TypeField>),
    Function {
        generics: Vec<TypeParameter>,
        params: Vec<TypeExpr>,
        ret: Box<TypeExpr>,
    },
    Optional(Box<TypeExpr>),
    Tuple(Vec<TypeExpr>),
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct TypeField {
    pub name: Symbol,
    pub ty: TypeExpr,
}

/// Trait utilitário para percorrer a AST.
pub trait Visitor {
    fn visit_module(&mut self, module: &Module) {
        self.visit_items(&module.items);
    }

    fn visit_items(&mut self, items: &[Item]) {
        for item in items {
            self.visit_item(item);
        }
    }

    fn visit_item(&mut self, item: &Item) {
        match &item.kind {
            ItemKind::Function(function) => self.visit_function(function),
            ItemKind::Let(decl) => self.visit_var_decl(decl),
        }
    }

    fn visit_function(&mut self, function: &Function) {
        for param in &function.params {
            if let Some(ty) = &param.ty {
                self.visit_type_expr(ty);
            }
        }
        if let Some(ret) = &function.return_type {
            self.visit_type_expr(ret);
        }
        self.visit_block(&function.body);
    }

    fn visit_block(&mut self, block: &Block) {
        for stmt in &block.statements {
            self.visit_statement(stmt);
        }
    }

    fn visit_statement(&mut self, statement: &Statement) {
        match &statement.kind {
            StatementKind::Let(decl) | StatementKind::Const(decl) => self.visit_var_decl(decl),
            StatementKind::Expr(expr) => self.visit_expression(expr),
            StatementKind::Return(expr) => {
                if let Some(expr) = expr {
                    self.visit_expression(expr);
                }
            }
            StatementKind::Block(block) => self.visit_block(block),
            StatementKind::If {
                condition,
                then_branch,
                else_branch,
            } => {
                self.visit_expression(condition);
                self.visit_statement(then_branch);
                if let Some(else_branch) = else_branch {
                    self.visit_statement(else_branch);
                }
            }
            StatementKind::While { condition, body } => {
                self.visit_expression(condition);
                self.visit_statement(body);
            }
            StatementKind::For { iterator, body, .. } => {
                self.visit_expression(iterator);
                self.visit_statement(body);
            }
            StatementKind::Break(_) | StatementKind::Continue(_) => {}
        }
    }

    fn visit_expression(&mut self, expression: &Expression) {
        match &expression.kind {
            ExpressionKind::Identifier(_)
            | ExpressionKind::Literal(_)
            | ExpressionKind::Assignment { .. } => {}
            ExpressionKind::Unary { expr, .. } => self.visit_expression(expr),
            ExpressionKind::Binary { left, right, .. }
            | ExpressionKind::Logical { left, right, .. }
            | ExpressionKind::NullishCoalesce { left, right }
            | ExpressionKind::Index {
                target: left,
                index: right,
            }
            | ExpressionKind::Call {
                callee: left,
                arguments: right,
            } => {
                self.visit_expression(left);
                for arg in right {
                    self.visit_expression(arg);
                }
            }
            ExpressionKind::Conditional {
                condition,
                then_branch,
                else_branch,
            } => {
                self.visit_expression(condition);
                self.visit_expression(then_branch);
                self.visit_expression(else_branch);
            }
            ExpressionKind::Member { target, .. } => self.visit_expression(target),
            ExpressionKind::ArrayLiteral(elements) => {
                for element in elements {
                    self.visit_expression(element);
                }
            }
            ExpressionKind::ObjectLiteral(fields) => {
                for field in fields {
                    self.visit_expression(&field.value);
                }
            }
            ExpressionKind::Lambda(lambda) => match &lambda.body {
                LambdaBody::Expression(expr) => self.visit_expression(expr),
                LambdaBody::Block(block) => self.visit_block(block),
            },
        }
    }

    fn visit_type_expr(&mut self, ty: &TypeExpr) {
        match &ty.kind {
            TypeExprKind::Simple(_)
            | TypeExprKind::Optional(_)
            | TypeExprKind::Array(_)
            | TypeExprKind::Tuple(_)
            | TypeExprKind::Function { .. }
            | TypeExprKind::Object(_) => {}
        }
    }

    fn visit_var_decl(&mut self, decl: &VarDecl) {
        if let Some(init) = &decl.initializer {
            self.visit_expression(init);
        }
        if let Some(ty) = &decl.type_annotation {
            self.visit_type_expr(ty);
        }
    }
}
