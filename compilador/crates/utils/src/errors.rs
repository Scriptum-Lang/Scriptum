use miette::Diagnostic as MietteDiagnostic;
use thiserror::Error;

/// Resultado padrão do compilador Scriptum.
pub type Result<T, E = Error> = core::result::Result<T, E>;

/// Categorias de erro de alto nível.
#[derive(Debug, Error, MietteDiagnostic)]
pub enum ErrorKind {
    #[error("erro léxico")]
    Lexico,
    #[error("erro sintático")]
    Sintatico,
    #[error("erro semântico")]
    Semantico,
    #[error("erro de geração de código")]
    Codegen,
    #[error("erro de runtime")]
    Runtime,
}

/// Erro estruturado com mensagem amigável.
#[derive(Debug, Error, MietteDiagnostic)]
#[error("{message}")]
pub struct Error {
    #[source]
    #[diagnostic_source]
    source: Option<Box<dyn std::error::Error + Send + Sync + 'static>>,
    #[diagnostic_source]
    kind: ErrorKind,
    #[help]
    message: String,
}

impl Error {
    pub fn new(kind: ErrorKind, message: impl Into<String>) -> Self {
        Self {
            source: None,
            kind,
            message: message.into(),
        }
    }

    pub fn with_source(
        kind: ErrorKind,
        message: impl Into<String>,
        source: impl Into<Box<dyn std::error::Error + Send + Sync + 'static>>,
    ) -> Self {
        Self {
            source: Some(source.into()),
            kind,
            message: message.into(),
        }
    }

    pub fn kind(&self) -> &ErrorKind {
        &self.kind
    }
}
