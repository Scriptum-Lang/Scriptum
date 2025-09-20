use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct CharRange {
    pub start: char,
    pub end: char,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Matcher {
    Char(char),
    Range(char, char),
    Set(&'static [CharRange]),
    Predicate(fn(char) -> bool, char),
}

impl Matcher {
    pub fn matches(&self, ch: char) -> bool {
        match self {
            Matcher::Char(c) => ch == *c,
            Matcher::Range(start, end) => (*start..=*end).contains(&ch),
            Matcher::Set(ranges) => ranges.iter().any(|r| (r.start..=r.end).contains(&ch)),
            Matcher::Predicate(pred, _) => pred(ch),
        }
    }

    pub fn sample_chars(&self) -> Vec<char> {
        match self {
            Matcher::Char(c) => vec![*c],
            Matcher::Range(start, _) => vec![*start],
            Matcher::Set(ranges) => ranges.first().map(|r| r.start).into_iter().collect(),
            Matcher::Predicate(_, sample) => vec![*sample],
        }
    }
}

#[derive(Clone, Debug)]
pub enum RegexAst {
    Empty,
    Epsilon,
    Symbol(Matcher),
    Concat(Vec<RegexAst>),
    Union(Vec<RegexAst>),
    Star(Box<RegexAst>),
    Optional(Box<RegexAst>),
}

impl RegexAst {
    pub fn symbol(m: Matcher) -> Self {
        RegexAst::Symbol(m)
    }

    pub fn literal(ch: char) -> Self {
        RegexAst::Symbol(Matcher::Char(ch))
    }

    pub fn literal_str(value: &str) -> Self {
        let nodes: Vec<_> = value.chars().map(RegexAst::literal).collect();
        RegexAst::concat(nodes)
    }

    pub fn concat<I: IntoIterator<Item = RegexAst>>(iter: I) -> Self {
        let mut parts: Vec<RegexAst> = iter.into_iter().collect();
        if parts.is_empty() {
            return RegexAst::Epsilon;
        }
        if parts.len() == 1 {
            return parts.pop().unwrap();
        }
        RegexAst::Concat(parts)
    }

    pub fn union<I: IntoIterator<Item = RegexAst>>(iter: I) -> Self {
        let mut parts: Vec<RegexAst> = iter.into_iter().collect();
        if parts.is_empty() {
            return RegexAst::Empty;
        }
        if parts.len() == 1 {
            return parts.pop().unwrap();
        }
        RegexAst::Union(parts)
    }

    pub fn star(self) -> Self {
        RegexAst::Star(Box::new(self))
    }

    pub fn optional(self) -> Self {
        RegexAst::Optional(Box::new(self))
    }

    pub fn plus(self) -> Self {
        let clone = self.clone();
        RegexAst::Concat(vec![self, RegexAst::Star(Box::new(clone))])
    }
}

#[derive(Clone, Debug)]
struct NfaState {
    transitions: Vec<(Matcher, usize)>,
    epsilon: Vec<usize>,
}

impl NfaState {
    fn new() -> Self {
        NfaState {
            transitions: Vec::new(),
            epsilon: Vec::new(),
        }
    }
}

#[derive(Clone, Debug)]
pub struct Nfa {
    states: Vec<NfaState>,
    start: usize,
    accept: usize,
}

impl Nfa {
    pub fn from_regex(ast: &RegexAst) -> Self {
        let mut builder = NfaBuilder::new();
        let (start, accept) = builder.build(ast);
        Nfa {
            states: builder.states,
            start,
            accept,
        }
    }

    fn epsilon_closure(&self, set: &HashSet<usize>) -> HashSet<usize> {
        let mut stack: Vec<usize> = set.iter().cloned().collect();
        let mut closure = set.clone();
        while let Some(state) = stack.pop() {
            for &next in &self.states[state].epsilon {
                if closure.insert(next) {
                    stack.push(next);
                }
            }
        }
        closure
    }

    fn move_on(&self, states: &HashSet<usize>, matcher: Matcher) -> HashSet<usize> {
        let mut next = HashSet::new();
        for &state_id in states {
            for &(m, target) in &self.states[state_id].transitions {
                if m == matcher {
                    next.insert(target);
                }
            }
        }
        next
    }

    fn alphabet(&self) -> Vec<Matcher> {
        let mut seen: HashSet<Matcher> = HashSet::new();
        let mut ordered = Vec::new();
        for state in &self.states {
            for &(m, _) in &state.transitions {
                if seen.insert(m) {
                    ordered.push(m);
                }
            }
        }
        ordered
    }

    pub fn to_dfa(&self) -> Dfa {
        let alphabet = self.alphabet();
        let mut subset_map: HashMap<Vec<usize>, usize> = HashMap::new();
        let mut states_vec: Vec<State> = Vec::new();
        let mut accepts: HashSet<usize> = HashSet::new();
        let mut queue: VecDeque<HashSet<usize>> = VecDeque::new();

        let mut start_set: HashSet<usize> = HashSet::new();
        start_set.insert(self.start);
        let start_closure = self.epsilon_closure(&start_set);
        let mut start_key: Vec<usize> = start_closure.iter().cloned().collect();
        start_key.sort_unstable();
        subset_map.insert(start_key.clone(), 0);
        queue.push_back(start_closure.clone());
        states_vec.push(State::new());
        if start_closure.contains(&self.accept) {
            accepts.insert(0);
        }

        while let Some(current_set) = queue.pop_front() {
            let current_key: Vec<usize> = {
                let mut tmp: Vec<usize> = current_set.iter().cloned().collect();
                tmp.sort_unstable();
                tmp
            };
            let current_index = subset_map[&current_key];
            let mut transitions_for_state: Vec<(Matcher, usize)> = Vec::new();

            for &symbol in &alphabet {
                let move_set = self.move_on(&current_set, symbol);
                if move_set.is_empty() {
                    continue;
                }
                let closure = self.epsilon_closure(&move_set);
                let mut key: Vec<usize> = closure.iter().cloned().collect();
                key.sort_unstable();
                let target_index = if let Some(&id) = subset_map.get(&key) {
                    id
                } else {
                    let new_id = states_vec.len();
                    subset_map.insert(key.clone(), new_id);
                    queue.push_back(closure.clone());
                    states_vec.push(State::new());
                    if closure.contains(&self.accept) {
                        accepts.insert(new_id);
                    }
                    new_id
                };
                transitions_for_state.push((symbol, target_index));
            }

            states_vec[current_index].transitions = transitions_for_state;
        }

        Dfa {
            states: states_vec,
            start: 0,
            accepts,
        }
    }
}

struct NfaBuilder {
    states: Vec<NfaState>,
}

impl NfaBuilder {
    fn new() -> Self {
        NfaBuilder { states: Vec::new() }
    }

    fn new_state(&mut self) -> usize {
        let id = self.states.len();
        self.states.push(NfaState::new());
        id
    }

    fn add_transition(&mut self, from: usize, matcher: Matcher, to: usize) {
        self.states[from].transitions.push((matcher, to));
    }

    fn add_epsilon(&mut self, from: usize, to: usize) {
        self.states[from].epsilon.push(to);
    }

    fn build(&mut self, ast: &RegexAst) -> (usize, usize) {
        match ast {
            RegexAst::Empty => {
                let start = self.new_state();
                let accept = self.new_state();
                (start, accept)
            }
            RegexAst::Epsilon => {
                let start = self.new_state();
                let accept = self.new_state();
                self.add_epsilon(start, accept);
                (start, accept)
            }
            RegexAst::Symbol(matcher) => {
                let start = self.new_state();
                let accept = self.new_state();
                self.add_transition(start, *matcher, accept);
                (start, accept)
            }
            RegexAst::Concat(parts) => {
                let mut parts_iter = parts.iter();
                let first = parts_iter
                    .next()
                    .expect("Concat requires at least one part");
                let (mut start, mut end) = self.build(first);
                for part in parts_iter {
                    let (next_start, next_end) = self.build(part);
                    self.add_epsilon(end, next_start);
                    end = next_end;
                }
                (start, end)
            }
            RegexAst::Union(parts) => {
                let start = self.new_state();
                let accept = self.new_state();
                for part in parts {
                    let (inner_start, inner_end) = self.build(part);
                    self.add_epsilon(start, inner_start);
                    self.add_epsilon(inner_end, accept);
                }
                (start, accept)
            }
            RegexAst::Star(inner) => {
                let start = self.new_state();
                let accept = self.new_state();
                let (inner_start, inner_end) = self.build(inner);
                self.add_epsilon(start, accept);
                self.add_epsilon(start, inner_start);
                self.add_epsilon(inner_end, inner_start);
                self.add_epsilon(inner_end, accept);
                (start, accept)
            }
            RegexAst::Optional(inner) => {
                let start = self.new_state();
                let accept = self.new_state();
                let (inner_start, inner_end) = self.build(inner);
                self.add_epsilon(start, inner_start);
                self.add_epsilon(inner_end, accept);
                self.add_epsilon(start, accept);
                (start, accept)
            }
        }
    }
}

#[derive(Clone, Debug)]
pub struct State {
    pub transitions: Vec<(Matcher, usize)>,
}

impl State {
    fn new() -> Self {
        State {
            transitions: Vec::new(),
        }
    }
}

#[derive(Clone, Debug)]
pub struct Dfa {
    pub states: Vec<State>,
    pub start: usize,
    pub accepts: HashSet<usize>,
}

impl Dfa {
    pub fn accepts(&self, input: &str) -> bool {
        let mut current = self.start;
        for ch in input.chars() {
            let mut advanced = false;
            for &(matcher, target) in &self.states[current].transitions {
                if matcher.matches(ch) {
                    current = target;
                    advanced = true;
                    break;
                }
            }
            if !advanced {
                return false;
            }
        }
        self.accepts.contains(&current)
    }

    fn alphabet_samples(&self) -> Vec<Option<char>> {
        let mut seen = HashSet::new();
        let mut samples = Vec::new();
        for state in &self.states {
            for &(matcher, _) in &state.transitions {
                for sample in matcher.sample_chars() {
                    if seen.insert(Some(sample)) {
                        samples.push(Some(sample));
                    }
                }
            }
        }
        samples.push(None);
        samples
    }

    fn next_state_option(&self, state: usize, ch: Option<char>) -> Option<usize> {
        match ch {
            Some(actual) => {
                for &(matcher, target) in &self.states[state].transitions {
                    if matcher.matches(actual) {
                        return Some(target);
                    }
                }
                None
            }
            None => None,
        }
    }

    pub fn minimize(&self) -> Dfa {
        if self.states.is_empty() {
            return self.clone();
        }
        let alphabet = self.alphabet_samples();
        const SINK: usize = usize::MAX;
        let mut partitions: Vec<usize> = (0..self.states.len())
            .map(|state| if self.accepts.contains(&state) { 1 } else { 0 })
            .collect();
        let mut changed = true;
        while changed {
            changed = false;
            let mut classes: HashMap<Vec<usize>, usize> = HashMap::new();
            let mut next_partitions = vec![0; self.states.len()];
            let mut next_id = 0;
            for state in 0..self.states.len() {
                let mut signature = Vec::with_capacity(alphabet.len() + 1);
                signature.push(partitions[state]);
                for symbol in &alphabet {
                    let target = self.next_state_option(state, *symbol);
                    let class = target.map(|t| partitions[t]).unwrap_or(SINK);
                    signature.push(class);
                }
                let entry = classes.entry(signature).or_insert_with(|| {
                    let id = next_id;
                    next_id += 1;
                    id
                });
                next_partitions[state] = *entry;
            }
            if next_partitions != partitions {
                partitions = next_partitions;
                changed = true;
            }
        }

        let mut block_map: HashMap<usize, Vec<usize>> = HashMap::new();
        for (state, class) in partitions.iter().enumerate() {
            block_map.entry(*class).or_insert_with(Vec::new).push(state);
        }
        let mut block_entries: Vec<(usize, Vec<usize>)> = block_map.into_iter().collect();
        block_entries.sort_by_key(|(class, _)| *class);

        let mut state_mapping: HashMap<usize, usize> = HashMap::new();
        for (new_state_id, (_, members)) in block_entries.iter().enumerate() {
            for &member in members {
                state_mapping.insert(member, new_state_id);
            }
        }

        let mut minimized_states: Vec<State> = Vec::new();
        let mut minimized_accepts: HashSet<usize> = HashSet::new();

        for (new_state_id, (_, members)) in block_entries.iter().enumerate() {
            let representative = members[0];
            let mut transitions = Vec::new();
            for &(matcher, target) in &self.states[representative].transitions {
                let mapped = state_mapping[&target];
                if !transitions.iter().any(|&(m, t)| m == matcher && t == mapped) {
                    transitions.push((matcher, mapped));
                }
            }
            if self.accepts.contains(&representative) {
                minimized_accepts.insert(new_state_id);
            }
            minimized_states.push(State { transitions });
        }

        let new_start = state_mapping[&self.start];

        Dfa {
            states: minimized_states,
            start: new_start,
            accepts: minimized_accepts,
        }
    }
}
