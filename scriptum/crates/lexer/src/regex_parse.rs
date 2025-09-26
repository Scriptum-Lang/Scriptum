use crate::regex_ast::{CharSet, RegexAst, RepeatKind};

#[derive(Debug)]
pub struct ParseError(pub String);

type ParseResult<T> = Result<T, ParseError>;

pub fn parse_regex(input: &str) -> ParseResult<RegexAst> {
    let mut parser = Parser::new(input);
    let expr = parser.parse_expression()?;
    if parser.peek().is_some() {
        return Err(ParseError(format!(
            "unexpected trailing input at position {}",
            parser.pos
        )));
    }
    Ok(expr)
}

struct Parser<'a> {
    chars: Vec<char>,
    pos: usize,
    source: &'a str,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Parser {
            chars: input.chars().collect(),
            pos: 0,
            source: input,
        }
    }

    fn peek(&self) -> Option<char> {
        self.chars.get(self.pos).copied()
    }

    fn next(&mut self) -> Option<char> {
        let ch = self.peek();
        if ch.is_some() {
            self.pos += 1;
        }
        ch
    }

    fn parse_expression(&mut self) -> ParseResult<RegexAst> {
        let mut parts = Vec::new();
        loop {
            let term = self.parse_concatenation()?;
            parts.push(term);
            if self.peek() == Some('|') {
                self.next();
            } else {
                break;
            }
        }
        if parts.len() == 1 {
            Ok(parts.pop().unwrap())
        } else {
            Ok(RegexAst::alternate(parts))
        }
    }

    fn parse_concatenation(&mut self) -> ParseResult<RegexAst> {
        let mut parts = Vec::new();
        while let Some(ch) = self.peek() {
            if matches!(ch, '|' | ')') {
                break;
            }
            let node = self.parse_quantified()?;
            match node {
                RegexAst::Empty => {}
                _ => parts.push(node),
            }
        }
        if parts.is_empty() {
            Ok(RegexAst::Empty)
        } else if parts.len() == 1 {
            Ok(parts.pop().unwrap())
        } else {
            Ok(RegexAst::concat(parts))
        }
    }

    fn parse_quantified(&mut self) -> ParseResult<RegexAst> {
        let mut node = self.parse_atom()?;
        loop {
            node = match self.peek() {
                Some('*') => {
                    self.next();
                    RegexAst::Repeat {
                        node: Box::new(node),
                        kind: RepeatKind::ZeroOrMore,
                    }
                }
                Some('+') => {
                    self.next();
                    RegexAst::Repeat {
                        node: Box::new(node),
                        kind: RepeatKind::OneOrMore,
                    }
                }
                Some('?') => {
                    self.next();
                    RegexAst::Repeat {
                        node: Box::new(node),
                        kind: RepeatKind::ZeroOrOne,
                    }
                }
                _ => break,
            };
        }
        Ok(node)
    }

    fn parse_atom(&mut self) -> ParseResult<RegexAst> {
        match self.next() {
            Some('(') => {
                let expr = self.parse_expression()?;
                if self.next() != Some(')') {
                    return Err(ParseError(format!("expected ')' at position {}", self.pos)));
                }
                Ok(expr)
            }
            Some('[') => {
                let set = self.parse_char_class()?;
                Ok(RegexAst::CharSet(set))
            }
            Some('.') => Ok(RegexAst::CharSet(CharSet::any())),
            Some('^') => Ok(RegexAst::CharSet(CharSet::singleton('^' as u32))),
            Some('$') => Ok(RegexAst::CharSet(CharSet::singleton('$' as u32))),
            Some('\\') => {
                let set = self.parse_escape(false)?;
                Ok(RegexAst::CharSet(set))
            }
            Some(ch) => Ok(RegexAst::CharSet(CharSet::singleton(ch as u32))),
            None => Ok(RegexAst::Empty),
        }
    }

    fn parse_char_class(&mut self) -> ParseResult<CharSet> {
        let mut negated = false;
        let mut first = true;
        if self.peek() == Some('^') {
            negated = true;
            self.next();
        }
        let mut result = CharSet::empty();
        while let Some(ch) = self.peek() {
            if ch == ']' && !first {
                break;
            }
            let item = self.next_class_item()?;
            let literal = item.singleton_value();
            if self.peek() == Some('-') {
                self.next();
                if self.peek() == Some(']') {
                    // treat '-' as literal
                    result.union(&item);
                    result.push_range('-' as u32, '-' as u32);
                    first = false;
                    continue;
                }
                let end_item = self.next_class_item()?;
                let end_literal = end_item.singleton_value().ok_or_else(|| {
                    ParseError(format!("invalid range end at position {}", self.pos))
                })?;
                let start_literal = literal.ok_or_else(|| {
                    ParseError(format!("invalid range start at position {}", self.pos))
                })?;
                let mut range = CharSet::empty();
                range.push_range(start_literal, end_literal);
                result.union(&range);
                first = false;
                continue;
            } else {
                result.union(&item);
            }
            first = false;
        }
        if self.next() != Some(']') {
            return Err(ParseError(format!(
                "unterminated character class in '{}'",
                self.source
            )));
        }
        if negated {
            result.negated = true;
        }
        Ok(result)
    }

    fn next_class_item(&mut self) -> ParseResult<CharSet> {
        match self.next() {
            Some('\\') => self.parse_escape(true),
            Some(ch) => Ok(CharSet::singleton(ch as u32)),
            None => Err(ParseError("unterminated character class".into())),
        }
    }

    fn parse_escape(&mut self, _in_class: bool) -> ParseResult<CharSet> {
        let ch = self
            .next()
            .ok_or_else(|| ParseError("incomplete escape sequence".into()))?;
        let set = match ch {
            'n' => CharSet::singleton('\n' as u32),
            'r' => CharSet::singleton('\r' as u32),
            't' => CharSet::singleton('\t' as u32),
            '\\' => CharSet::singleton('\\' as u32),
            '"' => CharSet::singleton('"' as u32),
            '\'' => CharSet::singleton('\'' as u32),
            'd' => CharSet::from_ranges(vec![(b'0' as u32, b'9' as u32)], false),
            'D' => CharSet::from_ranges(vec![(b'0' as u32, b'9' as u32)], true),
            's' => CharSet::from_ranges(
                vec![
                    (' ' as u32, ' ' as u32),
                    ('\t' as u32, '\t' as u32),
                    ('\r' as u32, '\r' as u32),
                    ('\n' as u32, '\n' as u32),
                ],
                false,
            ),
            'S' => CharSet::from_ranges(
                vec![
                    (' ' as u32, ' ' as u32),
                    ('\t' as u32, '\t' as u32),
                    ('\r' as u32, '\r' as u32),
                    ('\n' as u32, '\n' as u32),
                ],
                true,
            ),
            'w' => CharSet::from_ranges(
                vec![
                    (b'0' as u32, b'9' as u32),
                    (b'a' as u32, b'z' as u32),
                    (b'A' as u32, b'Z' as u32),
                    ('_' as u32, '_' as u32),
                ],
                false,
            ),
            'W' => CharSet::from_ranges(
                vec![
                    (b'0' as u32, b'9' as u32),
                    (b'a' as u32, b'z' as u32),
                    (b'A' as u32, b'Z' as u32),
                    ('_' as u32, '_' as u32),
                ],
                true,
            ),
            'x' => {
                let hi = self
                    .next()
                    .ok_or_else(|| ParseError("expected hex".into()))?;
                let lo = self
                    .next()
                    .ok_or_else(|| ParseError("expected hex".into()))?;
                let value = parse_hex_pair(hi, lo)?;
                CharSet::singleton(value as u32)
            }
            other => CharSet::singleton(other as u32),
        };
        Ok(set)
    }
}

fn parse_hex_pair(hi: char, lo: char) -> ParseResult<u8> {
    fn to_val(ch: char) -> Option<u8> {
        match ch {
            '0'..='9' => Some((ch as u8) - b'0'),
            'a'..='f' => Some((ch as u8) - b'a' + 10),
            'A'..='F' => Some((ch as u8) - b'A' + 10),
            _ => None,
        }
    }
    let hi_val = to_val(hi).ok_or_else(|| ParseError("invalid hex escape".into()))?;
    let lo_val = to_val(lo).ok_or_else(|| ParseError("invalid hex escape".into()))?;
    Ok((hi_val << 4) | lo_val)
}

trait CharSetExt {
    fn singleton_value(&self) -> Option<u32>;
}

impl CharSetExt for CharSet {
    fn singleton_value(&self) -> Option<u32> {
        if self.any || self.negated {
            return None;
        }
        if self.ranges.len() == 1 {
            let (s, e) = self.ranges[0];
            if s == e {
                return Some(s);
            }
        }
        None
    }
}
