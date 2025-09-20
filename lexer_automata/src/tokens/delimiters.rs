use crate::core::{Dfa, Nfa};
use crate::tokens::helpers;

pub const DELIMITERS: &[&str] = &[",", ";", ".", "(", ")", "[", "]", "{", "}"];

pub fn delimiters_dfa() -> Dfa {
    let ast = helpers::literal_union(DELIMITERS);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
