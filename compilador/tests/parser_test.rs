use std::fs;
use std::path::Path;

use scriptum_parser_ll::parse_module;

#[test]
fn parse_valid_fixtures() {
    let dir = Path::new("fixtures/programas_validos");
    for entry in fs::read_dir(dir).expect("não foi possível ler fixtures") {
        let entry = entry.expect("erro lendo entrada");
        let source = fs::read_to_string(entry.path()).expect("falha ao ler arquivo");
        parse_module(&source).expect("parser falhou em fixture válida");
    }
}
