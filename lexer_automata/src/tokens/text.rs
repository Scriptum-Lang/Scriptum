use crate::core::{Dfa, Nfa, RegexAst};
use crate::tokens::helpers;

fn escape_ast() -> RegexAst {
    let simple = RegexAst::concat(vec![RegexAst::literal('\\'), helpers::simple_escape_symbol()]);
    let hex = RegexAst::concat(vec![
        RegexAst::literal('\\'),
        RegexAst::literal('x'),
        helpers::hex_digit_symbol(),
        helpers::hex_digit_symbol(),
    ]);
    let hex_unit = helpers::hex_digit_symbol();
    let unicode_digits = helpers::repeat_range(&hex_unit, 1, 6);
    let unicode = RegexAst::concat(vec![
        RegexAst::literal('\\'),
        RegexAst::literal('u'),
        RegexAst::literal('{'),
        unicode_digits,
        RegexAst::literal('}'),
    ]);
    RegexAst::union(vec![simple, hex, unicode])
}

pub fn string_literal_dfa() -> Dfa {
    let body_unit = RegexAst::union(vec![helpers::string_body_symbol(), escape_ast()]);
    let ast = RegexAst::concat(vec![
        RegexAst::literal('"'),
        body_unit.clone().star(),
        RegexAst::literal('"'),
    ]);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
