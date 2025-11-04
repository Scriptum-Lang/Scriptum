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

from . import errors, text, tokens
from .codegen import generate
from .ir import ModuleIr, lower_module
from .ir.interpreter import ExecutionResult, Interpreter
from .lexer.lexer import LexerConfig, ScriptumLexer
from .parser.parser import ScriptumParser
from .sema.analyzer import SemanticAnalyzer, SemanticDiagnostic


class Stage(enum.Enum):
    """Compilation stages supported by the driver."""

    LEXER = "lexer"
    PARSER = "parser"
    SEMANTIC = "semantic"
    IR = "ir"
    CODEGEN = "codegen"
    FMT = "fmt"
    RUN = "run"


@dataclass(slots=True)
class DriverConfig:
    """Configuration options for the compilation pipeline."""

    until: Stage = Stage.CODEGEN


class CompilerDriver:
    """Entry point that coordinates the Scriptum compilation pipeline."""

    def __init__(self, config: Optional[DriverConfig] = None) -> None:
        self.config = config or DriverConfig()
        self._lexer = ScriptumLexer(LexerConfig())
        self._parser = ScriptumParser()

    @dataclass(slots=True)
    class Result:
        source: text.SourceFile
        tokens: Optional[list[tokens.Token]] = None
        ast: Optional["nodes.Module"] = None  # type: ignore[name-defined]
        diagnostics: Optional[list[SemanticDiagnostic]] = None
        ir: Optional[ModuleIr] = None
        formatted: Optional[str] = None
        execution: Optional[ExecutionResult] = None

    def run(self, source: Optional[pathlib.Path], until: Optional[Stage] = None) -> "CompilerDriver.Result":
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
        source_file = text.SourceFile(path=str(source) if source else "<stdin>", text=source_text)

        result = CompilerDriver.Result(source=source_file)

        result.tokens = self.lex(source_file)
        if target_stage == Stage.LEXER:
            return result

        result.ast = self.parse(source_file)
        if target_stage == Stage.PARSER:
            return result

        diagnostics = self.analyze(result.ast)
        result.diagnostics = diagnostics
        if target_stage == Stage.SEMANTIC:
            return result
        if diagnostics:
            raise errors.SemanticError(diagnostics)

        result.ir = lower_module(result.ast)
        if target_stage == Stage.IR:
            return result

        formatted_output = generate(result.ir)
        result.formatted = formatted_output.formatted
        if target_stage in {Stage.CODEGEN, Stage.FMT}:
            return result

        interpreter = Interpreter(result.ir)
        result.execution = interpreter.execute()
        if target_stage == Stage.RUN:
            return result

        return result

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

    def lex(self, source: text.SourceFile) -> list[tokens.Token]:
        return self._lexer.tokenize(source)

    def parse(self, source: text.SourceFile):
        return self._parser.parse(source)

    def analyze(self, module):
        analyzer = SemanticAnalyzer()
        return analyzer.analyze(module)
