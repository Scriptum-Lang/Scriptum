"""
High-level orchestration and command-line entry point for the Scriptum toolchain.

This module keeps the existing compilation driver used by other parts of the
project and exposes a user-facing CLI with `lex`, `parse`, and `sema` helpers.
"""

from __future__ import annotations

import argparse
import enum
import importlib
import importlib.util
import json
import pathlib
import sys
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable, Optional, Sequence

if __package__ in (None, ""):
    # Running as a script or PyInstaller entrypoint; register the package manually.
    _PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
    _PACKAGE_PARENT = _PACKAGE_ROOT.parent
    if str(_PACKAGE_PARENT) not in sys.path:
        sys.path.insert(0, str(_PACKAGE_PARENT))

    _PACKAGE_NAME = _PACKAGE_ROOT.name
    if _PACKAGE_NAME not in sys.modules:
        init_path = _PACKAGE_ROOT / "__init__.py"
        if init_path.exists():
            spec = importlib.util.spec_from_file_location(
                _PACKAGE_NAME,
                init_path,
                submodule_search_locations=[str(_PACKAGE_ROOT)],
            )
            module = importlib.util.module_from_spec(spec) if spec else None
            if module and spec and spec.loader:
                sys.modules[_PACKAGE_NAME] = module
                spec.loader.exec_module(module)
        else:
            importlib.import_module(_PACKAGE_NAME)

try:
    from . import errors, text, tokens
    from .codegen import generate
    from .ir import ModuleIr, lower_module
    from .ir.interpreter import ExecutionResult, Interpreter
    from .lexer.lexer import LexerConfig, ScriptumLexer
    from .parser.parser import ScriptumParser
    from .sema.analyzer import SemanticAnalyzer, SemanticDiagnostic
except ImportError:  # pragma: no cover - standalone PyInstaller execution
    errors = importlib.import_module("scriptum.errors")
    text = importlib.import_module("scriptum.text")
    tokens = importlib.import_module("scriptum.tokens")

    codegen_module = importlib.import_module("scriptum.codegen")
    generate = codegen_module.generate

    ir_module = importlib.import_module("scriptum.ir")
    ModuleIr = ir_module.ModuleIr
    lower_module = ir_module.lower_module

    ir_interpreter_module = importlib.import_module("scriptum.ir.interpreter")
    ExecutionResult = ir_interpreter_module.ExecutionResult
    Interpreter = ir_interpreter_module.Interpreter

    lexer_module = importlib.import_module("scriptum.lexer.lexer")
    LexerConfig = lexer_module.LexerConfig
    ScriptumLexer = lexer_module.ScriptumLexer

    parser_module = importlib.import_module("scriptum.parser.parser")
    ScriptumParser = parser_module.ScriptumParser

    sema_module = importlib.import_module("scriptum.sema.analyzer")
    SemanticAnalyzer = sema_module.SemanticAnalyzer
    SemanticDiagnostic = sema_module.SemanticDiagnostic

VERSION = "0.3.2"
CommandHandler = Callable[[argparse.Namespace], int]


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


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scriptum",
        description="Scriptum language toolchain helpers.",
    )
    parser.add_argument("--version", action="version", version=f"scriptum {VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    lex_parser = subparsers.add_parser("lex", help="Tokenise a Scriptum source file and emit JSON.")
    lex_parser.add_argument("source", metavar="FILE", help="Scriptum source (.stm) to tokenise.")
    lex_parser.set_defaults(handler=_cmd_lex)

    parse_parser = subparsers.add_parser("parse", help="Parse a Scriptum source file and emit an AST in JSON.")
    parse_parser.add_argument("source", metavar="FILE", help="Scriptum source (.stm) to parse.")
    parse_parser.set_defaults(handler=_cmd_parse)

    sema_parser = subparsers.add_parser(
        "sema", help="Run semantic analysis and report diagnostics, if any."
    )
    sema_parser.add_argument("source", metavar="FILE", help="Scriptum source (.stm) to analyse.")
    sema_parser.set_defaults(handler=_cmd_sema)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _create_parser()
    args = parser.parse_args(argv)

    handler: Optional[CommandHandler] = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    try:
        return handler(args)
    except errors.CompilerError as exc:
        _emit_error(str(exc))
        return 1
    except Exception as exc:  # pragma: no cover - safeguard for unexpected issues
        _emit_error(f"Internal error: {exc}")
        return 2


def _cmd_lex(args: argparse.Namespace) -> int:
    source = _resolve_source(args.source)
    driver = CompilerDriver()
    result = driver.run(source, until=Stage.LEXER)

    payload = [
        {
            "kind": token.kind.name,
            "lexeme": token.lexeme,
            "value": token.value,
            "span": {"start": token.span.start, "end": token.span.end},
        }
        for token in (result.tokens or [])
        if token.kind is not tokens.TokenKind.EOF
    ]
    _emit_json(payload)
    return 0


def _cmd_parse(args: argparse.Namespace) -> int:
    source = _resolve_source(args.source)
    driver = CompilerDriver()
    result = driver.run(source, until=Stage.PARSER)

    if result.ast is None:
        _emit_json({})
        return 0

    payload = _ast_to_json(result.ast)
    _emit_json(payload)
    return 0


def _cmd_sema(args: argparse.Namespace) -> int:
    source = _resolve_source(args.source)
    driver = CompilerDriver()
    result = driver.run(source, until=Stage.SEMANTIC)
    diagnostics = result.diagnostics or []

    if not diagnostics:
        print("Semantic analysis completed without errors.")
        return 0

    source_text = result.source.text
    display_path = result.source.path or str(source)

    for diagnostic in diagnostics:
        if diagnostic.span:
            line, column = diagnostic.span.line_col(source_text)
            message = f"{diagnostic.code} {display_path}:{line}:{column}: {diagnostic.message}"
            _emit_error(message)
            snippet = diagnostic.span.highlight(source_text)
            if snippet:
                for line_text in snippet.splitlines():
                    _emit_error(f"  {line_text}")
        else:
            _emit_error(f"{diagnostic.code}: {diagnostic.message}")
    return 1


def _resolve_source(raw: str) -> pathlib.Path:
    path = pathlib.Path(raw)
    if path.suffix.lower() != ".stm":
        raise errors.CompilerInputError("Scriptum source files must use the .stm extension.")
    return path.resolve()


def _emit_json(payload: Any) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def _emit_error(message: str) -> None:
    print(message, file=sys.stderr)


def _ast_to_json(value: Any) -> Any:
    if is_dataclass(value):
        result: dict[str, Any] = {"__type__": value.__class__.__name__}
        for field in fields(value):
            result[field.name] = _ast_to_json(getattr(value, field.name))
        return result
    if isinstance(value, enum.Enum):
        return value.name
    if isinstance(value, (list, tuple, set)):
        return [_ast_to_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _ast_to_json(val) for key, val in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


__all__ = [
    "CompilerDriver",
    "DriverConfig",
    "Stage",
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
