use std::fs;

use glob::glob;
use pretty_assertions::assert_eq;
use proptest::prelude::*;
use scriptum_codegen::generate;

mod support;
use support::{manifest_path, snapshot_name};

#[test]
fn pretty_printer_idempotente_para_programa_basico() {
    let source = "functio soma(numerus a, numerus b) -> numerus { redde a + b; }";
    let parsed = scriptum_parser::parse_module(source).expect("parse");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados: {:?}", parsed.diagnostics);
    let primeiro = generate(&parsed.module);
    let reparse = scriptum_parser::parse_module(&primeiro.formatted).expect("parse2");
    assert!(
        reparse.diagnostics.is_empty(),
        "diagnósticos inesperados: {:?}",
        reparse.diagnostics
    );
    let segundo = generate(&reparse.module);
    assert_eq!(primeiro.formatted, segundo.formatted);
}

#[test]
fn snapshots_codegen_para_exemplos_ok() {
    let base = manifest_path("../../examples/ok");
    assert!(base.exists(), "diretório de exemplos esperado");
    let pattern = format!("{}/**/*.stm", base.display());
    for entry in glob(&pattern).expect("glob inválido") {
        let path = entry.expect("path inválido");
        let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
        let parsed = scriptum_parser::parse_module(&source).expect("parse");
        assert!(
            parsed.diagnostics.is_empty(),
            "diagnósticos inesperados em {:?}: {:?}",
            path,
            parsed.diagnostics
        );
        let output = generate(&parsed.module);
        let snap_name = snapshot_name(&base, &path);
        insta::assert_snapshot!(format!("codegen__{}", snap_name), output.formatted);
    }
}

fn declaracao(mutavel: bool, idx: usize, valor: i32) -> String {
    format!("{} numerus x{} = {};", if mutavel { "mutabilis" } else { "constans" }, idx, valor)
}

fn program_strategy() -> impl Strategy<Value = String> {
    prop::collection::vec((any::<bool>(), 0usize..4, -1000i32..=1000), 0..6).prop_map(|decls| {
        let mut corpo = String::new();
        for (mutable, idx, value) in decls {
            corpo.push_str(&declaracao(mutable, idx, value));
            corpo.push('\n');
        }
        corpo.push_str(&format!("redde {}\n", 0));
        format!("functio randomica() {{\n{}\n}}", corpo)
    })
}

proptest! {
    #[test]
    fn pretty_printer_round_trip(program in program_strategy()) {
        let parsed = scriptum_parser::parse_module(&program).expect("parse");
        prop_assume!(parsed.diagnostics.is_empty());
        let output = generate(&parsed.module);
        let reparsed = scriptum_parser::parse_module(&output.formatted).expect("parse2");
        prop_assume!(reparsed.diagnostics.is_empty());
        let regen = generate(&reparsed.module);
        prop_assert_eq!(output.formatted, regen.formatted);
    }
}
