use std::fs;
use std::path::Path;

use pretty_assertions::assert_eq;
use scriptum_ast::{BinaryOp, Expression, ExpressionKind, ItemKind, StatementKind};
use scriptum_parser::parse_module;

fn parse_return_expr(source: &str) -> Expression {
    let parsed = parse_module(source).expect("parser executou");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados: {:?}", parsed.diagnostics);
    let module = parsed.module;
    let item = module.items.first().expect("item");
    let function = match &item.kind {
        ItemKind::Function(func) => func,
        _ => panic!("esperava função"),
    };
    let stmt = function
        .body
        .statements
        .iter()
        .find_map(|stmt| match &stmt.kind {
            StatementKind::Return(Some(expr)) => Some(expr.clone()),
            StatementKind::Expr(expr) => Some(expr.clone()),
            _ => None,
        })
        .expect("retorno ou expressão");
    stmt
}

#[test]
fn precedencia_multiplicacao_sobre_soma() {
    let expr = parse_return_expr("functio main() { redde 1 + 2 * 3; }");
    match expr.kind {
        ExpressionKind::Binary { op, left, right } => {
            assert_eq!(op, BinaryOp::Add);
            assert!(matches!(left.kind, ExpressionKind::Literal(_)));
            match right.kind {
                ExpressionKind::Binary { op, .. } => assert_eq!(op, BinaryOp::Mul),
                other => panic!("esperava multiplicação, obtive {:?}", other),
            }
        }
        other => panic!("esperava expressão binária, obtive {:?}", other),
    }
}

#[test]
fn precedencia_exponenciacao_direita() {
    let expr = parse_return_expr("functio main() { redde 2 ** 3 ** 2; }");
    match expr.kind {
        ExpressionKind::Binary { op, left, right } => {
            assert_eq!(op, BinaryOp::Power);
            assert!(matches!(left.kind, ExpressionKind::Literal(_)));
            match right.kind {
                ExpressionKind::Binary { op, left: inner_left, .. } => {
                    assert_eq!(op, BinaryOp::Power);
                    assert!(matches!(inner_left.kind, ExpressionKind::Literal(_)));
                }
                other => panic!("esperava potenciação direita, obtive {:?}", other),
            }
        }
        other => panic!("esperava potência, obtive {:?}", other),
    }
}

#[test]
fn ternario_tem_menor_precedencia_que_coalescencia() {
    let expr = parse_return_expr("functio main() { redde a ?? b ? c : d; }");
    match expr.kind {
        ExpressionKind::Conditional { condition, then_branch, else_branch } => {
            match condition.kind {
                ExpressionKind::NullishCoalesce { .. } => {}
                other => panic!("esperava coalescência no condicional, obtive {:?}", other),
            }
            assert!(matches!(then_branch.kind, ExpressionKind::Identifier(_)));
            assert!(matches!(else_branch.kind, ExpressionKind::Identifier(_)));
        }
        other => panic!("esperava condicional, obtive {:?}", other),
    }
}

#[test]
fn dangling_else_associa_ao_si_mais_proximo() {
    let parsed = parse_module(
        "functio decidir() { si verum si falsum redde 1; aliter redde 2; aliter redde 3; }",
    )
    .expect("parser executou");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados: {:?}", parsed.diagnostics);
    let module = parsed.module;
    let func = match &module.items[0].kind {
        ItemKind::Function(f) => f,
        _ => panic!("esperava função"),
    };
    let stmt = func.body.statements.first().expect("stmt inicial");
    let StatementKind::If { then_branch, else_branch, .. } = &stmt.kind else {
        panic!("esperava if");
    };
    let then_if = match &then_branch.kind {
        StatementKind::If { else_branch: inner_else, .. } => {
            assert!(inner_else.is_some(), "inner else deve existir");
            inner_else
        }
        other => panic!("esperava if aninhado, obtive {:?}", other),
    };
    assert!(else_branch.is_some(), "outer else deve existir");
    let inner_else_stmt = then_if.as_ref().unwrap();
    match inner_else_stmt.kind {
        StatementKind::Return(Some(_)) => {}
        ref other => panic!("esperava retorno no else interno, obtive {:?}", other),
    }
}

#[test]
fn recuperacao_de_erro_reporta_multiplos_diagnosticos() {
    let parsed = parse_module("functio main() { mutabilis numerus x = 1 mutabilis numerus y = 2 redde x + y }")
        .expect("parser executou");
    assert!(parsed.diagnostics.len() >= 2, "esperava múltiplos diagnósticos: {:?}", parsed.diagnostics);
}

#[test]
fn snapshots_de_sucesso() {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("examples")
        .join("ok");
    assert!(base.exists(), "diretório de exemplos esperado");
    insta::glob!("../examples/ok/**/*.stm", |path| {
        let source = fs::read_to_string(path).expect("falha ao ler exemplo");
        let parsed = parse_module(&source).expect("parser executou");
        assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados em {:?}: {:?}", path, parsed.diagnostics);
        let snap_name = path
            .strip_prefix(&base)
            .unwrap()
            .with_extension("")
            .to_string_lossy()
            .replace(['\', '/'], "__");
        insta::assert_json_snapshot!(format!("parser_ok__{}", snap_name), parsed.module);
    });
}

#[test]
fn snapshots_de_erro() {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("examples")
        .join("err");
    assert!(base.exists(), "diretório de erros esperado");
    insta::glob!("../examples/err/**/*.stm", |path| {
        let source = fs::read_to_string(path).expect("falha ao ler exemplo");
        let parsed = parse_module(&source).expect("parser executou");
        let snap_name = path
            .strip_prefix(&base)
            .unwrap()
            .with_extension("")
            .to_string_lossy()
            .replace(['\', '/'], "__");
        insta::assert_json_snapshot!(format!("parser_err__{}", snap_name), parsed.diagnostics);
    });
}
