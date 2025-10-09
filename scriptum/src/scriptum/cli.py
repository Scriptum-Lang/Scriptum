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

from . import __version__, tokens
from .driver import CompilerDriver, Stage
from .lexer.lexer import LexerConfig, ScriptumLexer
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
    driver.run(source=source, until=Stage(stage))


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
@click.option("--no-skip-whitespace", is_flag=True, help="Emit whitespace and comment tokens")
def lex_cmd(source: pathlib.Path, no_skip_whitespace: bool) -> None:
    """Tokenise a Scriptum source file and print the resulting tokens."""

    text_data = source.read_text(encoding="utf8")
    lexer = ScriptumLexer(config=LexerConfig(skip_whitespace=not no_skip_whitespace))
    stream = lexer.tokenize(SourceFile(str(source), text_data))
    for token in stream:
        if token.kind is tokens.TokenKind.EOF:
            continue
        value_repr = "" if token.value in (None, token.lexeme) else f" value={token.value!r}"
        click.echo(f"{token.kind.name:16} {token.lexeme!r}{value_repr}")


@cli.command("parse")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option("--dump-ast", is_flag=True, help="Print the parsed AST as JSON")
def parse_cmd(source: pathlib.Path, dump_ast: bool) -> None:
    """Parse a Scriptum source file and optionally dump the AST."""

    text_data = source.read_text(encoding="utf8")
    parser = ScriptumParser()
    module = parser.parse(SourceFile(str(source), text_data))
    if dump_ast:
        click.echo(json.dumps(_ast_to_dict(module), indent=2, ensure_ascii=False))
    else:
        click.echo(f"Parsed {source}")


@cli.command("run")
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
def run_cmd(source: pathlib.Path) -> None:
    """
    Run a Scriptum program (placeholder).

    This command will eventually execute the full compilation pipeline and run
    the generated program. For now, it simply notifies the feature gap.
    """

    click.echo(
        f"'scriptum run' is not implemented yet. Parsed {source.name} successfully.",
    )


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
