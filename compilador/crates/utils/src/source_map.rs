use std::sync::Arc;

use ahash::AHashMap;

use crate::Span;

/// Representa um arquivo Scriptum carregado em memória.
#[derive(Clone)]
pub struct SourceFile {
    name: Arc<str>,
    source: Arc<str>,
}

impl SourceFile {
    pub fn new(name: impl Into<Arc<str>>, source: impl Into<Arc<str>>) -> Self {
        Self {
            name: name.into(),
            source: source.into(),
        }
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn source(&self) -> &str {
        &self.source
    }

    pub fn slice(&self, span: Span) -> &str {
        &self.source[span.start()..span.end()]
    }
}

/// Estrutura leve que mantém `SourceFile`s indexados pelo caminho lógico.
#[derive(Default)]
pub struct SourceMap {
    files: AHashMap<Arc<str>, SourceFile>,
}

impl SourceMap {
    pub fn new() -> Self {
        Self {
            files: AHashMap::new(),
        }
    }

    pub fn insert(&mut self, name: impl Into<Arc<str>>, source: impl Into<Arc<str>>) -> SourceFile {
        let name_arc = name.into();
        let file = SourceFile::new(name_arc.clone(), source);
        self.files.insert(name_arc.clone(), file.clone());
        file
    }

    pub fn get(&self, name: &str) -> Option<&SourceFile> {
        self.files.get(name)
    }
}
