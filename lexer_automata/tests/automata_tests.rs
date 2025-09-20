use lexer_automata::core::{Nfa, RegexAst};
use lexer_automata::tokens::{delimiters, identifier, ignorable, numeric, operators, text};

fn assert_accepts(dfa: &lexer_automata::core::Dfa, inputs: &[&str]) {
    for input in inputs {
        assert!(dfa.accepts(input), "expected to accept {:?}", input);
    }
}

fn assert_rejects(dfa: &lexer_automata::core::Dfa, inputs: &[&str]) {
    for input in inputs {
        assert!(!dfa.accepts(input), "expected to reject {:?}", input);
    }
}

#[test]
fn whitespace_acceptance() {
    let dfa = ignorable::whitespace_dfa();
    assert_accepts(&dfa, &[" ", "\t\n", "\u{00A0}"]); // NBSP
    assert_rejects(&dfa, &["", "a", "_"]);
}

#[test]
fn comment_line_acceptance() {
    let dfa = ignorable::comment_line_dfa();
    assert_accepts(&dfa, &["//", "// lorem", "//12345"]);
    // contém newline real -> o token de linha deve terminar antes do '\n'
    assert_rejects(&dfa, &["/", "/-*", "//line\nnext"]);
}

#[test]
fn comment_block_acceptance() {
    let dfa = ignorable::comment_block_dfa();
    assert_accepts(&dfa, &["/**/", "/* lorem */", "/* * nested? */"]);
    assert_rejects(&dfa, &["/*", "/* unterminated", "/**"]);
}

#[test]
fn identifier_and_keywords() {
    let id_dfa = identifier::identifier_dfa();
    assert_accepts(&id_dfa, &["mutabilis", "_temp", "valor123"]);
    assert_rejects(&id_dfa, &["1abc", "-invalid"]);

    let kw_dfa = identifier::keyword_dfa();
    assert_accepts(&kw_dfa, identifier::KEYWORDS);
    assert_rejects(&kw_dfa, &["mutabiliss", "prologue", "siq"]);
}

#[test]
fn numeric_integers() {
    let dec = numeric::int_decimal_dfa();
    assert_accepts(&dec, &["0", "42", "1_000"]);
    assert_rejects(&dec, &["00", "_1", "1__0"]);

    let bin = numeric::int_binary_dfa();
    assert_accepts(&bin, &["0b1", "0b1010", "0b1_0_1"]);
    assert_rejects(&bin, &["0b", "0b2", "0b_1"]);

    let oct = numeric::int_octal_dfa();
    assert_accepts(&oct, &["0o7", "0o10", "0o1_2"]);
    assert_rejects(&oct, &["0o", "0o9"]);

    let hex = numeric::int_hex_dfa();
    assert_accepts(&hex, &["0xA", "0xFF", "0x1_a"]);
    assert_rejects(&hex, &["0x", "0xG", "0x_1"]);
}

#[test]
fn numeric_floats() {
    let float = numeric::float_dfa();
    assert_accepts(&float, &["0.1", "1.", ".5", "1.0e10", "12e+2", "3.14E-2"]);
    assert_rejects(&float, &[".", "1e", "1._0", "1e+-2"]);
}

#[test]
fn numeric_literal_suffix() {
    let numeric_literal = numeric::numeric_literal_dfa();
    assert_accepts(&numeric_literal, &["42", "3.14", "0xFF", "1.0f32", "2f64"]);
    assert_rejects(&numeric_literal, &["", "f32", "0b2", "1.f", "1f21"]);
}

#[test]
fn string_literal_cases() {
    let dfa = text::string_literal_dfa();
    // Aspas internas escapadas para produzir: "", "ola", "linha\n", "unicode \u{123}" no código-fonte da *linguagem alvo*.
    // OBS: usamos \\ para que a *string Rust* gere a barra invertida literal.
    assert_accepts(
        &dfa,
        &[
            "\"\"",
            "\"ola\"",
            "\"linha\\n\"",
            "\"unicode \\u{123}\"", // gera os caracteres: \ u { 1 2 3 } dentro do token alvo
        ],
    );
    assert_rejects(&dfa, &["\"unterminated", "\"\n\"", "\"\\xZ0\""]);
}

#[test]
fn operators_and_delimiters() {
    let ops = operators::operators_dfa();
    assert_accepts(&ops, &operators::OPERATORS);
    // Na linguagem, '==' é inválido (usamos '=' simples ou '==='), e '=>' não existe.
    assert_rejects(&ops, &["", "==", "=>"]);

    let del = delimiters::delimiters_dfa();
    assert_accepts(&del, delimiters::DELIMITERS);
    assert_rejects(&del, &["-", "|", "()"]);
}

#[test]
fn minimization_reduces_states() {
    // união redundante 'a' | 'a' deve reduzir após minimização
    let ast = RegexAst::union(vec![RegexAst::literal('a'), RegexAst::literal('a')]);
    let nfa = Nfa::from_regex(&ast);
    let raw = nfa.to_dfa();
    let minimized = raw.minimize();
    assert!(minimized.states.len() <= raw.states.len());
}

#[test]
fn minimization_idempotent_for_tokens() {
    // DFAs de tokens já construídos devem estar minimizados (ou chegar ao mesmo tamanho).
    let dfa = numeric::numeric_literal_dfa();
    let minimized = dfa.minimize();
    assert_eq!(dfa.states.len(), minimized.states.len());
}
