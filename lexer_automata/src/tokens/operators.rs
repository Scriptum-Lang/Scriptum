use crate::core::{Dfa, Nfa};
use crate::tokens::helpers;

pub const OPERATORS: &[&str] = &[
    "**", "===", "!==", "==", "!=", "<=", ">=", "&&", "||", "??", "?.",
    "+=", "-=", "*=", "/=", "%=",
    "+", "-", "*", "/", "%", "=", "<", ">", "!", "?", ":",
];

pub fn operators_dfa() -> Dfa {
    let ast = helpers::literal_union(OPERATORS);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
