use core::fmt;

/// Representa um intervalo dentro de um arquivo fonte Scriptum.
#[derive(Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct Span {
    start: u32,
    end: u32,
}

impl Span {
    /// Cria um novo `Span` a partir dos offsets (em bytes UTF-8).
    pub fn new(start: usize, end: usize) -> Self {
        debug_assert!(start <= end);
        Self {
            start: start as u32,
            end: end as u32,
        }
    }

    /// Offset inicial (inclusivo).
    #[inline]
    pub fn start(&self) -> usize {
        self.start as usize
    }

    /// Offset final (exclusivo).
    #[inline]
    pub fn end(&self) -> usize {
        self.end as usize
    }

    /// Comprimento do trecho em bytes.
    #[inline]
    pub fn len(&self) -> usize {
        (self.end - self.start) as usize
    }
}

impl Default for Span {
    fn default() -> Self {
        Self { start: 0, end: 0 }
    }
}

impl fmt::Debug for Span {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}..{}", self.start, self.end)
    }
}
