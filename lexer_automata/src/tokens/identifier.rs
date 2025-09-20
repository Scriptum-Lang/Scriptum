use crate::core::{Dfa, Nfa, RegexAst};
use crate::tokens::helpers;

pub const KEYWORDS: &[&str] = &[
    "mutabilis", "constans", "functio", "classis", "structor", "novum", "hoc", "super",
    "si", "aliter", "dum", "pro", "in", "de", "redde", "frange", "perge",
    "verum", "falsum", "nullum", "indefinitum",
    "numerus", "textus", "booleanum", "vacuum", "quodlibet",
];

pub fn identifier_dfa() -> Dfa {
    let start = RegexAst::union(vec![helpers::underscore_symbol(), helpers::xid_start_symbol()]);
    let tail_unit = RegexAst::union(vec![helpers::underscore_symbol(), helpers::xid_continue_symbol()]);
    let ast = RegexAst::concat(vec![start, tail_unit.star()]);
    Nfa::from_regex(&ast).to_dfa().minimize()
}

pub fn keyword_dfa() -> Dfa {
    let ast = helpers::literal_union(KEYWORDS);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
