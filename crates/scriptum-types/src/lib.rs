#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Verificador de tipos e tabela de símbolos da linguagem Scriptum.

use std::collections::HashMap;

use indexmap::IndexMap;

use scriptum_ast::{
    BinaryOp, Block, Expression, ExpressionKind, Function, Item, ItemKind, Literal, LogicalOp,
    Module, Statement, StatementKind, Symbol, TypeExpr, TypeExprKind, UnaryOp, VarDecl,
};
use scriptum_utils::Span;

/// Resultado da checagem de tipos.
#[derive(Debug, Default, serde::Serialize)]
pub struct TypeCheckOutput {
    pub diagnostics: Vec<TypeDiagnostic>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct TypeDiagnostic {
    pub code: &'static str,
    pub message: String,
    pub span: Span,
    pub notes: Vec<String>,
}

impl TypeDiagnostic {
    fn new(code: &'static str, message: impl Into<String>, span: Span) -> Self {
        Self {
            code,
            message: message.into(),
            span,
            notes: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Type {
    Numerus,
    Textus,
    Booleanum,
    Vacuum,
    Nullum,
    Indefinitum,
    Quodlibet,
    Array(Box<Type>),
    Object(IndexMap<Symbol, Type>),
    Function { params: Vec<Type>, ret: Box<Type> },
    Optional(Box<Type>),
}

impl Type {
    pub fn name(&self, interner: &scriptum_ast::StringInterner) -> String {
        match self {
            Type::Numerus => "numerus".into(),
            Type::Textus => "textus".into(),
            Type::Booleanum => "booleanum".into(),
            Type::Vacuum => "vacuum".into(),
            Type::Nullum => "nullum".into(),
            Type::Indefinitum => "indefinitum".into(),
            Type::Quodlibet => "quodlibet".into(),
            Type::Array(inner) => format!("array<{}>", inner.name(interner)),
            Type::Object(fields) => {
                let mut pieces = Vec::new();
                for (key, value) in fields.iter() {
                    pieces.push(format!(
                        "{}: {}",
                        interner.resolve(*key),
                        value.name(interner)
                    ));
                }
                format!("{{{}}}", pieces.join(", "))
            }
            Type::Function { params, ret } => {
                let params = params
                    .iter()
                    .map(|ty| ty.name(interner))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("functio({}) -> {}", params, ret.name(interner))
            }
            Type::Optional(inner) => format!("{}?", inner.name(interner)),
        }
    }
}

#[derive(Debug)]
pub struct SymbolTable {
    scopes: Vec<HashMap<Symbol, SymbolInfo>>,
}

#[derive(Debug, Clone)]
struct SymbolInfo {
    ty: Type,
    mutable: bool,
    span: Span,
}

impl SymbolTable {
    pub fn new() -> Self {
        Self {
            scopes: vec![HashMap::new()],
        }
    }

    pub fn enter_scope(&mut self) {
        self.scopes.push(HashMap::new());
    }

    pub fn exit_scope(&mut self) {
        self.scopes.pop();
    }

    pub fn insert(&mut self, symbol: Symbol, info: SymbolInfo) -> Option<SymbolInfo> {
        self.scopes
            .last_mut()
            .expect("há sempre um escopo")
            .insert(symbol, info)
    }

    pub fn get(&self, symbol: Symbol) -> Option<&SymbolInfo> {
        for scope in self.scopes.iter().rev() {
            if let Some(info) = scope.get(&symbol) {
                return Some(info);
            }
        }
        None
    }

    pub fn contains_in_current(&self, symbol: Symbol) -> bool {
        self.scopes
            .last()
            .map(|scope| scope.contains_key(&symbol))
            .unwrap_or(false)
    }
}

/// Executa a checagem de tipos de um módulo.
pub fn check_module(module: &Module) -> TypeCheckOutput {
    let mut checker = Checker::new(module);
    checker.visit_module();
    TypeCheckOutput {
        diagnostics: checker.diagnostics,
    }
}

struct Checker<'a> {
    module: &'a Module,
    interner: &'a scriptum_ast::StringInterner,
    diagnostics: Vec<TypeDiagnostic>,
    symbols: SymbolTable,
    functions: HashMap<Symbol, FunctionSignature>,
    current_return: Option<Type>,
}

#[derive(Debug, Clone)]
struct FunctionSignature {
    params: Vec<Type>,
    ret: Type,
}

impl<'a> Checker<'a> {
    fn new(module: &'a Module) -> Self {
        Self {
            module,
            interner: &module.interner,
            diagnostics: Vec::new(),
            symbols: SymbolTable::new(),
            functions: HashMap::new(),
            current_return: None,
        }
    }

    fn visit_module(&mut self) {
        for item in &self.module.items {
            if let ItemKind::Function(function) = &item.kind {
                let signature = self.function_signature(function);
                self.functions.insert(function.name, signature);
            }
        }
        for item in &self.module.items {
            match &item.kind {
                ItemKind::Function(function) => self.visit_function(function),
                ItemKind::Let(decl) => self.declare_global(decl, item.span),
            }
        }
    }

    fn declare_global(&mut self, decl: &VarDecl, span: Span) {
        if self.symbols.contains_in_current(decl.name) {
            let name = self.interner.resolve(decl.name);
            self.diagnostics.push(TypeDiagnostic::new(
                "S001",
                format!("variável '{}' já declarada", name),
                span,
            ));
            return;
        }
        let ty = decl
            .type_annotation
            .as_ref()
            .map(|ty| self.resolve_type_expr(ty))
            .unwrap_or(Type::Quodlibet);
        let init_ty = decl
            .initializer
            .as_ref()
            .map(|expr| self.visit_expr(expr))
            .unwrap_or(Type::Vacuum);
        if let Some(init) = &decl.initializer {
            if let Some(annot) = &decl.type_annotation {
                if !self.is_assignable(&ty, &init_ty) {
                    let msg = format!(
                        "tipo incompatível: esperado {}, obtido {}",
                        ty.name(self.interner),
                        init_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T005", msg, init.span));
                }
            }
        }
        self.symbols.insert(
            decl.name,
            SymbolInfo {
                ty,
                mutable: decl.mutable,
                span,
            },
        );
    }

    fn visit_function(&mut self, function: &Function) {
        self.symbols.enter_scope();
        let signature = self
            .functions
            .get(&function.name)
            .cloned()
            .unwrap_or(FunctionSignature {
                params: vec![Type::Quodlibet; function.params.len()],
                ret: Type::Quodlibet,
            });
        for (param, ty) in function.params.iter().zip(signature.params.iter()) {
            self.symbols.insert(
                param.name,
                SymbolInfo {
                    ty: ty.clone(),
                    mutable: true,
                    span: param.span,
                },
            );
        }
        let prev_return = self.current_return.clone();
        self.current_return = Some(signature.ret.clone());
        self.visit_block(&function.body);
        self.current_return = prev_return;
        self.symbols.exit_scope();
    }

    fn function_signature(&self, function: &Function) -> FunctionSignature {
        let mut params = Vec::new();
        for param in &function.params {
            let ty = param
                .ty
                .as_ref()
                .map(|ty| self.resolve_type_expr(ty))
                .unwrap_or(Type::Quodlibet);
            params.push(ty);
        }
        let ret = function
            .return_type
            .as_ref()
            .map(|ty| self.resolve_type_expr(ty))
            .unwrap_or(Type::Vacuum);
        FunctionSignature { params, ret }
    }

    fn visit_block(&mut self, block: &Block) {
        self.symbols.enter_scope();
        for statement in &block.statements {
            self.visit_statement(statement);
        }
        self.symbols.exit_scope();
    }

    fn visit_statement(&mut self, statement: &Statement) {
        match &statement.kind {
            StatementKind::Let(decl) | StatementKind::Const(decl) => {
                if self.symbols.contains_in_current(decl.name) {
                    let name = self.interner.resolve(decl.name);
                    self.diagnostics.push(TypeDiagnostic::new(
                        "S001",
                        format!("variável '{}' já declarada neste escopo", name),
                        statement.span,
                    ));
                    return;
                }
                let ty = decl
                    .type_annotation
                    .as_ref()
                    .map(|ty| self.resolve_type_expr(ty))
                    .unwrap_or(Type::Quodlibet);
                let init_ty = decl
                    .initializer
                    .as_ref()
                    .map(|expr| self.visit_expr(expr))
                    .unwrap_or(Type::Vacuum);
                if let Some(annot) = &decl.type_annotation {
                    if !self.is_assignable(&ty, &init_ty) {
                        let msg = format!(
                            "tipo incompatível: esperado {}, obtido {}",
                            ty.name(self.interner),
                            init_ty.name(self.interner)
                        );
                        self.diagnostics
                            .push(TypeDiagnostic::new("T005", msg, annot.span));
                    }
                }
                self.symbols.insert(
                    decl.name,
                    SymbolInfo {
                        ty: if decl.type_annotation.is_some() {
                            ty
                        } else {
                            init_ty
                        },
                        mutable: decl.mutable,
                        span: statement.span,
                    },
                );
            }
            StatementKind::Expr(expr) => {
                self.visit_expr(expr);
            }
            StatementKind::Return(value) => {
                let expr_ty = value.as_ref().map(|expr| self.visit_expr(expr));
                if let Some(expected) = &self.current_return {
                    match (expected, expr_ty) {
                        (Type::Vacuum, None) | (Type::Vacuum, Some(Type::Vacuum)) => {}
                        (expected, Some(found)) => {
                            if !self.is_assignable(expected, &found) {
                                let msg = format!(
                                    "retorno incompatível: esperado {}, obteve {}",
                                    expected.name(self.interner),
                                    found.name(self.interner)
                                );
                                let span = value
                                    .as_ref()
                                    .map(|expr| expr.span)
                                    .unwrap_or(statement.span);
                                self.diagnostics
                                    .push(TypeDiagnostic::new("T010", msg, span));
                            }
                        }
                        (expected, None) => {
                            if *expected != Type::Vacuum {
                                let msg = format!(
                                    "retorno incompatível: esperado {}, obteve vazio",
                                    expected.name(self.interner)
                                );
                                self.diagnostics.push(TypeDiagnostic::new(
                                    "T010",
                                    msg,
                                    statement.span,
                                ));
                            }
                        }
                    }
                }
            }
            StatementKind::Block(block) => self.visit_block(block),
            StatementKind::If {
                condition,
                then_branch,
                else_branch,
            } => {
                let cond_ty = self.visit_expr(condition);
                if cond_ty != Type::Booleanum && cond_ty != Type::Quodlibet {
                    let msg = format!(
                        "condição precisa ser booleanum, obteve {}",
                        cond_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T020", msg, condition.span));
                }
                self.visit_statement(then_branch);
                if let Some(else_branch) = else_branch {
                    self.visit_statement(else_branch);
                }
            }
            StatementKind::While { condition, body } => {
                let cond_ty = self.visit_expr(condition);
                if cond_ty != Type::Booleanum && cond_ty != Type::Quodlibet {
                    let msg = format!(
                        "condição precisa ser booleanum, obteve {}",
                        cond_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T021", msg, condition.span));
                }
                self.visit_statement(body);
            }
            StatementKind::For {
                binding,
                iterator,
                body,
            } => {
                let iter_ty = self.visit_expr(iterator);
                let element_ty = match iter_ty {
                    Type::Array(inner) => *inner,
                    Type::Quodlibet => Type::Quodlibet,
                    other => {
                        let msg = format!("tipo '{}' não é iterável", other.name(self.interner));
                        self.diagnostics
                            .push(TypeDiagnostic::new("T030", msg, iterator.span));
                        Type::Quodlibet
                    }
                };
                self.symbols.enter_scope();
                self.symbols.insert(
                    *binding,
                    SymbolInfo {
                        ty: element_ty,
                        mutable: true,
                        span: body.span,
                    },
                );
                self.visit_statement(body);
                self.symbols.exit_scope();
            }
            StatementKind::Break(_) | StatementKind::Continue(_) => {}
        }
    }

    fn visit_expr(&mut self, expr: &Expression) -> Type {
        match &expr.kind {
            ExpressionKind::Identifier(symbol) => {
                if let Some(info) = self.symbols.get(*symbol) {
                    info.ty.clone()
                } else if let Some(function) = self.functions.get(symbol) {
                    Type::Function {
                        params: function.params.clone(),
                        ret: Box::new(function.ret.clone()),
                    }
                } else {
                    let name = self.interner.resolve(*symbol);
                    self.diagnostics.push(TypeDiagnostic::new(
                        "S100",
                        format!("identificador '{}' não declarado", name),
                        expr.span,
                    ));
                    Type::Quodlibet
                }
            }
            ExpressionKind::Literal(lit) => match lit {
                Literal::Numerus(_) => Type::Numerus,
                Literal::Textus(_) => Type::Textus,
                Literal::Booleanum(_) => Type::Booleanum,
                Literal::Nullum => Type::Nullum,
                Literal::Indefinitum => Type::Indefinitum,
            },
            ExpressionKind::Unary { op, expr } => {
                let ty = self.visit_expr(expr);
                match op {
                    UnaryOp::Pos | UnaryOp::Neg => {
                        if ty != Type::Numerus && ty != Type::Quodlibet {
                            let msg = format!(
                                "operador unário requer numerus, obteve {}",
                                ty.name(self.interner)
                            );
                            self.diagnostics
                                .push(TypeDiagnostic::new("T101", msg, expr.span));
                        }
                        Type::Numerus
                    }
                    UnaryOp::Not => Type::Booleanum,
                }
            }
            ExpressionKind::Binary { op, left, right } => {
                let left_ty = self.visit_expr(left);
                let right_ty = self.visit_expr(right);
                self.type_binary(*op, left, &left_ty, right, &right_ty)
            }
            ExpressionKind::Logical { op: _, left, right } => {
                let left_ty = self.visit_expr(left);
                let right_ty = self.visit_expr(right);
                if left_ty != Type::Booleanum {
                    let msg = format!(
                        "operador lógico requer booleanum, obteve {}",
                        left_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T110", msg, left.span));
                }
                if right_ty != Type::Booleanum {
                    let msg = format!(
                        "operador lógico requer booleanum, obteve {}",
                        right_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T110", msg, right.span));
                }
                Type::Booleanum
            }
            ExpressionKind::NullishCoalesce { left, right } => {
                let left_ty = self.visit_expr(left);
                let right_ty = self.visit_expr(right);
                match left_ty {
                    Type::Nullum | Type::Indefinitum => right_ty,
                    Type::Optional(inner) => *inner,
                    other => other,
                }
            }
            ExpressionKind::Conditional {
                condition,
                then_branch,
                else_branch,
            } => {
                let cond_ty = self.visit_expr(condition);
                if cond_ty != Type::Booleanum && cond_ty != Type::Quodlibet {
                    let msg = format!(
                        "condição do operador ternário deve ser booleanum, obteve {}",
                        cond_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T111", msg, condition.span));
                }
                let then_ty = self.visit_expr(then_branch);
                let else_ty = self.visit_expr(else_branch);
                if self.is_assignable(&then_ty, &else_ty) {
                    then_ty
                } else if self.is_assignable(&else_ty, &then_ty) {
                    else_ty
                } else {
                    Type::Quodlibet
                }
            }
            ExpressionKind::Assignment { target, value } => {
                if let ExpressionKind::Identifier(symbol) = &target.as_ref().kind {
                    if let Some(info) = self.symbols.get(*symbol) {
                        if !info.mutable {
                            let name = self.interner.resolve(*symbol);
                            self.diagnostics.push(TypeDiagnostic::new(
                                "S200",
                                format!("variável '{}' é imutável", name),
                                target.span,
                            ));
                        }
                    }
                }
                let target_ty = self.visit_expr(target);
                let value_ty = self.visit_expr(value);
                if !self.is_assignable(&target_ty, &value_ty) {
                    let msg = format!(
                        "atribuição inválida: {} não compatível com {}",
                        value_ty.name(self.interner),
                        target_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T200", msg, value.span));
                }
                target_ty
            }
            ExpressionKind::Call { callee, arguments } => {
                let callee_ty = self.visit_expr(callee);
                if let Type::Function { params, ret } = callee_ty {
                    if params.len() != arguments.len() {
                        let msg = format!(
                            "número de argumentos incorreto: esperado {}, obteve {}",
                            params.len(),
                            arguments.len()
                        );
                        self.diagnostics
                            .push(TypeDiagnostic::new("T300", msg, expr.span));
                    }
                    for (expected, arg) in params.iter().zip(arguments.iter()) {
                        let arg_ty = self.visit_expr(arg);
                        if !self.is_assignable(expected, &arg_ty) {
                            let msg = format!(
                                "argumento incompatível: esperado {}, obteve {}",
                                expected.name(self.interner),
                                arg_ty.name(self.interner)
                            );
                            self.diagnostics
                                .push(TypeDiagnostic::new("T301", msg, arg.span));
                        }
                    }
                    *ret
                } else {
                    self.diagnostics.push(TypeDiagnostic::new(
                        "T302",
                        "tentativa de chamar algo que não é functio",
                        callee.span,
                    ));
                    Type::Quodlibet
                }
            }
            ExpressionKind::Index { target, index } => {
                let target_ty = self.visit_expr(target);
                let index_ty = self.visit_expr(index);
                if index_ty != Type::Numerus && index_ty != Type::Quodlibet {
                    let msg = format!(
                        "índice precisa ser numerus, obteve {}",
                        index_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T400", msg, index.span));
                }
                match target_ty {
                    Type::Array(inner) => *inner,
                    Type::Quodlibet => Type::Quodlibet,
                    other => {
                        let msg =
                            format!("tipo '{}' não suporta indexação", other.name(self.interner));
                        self.diagnostics
                            .push(TypeDiagnostic::new("T401", msg, target.span));
                        Type::Quodlibet
                    }
                }
            }
            ExpressionKind::Member { target, property } => {
                let target_ty = self.visit_expr(target);
                match target_ty {
                    Type::Object(fields) => {
                        fields.get(property).cloned().unwrap_or(Type::Quodlibet)
                    }
                    Type::Quodlibet => Type::Quodlibet,
                    other => {
                        let msg =
                            format!("tipo '{}' não possui membros", other.name(self.interner));
                        self.diagnostics
                            .push(TypeDiagnostic::new("T410", msg, target.span));
                        Type::Quodlibet
                    }
                }
            }
            ExpressionKind::ArrayLiteral(values) => {
                let mut element_ty = Type::Quodlibet;
                for value in values {
                    let ty = self.visit_expr(value);
                    if element_ty == Type::Quodlibet {
                        element_ty = ty;
                    } else if !self.is_assignable(&element_ty, &ty) {
                        element_ty = Type::Quodlibet;
                    }
                }
                Type::Array(Box::new(element_ty))
            }
            ExpressionKind::ObjectLiteral(fields) => {
                let mut map = IndexMap::new();
                for field in fields {
                    let ty = self.visit_expr(&field.value);
                    map.insert(field.key, ty);
                }
                Type::Object(map)
            }
            ExpressionKind::Lambda(lambda) => {
                let params = lambda
                    .params
                    .iter()
                    .map(|param| {
                        param
                            .ty
                            .as_ref()
                            .map(|ty| self.resolve_type_expr(ty))
                            .unwrap_or(Type::Quodlibet)
                    })
                    .collect();
                let ret = lambda
                    .return_type
                    .as_ref()
                    .map(|ty| self.resolve_type_expr(ty))
                    .unwrap_or(Type::Vacuum);
                Type::Function {
                    params,
                    ret: Box::new(ret),
                }
            }
        }
    }

    fn type_binary(
        &mut self,
        op: BinaryOp,
        left: &Expression,
        left_ty: &Type,
        right: &Expression,
        right_ty: &Type,
    ) -> Type {
        use BinaryOp::*;
        match op {
            Add | Sub | Mul | Div | Mod | Power => {
                self.ensure_numeric(left, left_ty);
                self.ensure_numeric(right, right_ty);
                Type::Numerus
            }
            Equal | NotEqual | StrictEqual | StrictNotEqual | Greater | GreaterEqual | Less
            | LessEqual => {
                if !self.is_assignable(left_ty, right_ty) && !self.is_assignable(right_ty, left_ty)
                {
                    let msg = format!(
                        "comparação entre {} e {} pode ser inválida",
                        left_ty.name(self.interner),
                        right_ty.name(self.interner)
                    );
                    self.diagnostics
                        .push(TypeDiagnostic::new("T120", msg, left.span));
                }
                Type::Booleanum
            }
            BitAnd | BitOr | BitXor | ShiftLeft | ShiftRight | Range => {
                self.ensure_numeric(left, left_ty);
                self.ensure_numeric(right, right_ty);
                Type::Numerus
            }
        }
    }

    fn ensure_numeric(&mut self, expr: &Expression, ty: &Type) {
        if *ty != Type::Numerus && *ty != Type::Quodlibet {
            let msg = format!("operador requer numerus, obteve {}", ty.name(self.interner));
            self.diagnostics
                .push(TypeDiagnostic::new("T100", msg, expr.span));
        }
    }

    fn resolve_type_expr(&self, ty: &TypeExpr) -> Type {
        match &ty.kind {
            TypeExprKind::Simple(sym) => match self.interner.resolve(*sym) {
                "numerus" => Type::Numerus,
                "textus" => Type::Textus,
                "booleanum" => Type::Booleanum,
                "vacuum" => Type::Vacuum,
                "nullum" => Type::Nullum,
                "indefinitum" => Type::Indefinitum,
                "quodlibet" => Type::Quodlibet,
                _ => Type::Quodlibet,
            },
            TypeExprKind::Array(inner) => Type::Array(Box::new(self.resolve_type_expr(inner))),
            TypeExprKind::Object(fields) => {
                let mut map = IndexMap::new();
                for field in fields {
                    map.insert(field.name, self.resolve_type_expr(&field.ty));
                }
                Type::Object(map)
            }
            TypeExprKind::Function { params, ret, .. } => Type::Function {
                params: params.iter().map(|ty| self.resolve_type_expr(ty)).collect(),
                ret: Box::new(self.resolve_type_expr(ret)),
            },
            TypeExprKind::Optional(inner) => {
                Type::Optional(Box::new(self.resolve_type_expr(inner)))
            }
            TypeExprKind::Tuple(items) => Type::Object(
                items
                    .iter()
                    .enumerate()
                    .map(|(idx, ty)| (Symbol::from_u32(idx as u32), self.resolve_type_expr(ty)))
                    .collect(),
            ),
        }
    }

    fn is_assignable(&self, expected: &Type, found: &Type) -> bool {
        if expected == &Type::Quodlibet || found == &Type::Quodlibet {
            return true;
        }
        match (expected, found) {
            (Type::Numerus, Type::Numerus)
            | (Type::Textus, Type::Textus)
            | (Type::Booleanum, Type::Booleanum)
            | (Type::Vacuum, Type::Vacuum)
            | (Type::Nullum, Type::Nullum)
            | (Type::Indefinitum, Type::Indefinitum) => true,
            (Type::Array(a), Type::Array(b)) => self.is_assignable(a, b),
            (Type::Object(a), Type::Object(b)) => a.iter().all(|(key, ty)| {
                b.get(key)
                    .map_or(false, |value| self.is_assignable(ty, value))
            }),
            (
                Type::Function {
                    params: pa,
                    ret: ra,
                },
                Type::Function {
                    params: pb,
                    ret: rb,
                },
            ) => {
                pa.len() == pb.len()
                    && pa
                        .iter()
                        .zip(pb.iter())
                        .all(|(a, b)| self.is_assignable(a, b))
                    && self.is_assignable(ra, rb)
            }
            (Type::Optional(a), Type::Optional(b)) => self.is_assignable(a, b),
            (Type::Optional(a), other) => {
                self.is_assignable(a, other) || matches!(other, Type::Nullum)
            }
            (other, Type::Optional(b)) => {
                self.is_assignable(other, b) || matches!(other, Type::Nullum)
            }
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use scriptum_parser::parse_module;

    fn check(source: &str) -> TypeCheckOutput {
        let parsed = parse_module(source).expect("parse");
        let module = parsed.module;
        check_module(&module)
    }

    #[test]
    fn detects_missing_variable() {
        let out = check("functio main() { redde x; }");
        assert!(!out.diagnostics.is_empty());
    }

    #[test]
    fn accepts_simple_return() {
        let out = check("functio main() -> numerus { redde 42; }");
        assert!(out.diagnostics.is_empty());
    }
}
