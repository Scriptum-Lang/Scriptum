use scriptum_codegen::generate;
use scriptum_parser::parse_module;

#[test]
fn fmt_is_idempotent() {
    let source = "functio soma(numerus a, numerus b) -> numerus { redde a + b; }";
    let parsed = parse_module(source).expect("parse falhou");
    assert!(parsed.diagnostics.is_empty());
    let formatted = generate(&parsed.module).formatted;
    let parsed2 = parse_module(&formatted).expect("parse falhou após formatar");
    assert!(parsed2.diagnostics.is_empty());
    let formatted2 = generate(&parsed2.module).formatted;
    assert_eq!(formatted, formatted2);
}
