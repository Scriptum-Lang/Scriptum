use std::ops::Range;

use ariadne::{Color, Label, Report, ReportKind, Source};
use miette::{LabeledSpan, MietteDiagnostic, NamedSource, Report as MietteReport};

use crate::{source_map::SourceFile, Span};

/// Auxiliar para construir diagnósticos padronizados.
pub struct DiagnosticBuilder<'a> {
    file: &'a SourceFile,
    span: Span,
    message: String,
    labels: Vec<(Span, String)>,
}

impl<'a> DiagnosticBuilder<'a> {
    pub fn new(file: &'a SourceFile, span: Span, message: impl Into<String>) -> Self {
        Self {
            file,
            span,
            message: message.into(),
            labels: Vec::new(),
        }
    }

    pub fn label(mut self, span: Span, message: impl Into<String>) -> Self {
        self.labels.push((span, message.into()));
        self
    }

    pub fn finish(self) -> Diagnostic {
        Diagnostic {
            file: self.file.clone(),
            span: self.span,
            message: self.message,
            labels: self.labels,
        }
    }
}

/// Representação de diagnóstico pronto para exibição.
pub struct Diagnostic {
    file: SourceFile,
    span: Span,
    message: String,
    labels: Vec<(Span, String)>,
}

impl Diagnostic {
    pub fn to_ariadne(&self) -> Report<'_, (&str, Range<usize>)> {
        let mut report = Report::build(ReportKind::Error, self.file.name(), self.span.start())
            .with_message(&self.message)
            .with_label(
                Label::new((self.file.name(), self.span.start()..self.span.end()))
                    .with_message(self.message.clone())
                    .with_color(Color::Red),
            );

        for (span, message) in &self.labels {
            report = report.with_label(
                Label::new((self.file.name(), span.start()..span.end()))
                    .with_message(message.clone())
                    .with_color(Color::Yellow),
            );
        }

        report.finish()
    }

    pub fn to_miette(&self) -> MietteReport {
        let source = NamedSource::new(self.file.name().to_string(), self.file.source().to_string());
        let primary = LabeledSpan::new_primary_with_span(
            Some(self.message.clone()),
            self.span.start()..self.span.end(),
        );
        let mut diag = MietteDiagnostic::new(self.message.clone()).with_label(primary);
        for (span, message) in &self.labels {
            let label = LabeledSpan::new_with_span(Some(message.clone()), span.start()..span.end());
            diag = diag.and_label(label);
        }
        MietteReport::new(diag).with_source_code(source)
    }
}

impl std::fmt::Display for Diagnostic {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut output = Vec::new();
        self.to_ariadne()
            .write_for_stdout(
                (self.file.name(), Source::from(self.file.source())),
                &mut output,
            )
            .map_err(|_| std::fmt::Error)?;
        let rendered = String::from_utf8_lossy(&output);
        write!(f, "{}", rendered)
    }
}

impl std::fmt::Debug for Diagnostic {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self)
    }
}
