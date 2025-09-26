use std::collections::HashMap;

use crate::subset::{Accepting, Dfa};

#[derive(Debug, Clone)]
pub struct MinDfa {
    pub class_count: usize,
    pub transitions: Vec<Vec<usize>>,
    pub accept: Vec<Option<Accepting>>,
    pub start: usize,
}

#[derive(Debug, Clone, Copy)]
pub struct HopcroftStats {
    pub states_before: usize,
    pub states_after: usize,
}

pub fn minimize(dfa: &Dfa) -> (MinDfa, HopcroftStats) {
    let class_count = dfa.class_count;
    let mut partitions: Vec<Vec<usize>> = Vec::new();
    let mut accept_groups: HashMap<Option<Accepting>, Vec<usize>> = HashMap::new();
    for (idx, acc) in dfa.accept.iter().enumerate() {
        accept_groups.entry(*acc).or_default().push(idx);
    }
    for (_, group) in accept_groups.into_iter() {
        partitions.push(group);
    }

    loop {
        let mut changed = false;
        let mut new_partitions: Vec<Vec<usize>> = Vec::new();
        let mut state_to_partition = vec![usize::MAX; dfa.transitions.len()];
        for (idx, part) in partitions.iter().enumerate() {
            for &state in part {
                state_to_partition[state] = idx;
            }
        }
        for part in partitions.into_iter() {
            if part.len() <= 1 {
                new_partitions.push(part);
                continue;
            }
            let mut groups: HashMap<Vec<usize>, Vec<usize>> = HashMap::new();
            for &state in &part {
                let signature: Vec<usize> = dfa.transitions[state]
                    .iter()
                    .map(|&target| state_to_partition[target.expect("deterministic transition")])
                    .collect();
                groups.entry(signature).or_default().push(state);
            }
            if groups.len() == 1 {
                new_partitions.push(part);
            } else {
                changed = true;
                for group in groups.into_values() {
                    new_partitions.push(group);
                }
            }
        }
        if !changed {
            partitions = new_partitions;
            break;
        }
        partitions = new_partitions;
    }

    let mut state_map = vec![0usize; dfa.transitions.len()];
    for (new_idx, part) in partitions.iter().enumerate() {
        for &state in part {
            state_map[state] = new_idx;
        }
    }

    let new_state_count = partitions.len();
    let mut transitions = vec![vec![0usize; class_count]; new_state_count];
    let mut accept = vec![None; new_state_count];
    for (new_idx, part) in partitions.iter().enumerate() {
        let repr = part[0];
        for class_id in 0..class_count {
            let target = dfa.transitions[repr][class_id].expect("deterministic transition");
            transitions[new_idx][class_id] = state_map[target];
        }
        accept[new_idx] = dfa.accept[repr];
    }

    let start = state_map[dfa.start];
    let stats = HopcroftStats {
        states_before: dfa.transitions.len(),
        states_after: new_state_count,
    };
    (
        MinDfa {
            class_count,
            transitions,
            accept,
            start,
        },
        stats,
    )
}
