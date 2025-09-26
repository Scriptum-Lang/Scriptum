use scriptum_lexer::charclass::classify;
use scriptum_lexer::pipeline::{build_tokens, TokenDefinition};

fn to_data(s: &str) -> Vec<u32> {
    s.chars().map(|c| c as u32).collect()
}

#[test]
fn hopcroft_reduces_states_for_ident() {
    let defs = vec![TokenDefinition {
        name: "TEST_IDENT".into(),
        pattern: "[A-Za-z_][A-Za-z0-9_]*".into(),
        discard: false,
        priority: 0,
    }];
    let built = build_tokens(&defs).expect("pipeline");
    let token = &built[0];
    assert!(token.stats.dfa_states >= token.stats.minimized_states);
    let samples = ["abc", "a1", "_foo"];
    for sample in samples {
        assert_eq!(
            run_min_dfa(&token.dfa, &to_data(sample)),
            Some(sample.len())
        );
    }
    assert_eq!(run_min_dfa(&token.dfa, &to_data("1abc")), None);
}

fn run_min_dfa(dfa: &scriptum_lexer::hopcroft::MinDfa, data: &[u32]) -> Option<usize> {
    let mut state = dfa.start;
    let mut last = if dfa.accept[state].is_some() {
        Some(0)
    } else {
        None
    };
    for (idx, &ch) in data.iter().enumerate() {
        let class = classify(ch) as usize;
        state = dfa.transitions[state][class];
        if dfa.accept[state].is_some() {
            last = Some(idx + 1);
        }
    }
    last
}
