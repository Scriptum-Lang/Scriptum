use std::collections::{BTreeMap, VecDeque};

use crate::charclass::{all_classes, classify};
use crate::nfa::Nfa;
use crate::regex_ast::CharSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Accepting {
    pub token_index: usize,
    pub priority: i32,
}

#[derive(Debug, Clone)]
pub struct Dfa {
    pub class_count: usize,
    pub transitions: Vec<Vec<Option<usize>>>,
    pub accept: Vec<Option<Accepting>>,
    pub start: usize,
}

pub fn subset_construction(nfa: &Nfa, token_index: usize, priority: i32) -> Dfa {
    let classes = all_classes();
    let class_count = classes.len();
    let mut state_sets: Vec<Vec<usize>> = Vec::new();
    let mut map: BTreeMap<Vec<usize>, usize> = BTreeMap::new();
    let mut queue = VecDeque::new();

    let start_set = epsilon_closure(nfa, &[nfa.start]);
    map.insert(start_set.clone(), 0);
    state_sets.push(start_set);
    queue.push_back(0);

    let mut transitions: Vec<Vec<Option<usize>>> = Vec::new();
    let mut accept: Vec<Option<Accepting>> = Vec::new();

    while let Some(idx) = queue.pop_front() {
        ensure_state(&mut transitions, &mut accept, idx, class_count);
        let current_set = state_sets[idx].clone();
        let mut target_sets: Vec<Vec<usize>> = vec![Vec::new(); class_count];
        for &state in &current_set {
            let nfa_state = &nfa.states[state];
            for (set, to) in &nfa_state.transitions {
                for info in classes {
                    if set_matches_class(set, info.id) {
                        target_sets[info.id as usize].push(*to);
                    }
                }
            }
        }
        for class_id in 0..class_count {
            if target_sets[class_id].is_empty() {
                transitions[idx][class_id] = None;
                continue;
            }
            let closure = epsilon_closure(nfa, &target_sets[class_id]);
            if closure.is_empty() {
                transitions[idx][class_id] = None;
                continue;
            }
            let state_id = if let Some(existing) = map.get(&closure) {
                *existing
            } else {
                let new_id = state_sets.len();
                map.insert(closure.clone(), new_id);
                state_sets.push(closure);
                queue.push_back(new_id);
                new_id
            };
            transitions[idx][class_id] = Some(state_id);
        }
        let is_accept = current_set.iter().any(|&s| s == nfa.accept);
        if is_accept {
            accept[idx] = Some(Accepting {
                token_index,
                priority,
            });
        }
    }

    let mut sink_index = None;
    for state in 0..transitions.len() {
        for class_id in 0..class_count {
            if transitions[state][class_id].is_none() {
                let sink = *sink_index.get_or_insert_with(|| {
                    let idx = transitions.len();
                    transitions.push(vec![None; class_count]);
                    accept.push(None);
                    for class in 0..class_count {
                        transitions[idx][class] = Some(idx);
                    }
                    idx
                });
                transitions[state][class_id] = Some(sink);
            }
        }
    }

    Dfa {
        class_count,
        transitions,
        accept,
        start: 0,
    }
}

fn set_matches_class(set: &CharSet, class_id: u16) -> bool {
    for code in 0u32..=0x7F {
        if classify(code) == class_id && set.contains(code) {
            return true;
        }
    }
    false
}

fn ensure_state(
    transitions: &mut Vec<Vec<Option<usize>>>,
    accept: &mut Vec<Option<Accepting>>,
    idx: usize,
    class_count: usize,
) {
    while transitions.len() <= idx {
        transitions.push(vec![None; class_count]);
        accept.push(None);
    }
}

fn epsilon_closure(nfa: &Nfa, states: &[usize]) -> Vec<usize> {
    let mut stack: Vec<usize> = states.to_vec();
    let mut visited = vec![false; nfa.states.len()];
    let mut result: Vec<usize> = Vec::new();
    while let Some(state) = stack.pop() {
        if visited[state] {
            continue;
        }
        visited[state] = true;
        result.push(state);
        for &next in &nfa.states[state].epsilon {
            stack.push(next);
        }
    }
    result.sort_unstable();
    result
}
