use std::cmp::max;

#[derive(Debug, Clone)]
pub enum RegexAst {
    Empty,
    CharSet(CharSet),
    Concat(Vec<RegexAst>),
    Alternate(Vec<RegexAst>),
    Repeat {
        node: Box<RegexAst>,
        kind: RepeatKind,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RepeatKind {
    ZeroOrMore,
    OneOrMore,
    ZeroOrOne,
}

#[derive(Debug, Clone)]
pub struct CharSet {
    pub ranges: Vec<(u32, u32)>,
    pub negated: bool,
    pub any: bool,
}

impl CharSet {
    pub fn empty() -> Self {
        CharSet {
            ranges: Vec::new(),
            negated: false,
            any: false,
        }
    }

    pub fn any() -> Self {
        CharSet {
            ranges: Vec::new(),
            negated: false,
            any: true,
        }
    }

    pub fn singleton(ch: u32) -> Self {
        CharSet {
            ranges: vec![(ch, ch)],
            negated: false,
            any: false,
        }
    }

    pub fn negate(mut self) -> Self {
        self.negated = !self.negated;
        self
    }

    pub fn push_range(&mut self, start: u32, end: u32) {
        let (s, e) = if start <= end {
            (start, end)
        } else {
            (end, start)
        };
        self.ranges.push((s, e));
        self.normalize();
    }

    pub fn union(&mut self, other: &CharSet) {
        if self.any || other.any {
            self.any = true;
            self.negated = false;
            self.ranges.clear();
            return;
        }
        if other.negated {
            if !self.negated {
                self.negated = true;
            }
        }
        for &(s, e) in &other.ranges {
            self.ranges.push((s, e));
        }
        self.normalize();
    }

    pub fn contains(&self, ch: u32) -> bool {
        if self.any {
            return true;
        }
        let mut inside = false;
        for &(s, e) in &self.ranges {
            if ch >= s && ch <= e {
                inside = true;
                break;
            }
        }
        if self.negated {
            !inside
        } else {
            inside
        }
    }

    fn normalize(&mut self) {
        if self.any {
            self.ranges.clear();
            self.negated = false;
            return;
        }
        if self.ranges.is_empty() {
            return;
        }
        self.ranges.sort_by(|a, b| a.0.cmp(&b.0));
        let mut merged: Vec<(u32, u32)> = Vec::new();
        for &(s, e) in &self.ranges {
            if let Some(last) = merged.last_mut() {
                if s <= last.1 + 1 {
                    last.1 = max(last.1, e);
                } else {
                    merged.push((s, e));
                }
            } else {
                merged.push((s, e));
            }
        }
        self.ranges = merged;
    }

    pub fn from_ranges(ranges: Vec<(u32, u32)>, negated: bool) -> Self {
        let mut set = CharSet {
            ranges,
            negated,
            any: false,
        };
        set.normalize();
        set
    }

    pub fn is_empty(&self) -> bool {
        !self.any && self.ranges.is_empty() && !self.negated
    }
}

impl RegexAst {
    pub fn concat(parts: Vec<RegexAst>) -> RegexAst {
        let mut flat = Vec::new();
        for part in parts {
            match part {
                RegexAst::Concat(inner) => flat.extend(inner),
                RegexAst::Empty => {}
                other => flat.push(other),
            }
        }
        if flat.is_empty() {
            RegexAst::Empty
        } else if flat.len() == 1 {
            flat.into_iter().next().unwrap()
        } else {
            RegexAst::Concat(flat)
        }
    }

    pub fn alternate(parts: Vec<RegexAst>) -> RegexAst {
        let mut flat = Vec::new();
        for part in parts {
            match part {
                RegexAst::Alternate(inner) => flat.extend(inner),
                other => flat.push(other),
            }
        }
        if flat.len() == 1 {
            flat.into_iter().next().unwrap()
        } else {
            RegexAst::Alternate(flat)
        }
    }
}
