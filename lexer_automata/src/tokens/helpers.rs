use crate::core::{CharRange, Matcher, RegexAst};
use unicode_ident::{is_xid_continue, is_xid_start};

const SPACE_RANGES: &[CharRange] = &[
    CharRange { start: '\u{0009}', end: '\u{0009}' },
    CharRange { start: '\u{000B}', end: '\u{000C}' },
    CharRange { start: '\u{0020}', end: '\u{0020}' },
    CharRange { start: '\u{00A0}', end: '\u{00A0}' },
    CharRange { start: '\u{FEFF}', end: '\u{FEFF}' },
];

const DIGIT_RANGE: CharRange = CharRange { start: '0', end: '9' };
const BIN_RANGE: CharRange = CharRange { start: '0', end: '1' };
const OCT_RANGE: CharRange = CharRange { start: '0', end: '7' };
const HEX_UPPER: CharRange = CharRange { start: 'A', end: 'F' };
const HEX_LOWER: CharRange = CharRange { start: 'a', end: 'f' };

pub fn whitespace_unit() -> RegexAst {
    RegexAst::union([
        RegexAst::symbol(Matcher::Set(SPACE_RANGES)),
        RegexAst::symbol(newline_matcher()),
    ])
}

fn is_newline(ch: char) -> bool {
    matches!(ch, '\u{000A}' | '\u{000D}' | '\u{2028}' | '\u{2029}')
}

pub fn newline_matcher() -> Matcher {
    Matcher::Predicate(is_newline, '\n')
}

fn is_comment_line_body(ch: char) -> bool {
    !matches!(ch, '\n' | '\r')
}

pub fn comment_line_body() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(is_comment_line_body, 'a'))
}

fn is_not_star(ch: char) -> bool {
    ch != '*'
}

fn is_not_slash(ch: char) -> bool {
    ch != '/'
}

pub fn any_not_star() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(is_not_star, 'a'))
}

pub fn any_not_slash() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(is_not_slash, 'a'))
}

fn xid_start_pred(ch: char) -> bool {
    is_xid_start(ch)
}

fn xid_continue_pred(ch: char) -> bool {
    is_xid_continue(ch)
}

pub fn xid_start_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(xid_start_pred, 'a'))
}

pub fn xid_continue_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(xid_continue_pred, 'a'))
}

pub fn underscore_symbol() -> RegexAst {
    RegexAst::literal('_')
}

pub fn digit_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Range(DIGIT_RANGE.start, DIGIT_RANGE.end))
}

pub fn non_zero_digit_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Range('1', '9'))
}

pub fn binary_digit_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Range(BIN_RANGE.start, BIN_RANGE.end))
}

pub fn octal_digit_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Range(OCT_RANGE.start, OCT_RANGE.end))
}

pub fn hex_digit_symbol() -> RegexAst {
    RegexAst::union([
        digit_symbol(),
        RegexAst::symbol(Matcher::Range(HEX_UPPER.start, HEX_UPPER.end)),
        RegexAst::symbol(Matcher::Range(HEX_LOWER.start, HEX_LOWER.end)),
    ])
}

pub fn ascii_letter_symbol() -> RegexAst {
    RegexAst::union([
        RegexAst::symbol(Matcher::Range('a', 'z')),
        RegexAst::symbol(Matcher::Range('A', 'Z')),
    ])
}

fn is_string_body(ch: char) -> bool {
    ch != '"' && ch != '\\' && ch != '\n' && ch != '\r'
}

pub fn string_body_symbol() -> RegexAst {
    RegexAst::symbol(Matcher::Predicate(is_string_body, 'a'))
}

pub fn simple_escape_symbol() -> RegexAst {
    RegexAst::union([
        RegexAst::literal('\\'),
        RegexAst::literal('"'),
        RegexAst::literal('\''),
        RegexAst::literal('b'),
        RegexAst::literal('n'),
        RegexAst::literal('r'),
        RegexAst::literal('t'),
        RegexAst::literal('0'),
    ])
}
pub fn digits_with_optional_underscores(unit: RegexAst) -> RegexAst {
    let first = unit.clone();
    let tail_piece = RegexAst::concat([
        underscore_symbol().optional(),
        unit,
    ]);
    RegexAst::concat([
        first,
        tail_piece.star(),
    ])
}

pub fn literal_union(strings: &[&str]) -> RegexAst {
    let parts: Vec<RegexAst> = strings.iter().map(|s| RegexAst::literal_str(s)).collect();
    RegexAst::union(parts)
}
pub fn repeat_range(unit: &RegexAst, min: usize, max: usize) -> RegexAst {
    let mut options = Vec::new();
    for len in min..=max {
        let mut seq = Vec::new();
        for _ in 0..len {
            seq.push(unit.clone());
        }
        options.push(RegexAst::concat(seq));
    }
    RegexAst::union(options)
}
