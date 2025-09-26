use indexmap::IndexMap;
use thiserror::Error;

use scriptum_ast::{
    BinaryOp, Block, Expression, ExpressionKind, Module, Statement, StatementKind, Symbol,
};
use scriptum_utils::Span;

use crate::symbol_table::SymbolTable;
use crate::type_system::Type;

/// Erros emitidos pelo analisador semântico.
#[derive(Debug, Error)]
#[error("{message}")]
pub struct SemanticError {
    pub message: String,
    pub span: Span,
}

impl SemanticError {
    fn new(message: impl Into<String>, span: Span) -> Self {
        Self {
            message: message.into(),
            span,
        }
    }
}

struct FunctionInfo {
    return_type: Option<Type>,
}

/// Executa a análise semântica do módulo.
pub fn analyze_module(module: &Module) -> Result<(), SemanticError> {
    let mut functions: IndexMap<Symbol, FunctionInfo> = IndexMap::new();
    for func in &module.functions {
        functions.insert(func.name, FunctionInfo { return_type: None });
    }

    for func in &module.functions {
        analyze_function(func, &mut functions)?;
    }

    Ok(())
}

fn analyze_function(
    func: &scriptum_ast::Function,
    functions: &mut IndexMap<Symbol, FunctionInfo>,
) -> Result<(), SemanticError> {
    let mut table = SymbolTable::new();
    for param in &func.params {
        table.insert(*param, Type::Numerus, func.span);
    }

    let mut inferred_return: Option<Type> = None;
    analyze_block(&func.body, &mut table, functions, &mut inferred_return)?;
    if let Some(info) = functions.get_mut(&func.name) {
        info.return_type = inferred_return;
    }
    Ok(())
}

fn analyze_block(
    block: &Block,
    table: &mut SymbolTable,
    functions: &mut IndexMap<Symbol, FunctionInfo>,
    inferred_return: &mut Option<Type>,
) -> Result<(), SemanticError> {
    table.enter_scope();
    for statement in &block.statements {
        analyze_statement(statement, table, functions, inferred_return)?;
    }
    table.exit_scope();
    Ok(())
}

fn analyze_statement(
    statement: &Statement,
    table: &mut SymbolTable,
    functions: &mut IndexMap<Symbol, FunctionInfo>,
    inferred_return: &mut Option<Type>,
) -> Result<(), SemanticError> {
    match &statement.kind {
        StatementKind::Let { name, value } => {
            let ty = analyze_expression(value, table, functions)?;
            if table.contains_in_current(*name) {
                return Err(SemanticError::new(
                    "identificador já declarado neste escopo",
                    statement.span,
                ));
            }
            table.insert(*name, ty, statement.span);
        }
        StatementKind::Assign { target, value } => {
            let ty = analyze_expression(value, table, functions)?;
            let (existing, _) = table
                .lookup(*target)
                .ok_or_else(|| SemanticError::new("variável não declarada", statement.span))?;
            if existing != ty {
                return Err(SemanticError::new(
                    format!(
                        "atribuição inválida: {} esperado, obteve {}",
                        existing.name(),
                        ty.name()
                    ),
                    statement.span,
                ));
            }
        }
        StatementKind::If {
            cond,
            then_branch,
            else_branch,
        } => {
            let cond_ty = analyze_expression(cond, table, functions)?;
            if cond_ty != Type::Boolean {
                return Err(SemanticError::new(
                    format!("condição deve ser boolean, obteve {}", cond_ty.name()),
                    cond.span,
                ));
            }
            analyze_block(then_branch, table, functions, inferred_return)?;
            if let Some(else_branch) = else_branch {
                analyze_block(else_branch, table, functions, inferred_return)?;
            }
        }
        StatementKind::While { cond, body } => {
            let cond_ty = analyze_expression(cond, table, functions)?;
            if cond_ty != Type::Boolean {
                return Err(SemanticError::new(
                    format!("condição deve ser boolean, obteve {}", cond_ty.name()),
                    cond.span,
                ));
            }
            analyze_block(body, table, functions, inferred_return)?;
        }
        StatementKind::Return { value } => {
            let ty = analyze_expression(value, table, functions)?;
            match inferred_return {
                Some(expected) if *expected != ty => {
                    return Err(SemanticError::new(
                        format!(
                            "tipo de retorno inconsistente: {} vs {}",
                            expected.name(),
                            ty.name()
                        ),
                        statement.span,
                    ));
                }
                None => {
                    *inferred_return = Some(ty);
                }
                _ => {}
            }
        }
        StatementKind::Expr(expr) => {
            analyze_expression(expr, table, functions)?;
        }
    }
    Ok(())
}

fn analyze_expression(
    expression: &Expression,
    table: &SymbolTable,
    functions: &IndexMap<Symbol, FunctionInfo>,
) -> Result<Type, SemanticError> {
    match &expression.kind {
        ExpressionKind::Number(_) => Ok(Type::Numerus),
        ExpressionKind::Bool(_) => Ok(Type::Boolean),
        ExpressionKind::Symbol(sym) => table
            .lookup(*sym)
            .map(|(ty, _)| ty)
            .ok_or_else(|| SemanticError::new("símbolo não declarado", expression.span)),
        ExpressionKind::Binary { op, left, right } => {
            let left_ty = analyze_expression(left, table, functions)?;
            let right_ty = analyze_expression(right, table, functions)?;
            match op {
                BinaryOp::Add | BinaryOp::Sub | BinaryOp::Mul | BinaryOp::Div => {
                    if left_ty != Type::Numerus || right_ty != Type::Numerus {
                        Err(SemanticError::new(
                            "operações aritméticas exigem numerus",
                            expression.span,
                        ))
                    } else {
                        Ok(Type::Numerus)
                    }
                }
                BinaryOp::Eq
                | BinaryOp::Ne
                | BinaryOp::Lt
                | BinaryOp::Le
                | BinaryOp::Gt
                | BinaryOp::Ge => {
                    if left_ty != right_ty {
                        Err(SemanticError::new(
                            "comparações exigem operandos compatíveis",
                            expression.span,
                        ))
                    } else {
                        Ok(Type::Boolean)
                    }
                }
            }
        }
        ExpressionKind::Call { callee, args } => {
            let info = functions
                .get(callee)
                .ok_or_else(|| SemanticError::new("função não declarada", expression.span))?;
            for arg in args {
                analyze_expression(arg, table, functions)?;
            }
            Ok(info.return_type.unwrap_or(Type::Numerus))
        }
    }
}
