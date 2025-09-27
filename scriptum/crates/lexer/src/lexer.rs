use std::fmt;

use crate::dfa::run_dfa;
use crate::tokens::{keywords, token_dfas, token_specs};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TokenKind {
    Keyword(&'static str),
    Named(&'static str),
}

impl TokenKind {
    pub fn type_label(&self) -> String {
        match self {
            TokenKind::Keyword(keyword) => format!("Keyword({})", keyword),
            TokenKind::Named(name) => (*name).to_string(),
        }
    }
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
    pub line: usize,
    pub column: usize,
}

impl fmt::Display for LexError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "lexical error at position {} (line {}, column {})",
            self.position, self.line, self.column
        )
    }
}

impl std::error::Error for LexError {}

pub fn tokenize(source: &str) -> Result<Vec<LexToken>, LexError> {
    let data: Vec<u32> = source.chars().map(|ch| ch as u32).collect();
    let line_starts = compute_line_starts(source);
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
            let (line, column) = line_column(&line_starts, pos);
            return Err(LexError {
                position: pos,
                line,
                column,
            });
        }
    }
    Ok(tokens)
}

fn compute_line_starts(source: &str) -> Vec<usize> {
    let mut starts = Vec::new();
    starts.push(0);
    for (idx, ch) in source.chars().enumerate() {
        if ch == '\n' {
            starts.push(idx + 1);
        }
    }
    starts
}

fn line_column(line_starts: &[usize], pos: usize) -> (usize, usize) {
    let line_index = match line_starts.binary_search(&pos) {
        Ok(idx) => idx,
        Err(idx) => idx.saturating_sub(1),
    };
    let line_start = line_starts.get(line_index).copied().unwrap_or_default();
    let line = line_index + 1;
    let column = pos.saturating_sub(line_start) + 1;
    (line, column)
}
