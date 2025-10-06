use std::fs;

use glob::glob;
use pretty_assertions::assert_eq;
use proptest::prelude::*;
use scriptum_lexer::lex;
use scriptum_lexer::tokens::{Keyword, Operator, Punctuation, TokenKind};

mod support;
use support::{manifest_path, snapshot_name};

fn kinds(source: &str) -> Vec<TokenKind> {
    lex(source)
        .expect("análise léxica bem-sucedida")
        .into_iter()
        .map(|token| token.kind)
        .collect()
}

#[test]
fn reconhece_palavras_chave_e_identificadores() {
    let tokens = kinds("functio mutabilis constans verum falsum nullum indefinitum x");
    assert_eq!(
        tokens,
        vec![
            TokenKind::Keyword(Keyword::Functio),
            TokenKind::Keyword(Keyword::Mutabilis),
            TokenKind::Keyword(Keyword::Constans),
            TokenKind::Keyword(Keyword::Verum),
            TokenKind::Keyword(Keyword::Falsum),
            TokenKind::Keyword(Keyword::Nullum),
            TokenKind::Keyword(Keyword::Indefinitum),
            TokenKind::Identifier,
        ],
    );
}

#[test]
fn reconhece_operadores_compostos() {
    let tokens = kinds("== === != !== ?? ?. -> ::");
    assert_eq!(
        tokens,
        vec![
            TokenKind::Operator(Operator::Equal),
            TokenKind::Operator(Operator::StrictEqual),
            TokenKind::Operator(Operator::NotEqual),
            TokenKind::Operator(Operator::StrictNotEqual),
            TokenKind::Operator(Operator::NullishCoalesce),
            TokenKind::Operator(Operator::QuestionDot),
            TokenKind::Punctuation(Punctuation::Arrow),
            TokenKind::Punctuation(Punctuation::DoubleColon),
        ],
    );
}

#[test]
fn reconhece_numeros_varios_formatos() {
    let tokens = lex("42 3.14 2_500 1.0e-3")
        .expect("ok")
        .into_iter()
        .filter(|t| matches!(t.kind, TokenKind::NumeroLiteral))
        .collect::<Vec<_>>();
    assert_eq!(tokens.len(), 4);
}

#[test]
fn ignora_comentarios_e_whitespace() {
    let tokens = kinds("// comentario\n42 /* bloco */ 13");
    assert_eq!(
        tokens,
        vec![TokenKind::NumeroLiteral, TokenKind::NumeroLiteral],
    );
}

#[test]
fn strings_com_escapes() {
    let tokens = kinds("\"ola\nmundus\"\n\"\"\");
    assert_eq!(
        tokens,
        vec![TokenKind::TextoLiteral, TokenKind::TextoLiteral],
    );
}

#[test]
fn snapshots_para_exemplos_ok() {
    let base = manifest_path("../../examples/ok");
    assert!(base.exists(), "diretório de exemplos esperado");
    let pattern = format!("{}/**/*.stm", base.display());
    for entry in glob(&pattern).expect("glob inválido") {
        let path = entry.expect("path inválido");
        let source = fs::read_to_string(&path).expect("falha ao ler exemplo");
        let tokens = lex(&source).expect("lex");
        let snap_name = snapshot_name(&base, &path);
        insta::assert_json_snapshot!(format!("lexer__{}", snap_name), tokens);
    }
}

proptest! {
    #[test]
    fn lexer_nao_panica_para_ascii(input in proptest::collection::vec(proptest::char::range('\u{0000}', '\u{00FF}'), 0..256)) {
        let texto: String = input.into_iter().collect();
        let _ = scriptum_lexer::lex(&texto);
    }
}
