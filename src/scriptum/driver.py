"""
High-level orchestration for the Scriptum compilation pipeline.

This module will eventually connect lexing, parsing, semantic analysis, IR
lowering, and code generation. For now, it lays out the expected structure so
the remaining stages can be implemented incrementally.
"""

from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass
from typing import Optional

from . import errors, text


class Stage(enum.Enum):
    """Compilation stages supported by the driver."""

    LEXER = "lexer"
    PARSER = "parser"
    SEMANTIC = "semantic"
    IR = "ir"
    CODEGEN = "codegen"


@dataclass(slots=True)
class DriverConfig:
    """Configuration options for the compilation pipeline."""

    until: Stage = Stage.CODEGEN


class CompilerDriver:
    """Entry point that coordinates the Scriptum compilation pipeline."""

    def __init__(self, config: Optional[DriverConfig] = None) -> None:
        self.config = config or DriverConfig()

    def run(self, source: Optional[pathlib.Path], until: Optional[Stage] = None) -> None:
        """
        Run the compilation pipeline on *source* until the requested stage.

        Parameters
        ----------
        source:
            Path to the Scriptum source file. When None, the driver is expected
            to read from standard input (not yet implemented).
        until:
            Overrides the driver's configured stopping point for this invocation.
        """

        target_stage = until or self.config.until
        source_text = self._read_source(source)
        module = text.SourceFile(path=source, text=source_text)

        # The following calls are placeholders to be filled as the respective
        # modules become available. They intentionally raise to surface the
        # missing implementation clearly during early development.
        if target_stage == Stage.LEXER:
            raise errors.CompilerNotImplemented("Lexer pipeline not yet implemented.")
        if target_stage == Stage.PARSER:
            raise errors.CompilerNotImplemented("Parser pipeline not yet implemented.")
        if target_stage == Stage.SEMANTIC:
            raise errors.CompilerNotImplemented("Semantic analysis not yet implemented.")
        if target_stage == Stage.IR:
            raise errors.CompilerNotImplemented("IR lowering not yet implemented.")

        raise errors.CompilerNotImplemented("Code generation not yet implemented.")

    @staticmethod
    def _read_source(source: Optional[pathlib.Path]) -> str:
        """Load the contents of *source* or raise a friendly error."""

        if source is None:
            raise errors.CompilerNotImplemented(
                "Reading Scriptum source from stdin is not implemented yet."
            )

        try:
            return source.read_text(encoding="utf8")
        except FileNotFoundError as exc:
            raise errors.CompilerInputError(f"Source file not found: {source}") from exc
        except OSError as exc:
            raise errors.CompilerInputError(f"Unable to read source file: {source}") from exc
