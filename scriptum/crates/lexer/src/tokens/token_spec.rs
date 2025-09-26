use std::sync::OnceLock;

use super::types::{TokenDfaSpec, TokenRegex};

static KEYWORDS_DATA: OnceLock<&'static [&'static str]> = OnceLock::new();
static TOKEN_SPECS_DATA: OnceLock<&'static [TokenRegex]> = OnceLock::new();
static TOKEN_DFAS_DATA: OnceLock<&'static [TokenDfaSpec]> = OnceLock::new();
static CLASS_COUNT_DATA: OnceLock<usize> = OnceLock::new();

pub fn keywords() -> &'static [&'static str] {
    KEYWORDS_DATA.get_or_init(|| include!(concat!(env!("OUT_DIR"), "/keywords.rs")))
}

pub fn token_specs() -> &'static [TokenRegex] {
    TOKEN_SPECS_DATA.get_or_init(|| include!(concat!(env!("OUT_DIR"), "/token_specs.rs")))
}

pub fn token_dfas() -> &'static [TokenDfaSpec] {
    TOKEN_DFAS_DATA.get_or_init(|| include!(concat!(env!("OUT_DIR"), "/token_dfas.rs")))
}

pub fn class_count() -> usize {
    *CLASS_COUNT_DATA.get_or_init(|| include!(concat!(env!("OUT_DIR"), "/class_count.rs")))
}
