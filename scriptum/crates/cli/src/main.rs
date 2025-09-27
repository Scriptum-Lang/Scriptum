use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

use scriptum_lexer::{tokenize, LexToken};

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
    match tokenize(&content) {
        Ok(tokens) => {
            print_table(&tokens);
            Ok(())
        }
        Err(err) => {
            eprintln!(
                "Erro léxico em {}:{}:{} -> {}",
                path.display(),
                err.line,
                err.column,
                err
            );
            Err(Box::new(err))
        }
    }
}

fn print_table(tokens: &[LexToken]) {
    println!("{:<30} | {:<20}", "TOKEN", "TIPO");
    println!("{}", "-".repeat(53));
    for token in tokens {
        println!("{:<30} | {:<20}", token.lexeme, token.kind.type_label());
    }
}
