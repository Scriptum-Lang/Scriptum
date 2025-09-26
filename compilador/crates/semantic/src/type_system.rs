use thiserror::Error;

/// Tipos primitivos da linguagem.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Type {
    Numerus,
    Boolean,
    Void,
}

impl Type {
    pub fn name(self) -> &'static str {
        match self {
            Type::Numerus => "numerus",
            Type::Boolean => "boolean",
            Type::Void => "void",
        }
    }
}

/// Erros de tipo.
#[derive(Debug, Error)]
pub enum TypeError {
    #[error("tipos incompatíveis: {0} vs {1}")]
    Mismatch(&'static str, &'static str),
}
