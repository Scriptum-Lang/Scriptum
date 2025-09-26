use std::collections::HashSet;

use crate::charclass;
use crate::pipeline::{BuiltToken, TokenDefinition};

#[derive(Debug, Clone)]
pub struct SpecData {
    pub keywords: Vec<String>,
    pub literals: Vec<String>,
}

pub fn parse_spec(markdown: &str) -> SpecData {
    let mut inside = false;
    let mut raw_tokens = Vec::new();
    for line in markdown.lines() {
        if !inside {
            if line.contains("T = {") {
                inside = true;
            }
            continue;
        }
        if line.contains('}') {
            break;
        }
        let content = if let Some(idx) = line.find("//") {
            &line[..idx]
        } else {
            line
        };
        for part in content.split(',') {
            let item = part.trim();
            if !item.is_empty() {
                raw_tokens.push(item.to_string());
            }
        }
    }
    let mut keywords = Vec::new();
    let mut literals = Vec::new();
    for token in raw_tokens {
        if token.starts_with('"') && token.ends_with('"') {
            literals.push(token[1..token.len() - 1].to_string());
        } else {
            match token.as_str() {
                "Ident" | "NumeroLiteral" | "TextoLiteral" => {}
                other => {
                    if other.chars().all(|c| c.is_ascii_lowercase()) {
                        keywords.push(other.to_string());
                    }
                }
            }
        }
    }
    keywords.sort();
    keywords.dedup();
    literals.sort();
    literals.dedup();
    SpecData { keywords, literals }
}

pub fn build_token_definitions(spec: &SpecData) -> Vec<TokenDefinition> {
    let mut defs = Vec::new();
    defs.push(TokenDefinition {
        name: "WS".into(),
        pattern: "[ \t\r\n]+".into(),
        discard: true,
        priority: 0,
    });
    defs.push(TokenDefinition {
        name: "LINE_COMMENT".into(),
        pattern: "//[^\n]*".into(),
        discard: true,
        priority: 0,
    });
    defs.push(TokenDefinition {
        name: "BLOCK_COMMENT".into(),
        pattern: "/\\*([^*]|\\*+[^/])*\\*/".into(),
        discard: true,
        priority: 0,
    });
    defs.push(TokenDefinition {
        name: "STRING".into(),
        pattern: "\"(\\\\.|[^\"\\\\\n\r])*\"".into(),
        discard: false,
        priority: 0,
    });
    defs.push(TokenDefinition {
        name: "NUMBER".into(),
        pattern: "(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?".into(),
        discard: false,
        priority: 0,
    });
    defs.push(TokenDefinition {
        name: "IDENT".into(),
        pattern: "[a-z][a-z0-9_]*".into(),
        discard: false,
        priority: 0,
    });

    let mut seen = HashSet::new();
    for literal in &spec.literals {
        let name = literal_to_name(literal);
        if seen.insert(name.clone()) {
            defs.push(TokenDefinition {
                name,
                pattern: escape_literal(literal),
                discard: false,
                priority: literal.chars().count() as i32,
            });
        }
    }
    for literal in &[",", ";", ".", ":", "?", "(", ")", "[", "]", "{", "}"] {
        let name = literal_to_name(literal);
        if seen.insert(name.clone()) {
            defs.push(TokenDefinition {
                name,
                pattern: escape_literal(literal),
                discard: false,
                priority: literal.chars().count() as i32,
            });
        }
    }
    defs
}

fn escape_literal(literal: &str) -> String {
    let mut out = String::new();
    for ch in literal.chars() {
        if matches!(
            ch,
            '.' | '+'
                | '*'
                | '?'
                | '^'
                | '$'
                | '('
                | ')'
                | '['
                | ']'
                | '{'
                | '}'
                | '|'
                | '\\'
                | '/'
        ) {
            out.push('\\');
        }
        out.push(ch);
    }
    out
}

fn literal_to_name(literal: &str) -> String {
    match literal {
        "+" => "PLUS".into(),
        "-" => "MINUS".into(),
        "*" => "STAR".into(),
        "/" => "SLASH".into(),
        "%" => "PERCENT".into(),
        "**" => "STAR_STAR".into(),
        "=" => "EQUAL".into(),
        "+=" => "PLUS_EQUAL".into(),
        "-=" => "MINUS_EQUAL".into(),
        "*=" => "STAR_EQUAL".into(),
        "/=" => "SLASH_EQUAL".into(),
        "%=" => "PERCENT_EQUAL".into(),
        "==" => "EQUAL_EQUAL".into(),
        "!=" => "BANG_EQUAL".into(),
        "===" => "TRIPLE_EQUAL".into(),
        "!==" => "BANG_TRIPLE_EQUAL".into(),
        "<" => "LESS".into(),
        "<=" => "LESS_EQUAL".into(),
        ">" => "GREATER".into(),
        ">=" => "GREATER_EQUAL".into(),
        "&&" => "AND_AND".into(),
        "||" => "OR_OR".into(),
        "!" => "BANG".into(),
        "??" => "QUESTION_QUESTION".into(),
        "?." => "QUESTION_DOT".into(),
        "," => "COMMA".into(),
        ";" => "SEMICOLON".into(),
        "." => "DOT".into(),
        ":" => "COLON".into(),
        "?" => "QUESTION".into(),
        "(" => "LPAREN".into(),
        ")" => "RPAREN".into(),
        "[" => "LBRACKET".into(),
        "]" => "RBRACKET".into(),
        "{" => "LBRACE".into(),
        "}" => "RBRACE".into(),
        other => format!(
            "TOKEN_{}",
            other.replace(|c: char| !c.is_ascii_alphanumeric(), "_")
        ),
    }
}

pub fn render_mermaid(defs: &[TokenDefinition], built: &[BuiltToken]) -> String {
    let mut buffer = String::new();
    buffer.push_str("# DFAs minimizados\n\n");
    for (def, token) in defs.iter().zip(built.iter()) {
        buffer.push_str(&format!(
            "## {}\\n\\nEstados: NFA {} → DFA {} → Min {}\\n\\n",
            def.name, token.stats.nfa_states, token.stats.dfa_states, token.stats.minimized_states
        ));
        buffer.push_str("```mermaid\nstateDiagram-v2\n");
        buffer.push_str(&format!("  [*] --> S{}\n", token.dfa.start));
        for (state_idx, targets) in token.dfa.transitions.iter().enumerate() {
            let mut grouped: std::collections::BTreeMap<usize, Vec<&'static str>> =
                std::collections::BTreeMap::new();
            for (class_idx, &target) in targets.iter().enumerate() {
                let name = charclass::CLASS_INFOS[class_idx].name;
                grouped.entry(target).or_default().push(name);
            }
            for (target, classes) in grouped {
                let label = classes.join(", ");
                buffer.push_str(&format!("  S{} --> S{}: {}\n", state_idx, target, label));
            }
        }
        for (state_idx, acc) in token.dfa.accept.iter().enumerate() {
            if acc.is_some() {
                buffer.push_str(&format!("  state S{} <<accept>>\n", state_idx));
            }
        }
        buffer.push_str("```\n\n");
    }
    buffer
}
