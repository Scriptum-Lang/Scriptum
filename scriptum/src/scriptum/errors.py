"""
Custom exception hierarchy for the Scriptum compiler.

These errors will be raised both internally and by the CLI to provide users
with actionable feedback.
"""

from __future__ import annotations


class CompilerError(RuntimeError):
    """Base class for Scriptum-related errors."""


class CompilerInputError(CompilerError):
    """Raised when user-provided input cannot be consumed."""


class CompilerInternalError(CompilerError):
    """Raised when the compiler encounters an unexpected internal condition."""


class CompilerNotImplemented(CompilerError):
    """Raised for pipeline stages that lack an implementation."""


class LexerError(CompilerError):
    """Raised when the lexer cannot tokenise the provided input."""

    def __init__(self, message: str, span: "Span") -> None:
        super().__init__(message)
        self.span = span


from .text import Span  # noqa: E402  (late import to avoid circular dependency)


class SemanticError(CompilerError):
    """Raised when semantic analysis reports diagnostics."""

    def __init__(self, diagnostics: list) -> None:
        super().__init__("Semantic analysis failed.")
        self.diagnostics = diagnostics


class ExecutionError(CompilerError):
    """Raised when executing Scriptum IR fails."""
