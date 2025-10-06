use scriptum_lexer::{lex, tokens::TokenKind};

#[test]
fn lex_identifiers_numbers_and_operators() {
    let source = "functio init() { mutabilis numerus valor = 42; valor = valor + 8 ?? 0; redde valor; }";
    let tokens = lex(source).expect("lexer falhou");
    assert!(tokens.iter().any(|t| t.kind == TokenKind::Identifier));
    assert!(tokens.iter().any(|t| t.kind == TokenKind::NumeroLiteral));
    assert!(tokens
        .iter()
        .any(|t| matches!(t.kind, TokenKind::Operator(_))));
}
