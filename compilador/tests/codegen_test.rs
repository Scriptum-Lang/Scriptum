use scriptum_codegen::{emit_module, lower_module};
use scriptum_parser_ll::parse_module;

#[test]
fn codegen_emits_bytecode() {
    let source = "def init() {\n  def x = 1;\n  reditus x + 2;\n}";
    let module = parse_module(source).expect("parse falhou");
    let ir = lower_module(&module);
    let bytes = emit_module(&ir);
    assert!(bytes.starts_with(b"SBC0"));
    assert!(bytes.len() > 8);
}
