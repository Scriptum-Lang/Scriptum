"""Command-line interface for the Scriptum toolchain."""

from __future__ import annotations

import json
import pathlib
from typing import Optional

import click

from .driver import CompilerDriver, Stage
from .lexer.generator import write_tables
from .lexer.lexer import LexerConfig, ScriptumLexer
from .text import SourceFile
from . import tokens


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """Scriptum build and developer utilities."""


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
@click.option("--show", is_flag=True, help="Print the generated tables to stdout")
def build_lexer_cmd(show: bool) -> None:
    """Regenerate the lexer DFA tables."""

    tables_path = ScriptumLexer.tables_path()
    tables = write_tables(tables_path)
    click.echo(f"Lexer tables written to {tables_path}")
    if show:
        click.echo(json.dumps(tables, indent=2, ensure_ascii=False))


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


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
