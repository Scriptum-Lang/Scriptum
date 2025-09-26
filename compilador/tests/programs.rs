use std::fs;
use std::path::Path;

use scriptum_parser_ll::parse_module;
use scriptum_sema::analyze_module;

#[test]
fn valid_programs_compile() {
    let dir = Path::new("fixtures/programas_validos");
    for entry in fs::read_dir(dir).expect("não foi possível ler fixtures válidos") {
        let entry = entry.expect("erro lendo fixture");
        let source = fs::read_to_string(entry.path()).expect("falha ao ler arquivo válido");
        let module = parse_module(&source).expect("parser falhou em programa válido");
        analyze_module(&module).expect("semântica falhou em programa válido");
    }
}

#[test]
fn invalid_programs_fail() {
    let dir = Path::new("fixtures/programas_com_erro");
    for entry in fs::read_dir(dir).expect("não foi possível ler fixtures de erro") {
        let entry = entry.expect("erro lendo fixture");
        let source = fs::read_to_string(entry.path()).expect("falha ao ler arquivo inválido");
        match parse_module(&source) {
            Ok(module) => {
                assert!(
                    analyze_module(&module).is_err(),
                    "esperava erro semântico em {}",
                    entry.path().display()
                );
            }
            Err(_) => {
                // erros léxicos ou sintáticos são esperados
            }
        }
    }
}
