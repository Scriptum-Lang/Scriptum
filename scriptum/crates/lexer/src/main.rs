use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--emit-diagrams") {
        generate_diagrams()?;
    } else {
        println!("Uso: cargo run -p scriptum-lexer -- --emit-diagrams");
    }
    Ok(())
}

fn generate_diagrams() -> Result<(), Box<dyn Error>> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let spec_path = manifest_dir.join("../../../gramatica_formal.md");
    let diagrams_path = manifest_dir.join("diagrams/afd.md");
    let content = fs::read_to_string(&spec_path)?;
    let spec_data = scriptum_lexer::spec::parse_spec(&content);
    let defs = scriptum_lexer::spec::build_token_definitions(&spec_data);
    let built = scriptum_lexer::pipeline::build_tokens(&defs)?;
    let mermaid = scriptum_lexer::spec::render_mermaid(&defs, &built);
    if let Some(parent) = diagrams_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&diagrams_path, mermaid)?;
    println!("Diagramas gerados em {}", diagrams_path.display());
    Ok(())
}
