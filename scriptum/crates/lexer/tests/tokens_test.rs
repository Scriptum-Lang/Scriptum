use scriptum_lexer::dfa::run_dfa;
use scriptum_lexer::tokens::{token_dfas, token_specs};

fn find_token_index(name: &str) -> usize {
    let specs = token_specs();
    specs
        .iter()
        .position(|spec| spec.name == name)
        .expect("token not found")
}

#[test]
fn string_literal_accepts_simple() {
    let idx = find_token_index("STRING");
    let dfa = &token_dfas()[idx].dfa;
    let data: Vec<u32> = "\"abc\\n\"".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &data, 0), Some(data.len()));
}

#[test]
fn string_literal_rejects_unclosed() {
    let idx = find_token_index("STRING");
    let dfa = &token_dfas()[idx].dfa;
    let data: Vec<u32> = "\"unterminated".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &data, 0), None);
}

#[test]
fn number_with_exponent() {
    let idx = find_token_index("NUMBER");
    let dfa = &token_dfas()[idx].dfa;
    let valid: Vec<u32> = "12.5e+3".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &valid, 0), Some(valid.len()));

    let negative: Vec<u32> = "-12.5e+3".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &negative, 0), None);
}

#[test]
fn number_plain_integer() {
    let idx = find_token_index("NUMBER");
    let dfa = &token_dfas()[idx].dfa;
    let data: Vec<u32> = "10".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &data, 0), Some(data.len()));
}

#[test]
fn identifier_requires_snake_case() {
    let idx = find_token_index("IDENT");
    let dfa = &token_dfas()[idx].dfa;

    let snake: Vec<u32> = "foo_bar1".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &snake, 0), Some(snake.len()));

    let camel: Vec<u32> = "FooBar".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &camel, 0), None);

    let leading_underscore: Vec<u32> = "_leading".chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &leading_underscore, 0), None);
}

#[test]
fn block_comment_spans_multiple_lines() {
    let idx = find_token_index("BLOCK_COMMENT");
    let dfa = &token_dfas()[idx].dfa;
    let text = "/* comment\n* second line\n*/";
    let data: Vec<u32> = text.chars().map(|c| c as u32).collect();
    assert_eq!(run_dfa(dfa, &data, 0), Some(data.len()));
}
