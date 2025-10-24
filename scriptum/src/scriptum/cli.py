"""Command-line interface for the Scriptum toolchain."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Optional

import click

from . import __version__, errors, tokens
from .codegen import generate
from .driver import CompilerDriver, Stage
from .ir import format_module_ir
from .lexer.lexer import ScriptumLexer
from .parser.parser import ScriptumParser
from .text import SourceFile


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """Scriptum build and developer utilities."""


@cli.command("version")
def version_cmd() -> None:
    """Show Scriptum CLI version."""
    click.echo(f"Scriptum CLI version {__version__}")


@cli.command("compile")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=False,
)
@click.option(
    "--stage",
    type=click.Choice([stage.value for stage in Stage]),
    default=Stage.CODEGEN.value,
    help="Pipeline stage to stop after.",
)
def compile_cmd(source: Optional[pathlib.Path], stage: str) -> None:
    """Compile a Scriptum source file."""

    driver = CompilerDriver()
    try:
        driver.run(source=source, until=Stage(stage))
    except errors.SemanticError as exc:
        text_data = source.read_text(encoding="utf8") if source else ""
        payload = [_diagnostic_to_json(diag, text_data) for diag in exc.diagnostics]
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(1)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)


@cli.command("build-lexer")
def build_lexer_cmd() -> None:
    """Gera tables.json e docs/diagramas/afd_final.md a partir das ERs."""

    root = pathlib.Path(__file__).resolve().parents[2]
    script = root / "scripts" / "build_afd.py"
    subprocess.check_call([sys.executable, str(script)])
    ScriptumLexer._TABLES_CACHE = None
    click.echo("AFD gerado com sucesso.")


@cli.command("lex")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def lex_cmd(source: pathlib.Path) -> None:
    """Tokenise a Scriptum source file and emit JSON."""

    driver = CompilerDriver()
    try:
        result = driver.run(source, until=Stage.LEXER)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    token_payload = [
        _token_to_json(token)
        for token in (result.tokens or [])
        if token.kind is not tokens.TokenKind.EOF
    ]
    click.echo(json.dumps(token_payload, ensure_ascii=False, indent=2))


@cli.command("parse")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def parse_cmd(source: pathlib.Path) -> None:
    """Parse a Scriptum source file and print the AST as JSON."""

    driver = CompilerDriver()
    try:
        result = driver.run(source, until=Stage.PARSER)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    module = result.ast
    payload = _ast_to_dict(module) if module is not None else {}
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@cli.command("sema")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def sema_cmd(source: pathlib.Path) -> None:
    """Run semantic analysis and report diagnostics as JSON."""

    driver = CompilerDriver()
    text_data = source.read_text(encoding="utf8")
    try:
        result = driver.run(source, until=Stage.SEMANTIC)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    diagnostics = result.diagnostics or []
    payload = [_diagnostic_to_json(diag, text_data) for diag in diagnostics]
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    if diagnostics:
        sys.exit(1)


@cli.command("ir")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def ir_cmd(source: pathlib.Path) -> None:
    """Lower a Scriptum source file to IR and print it as JSON."""

    driver = CompilerDriver()
    try:
        result = driver.run(source, until=Stage.IR)
    except errors.SemanticError as exc:
        text_data = source.read_text(encoding="utf8")
        payload = [_diagnostic_to_json(diag, text_data) for diag in exc.diagnostics]
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(1)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    if result.ir is None:
        click.echo("{}")
        return
    click.echo(format_module_ir(result.ir))


@cli.command("run")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def run_cmd(source: pathlib.Path) -> None:
    """Interpret a Scriptum program via the IR mini-VM."""

    driver = CompilerDriver()
    try:
        result = driver.run(source, until=Stage.RUN)
    except errors.SemanticError as exc:
        text_data = source.read_text(encoding="utf8")
        payload = [_diagnostic_to_json(diag, text_data) for diag in exc.diagnostics]
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(1)
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    execution = result.execution
    value = execution.value if execution else None
    click.echo(json.dumps(value, ensure_ascii=False))


@cli.command("fmt")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=False,
)
def fmt_cmd(source: Optional[pathlib.Path]) -> None:
    """
    Format Scriptum source code from a file or standard input.
    """

    parser = ScriptumParser()

    if source is None:
        text_data = sys.stdin.read()
        if not text_data:
            raise click.UsageError("No input provided on stdin.")
        try:
            module = parser.parse(SourceFile("<stdin>", text_data))
        except errors.CompilerError as exc:
            _print_error(exc)
            sys.exit(1)
        formatted = generate(module).formatted
        click.echo(formatted, nl=False)
        return

    original_text = source.read_text(encoding="utf8")
    try:
        module = parser.parse(SourceFile(str(source), original_text))
    except errors.CompilerError as exc:
        _print_error(exc)
        sys.exit(1)

    formatted = generate(module).formatted
    if original_text != formatted:
        source.write_text(formatted, encoding="utf8")
        click.echo(f"Formatted {source}")
    else:
        click.echo(f"{source} already formatted")


def _token_to_json(token: tokens.Token) -> dict[str, Any]:
    return {
        "kind": token.kind.name,
        "lexeme": token.lexeme,
        "value": token.value,
        "span": [token.span.start, token.span.end],
    }


def _diagnostic_to_json(diagnostic, source_text: Optional[str]) -> dict[str, Any]:
    span = diagnostic.span if diagnostic.span else None
    payload = {
        "code": getattr(diagnostic, "code", ""),
        "message": diagnostic.message if hasattr(diagnostic, "message") else str(diagnostic),
        "span": [span.start, span.end] if span else None,
    }
    if span and source_text is not None:
        payload["snippet"] = source_text[span.start : span.end]
    return payload


def _print_error(exc: Exception) -> None:
    click.echo(str(exc), err=True)


def _ast_to_dict(value: Any) -> Any:
    """Convert AST dataclasses into a JSON-serialisable structure."""

    if is_dataclass(value):
        result = {"__type__": value.__class__.__name__}
        for field in fields(value):
            result[field.name] = _ast_to_dict(getattr(value, field.name))
        return result
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, (list, tuple, set)):
        return [_ast_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _ast_to_dict(val) for key, val in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Fallback for types like Span; rely on their repr for now.
    return repr(value)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
