use crate::charclass::classify;
use crate::tokens::SerializedDfa;

pub fn run_dfa(dfa: &SerializedDfa, data: &[u32], offset: usize) -> Option<usize> {
    let start_state = dfa.start;
    if start_state >= dfa.state_count {
        return None;
    }
    if offset >= data.len() {
        return if dfa.accept[start_state] != 0 {
            Some(offset)
        } else {
            None
        };
    }
    let stride = dfa.class_count;
    let mut state = start_state;
    let mut last_match: Option<usize> = if dfa.accept[start_state] != 0 {
        Some(offset)
    } else {
        None
    };
    let state_count = dfa.state_count;
    for (position, &ch) in data.iter().enumerate().skip(offset) {
        let class = classify(ch) as usize;
        let table_index = state * stride + class;
        if table_index >= dfa.transitions.len() {
            break;
        }
        let next = dfa.transitions[table_index] as usize;
        state = next;
        if state >= state_count {
            break;
        }
        let pos = position + 1;
        if dfa.accept[state] != 0 {
            last_match = Some(pos);
        }
    }
    last_match
}
