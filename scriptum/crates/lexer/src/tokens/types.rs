#[derive(Debug, Clone)]
pub struct TokenRegex {
    pub name: &'static str,
    pub pattern: &'static str,
    pub discard: bool,
    pub priority: i32,
}

#[derive(Debug)]
pub struct SerializedDfa {
    pub start: usize,
    pub class_count: usize,
    pub state_count: usize,
    pub transitions: &'static [u32],
    pub accept: &'static [u8],
}

#[derive(Debug)]
pub struct TokenDfaSpec {
    pub regex_index: usize,
    pub dfa: SerializedDfa,
}
