use std::fmt;

use crate::hopcroft::{minimize, HopcroftStats, MinDfa};
use crate::nfa::build_nfa;
use crate::regex_parse::{parse_regex, ParseError};
use crate::subset::subset_construction;

#[derive(Debug, Clone)]
pub struct TokenDefinition {
    pub name: String,
    pub pattern: String,
    pub discard: bool,
    pub priority: i32,
}

#[derive(Debug, Clone)]
pub struct BuiltToken {
    pub name: String,
    pub pattern: String,
    pub discard: bool,
    pub priority: i32,
    pub dfa: MinDfa,
    pub stats: BuildStats,
}

#[derive(Debug, Clone)]
pub struct BuildStats {
    pub nfa_states: usize,
    pub dfa_states: usize,
    pub minimized_states: usize,
    pub hopcroft: HopcroftStats,
}

#[derive(Debug)]
pub enum PipelineError {
    Parse(ParseError),
    Message(String),
}

impl fmt::Display for PipelineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PipelineError::Parse(err) => write!(f, "regex parse error: {}", err.0),
            PipelineError::Message(msg) => f.write_str(msg),
        }
    }
}

impl std::error::Error for PipelineError {}

impl From<ParseError> for PipelineError {
    fn from(value: ParseError) -> Self {
        PipelineError::Parse(value)
    }
}

pub fn build_tokens(defs: &[TokenDefinition]) -> Result<Vec<BuiltToken>, PipelineError> {
    let mut result = Vec::new();
    for (index, def) in defs.iter().enumerate() {
        let ast = parse_regex(&def.pattern)?;
        let nfa = build_nfa(&ast);
        let dfa = subset_construction(&nfa, index, def.priority);
        let (min_dfa, hopcroft_stats) = minimize(&dfa);
        let stats = BuildStats {
            nfa_states: nfa.states.len(),
            dfa_states: dfa.transitions.len(),
            minimized_states: min_dfa.transitions.len(),
            hopcroft: hopcroft_stats,
        };
        result.push(BuiltToken {
            name: def.name.clone(),
            pattern: def.pattern.clone(),
            discard: def.discard,
            priority: def.priority,
            dfa: min_dfa,
            stats,
        });
    }
    Ok(result)
}
