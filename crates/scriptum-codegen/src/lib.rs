#![forbid(unsafe_code)]
#![deny(unused_must_use)]

//! Geração de código Scriptum: pretty-printer baseado em IR.

use std::fmt::Write;

use scriptum_ast::{Module, StringInterner, Symbol, UnaryOp};
use scriptum_ir::{
    lower_module, FunctionIr, IrExpr, IrLambdaBody, IrLiteral, IrStmt, IrTypeExpr, IrTypeExprKind,
    ModuleIr,
};

/// Resultado completo da geração de código.
pub struct CodegenOutput {
    pub ir: ModuleIr,
    pub formatted: String,
}

/// Converte um módulo Scriptum em código formatado.
pub fn generate(module: &Module) -> CodegenOutput {
    let ir = lower_module(module);
    let mut printer = PrettyPrinter::new(&module.interner);
    printer.module(&ir);
    let formatted = printer.finish();
    CodegenOutput { ir, formatted }
}

struct PrettyPrinter<'a> {
    interner: &'a StringInterner,
    buffer: String,
    indent: usize,
}

impl<'a> PrettyPrinter<'a> {
    fn new(interner: &'a StringInterner) -> Self {
        Self {
            interner,
            buffer: String::new(),
            indent: 0,
        }
    }

    fn finish(self) -> String {
        self.buffer
    }

    fn module(&mut self, module: &ModuleIr) {
        for global in &module.globals {
            self.write_indent();
            let name = self.interner.resolve(global.name);
            if global.mutable {
                self.buffer.push_str("mutabilis ");
            } else {
                self.buffer.push_str("constans ");
            }
            self.buffer.push_str(name);
            if let Some(ty) = &global.ty {
                self.buffer.push_str(": ");
                self.type_expr(ty);
            }
            if let Some(value) = &global.initializer {
                write!(self.buffer, " = ").unwrap();
                self.expr(value);
            }
            self.buffer.push_str(";\n\n");
        }
        for function in &module.functions {
            self.function(function);
            self.buffer.push_str("\n");
        }
    }

    fn function(&mut self, function: &FunctionIr) {
        self.write_indent();
        let name = self.interner.resolve(function.name);
        self.buffer.push_str("functio ");
        self.buffer.push_str(name);
        if !function.generics.is_empty() {
            self.buffer.push('<');
            for (idx, generic) in function.generics.iter().enumerate() {
                if idx > 0 {
                    self.buffer.push_str(", ");
                }
                let generic_name = self.interner.resolve(*generic);
                self.buffer.push_str(generic_name);
            }
            self.buffer.push('>');
        }
        self.buffer.push('(');
        for (idx, param) in function.params.iter().enumerate() {
            if idx > 0 {
                self.buffer.push_str(", ");
            }
            let param_name = self.interner.resolve(param.name);
            self.buffer.push_str(param_name);
            if let Some(ty) = &param.ty {
                self.buffer.push_str(": ");
                self.type_expr(ty);
            }
        }
        self.buffer.push(')');
        if let Some(ret) = &function.return_type {
            self.buffer.push_str(" -> ");
            self.type_expr(ret);
        }
        self.buffer.push(' ');
        self.block(&function.body);
    }

    fn block(&mut self, statements: &[IrStmt]) {
        self.buffer.push_str("{\n");
        self.indent += 1;
        for stmt in statements {
            self.statement(stmt);
        }
        self.indent -= 1;
        self.write_indent();
        self.buffer.push_str("}\n");
    }

    fn statement(&mut self, stmt: &IrStmt) {
        match stmt {
            IrStmt::Let {
                name,
                mutable,
                ty,
                value,
                ..
            } => {
                self.write_indent();
                let name_text = self.interner.resolve(*name);
                if *mutable {
                    self.buffer.push_str("mutabilis ");
                } else {
                    self.buffer.push_str("constans ");
                }
                self.buffer.push_str(name_text);
                if let Some(ty) = ty {
                    write!(self.buffer, ": ").unwrap();
                    self.type_expr(ty);
                }
                if let Some(value) = value {
                    write!(self.buffer, " = ").unwrap();
                    self.expr(value);
                }
                self.buffer.push_str(";\n");
            }
            IrStmt::Expr(expr, _) => {
                self.write_indent();
                self.expr(expr);
                self.buffer.push_str(";\n");
            }
            IrStmt::Return(value, _) => {
                self.write_indent();
                self.buffer.push_str("redde");
                if let Some(expr) = value {
                    self.buffer.push(' ');
                    self.expr(expr);
                }
                self.buffer.push_str(";\n");
            }
            IrStmt::Block(stmts, _) => {
                self.write_indent();
                self.block(stmts);
            }
            IrStmt::If {
                cond,
                then_branch,
                else_branch,
                ..
            } => {
                self.write_indent();
                self.buffer.push_str("si ");
                self.expr(cond);
                self.buffer.push(' ');
                self.block(then_branch);
                if !else_branch.is_empty() {
                    self.write_indent();
                    self.buffer.push_str("aliter ");
                    self.block(else_branch);
                }
            }
            IrStmt::While { cond, body, .. } => {
                self.write_indent();
                self.buffer.push_str("dum ");
                self.expr(cond);
                self.buffer.push(' ');
                self.block(body);
            }
            IrStmt::For {
                binding,
                iterator,
                body,
                ..
            } => {
                self.write_indent();
                let binding_name = self.interner.resolve(*binding);
                self.buffer.push_str("pro ");
                self.buffer.push_str(binding_name);
                self.buffer.push_str(" in ");
                self.expr(iterator);
                self.buffer.push(' ');
                self.block(body);
            }
            IrStmt::Break(_) => {
                self.write_indent();
                self.buffer.push_str("frange;\n");
            }
            IrStmt::Continue(_) => {
                self.write_indent();
                self.buffer.push_str("perge;\n");
            }
        }
    }

    fn expr(&mut self, expr: &IrExpr) {
        match expr {
            IrExpr::Identifier(sym, _) => {
                let name = self.interner.resolve(*sym);
                self.buffer.push_str(name);
            }
            IrExpr::Literal(lit, _) => self.literal(lit),
            IrExpr::Unary { op, expr, .. } => {
                let symbol = match op {
                    UnaryOp::Pos => "+",
                    UnaryOp::Neg => "-",
                    UnaryOp::Not => "!",
                };
                self.buffer.push_str(symbol);
                self.expr(expr);
            }
            IrExpr::Binary {
                op, left, right, ..
            } => {
                self.expr(left);
                self.buffer.push(' ');
                self.buffer.push_str(binary_symbol(*op));
                self.buffer.push(' ');
                self.expr(right);
            }
            IrExpr::Logical {
                op, left, right, ..
            } => {
                self.expr(left);
                self.buffer.push(' ');
                self.buffer.push_str(match op {
                    scriptum_ast::LogicalOp::And => "&&",
                    scriptum_ast::LogicalOp::Or => "||",
                });
                self.buffer.push(' ');
                self.expr(right);
            }
            IrExpr::NullishCoalesce { left, right, .. } => {
                self.expr(left);
                self.buffer.push_str(" ?? ");
                self.expr(right);
            }
            IrExpr::Conditional {
                cond,
                then_branch,
                else_branch,
                ..
            } => {
                self.expr(cond);
                self.buffer.push_str(" ? ");
                self.expr(then_branch);
                self.buffer.push_str(" : ");
                self.expr(else_branch);
            }
            IrExpr::Assignment { target, value, .. } => {
                self.expr(target);
                self.buffer.push_str(" = ");
                self.expr(value);
            }
            IrExpr::Call { callee, args, .. } => {
                self.expr(callee);
                self.buffer.push('(');
                for (idx, arg) in args.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    self.expr(arg);
                }
                self.buffer.push(')');
            }
            IrExpr::Index { target, index, .. } => {
                self.expr(target);
                self.buffer.push('[');
                self.expr(index);
                self.buffer.push(']');
            }
            IrExpr::Member {
                target, property, ..
            } => {
                self.expr(target);
                self.buffer.push('.');
                let property_name = self.interner.resolve(*property);
                self.buffer.push_str(property_name);
            }
            IrExpr::ArrayLiteral(elements, _) => {
                self.buffer.push('[');
                for (idx, element) in elements.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    self.expr(element);
                }
                self.buffer.push(']');
            }
            IrExpr::ObjectLiteral(fields, _) => {
                self.buffer.push_str("structura {");
                for (idx, field) in fields.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    let field_name = self.interner.resolve(field.key);
                    self.buffer.push_str(field_name);
                    self.buffer.push_str(": ");
                    self.expr(&field.value);
                }
                self.buffer.push('}');
            }
            IrExpr::Lambda(lambda, _) => {
                self.buffer.push_str("functio");
                if !lambda.generics.is_empty() {
                    self.buffer.push('<');
                    for (idx, generic) in lambda.generics.iter().enumerate() {
                        if idx > 0 {
                            self.buffer.push_str(", ");
                        }
                        let generic_name = self.interner.resolve(*generic);
                self.buffer.push_str(generic_name);
                    }
                    self.buffer.push('>');
                }
                self.buffer.push('(');
                for (idx, param) in lambda.params.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    let param_name = self.interner.resolve(param.name);
            self.buffer.push_str(param_name);
                    if let Some(ty) = &param.ty {
                        self.buffer.push_str(": ");
                        self.type_expr(ty);
                    }
                }
                self.buffer.push(')');
                if let Some(ret) = &lambda.return_type {
                    self.buffer.push_str(" -> ");
                    self.type_expr(ret);
                }
                match &lambda.body {
                    IrLambdaBody::Expr(expr) => {
                        self.buffer.push_str(" => ");
                        self.expr(expr);
                    }
                    IrLambdaBody::Block(block) => {
                        self.buffer.push(' ');
                        self.block(block);
                    }
                }
            }
        }
    }

    fn literal(&mut self, lit: &IrLiteral) {
        match lit {
            IrLiteral::Numerus(value) => {
                write!(self.buffer, "{}", value).unwrap();
            }
            IrLiteral::Textus(value) => {
                self.buffer.push('"');
                for ch in value.chars() {
                    match ch {
                        '\n' => self.buffer.push_str("\\n"),
                        '\r' => self.buffer.push_str("\\r"),
                        '\t' => self.buffer.push_str("\\t"),
                        '"' => self.buffer.push_str("\\\""),
                        '\\' => self.buffer.push_str("\\\\"),
                        other => self.buffer.push(other),
                    }
                }
                self.buffer.push('"');
            }
            IrLiteral::Booleanum(true) => self.buffer.push_str("verum"),
            IrLiteral::Booleanum(false) => self.buffer.push_str("falsum"),
            IrLiteral::Nullum => self.buffer.push_str("nullum"),
            IrLiteral::Indefinitum => self.buffer.push_str("indefinitum"),
        }
    }

    fn type_expr(&mut self, ty: &IrTypeExpr) {
        match &ty.kind {
            IrTypeExprKind::Simple(sym) => {
                let name = self.interner.resolve(*sym);
                self.buffer.push_str(name);
            }
            IrTypeExprKind::Array(inner) => {
                self.buffer.push('[');
                self.type_expr(inner);
                self.buffer.push(']');
            }
            IrTypeExprKind::Object(fields) => {
                self.buffer.push('{');
                for (idx, field) in fields.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    let field_name = self.interner.resolve(field.name);
                    self.buffer.push_str(field_name);
                    self.buffer.push_str(": ");
                    self.type_expr(&field.ty);
                }
                self.buffer.push('}');
            }
            IrTypeExprKind::Function {
                generics,
                params,
                ret,
            } => {
                self.buffer.push_str("functio");
                if !generics.is_empty() {
                    self.buffer.push('<');
                    for (idx, generic) in generics.iter().enumerate() {
                        if idx > 0 {
                            self.buffer.push_str(", ");
                        }
                        let generic_name = self.interner.resolve(*generic);
                self.buffer.push_str(generic_name);
                    }
                    self.buffer.push('>');
                }
                self.buffer.push('(');
                for (idx, param) in params.iter().enumerate() {
                    if idx > 0 {
                        self.buffer.push_str(", ");
                    }
                    self.type_expr(param);
                }
                self.buffer.push_str(") -> ");
                self.type_expr(ret);
            }
            IrTypeExprKind::Optional(inner) => {
                self.type_expr(inner);
                self.buffer.push('?');
            }
        }
    }

    fn write_indent(&mut self) {
        for _ in 0..self.indent {
            self.buffer.push_str("    ");
        }
    }
}

fn binary_symbol(op: scriptum_ast::BinaryOp) -> &'static str {
    use scriptum_ast::BinaryOp::*;
    match op {
        Power => "**",
        Mul => "*",
        Div => "/",
        Mod => "%",
        Add => "+",
        Sub => "-",
        BitAnd => "&",
        BitOr => "|",
        BitXor => "^",
        ShiftLeft => "<<",
        ShiftRight => ">>",
        Equal => "==",
        StrictEqual => "===",
        NotEqual => "!=",
        StrictNotEqual => "!==",
        Greater => ">",
        GreaterEqual => ">=",
        Less => "<",
        LessEqual => "<=",
        Range => "..",
    }
}
