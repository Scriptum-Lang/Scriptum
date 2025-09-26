#[derive(Debug, Clone, Copy)]
pub struct CharClassInfo {
    pub id: u16,
    pub name: &'static str,
}

pub const CLASS_LOWER: u16 = 0;
pub const CLASS_UPPER: u16 = 1;
pub const CLASS_ZERO: u16 = 2;
pub const CLASS_DIGIT: u16 = 3;
pub const CLASS_UNDERSCORE: u16 = 4;
pub const CLASS_SPACE: u16 = 5;
pub const CLASS_TAB: u16 = 6;
pub const CLASS_CARRIAGE_RETURN: u16 = 7;
pub const CLASS_NEWLINE: u16 = 8;
pub const CLASS_SLASH: u16 = 9;
pub const CLASS_STAR: u16 = 10;
pub const CLASS_PLUS: u16 = 11;
pub const CLASS_MINUS: u16 = 12;
pub const CLASS_EQUAL: u16 = 13;
pub const CLASS_LESS: u16 = 14;
pub const CLASS_GREATER: u16 = 15;
pub const CLASS_AMPERSAND: u16 = 16;
pub const CLASS_PIPE: u16 = 17;
pub const CLASS_QUESTION: u16 = 18;
pub const CLASS_DOT: u16 = 19;
pub const CLASS_COMMA: u16 = 20;
pub const CLASS_SEMICOLON: u16 = 21;
pub const CLASS_COLON: u16 = 22;
pub const CLASS_EXCLAMATION: u16 = 23;
pub const CLASS_PERCENT: u16 = 24;
pub const CLASS_BACKSLASH: u16 = 25;
pub const CLASS_DOUBLE_QUOTE: u16 = 26;
pub const CLASS_SINGLE_QUOTE: u16 = 27;
pub const CLASS_LPAREN: u16 = 28;
pub const CLASS_RPAREN: u16 = 29;
pub const CLASS_LBRACE: u16 = 30;
pub const CLASS_RBRACE: u16 = 31;
pub const CLASS_LBRACKET: u16 = 32;
pub const CLASS_RBRACKET: u16 = 33;
pub const CLASS_CARET: u16 = 34;
pub const CLASS_TILDE: u16 = 35;
pub const CLASS_OTHER: u16 = 36;

pub const CLASS_INFOS: &[CharClassInfo] = &[
    CharClassInfo {
        id: CLASS_LOWER,
        name: "LOWER",
    },
    CharClassInfo {
        id: CLASS_UPPER,
        name: "UPPER",
    },
    CharClassInfo {
        id: CLASS_ZERO,
        name: "ZERO",
    },
    CharClassInfo {
        id: CLASS_DIGIT,
        name: "DIGIT",
    },
    CharClassInfo {
        id: CLASS_UNDERSCORE,
        name: "UNDERSCORE",
    },
    CharClassInfo {
        id: CLASS_SPACE,
        name: "SPACE",
    },
    CharClassInfo {
        id: CLASS_TAB,
        name: "TAB",
    },
    CharClassInfo {
        id: CLASS_CARRIAGE_RETURN,
        name: "CR",
    },
    CharClassInfo {
        id: CLASS_NEWLINE,
        name: "NL",
    },
    CharClassInfo {
        id: CLASS_SLASH,
        name: "SLASH",
    },
    CharClassInfo {
        id: CLASS_STAR,
        name: "STAR",
    },
    CharClassInfo {
        id: CLASS_PLUS,
        name: "PLUS",
    },
    CharClassInfo {
        id: CLASS_MINUS,
        name: "MINUS",
    },
    CharClassInfo {
        id: CLASS_EQUAL,
        name: "EQUAL",
    },
    CharClassInfo {
        id: CLASS_LESS,
        name: "LESS",
    },
    CharClassInfo {
        id: CLASS_GREATER,
        name: "GREATER",
    },
    CharClassInfo {
        id: CLASS_AMPERSAND,
        name: "AMP",
    },
    CharClassInfo {
        id: CLASS_PIPE,
        name: "PIPE",
    },
    CharClassInfo {
        id: CLASS_QUESTION,
        name: "QUESTION",
    },
    CharClassInfo {
        id: CLASS_DOT,
        name: "DOT",
    },
    CharClassInfo {
        id: CLASS_COMMA,
        name: "COMMA",
    },
    CharClassInfo {
        id: CLASS_SEMICOLON,
        name: "SEMI",
    },
    CharClassInfo {
        id: CLASS_COLON,
        name: "COLON",
    },
    CharClassInfo {
        id: CLASS_EXCLAMATION,
        name: "EXCL",
    },
    CharClassInfo {
        id: CLASS_PERCENT,
        name: "PERCENT",
    },
    CharClassInfo {
        id: CLASS_BACKSLASH,
        name: "BACKSLASH",
    },
    CharClassInfo {
        id: CLASS_DOUBLE_QUOTE,
        name: "DQUOTE",
    },
    CharClassInfo {
        id: CLASS_SINGLE_QUOTE,
        name: "SQUOTE",
    },
    CharClassInfo {
        id: CLASS_LPAREN,
        name: "LPAREN",
    },
    CharClassInfo {
        id: CLASS_RPAREN,
        name: "RPAREN",
    },
    CharClassInfo {
        id: CLASS_LBRACE,
        name: "LBRACE",
    },
    CharClassInfo {
        id: CLASS_RBRACE,
        name: "RBRACE",
    },
    CharClassInfo {
        id: CLASS_LBRACKET,
        name: "LBRACKET",
    },
    CharClassInfo {
        id: CLASS_RBRACKET,
        name: "RBRACKET",
    },
    CharClassInfo {
        id: CLASS_CARET,
        name: "CARET",
    },
    CharClassInfo {
        id: CLASS_TILDE,
        name: "TILDE",
    },
    CharClassInfo {
        id: CLASS_OTHER,
        name: "OTHER",
    },
];

pub const CLASS_COUNT: usize = CLASS_INFOS.len();

pub fn all_classes() -> &'static [CharClassInfo] {
    CLASS_INFOS
}

pub fn classify(ch: u32) -> u16 {
    match ch {
        0x61..=0x7A => CLASS_LOWER,
        0x41..=0x5A => CLASS_UPPER,
        0x30 => CLASS_ZERO,
        0x31..=0x39 => CLASS_DIGIT,
        0x5F => CLASS_UNDERSCORE,
        0x20 => CLASS_SPACE,
        0x09 => CLASS_TAB,
        0x0D => CLASS_CARRIAGE_RETURN,
        0x0A => CLASS_NEWLINE,
        0x2F => CLASS_SLASH,
        0x2A => CLASS_STAR,
        0x2B => CLASS_PLUS,
        0x2D => CLASS_MINUS,
        0x3D => CLASS_EQUAL,
        0x3C => CLASS_LESS,
        0x3E => CLASS_GREATER,
        0x26 => CLASS_AMPERSAND,
        0x7C => CLASS_PIPE,
        0x3F => CLASS_QUESTION,
        0x2E => CLASS_DOT,
        0x2C => CLASS_COMMA,
        0x3B => CLASS_SEMICOLON,
        0x3A => CLASS_COLON,
        0x21 => CLASS_EXCLAMATION,
        0x25 => CLASS_PERCENT,
        0x5C => CLASS_BACKSLASH,
        0x22 => CLASS_DOUBLE_QUOTE,
        0x27 => CLASS_SINGLE_QUOTE,
        0x28 => CLASS_LPAREN,
        0x29 => CLASS_RPAREN,
        0x7B => CLASS_LBRACE,
        0x7D => CLASS_RBRACE,
        0x5B => CLASS_LBRACKET,
        0x5D => CLASS_RBRACKET,
        0x5E => CLASS_CARET,
        0x7E => CLASS_TILDE,
        _ => CLASS_OTHER,
    }
}
