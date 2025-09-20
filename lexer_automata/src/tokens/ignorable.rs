use crate::core::{Dfa, Nfa, RegexAst};
use crate::tokens::helpers;

pub fn whitespace_dfa() -> Dfa {
    let ast = helpers::whitespace_unit().plus();
    Nfa::from_regex(&ast).to_dfa().minimize()
}

pub fn comment_line_dfa() -> Dfa {
    let ast = RegexAst::concat(vec![
        RegexAst::literal_str("//"),
        helpers::comment_line_body().star(),
    ]);
    Nfa::from_regex(&ast).to_dfa().minimize()
}

pub fn comment_block_dfa() -> Dfa {
    let open = RegexAst::literal_str("/*");
    let close = RegexAst::literal_str("*/");
    let body_unit = RegexAst::union(vec![
        helpers::any_not_star(),
        RegexAst::concat(vec![RegexAst::literal('*').plus(), helpers::any_not_slash()]),
    ]);
    let ast = RegexAst::concat(vec![open, body_unit.star(), close]);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
