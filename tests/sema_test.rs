use scriptum_parser::parse_module;
use scriptum_types::check_module;

fn check_source(src: &str) -> scriptum_types::TypeCheckOutput {
    let parsed = parse_module(src).expect("parser falhou");
    assert!(parsed.diagnostics.is_empty(), "diagnósticos de parsing inesperados");
    check_module(&parsed.module)
}

#[test]
fn sema_detects_assignment_type_error() {
    let source = "functio init() { mutabilis numerus x = 10; x = verum; redde x; }";
    let result = check_source(source);
    assert!(result.diagnostics.iter().any(|d| d.code.starts_with("T")));
}

#[test]
fn sema_accepts_numeric_program() {
    let source = "functio init() -> numerus { mutabilis numerus x = 10; x = x + 1; redde x; }";
    let result = check_source(source);
    assert!(result.diagnostics.is_empty());
}
