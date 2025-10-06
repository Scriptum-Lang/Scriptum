use std::fs;

use glob::glob;
use scriptum_parser::parse_module;
use scriptum_types::{check_module, TypeCheckOutput};

mod support;
use support::{manifest_path, snapshot_name};

fn check(source: &str) -> TypeCheckOutput {
    let parsed = parse_module(source).expect("parser executou");
    assert!(
        parsed.diagnostics.is_empty(),
        "diagnósticos de parsing inesperados: {:?}",
        parsed.diagnostics
    );
    check_module(&parsed.module)
}

#[test]
fn detecta_identificador_nao_declarado() {
    let output = check("functio main() { redde x; }");
    assert!(output.diagnostics.iter().any(|d| d.code == "S100"));
}

#[test]
fn verifica_retorno_incompativel() {
    let output = check("functio main() -> numerus { redde \"texto\"; }");
    assert!(output.diagnostics.iter().any(|d| d.code == "T010"));
}

#[test]
fn aceita_arrays_e_objetos() {
    let output = check(
        "functio main() { mutabilis array<numerus> xs = [1, 2, 3]; \
                          mutabilis { campo: numerus } obj = { campo: 42 }; \
                          redde xs[0] + obj.campo; }",
    );
    assert!(output.diagnostics.is_empty());
}

#[test]
fn impede_atribuicao_em_constantes() {
    let output = check("functio main() { constans numerus x = 1; x = 2; }");
    assert!(output.diagnostics.iter().any(|d| d.code == "T300"));
}

#[test]
fn snapshots_para_programas_com_erro() {
    let base = manifest_path("../../examples/err");
    assert!(base.exists(), "diretório de erros esperado");
    let pattern = format!("{}/**/*.stm", base.display());
    for entry in glob(&pattern).expect("glob inválido") {
        let path = entry.expect("path inválido");
        let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
        let parsed = parse_module(&source).expect("parser executou");
        let output = check_module(&parsed.module);
        let snap_name = snapshot_name(&base, &path);
        insta::assert_json_snapshot!(format!("types_err__{}", snap_name), output.diagnostics);
    }
}
