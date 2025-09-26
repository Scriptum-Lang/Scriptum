use scriptum_parser_ll::parse_module;
use scriptum_sema::analyze_module;

#[test]
fn sema_detects_assignment_type_error() {
    let source = "definire init() {\n  definire x = 10;\n  x = falsum;\n  reditus x;\n}";
    let module = parse_module(source).expect("parse falhou");
    assert!(analyze_module(&module).is_err());
}

#[test]
fn sema_accepts_numeric_program() {
    let source = "definire init() {\n  definire x = 10;\n  x = x + 1;\n  reditus x;\n}";
    let module = parse_module(source).expect("parse falhou");
    assert!(analyze_module(&module).is_ok());
}
