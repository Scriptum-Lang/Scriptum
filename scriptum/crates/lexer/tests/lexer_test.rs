use scriptum_lexer::{tokenize, TokenKind};

#[test]
fn lex_program_with_keywords_and_comments() {
    let source = "mutabilis x: numerus = 10; // comentario\nredde x;";
    let tokens = tokenize(source).expect("lex");
    let summary: Vec<String> = tokens
        .iter()
        .map(|t| match &t.kind {
            TokenKind::Keyword(kw) => format!("KW:{kw}"),
            TokenKind::Named(name) => format!("TK:{name}"),
        })
        .collect();
    assert_eq!(
        summary,
        vec![
            "KW:mutabilis",
            "TK:IDENT",
            "TK:COLON",
            "KW:numerus",
            "TK:EQUAL",
            "TK:NUMBER",
            "TK:SEMICOLON",
            "KW:redde",
            "TK:IDENT",
            "TK:SEMICOLON",
        ]
    );
}

#[test]
fn lex_reports_error_on_unknown_symbol() {
    let err = tokenize("$").expect_err("should fail");
    assert_eq!(err.position, 0);
}

#[test]
fn lex_splits_minus_from_number() {
    let tokens = tokenize("-42").expect("lex negative");
    assert_eq!(tokens.len(), 2);
    assert_eq!(tokens[0].kind, TokenKind::Named("MINUS"));
    assert_eq!(tokens[1].kind, TokenKind::Named("NUMBER"));
    assert_eq!(tokens[1].lexeme, "42");
}

#[test]
fn lex_handles_optional_chain() {
    let tokens = tokenize("hoc?.prop;").expect("lex optional chain");
    let kinds: Vec<_> = tokens.iter().map(|t| &t.kind).collect();
    assert_eq!(kinds.len(), 4);
    assert_eq!(kinds[0], &TokenKind::Keyword("hoc"));
    assert_eq!(kinds[1], &TokenKind::Named("QUESTION_DOT"));
    assert_eq!(kinds[2], &TokenKind::Named("IDENT"));
    assert_eq!(kinds[3], &TokenKind::Named("SEMICOLON"));
}
