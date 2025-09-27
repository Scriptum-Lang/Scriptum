use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

use scriptum_lexer::{tokenize, LexError, LexToken};

fn main() -> Result<(), Box<dyn Error>> {
    let mut args = env::args().skip(1);
    match args.next() {
        Some(arg) if arg == "--emit-diagrams" => generate_diagrams(),
        Some(path) => lex_file(PathBuf::from(path)),
        None => {
            eprintln!(
                "Uso:\n  cargo run -p scriptum-lexer -- --emit-diagrams\n  cargo run -p scriptum-lexer -- <arquivo.scriptum>"
            );
            Ok(())
        }
    }
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

fn lex_file(path: PathBuf) -> Result<(), Box<dyn Error>> {
    let content = fs::read_to_string(&path)?;
    match tokenize(&content) {
        Ok(tokens) => {
            print_table(&tokens);
            Ok(())
        }
        Err(err) => Err(Box::new(format_lex_error(err, &content, path))),
    }
}

fn format_lex_error(err: LexError, content: &str, path: PathBuf) -> LexErrorWithContext {
    LexErrorWithContext {
        err,
        path,
        line_excerpt: extract_line(content, err.line),
    }
}

fn extract_line(content: &str, target_line: usize) -> String {
    content
        .lines()
        .nth(target_line.saturating_sub(1))
        .unwrap_or("")
        .to_string()
}

fn print_table(tokens: &[LexToken]) {
    println!("{:<30} | {:<20}", "TOKEN", "TIPO");
    println!("{}", "-".repeat(53));
    for token in tokens {
        println!("{:<30} | {:<20}", token.lexeme, token.kind.type_label());
    }
}

struct LexErrorWithContext {
    err: LexError,
    path: PathBuf,
    line_excerpt: String,
}

impl std::fmt::Debug for LexErrorWithContext {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        std::fmt::Display::fmt(self, f)
    }
}

impl std::fmt::Display for LexErrorWithContext {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(
            f,
            "Erro léxico em {}:{}:{}",
            self.path.display(),
            self.err.line,
            self.err.column
        )?;
        if !self.line_excerpt.is_empty() {
            writeln!(f, "    {}", self.line_excerpt)?;
            writeln!(f, "    {}^", " ".repeat(self.err.column.saturating_sub(1)))?;
        }
        write!(f, "{}", self.err)
    }
}

impl std::error::Error for LexErrorWithContext {}
