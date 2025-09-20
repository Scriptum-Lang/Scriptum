use crate::core::{Dfa, Nfa, RegexAst};
use crate::tokens::helpers;

fn with_separators(unit: RegexAst) -> RegexAst {
    let tail = RegexAst::concat(vec![helpers::underscore_symbol().optional(), unit.clone()]);
    RegexAst::concat(vec![unit, tail.star()])
}

fn decimal_int_ast() -> RegexAst {
    let tail = RegexAst::concat(vec![helpers::underscore_symbol().optional(), helpers::digit_symbol()]);
    let non_zero = RegexAst::concat(vec![helpers::non_zero_digit_symbol(), tail.clone().star()]);
    RegexAst::union(vec![RegexAst::literal('0'), non_zero])
}

fn binary_int_ast() -> RegexAst {
    let body = with_separators(helpers::binary_digit_symbol());
    RegexAst::concat(vec![RegexAst::literal_str("0b"), body])
}

fn octal_int_ast() -> RegexAst {
    let body = with_separators(helpers::octal_digit_symbol());
    RegexAst::concat(vec![RegexAst::literal_str("0o"), body])
}

fn hex_int_ast() -> RegexAst {
    let body = with_separators(helpers::hex_digit_symbol());
    RegexAst::concat(vec![RegexAst::literal_str("0x"), body])
}

fn exponent_ast() -> RegexAst {
    RegexAst::concat(vec![
        RegexAst::union(vec![RegexAst::literal('e'), RegexAst::literal('E')]),
        RegexAst::union(vec![RegexAst::literal('+'), RegexAst::literal('-')]).optional(),
        with_separators(helpers::digit_symbol()),
    ])
}

fn float_ast() -> RegexAst {
    let digits = with_separators(helpers::digit_symbol());
    let opt_digits = digits.clone().optional();

    let alt1 = RegexAst::concat(vec![opt_digits, RegexAst::literal('.'), digits.clone()]);
    let alt2 = RegexAst::concat(vec![digits.clone(), RegexAst::literal('.')]);
    let alt3 = RegexAst::concat(vec![
        digits.clone(),
        RegexAst::union(vec![
            exponent_ast(),
            RegexAst::concat(vec![RegexAst::literal('.'), digits.clone(), exponent_ast().optional()]),
        ]),
    ]);

    RegexAst::union(vec![alt1, alt2, alt3])
}

pub fn int_decimal_dfa() -> Dfa {
    Nfa::from_regex(&decimal_int_ast()).to_dfa().minimize()
}

pub fn int_binary_dfa() -> Dfa {
    Nfa::from_regex(&binary_int_ast()).to_dfa().minimize()
}

pub fn int_octal_dfa() -> Dfa {
    Nfa::from_regex(&octal_int_ast()).to_dfa().minimize()
}

pub fn int_hex_dfa() -> Dfa {
    Nfa::from_regex(&hex_int_ast()).to_dfa().minimize()
}

pub fn float_dfa() -> Dfa {
    Nfa::from_regex(&float_ast()).to_dfa().minimize()
}

pub fn numeric_literal_dfa() -> Dfa {
    let suffix = RegexAst::concat(vec![
        RegexAst::union(vec![RegexAst::literal('f'), RegexAst::literal('F')]),
        RegexAst::union(vec![RegexAst::literal_str("32"), RegexAst::literal_str("64")]),
    ]).optional();
    let body = RegexAst::union(vec![
        float_ast(),
        hex_int_ast(),
        binary_int_ast(),
        octal_int_ast(),
        decimal_int_ast(),
    ]);
    let ast = RegexAst::concat(vec![body, suffix]);
    Nfa::from_regex(&ast).to_dfa().minimize()
}
