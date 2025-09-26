use crate::regex_ast::{CharSet, RegexAst, RepeatKind};

#[derive(Debug, Clone)]
pub struct NfaState {
    pub epsilon: Vec<usize>,
    pub transitions: Vec<(CharSet, usize)>,
}

#[derive(Debug, Clone)]
pub struct Nfa {
    pub states: Vec<NfaState>,
    pub start: usize,
    pub accept: usize,
}

impl Nfa {
    pub fn new() -> Self {
        Nfa {
            states: Vec::new(),
            start: 0,
            accept: 0,
        }
    }
}

struct Fragment {
    start: usize,
    accept: usize,
}

pub fn build_nfa(ast: &RegexAst) -> Nfa {
    let mut nfa = Nfa::new();
    let fragment = build_fragment(ast, &mut nfa);
    nfa.start = fragment.start;
    nfa.accept = fragment.accept;
    nfa
}

fn build_fragment(ast: &RegexAst, nfa: &mut Nfa) -> Fragment {
    match ast {
        RegexAst::Empty => {
            let start = new_state(nfa);
            let accept = new_state(nfa);
            add_epsilon(nfa, start, accept);
            Fragment { start, accept }
        }
        RegexAst::CharSet(set) => {
            let start = new_state(nfa);
            let accept = new_state(nfa);
            add_transition(nfa, start, set.clone(), accept);
            Fragment { start, accept }
        }
        RegexAst::Concat(parts) => {
            if parts.is_empty() {
                return build_fragment(&RegexAst::Empty, nfa);
            }
            let mut iter = parts.iter();
            let first = build_fragment(iter.next().unwrap(), nfa);
            let mut current = first;
            for part in iter {
                let frag = build_fragment(part, nfa);
                add_epsilon(nfa, current.accept, frag.start);
                current = Fragment {
                    start: current.start,
                    accept: frag.accept,
                };
            }
            current
        }
        RegexAst::Alternate(parts) => {
            let start = new_state(nfa);
            let accept = new_state(nfa);
            for part in parts {
                let frag = build_fragment(part, nfa);
                add_epsilon(nfa, start, frag.start);
                add_epsilon(nfa, frag.accept, accept);
            }
            Fragment { start, accept }
        }
        RegexAst::Repeat { node, kind } => match kind {
            RepeatKind::ZeroOrMore => {
                let frag = build_fragment(node, nfa);
                let start = new_state(nfa);
                let accept = new_state(nfa);
                add_epsilon(nfa, start, frag.start);
                add_epsilon(nfa, start, accept);
                add_epsilon(nfa, frag.accept, frag.start);
                add_epsilon(nfa, frag.accept, accept);
                Fragment { start, accept }
            }
            RepeatKind::OneOrMore => {
                let frag = build_fragment(node, nfa);
                let start = new_state(nfa);
                let accept = new_state(nfa);
                add_epsilon(nfa, start, frag.start);
                add_epsilon(nfa, frag.accept, frag.start);
                add_epsilon(nfa, frag.accept, accept);
                Fragment { start, accept }
            }
            RepeatKind::ZeroOrOne => {
                let frag = build_fragment(node, nfa);
                let start = new_state(nfa);
                let accept = new_state(nfa);
                add_epsilon(nfa, start, frag.start);
                add_epsilon(nfa, start, accept);
                add_epsilon(nfa, frag.accept, accept);
                Fragment { start, accept }
            }
        },
    }
}

fn new_state(nfa: &mut Nfa) -> usize {
    let idx = nfa.states.len();
    nfa.states.push(NfaState {
        epsilon: Vec::new(),
        transitions: Vec::new(),
    });
    idx
}

fn add_epsilon(nfa: &mut Nfa, from: usize, to: usize) {
    nfa.states[from].epsilon.push(to);
}

fn add_transition(nfa: &mut Nfa, from: usize, set: CharSet, to: usize) {
    nfa.states[from].transitions.push((set, to));
}
