use std::fs;
use std::path::Path;

use scriptum_parser::parse_module;
use scriptum_types::check_module;

fn parse_and_check(path: &Path) -> Result<(), String> {
    let source = fs::read_to_string(path).map_err(|e| format!("falha ao ler {}: {e}", path.display()))?;
    let parsed = parse_module(&source).map_err(|e| format!("erro de parsing em {}: {}", path.display(), e.message))?;
    if !parsed.diagnostics.is_empty() {
        return Err(format!("diagnósticos de parsing em {}", path.display()));
    }
    let out = check_module(&parsed.module);
    if out.diagnostics.is_empty() {
        Ok(())
    } else {
        Err(format!("{} diagnósticos em {}", out.diagnostics.len(), path.display()))
    }
}

#[test]
fn valid_programs_compile() {
    let dirs = ["examples/basicos", "examples/intermediarios", "examples/avancados"];
    for dir in dirs {
        for entry in fs::read_dir(dir).expect("não foi possível ler exemplos") {
            let path = entry.expect("erro lendo exemplo").path();
            if path.extension().and_then(|e| e.to_str()) == Some("stm") {
                parse_and_check(&path).unwrap_or_else(|err| panic!("{err}"));
            }
        }
    }
}

#[test]
fn invalid_programs_fail() {
    let dir = Path::new("examples/negativos");
    for entry in fs::read_dir(dir).expect("não foi possível ler exemplos negativos") {
        let path = entry.expect("erro lendo exemplo").path();
        if path.extension().and_then(|e| e.to_str()) == Some("stm") {
            assert!(parse_and_check(&path).is_err(), "esperava erro em {}", path.display());
        }
    }
}
