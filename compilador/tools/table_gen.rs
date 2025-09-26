use scriptum_parser_ll::grammar::BNF;

fn main() {
    println!("Tabela LL(1) derivada da gramática:");
    for line in BNF.lines() {
        println!("{}", line);
    }
}
