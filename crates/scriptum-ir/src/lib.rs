#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! IR intermediária simplificada da linguagem Scriptum.

use serde::{Deserialize, Serialize};

use scriptum_ast::{
    BinaryOp, Expression, ExpressionKind, Function, Item, ItemKind, LambdaBody, LambdaExpression,
    Literal, LogicalOp, Module, Statement, StatementKind, Symbol, TypeExpr, TypeExprKind, UnaryOp,
};
use scriptum_utils::Span;

/// Representa um módulo em IR.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleIr {
    pub functions: Vec<FunctionIr>,
    pub globals: Vec<GlobalIr>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalIr {
    pub name: Symbol,
    pub mutable: bool,
    pub ty: Option<IrTypeExpr>,
    pub initializer: Option<IrExpr>,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionIr {
    pub name: Symbol,
    pub generics: Vec<Symbol>,
    pub params: Vec<IrParam>,
    pub return_type: Option<IrTypeExpr>,
    pub body: Vec<IrStmt>,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IrStmt {
    Let {
        name: Symbol,
        mutable: bool,
        ty: Option<IrTypeExpr>,
        value: Option<IrExpr>,
        span: Span,
    },
    Expr(IrExpr, Span),
    Return(Option<IrExpr>, Span),
    Block(Vec<IrStmt>, Span),
    If {
        cond: IrExpr,
        then_branch: Vec<IrStmt>,
        else_branch: Vec<IrStmt>,
        span: Span,
    },
    While {
        cond: IrExpr,
        body: Vec<IrStmt>,
        span: Span,
    },
    For {
        binding: Symbol,
        iterator: IrExpr,
        body: Vec<IrStmt>,
        span: Span,
    },
    Break(Span),
    Continue(Span),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IrExpr {
    Identifier(Symbol, Span),
    Literal(IrLiteral, Span),
    Unary {
        op: UnaryOp,
        expr: Box<IrExpr>,
        span: Span,
    },
    Binary {
        op: BinaryOp,
        left: Box<IrExpr>,
        right: Box<IrExpr>,
        span: Span,
    },
    Logical {
        op: LogicalOp,
        left: Box<IrExpr>,
        right: Box<IrExpr>,
        span: Span,
    },
    NullishCoalesce {
        left: Box<IrExpr>,
        right: Box<IrExpr>,
        span: Span,
    },
    Conditional {
        cond: Box<IrExpr>,
        then_branch: Box<IrExpr>,
        else_branch: Box<IrExpr>,
        span: Span,
    },
    Assignment {
        target: Box<IrExpr>,
        value: Box<IrExpr>,
        span: Span,
    },
    Call {
        callee: Box<IrExpr>,
        args: Vec<IrExpr>,
        span: Span,
    },
    Index {
        target: Box<IrExpr>,
        index: Box<IrExpr>,
        span: Span,
    },
    Member {
        target: Box<IrExpr>,
        property: Symbol,
        span: Span,
    },
    ArrayLiteral(Vec<IrExpr>, Span),
    ObjectLiteral(Vec<IrObjectField>, Span),
    Lambda(IrLambda, Span),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrLambda {
    pub generics: Vec<Symbol>,
    pub params: Vec<IrParam>,
    pub return_type: Option<IrTypeExpr>,
    pub body: IrLambdaBody,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IrLambdaBody {
    Expr(Box<IrExpr>),
    Block(Vec<IrStmt>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrParam {
    pub name: Symbol,
    pub ty: Option<IrTypeExpr>,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrObjectField {
    pub key: Symbol,
    pub value: IrExpr,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IrLiteral {
    Numerus(f64),
    Textus(String),
    Booleanum(bool),
    Nullum,
    Indefinitum,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrTypeExpr {
    pub kind: IrTypeExprKind,
    pub span: Span,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IrTypeExprKind {
    Simple(Symbol),
    Array(Box<IrTypeExpr>),
    Object(Vec<IrTypeField>),
    Function {
        generics: Vec<Symbol>,
        params: Vec<IrTypeExpr>,
        ret: Box<IrTypeExpr>,
    },
    Optional(Box<IrTypeExpr>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IrTypeField {
    pub name: Symbol,
    pub ty: IrTypeExpr,
}

/// Converte a AST para IR intermediária simplificada.
pub fn lower_module(module: &Module) -> ModuleIr {
    let mut globals = Vec::new();
    let mut functions = Vec::new();
    for item in &module.items {
        match &item.kind {
            ItemKind::Function(function) => {
                functions.push(lower_function(function));
            }
            ItemKind::Let(var) => {
                globals.push(GlobalIr {
                    name: var.name,
                    mutable: var.mutable,
                    ty: var.type_annotation.as_ref().map(lower_type_expr),
                    initializer: var.initializer.as_ref().map(lower_expr),
                    span: item.span,
                });
            }
        }
    }
    ModuleIr { functions, globals }
}

fn lower_function(function: &Function) -> FunctionIr {
    let body = lower_block_statements(&function.body.statements);
    FunctionIr {
        name: function.name,
        generics: function.generics.iter().map(|param| param.name).collect(),
        params: function
            .params
            .iter()
            .map(|param| IrParam {
                name: param.name,
                ty: param.ty.as_ref().map(lower_type_expr),
                span: param.span,
            })
            .collect(),
        return_type: function.return_type.as_ref().map(lower_type_expr),
        body,
        span: function.body.span,
    }
}

fn lower_block_statements(statements: &[Statement]) -> Vec<IrStmt> {
    statements.iter().map(lower_statement).collect()
}

fn lower_statement(statement: &Statement) -> IrStmt {
    match &statement.kind {
        StatementKind::Let(decl) | StatementKind::Const(decl) => IrStmt::Let {
            name: decl.name,
            mutable: decl.mutable,
            ty: decl.type_annotation.as_ref().map(lower_type_expr),
            value: decl.initializer.as_ref().map(lower_expr),
            span: statement.span,
        },
        StatementKind::Expr(expr) => IrStmt::Expr(lower_expr(expr), statement.span),
        StatementKind::Return(value) => {
            let lowered = value.as_ref().map(lower_expr);
            IrStmt::Return(lowered, statement.span)
        }
        StatementKind::Block(block) => {
            let stmts = lower_block_statements(&block.statements);
            IrStmt::Block(stmts, block.span)
        }
        StatementKind::If {
            condition,
            then_branch,
            else_branch,
        } => {
            let cond = lower_expr(condition);
            let then_branch = match &then_branch.kind {
                StatementKind::Block(block) => lower_block_statements(&block.statements),
                other => vec![lower_statement(&Statement {
                    id: then_branch.id,
                    span: then_branch.span,
                    kind: other.clone(),
                })],
            };
            let else_branch = else_branch
                .as_ref()
                .map(|stmt| match &stmt.kind {
                    StatementKind::Block(block) => lower_block_statements(&block.statements),
                    other => vec![lower_statement(&Statement {
                        id: stmt.id,
                        span: stmt.span,
                        kind: other.clone(),
                    })],
                })
                .unwrap_or_default();
            IrStmt::If {
                cond,
                then_branch,
                else_branch,
                span: statement.span,
            }
        }
        StatementKind::While { condition, body } => {
            let cond = lower_expr(condition);
            let body_ir = match &body.kind {
                StatementKind::Block(block) => lower_block_statements(&block.statements),
                other => vec![lower_statement(&Statement {
                    id: body.id,
                    span: body.span,
                    kind: other.clone(),
                })],
            };
            IrStmt::While {
                cond,
                body: body_ir,
                span: statement.span,
            }
        }
        StatementKind::For {
            binding,
            iterator,
            body,
        } => {
            let iter = lower_expr(iterator);
            let body_ir = match &body.kind {
                StatementKind::Block(block) => lower_block_statements(&block.statements),
                other => vec![lower_statement(&Statement {
                    id: body.id,
                    span: body.span,
                    kind: other.clone(),
                })],
            };
            IrStmt::For {
                binding: *binding,
                iterator: iter,
                body: body_ir,
                span: statement.span,
            }
        }
        StatementKind::Break(_) => IrStmt::Break(statement.span),
        StatementKind::Continue(_) => IrStmt::Continue(statement.span),
    }
}

fn lower_expr(expr: &Expression) -> IrExpr {
    match &expr.kind {
        ExpressionKind::Identifier(sym) => IrExpr::Identifier(*sym, expr.span),
        ExpressionKind::Literal(lit) => IrExpr::Literal(lower_literal(lit), expr.span),
        ExpressionKind::Unary { op, expr: inner } => IrExpr::Unary {
            op: *op,
            expr: Box::new(lower_expr(inner)),
            span: expr.span,
        },
        ExpressionKind::Binary { op, left, right } => IrExpr::Binary {
            op: *op,
            left: Box::new(lower_expr(left)),
            right: Box::new(lower_expr(right)),
            span: expr.span,
        },
        ExpressionKind::Logical { op, left, right } => IrExpr::Logical {
            op: *op,
            left: Box::new(lower_expr(left)),
            right: Box::new(lower_expr(right)),
            span: expr.span,
        },
        ExpressionKind::NullishCoalesce { left, right } => IrExpr::NullishCoalesce {
            left: Box::new(lower_expr(left)),
            right: Box::new(lower_expr(right)),
            span: expr.span,
        },
        ExpressionKind::Conditional {
            condition,
            then_branch,
            else_branch,
        } => IrExpr::Conditional {
            cond: Box::new(lower_expr(condition)),
            then_branch: Box::new(lower_expr(then_branch)),
            else_branch: Box::new(lower_expr(else_branch)),
            span: expr.span,
        },
        ExpressionKind::Assignment { target, value } => IrExpr::Assignment {
            target: Box::new(lower_expr(target)),
            value: Box::new(lower_expr(value)),
            span: expr.span,
        },
        ExpressionKind::Call { callee, arguments } => IrExpr::Call {
            callee: Box::new(lower_expr(callee)),
            args: arguments.iter().map(lower_expr).collect(),
            span: expr.span,
        },
        ExpressionKind::Index { target, index } => IrExpr::Index {
            target: Box::new(lower_expr(target)),
            index: Box::new(lower_expr(index)),
            span: expr.span,
        },
        ExpressionKind::Member { target, property } => IrExpr::Member {
            target: Box::new(lower_expr(target)),
            property: *property,
            span: expr.span,
        },
        ExpressionKind::ArrayLiteral(values) => {
            IrExpr::ArrayLiteral(values.iter().map(lower_expr).collect(), expr.span)
        }
        ExpressionKind::ObjectLiteral(fields) => IrExpr::ObjectLiteral(
            fields
                .iter()
                .map(|field| IrObjectField {
                    key: field.key,
                    value: lower_expr(&field.value),
                    span: field.value.span,
                })
                .collect(),
            expr.span,
        ),
        ExpressionKind::Lambda(lambda) => IrExpr::Lambda(lower_lambda(lambda.as_ref()), expr.span),
    }
}

fn lower_lambda(lambda: &LambdaExpression) -> IrLambda {
    IrLambda {
        generics: lambda.generics.iter().map(|param| param.name).collect(),
        params: lambda
            .params
            .iter()
            .map(|param| IrParam {
                name: param.name,
                ty: param.ty.as_ref().map(lower_type_expr),
                span: param.span,
            })
            .collect(),
        return_type: lambda.return_type.as_ref().map(lower_type_expr),
        body: match &lambda.body {
            LambdaBody::Expression(expr) => IrLambdaBody::Expr(Box::new(lower_expr(expr.as_ref()))),
            LambdaBody::Block(block) => {
                IrLambdaBody::Block(lower_block_statements(&block.statements))
            }
        },
    }
}

fn lower_literal(lit: &Literal) -> IrLiteral {
    match lit {
        Literal::Numerus(v) => IrLiteral::Numerus(*v),
        Literal::Textus(v) => IrLiteral::Textus(v.clone()),
        Literal::Booleanum(v) => IrLiteral::Booleanum(*v),
        Literal::Nullum => IrLiteral::Nullum,
        Literal::Indefinitum => IrLiteral::Indefinitum,
    }
}

fn lower_type_expr(ty: &TypeExpr) -> IrTypeExpr {
    let kind = match &ty.kind {
        TypeExprKind::Simple(sym) => IrTypeExprKind::Simple(*sym),
        TypeExprKind::Array(inner) => IrTypeExprKind::Array(Box::new(lower_type_expr(inner))),
        TypeExprKind::Object(fields) => IrTypeExprKind::Object(
            fields
                .iter()
                .map(|field| IrTypeField {
                    name: field.name,
                    ty: lower_type_expr(&field.ty),
                })
                .collect(),
        ),
        TypeExprKind::Function {
            generics,
            params,
            ret,
        } => IrTypeExprKind::Function {
            generics: generics.iter().map(|param| param.name).collect(),
            params: params.iter().map(lower_type_expr).collect(),
            ret: Box::new(lower_type_expr(ret)),
        },
        TypeExprKind::Optional(inner) => IrTypeExprKind::Optional(Box::new(lower_type_expr(inner))),
        TypeExprKind::Tuple(items) => IrTypeExprKind::Object(
            items
                .iter()
                .enumerate()
                .map(|(idx, ty)| IrTypeField {
                    name: Symbol::from_u32(idx as u32),
                    ty: lower_type_expr(ty),
                })
                .collect(),
        ),
    };
    IrTypeExpr {
        kind,
        span: ty.span,
    }
}
