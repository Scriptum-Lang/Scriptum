use std::fs;

use glob::glob;
use pretty_assertions::assert_eq;
use scriptum_ir::lower_module;

mod support;
use support::{manifest_path, snapshot_name};

#[test]
fn lowering_preserva_elems_basicos() {
    let source = "functio soma(numerus a, numerus b) -> numerus { redde a + b; }
                   mutabilis numerus global = 1;";
    let parsed = scriptum_parser::parse_module(source).expect("parse");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos inesperados: {:?}", parsed.diagnostics);
    let ir = lower_module(&parsed.module);
    assert_eq!(ir.functions.len(), 1);
    assert_eq!(ir.globals.len(), 1);
}

#[test]
fn snapshots_ir_para_exemplos_ok() {
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
        let ir = lower_module(&parsed.module);
        let snap_name = snapshot_name(&base, &path);
        insta::assert_json_snapshot!(format!("ir_ok__{}", snap_name), ir);
    }
}
