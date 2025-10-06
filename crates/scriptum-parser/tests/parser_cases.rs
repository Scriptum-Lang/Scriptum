use std::fs;

use glob::glob;
use pretty_assertions::assert_eq;
use scriptum_ast::{BinaryOp, Expression, ExpressionKind, ItemKind, StatementKind};
use scriptum_parser::parse_module;

mod support;
use support::{manifest_path, snapshot_name};

fn parse_return_expr(source: &str) -> Expression {
    let parsed = parse_module(source).expect("parser executou");
    assert!(
        parsed.diagnostics.is_empty(),
        "diagnosticos inesperados: {:?}",
        parsed.diagnostics
    );
    let module = parsed.module;
    let item = module.items.first().expect("item");
    let function = match &item.kind {
        ItemKind::Function(func) => func,
        _ => panic!("esperava funcao"),
    };
    function
        .body
        .statements
        .iter()
        .find_map(|stmt| match &stmt.kind {
            StatementKind::Return(Some(expr)) => Some(expr.clone()),
            StatementKind::Expr(expr) => Some(expr.clone()),
            _ => None,
        })
        .expect("retorno ou expressao")
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
                other => panic!("esperava multiplicacao, obtive {:?}", other),
            }
        }
        other => panic!("esperava expressao binaria, obtive {:?}", other),
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
                other => panic!("esperava potenciacao direita, obtive {:?}", other),
            }
        }
        other => panic!("esperava potencia, obtive {:?}", other),
    }
}

#[test]
fn ternario_tem_menor_precedencia_que_coalescencia() {
    let expr = parse_return_expr("functio main() { redde a ?? b ? c : d; }");
    match expr.kind {
        ExpressionKind::Conditional {
            condition,
            then_branch,
            else_branch,
        } => {
            match condition.kind {
                ExpressionKind::NullishCoalesce { .. } => {}
                other => panic!("esperava coalescencia no condicional, obtive {:?}", other),
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
    assert!(
        parsed.diagnostics.is_empty(),
        "diagnosticos inesperados: {:?}",
        parsed.diagnostics
    );
    let module = parsed.module;
    let func = match &module.items[0].kind {
        ItemKind::Function(f) => f,
        _ => panic!("esperava funcao"),
    };
    let stmt = func.body.statements.first().expect("stmt inicial");
    let StatementKind::If {
        then_branch,
        else_branch,
        ..
    } = &stmt.kind
    else {
        panic!("esperava if");
    };
    let inner_else = match &then_branch.kind {
        StatementKind::If { else_branch: inner, .. } => {
            assert!(inner.is_some(), "inner else deve existir");
            inner.as_ref().unwrap()
        }
        other => panic!("esperava if aninhado, obtive {:?}", other),
    };
    assert!(else_branch.is_some(), "outer else deve existir");
    match inner_else.kind {
        StatementKind::Return(Some(_)) => {}
        ref other => panic!("esperava retorno no else interno, obtive {:?}", other),
    }
}

#[test]
fn recuperacao_de_erro_reporta_multiplos_diagnosticos() {
    let parsed = parse_module(
        "functio main() { mutabilis numerus x = 1 mutabilis numerus y = 2 redde x + y }",
    )
    .expect("parser executou");
    assert!(
        parsed.diagnostics.len() >= 2,
        "esperava multiplos diagnosticos: {:?}",
        parsed.diagnostics
    );
}

#[test]
fn snapshots_de_sucesso() {
    let base = manifest_path("../../examples/ok");
    assert!(base.exists(), "diretorio de exemplos esperado");
    let pattern = format!("{}/**/*.stm", base.display());
    for entry in glob(&pattern).expect("glob invalido") {
        let path = entry.expect("path invalido");
        let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
        let parsed = parse_module(&source).expect("parser executou");
        assert!(
            parsed.diagnostics.is_empty(),
            "diagnosticos inesperados em {:?}: {:?}",
            path,
            parsed.diagnostics
        );
        let snap_name = snapshot_name(&base, &path);
        insta::assert_json_snapshot!(format!("parser_ok__{}", snap_name), parsed.module);
    }
}

#[test]
fn snapshots_de_erro() {
    let base = manifest_path("../../examples/err");
    assert!(base.exists(), "diretorio de erros esperado");
    let pattern = format!("{}/**/*.stm", base.display());
    for entry in glob(&pattern).expect("glob invalido") {
        let path = entry.expect("path invalido");
        let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
        let parsed = parse_module(&source).expect("parser executou");
        let snap_name = snapshot_name(&base, &path);
        insta::assert_json_snapshot!(format!("parser_err__{}", snap_name), parsed.diagnostics);
    }
}
