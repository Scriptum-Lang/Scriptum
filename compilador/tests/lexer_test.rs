use scriptum_lexer::{lex, TokenKind};

#[test]
fn lex_identifiers_numbers_and_operators() {
    let source = "definire init() { // comentÃ¡rio\n  definire numero = 42;\n  numero = numero + 8;\n  reditus numero;\n}";
    let tokens = lex(source).expect("lexer falhou");
    assert!(tokens.iter().any(|t| t.kind == TokenKind::Identifier));
    assert!(tokens.iter().any(|t| t.kind == TokenKind::Number));
    assert!(tokens.iter().any(|t| matches!(t.kind, TokenKind::Operator(_))));
}
