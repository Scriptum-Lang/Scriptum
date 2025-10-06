use std::fs;
use std::path::Path;

use scriptum_parser::parse_module;

#[test]
fn parse_examples() {
    fn visit(dir: &Path) {
        for entry in fs::read_dir(dir).expect("não foi possível ler diretório") {
            let entry = entry.expect("erro lendo entrada");
            let path = entry.path();
            if path.is_dir() {
                visit(&path);
            } else if path.extension().and_then(|e| e.to_str()) == Some("stm") {
                let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
                let output = parse_module(&source).expect("parser falhou");
                assert!(output.diagnostics.is_empty(), "diagnósticos inesperados em {:?}", path);
            }
        }
    }
    visit(Path::new("examples/ok"));
}
