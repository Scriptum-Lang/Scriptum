use std::fs;
use std::path::PathBuf;

use scriptum_parser_ll::grammar::BNF;

fn main() {
    let path = std::env::args().nth(1).map(PathBuf::from);
    if let Some(path) = path {
        let grammar = fs::read_to_string(path).expect("não foi possível ler gramática");
        println!("{}", grammar);
    } else {
        println!("{}", BNF);
    }
}
