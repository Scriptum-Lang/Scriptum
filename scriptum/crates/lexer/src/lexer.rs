use std::fmt;

use crate::dfa::run_dfa;
use crate::tokens::{keywords, token_dfas, token_specs};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TokenKind {
    Keyword(&'static str),
    Named(&'static str),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LexToken {
    pub kind: TokenKind,
    pub lexeme: String,
    pub span: (usize, usize),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LexError {
    pub position: usize,
}

impl fmt::Display for LexError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "lexical error at position {}", self.position)
    }
}

impl std::error::Error for LexError {}

pub fn tokenize(source: &str) -> Result<Vec<LexToken>, LexError> {
    let data: Vec<u32> = source.chars().map(|ch| ch as u32).collect();
    let dfa_specs = token_dfas();
    let regex_specs = token_specs();
    let keywords = keywords();
    let mut pos = 0usize;
    let mut tokens = Vec::new();
    while pos < data.len() {
        let mut best: Option<(usize, usize)> = None; // (end, spec index)
        for (idx, spec) in dfa_specs.iter().enumerate() {
            if let Some(end) = run_dfa(&spec.dfa, &data, pos) {
                if end <= pos {
                    continue;
                }
                let regex = &regex_specs[spec.regex_index];
                let spec_priority = regex.priority;
                match best {
                    Some((best_end, best_idx)) => {
                        let best_regex = &regex_specs[dfa_specs[best_idx].regex_index];
                        if end > best_end
                            || (end == best_end && spec_priority > best_regex.priority)
                            || (end == best_end
                                && spec_priority == best_regex.priority
                                && idx < best_idx)
                        {
                            best = Some((end, idx));
                        }
                    }
                    None => best = Some((end, idx)),
                }
            }
        }
        if let Some((end, idx)) = best {
            let spec = &dfa_specs[idx];
            let regex = &regex_specs[spec.regex_index];
            let start = pos;
            let slice = &data[start..end];
            let lexeme: String = slice
                .iter()
                .map(|&cp| char::from_u32(cp).unwrap())
                .collect();
            pos = end;
            if regex.discard {
                continue;
            }
            let mut kind = TokenKind::Named(regex.name);
            if regex.name == "IDENT" {
                if let Some(&kw) = keywords.iter().find(|&&kw| kw == lexeme) {
                    kind = TokenKind::Keyword(kw);
                }
            }
            tokens.push(LexToken {
                kind,
                lexeme,
                span: (start, end),
            });
        } else {
            return Err(LexError { position: pos });
        }
    }
    Ok(tokens)
}
