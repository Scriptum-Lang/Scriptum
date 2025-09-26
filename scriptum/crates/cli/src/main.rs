use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn Error>> {
    let mut args = env::args().skip(1);
    let path = match args.next() {
        Some(p) => PathBuf::from(p),
        None => {
            eprintln!("Uso: scriptum-lex <arquivo>");
            return Ok(());
        }
    };
    let content = fs::read_to_string(&path)?;
    let tokens = scriptum_lexer::tokenize(&content)?;
    for token in tokens {
        println!(
            "{:?}\t{:?}\t{}..{}",
            token.kind, token.lexeme, token.span.0, token.span.1
        );
    }
    Ok(())
}
