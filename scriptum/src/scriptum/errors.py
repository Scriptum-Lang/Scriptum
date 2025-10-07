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
