"""Command-line interface for the Scriptum toolchain."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Optional

import click

try:
    from pyfiglet import Figlet
except Exception:  # pragma: no cover - fallback when dependency is missing
    Figlet = None

from . import __version__, errors, tokens
from .codegen import generate
from .driver import CompilerDriver, Stage
from .ir import format_module_ir
from .lexer.lexer import ScriptumLexer
from .parser.parser import ScriptumParser
from .text import SourceFile, highlight_span, line_col

HELP_OPTIONS = ["-h", "--help"]


class ScriptumFile(click.ParamType):
    """Click parameter type that validates Scriptum source files."""

    name = "scriptum-source"

    def __init__(self, exists: bool = True) -> None:
        self._delegate = click.Path(exists=exists, dir_okay=False, path_type=pathlib.Path)

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> pathlib.Path:
        path = self._delegate.convert(value, param, ctx)
        if path.suffix.lower() != ".stm":
            self.fail("Scriptum source files must use the .stm extension.", param, ctx)
        return path


SCRIPTUM_FILE = ScriptumFile()


DEFAULT_BANNER = """
   _____           _       __
  / ___/__________(_)___  / /___  ______ ___
  \\__ \\/ ___/ ___/ / __ \\/ __/ / / / __ `__ \\
 ___/ / /__/ /  / / /_/ / /_/ /_/ / / / / / /
/____/\\___/_/  /_/ .___/\\__/\\__,_/_/ /_/ /_/
                /_/
""".strip("\n")


def _render_banner() -> str:
    text = "Scriptum"
    banner = DEFAULT_BANNER
    if Figlet is not None:
        try:
            banner = Figlet(font="slant").renderText(text).rstrip()
        except Exception:  # pragma: no cover - fallback to plain text
            banner = DEFAULT_BANNER
    return click.style(banner, fg="cyan")


class ScriptumGroup(click.Group):
    """Custom Click group that treats bare .stm arguments as an implicit run command."""

    def resolve_command(self, ctx: click.Context, args: list[str]):
        if args:
            head = args[0]
            if (
                head not in self.commands
                and not head.startswith("-")
                and head.lower().endswith(".stm")
            ):
                args.insert(0, "run")
        return super().resolve_command(ctx, args)

    def get_help(self, ctx: click.Context) -> str:  # type: ignore[override]
        base = super().get_help(ctx)
        banner = _render_banner()
        return f"{banner}\n{base}"


@click.group(
    cls=ScriptumGroup,
    context_settings={"help_option_names": HELP_OPTIONS},
    invoke_without_command=True,
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("-q", "--quiet", is_flag=True, help="Suppress informational output.")
@click.option(
    "--color",
    type=click.Choice(["auto", "always", "never"]),
    default="auto",
    show_default=True,
    help="Control colored output.",
)
@click.option(
    "--config",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    help="Configuration file path (reserved for future use).",
)
@click.option(
    "-c",
    "inline_code",
    help="Execute inline Scriptum code.",
)
@click.option(
    "-m",
    "module_name",
    help="Execute a Scriptum module using dotted notation (e.g., examples.basic).",
)
@click.version_option(__version__, "-V", "--version", message="Scriptum CLI %(version)s")
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool,
    quiet: bool,
    color: str,
    config: Optional[pathlib.Path],
    inline_code: Optional[str],
    module_name: Optional[str],
) -> None:
    """Scriptum build and developer utilities."""

    ctx.obj = {
        "verbose": verbose,
        "quiet": quiet,
        "color": color,
        "config": config,
    }

    if ctx.invoked_subcommand is None:
        _dispatch_default(ctx, inline_code=inline_code, module_name=module_name)


def _dispatch_default(ctx: click.Context, inline_code: Optional[str], module_name: Optional[str]) -> None:
    """Handle `scriptum <file>` / `scriptum -c` / `scriptum -m` when no subcommand is supplied."""

    args = list(ctx.args or [])
    source_value = args[0] if args else None

    if not inline_code and not module_name and not source_value:
        click.echo(ctx.command.get_help(ctx))
        ctx.exit(0)

    source_path = _coerce_source_argument(source_value) if source_value else None
    ctx.args = args[1:] if args else []
    ctx.invoke(run_cmd, source=source_path, inline_code=inline_code, module_name=module_name)


def _coerce_source_argument(value: Optional[str]) -> Optional[pathlib.Path]:
    if value is None:
        return None
    try:
        return SCRIPTUM_FILE.convert(value, None, None)
    except click.BadParameter as exc:
        raise click.UsageError(str(exc)) from exc


def _write_temp_source(payload: str) -> pathlib.Path:
    """Persist Scriptum code into a temporary file."""

    tmp = tempfile.NamedTemporaryFile("w", suffix=".stm", delete=False, encoding="utf8")
    tmp.write(payload)
    tmp.flush()
    tmp.close()
    return pathlib.Path(tmp.name)


def _resolve_module(module_name: str) -> pathlib.Path:
    relative_path = pathlib.Path(*module_name.split(".")).with_suffix(".stm")
    candidates = [
        pathlib.Path.cwd() / relative_path,
        pathlib.Path.cwd() / "examples" / relative_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise click.UsageError(f"Could not find module '{module_name}' ({relative_path}).")


def _wrap_inline_snippet(snippet: str) -> str:
    body = snippet.strip()
    if not body:
        return ""
    if not body.endswith(";"):
        body += ";"
    if not body.startswith("redde"):
        body = f"redde {body}"
    return "functio main() {\n    " + body + "\n}\n"


def _prepare_inline_program(snippet: str) -> str:
    stripped = snippet.strip()
    if not stripped:
        raise click.UsageError("Inline code cannot be empty.")
    if "functio" in stripped:
        return stripped
    wrapped = _wrap_inline_snippet(stripped)
    if not wrapped:
        raise click.UsageError("Inline code cannot be empty.")
    return wrapped


def _warn_legacy(command: str, replacement: str) -> None:
    click.secho(
        f"[warning] '{command}' will be removed in v0.4.0. Use '{replacement}'.",
        fg="yellow",
        err=True,
    )


def _handle_semantic_error(exc: errors.SemanticError, source: pathlib.Path) -> None:
    text_data = source.read_text(encoding="utf8")
    payload = [_diagnostic_to_json(diag, text_data) for diag in exc.diagnostics]
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    raise click.ClickException("Semantic analysis failed.") from exc


def _handle_compiler_error(exc: errors.CompilerError) -> None:
    raise click.ClickException(str(exc)) from exc


def _run_driver(source: pathlib.Path, stage: Stage) -> CompilerDriver.Result:
    driver = CompilerDriver()
    try:
        return driver.run(source=source, until=stage)
    except errors.SemanticError as exc:
        _handle_semantic_error(exc, source)
    except errors.CompilerError as exc:
        _handle_compiler_error(exc)
    raise AssertionError("unreachable")  # pragma: no cover


# ---------------------------------------------------------------------------
# Primary workflow commands
# ---------------------------------------------------------------------------


@cli.command("run", help="Execute a Scriptum program from a file, snippet, or module.")
@click.argument("source", type=SCRIPTUM_FILE, required=False)
@click.option("-c", "--command", "inline_code", help="Inline Scriptum code to execute.")
@click.option("-m", "--module", "module_name", help="Scriptum module to execute (dotted path).")
def run_cmd(source: Optional[pathlib.Path], inline_code: Optional[str], module_name: Optional[str]) -> None:
    provided = sum(val is not None for val in (source, inline_code, module_name))
    if provided == 0:
        raise click.UsageError("Provide a .stm file, -c, or -m.")
    if provided > 1:
        raise click.UsageError("Choose only one input source: file, -c, or -m.")

    delete_source: Optional[pathlib.Path] = None
    if inline_code:
        program_text = _prepare_inline_program(inline_code)
        source = _write_temp_source(program_text)
        delete_source = source
    elif module_name:
        source = _resolve_module(module_name)

    try:
        result = _run_driver(source, Stage.RUN)
    finally:
        if delete_source and delete_source.exists():
            delete_source.unlink(missing_ok=True)

    execution = result.execution
    value = execution.value if execution else None
    click.echo(json.dumps(value, ensure_ascii=False))


@cli.command("repl", help="Start an experimental Scriptum REPL.")
def repl_cmd() -> None:
    click.echo("Scriptum REPL (experimental). Type 'exit' to leave.")
    while True:
        try:
            line = click.prompt(">>>", prompt_suffix=" ", default="", show_default=False)
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break

        if line.strip() in {"exit", "quit"}:
            break
        wrapped = _wrap_inline_snippet(line)
        if not wrapped:
            continue
        temp_source = _write_temp_source(wrapped)
        try:
            result = _run_driver(temp_source, Stage.RUN)
            value = result.execution.value if result.execution else None
            click.echo(value)
        except click.ClickException as exc:
            click.secho(str(exc), fg="red")
        finally:
            temp_source.unlink(missing_ok=True)


@cli.command("build", help="Compile a Scriptum program and emit a formatted file or IR.")
@click.argument("source", type=SCRIPTUM_FILE, required=True)
@click.option(
    "--emit",
    type=click.Choice(["fmt", "ir"]),
    default="fmt",
    show_default=True,
    help="Select the artifact to emit.",
)
@click.option("--out", "output_path", type=click.Path(dir_okay=False, path_type=pathlib.Path))
def build_cmd(source: pathlib.Path, emit: str, output_path: Optional[pathlib.Path]) -> None:
    result = _run_driver(source, Stage.CODEGEN)
    if emit == "ir":
        payload = format_module_ir(result.ir) if result.ir else "{}"
    else:
        payload = result.formatted or ""
    _write_payload(payload, output_path)


def _write_payload(payload: str, destination: Optional[pathlib.Path]) -> None:
    if destination:
        destination.write_text(payload, encoding="utf8")
        click.echo(f"Artifact written to {destination}")
    else:
        click.echo(payload)


@cli.command("package", help="Build standalone binaries via PyInstaller.")
@click.option(
    "--spec",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    default=pathlib.Path("scriptum.spec"),
    show_default=True,
)
@click.option("--pyinstaller", default="pyinstaller", show_default=True, help="PyInstaller executable to invoke.")
def package_cmd(spec: pathlib.Path, pyinstaller: str) -> None:
    if not spec.exists():
        raise click.UsageError(f"PyInstaller spec file not found: {spec}")
    cmd = [pyinstaller, "--clean", "--noconfirm", str(spec)]
    click.echo(" ".join(cmd))
    subprocess.run(cmd, check=True)
    click.echo("Package generated under ./dist")


def _perform_semantic_check(source: pathlib.Path, json_output: bool, quiet_success: bool = False) -> bool:
    driver = CompilerDriver()
    try:
        result = driver.run(source, until=Stage.SEMANTIC)
    except errors.SemanticError as exc:
        _handle_semantic_error(exc, source)
        return
    except errors.CompilerError as exc:
        _handle_compiler_error(exc)
        return

    diagnostics = result.diagnostics or []
    if diagnostics:
        payload = [_diagnostic_to_json(diag, source.read_text(encoding="utf8")) for diag in diagnostics]
        if json_output:
            click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for diagnostic in payload:
                click.echo(f"{diagnostic['code']}: {diagnostic['message']}")
        raise click.ClickException("Semantic analysis reported issues.")

    if json_output and not quiet_success:
        click.echo("[]")
    return True


@cli.command("check", help="Run semantic analysis and report diagnostics.")
@click.argument("source", type=SCRIPTUM_FILE, required=True)
@click.option("--json", "json_output", is_flag=True, help="Return diagnostics as JSON.")
def check_cmd(source: pathlib.Path, json_output: bool) -> None:
    _perform_semantic_check(source, json_output, quiet_success=json_output)
    if not json_output:
        click.echo("Semantic analysis completed successfully.")


@cli.command("fmt", help="Format Scriptum files or stdin.")
@click.argument("source", type=SCRIPTUM_FILE, required=False)
def fmt_cmd(source: Optional[pathlib.Path]) -> None:
    parser = ScriptumParser()

    if source is None:
        text_data = sys.stdin.read()
        if not text_data:
            raise click.UsageError("No input received on stdin.")
        try:
            module = parser.parse(SourceFile("<stdin>", text_data))
        except errors.CompilerError as exc:
            _handle_compiler_error(exc)
        formatted = generate(module).formatted
        click.echo(formatted, nl=False)
        return

    original_text = source.read_text(encoding="utf8")
    try:
        module = parser.parse(SourceFile(str(source), original_text))
    except errors.CompilerError as exc:
        _handle_compiler_error(exc)

    formatted = generate(module).formatted
    if original_text != formatted:
        source.write_text(formatted, encoding="utf8")
        click.echo(f"Formatted {source}")
    else:
        click.echo(f"{source} already formatted")


@cli.command("test", help="Run the automated test suite.")
@click.option("--unit/--no-unit", default=True, show_default=True, help="Run pytest.")
@click.option("--smoke/--no-smoke", default=False, show_default=True, help="Run smoke-test scripts.")
def test_cmd(unit: bool, smoke: bool) -> None:
    if unit:
        click.echo("Running pytest...")
        subprocess.run([sys.executable, "-m", "pytest"], check=True)
    if smoke:
        script = pathlib.Path("scripts") / ("smoke_local.ps1" if os.name == "nt" else "smoke_local.sh")
        if not script.exists():
            raise click.ClickException(f"Smoke script not found: {script}")
        click.echo(f"Running {script}...")
        if script.suffix == ".ps1":
            subprocess.run(["powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass", "-File", str(script)], check=True)
        else:
            subprocess.run(["bash", str(script)], check=True)


@cli.group("doc", help="Documentation utilities.")
def doc_group() -> None:
    """Namespace for documentation commands."""


@doc_group.command("build", help="Copy docs/wiki into a build directory.")
@click.option(
    "--output",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    default=pathlib.Path("build/docs"),
    show_default=True,
)
def doc_build_cmd(output: pathlib.Path) -> None:
    wiki = pathlib.Path("docs") / "wiki"
    if not wiki.exists():
        raise click.ClickException("docs/wiki directory not found.")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(wiki, output)
    click.echo(f"Documentation copied to {output}")


@doc_group.command("serve", help="Serve the documentation locally.")
@click.option("--port", default=8000, show_default=True, type=int)
def doc_serve_cmd(port: int) -> None:
    wiki = pathlib.Path("docs") / "wiki"
    if not wiki.exists():
        raise click.ClickException("docs/wiki directory not found.")
    click.echo(f"Serving documentation at http://localhost:{port}")
    subprocess.run([sys.executable, "-m", "http.server", str(port), "--directory", str(wiki)], check=True)


# ---------------------------------------------------------------------------
# Developer utilities (`scriptum dev ...`)
# ---------------------------------------------------------------------------


@cli.group("dev", help="Developer tooling commands.")
def dev_group() -> None:
    """Namespace for development utilities."""


def _lex_impl(source: pathlib.Path) -> None:
    result = _run_driver(source, Stage.LEXER)
    payload = [
        _token_to_json(token)
        for token in (result.tokens or [])
        if token.kind is not tokens.TokenKind.EOF
    ]
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _ast_impl(source: pathlib.Path) -> None:
    result = _run_driver(source, Stage.PARSER)
    if result.ast is None:
        click.echo("{}")
        return
    payload = _ast_to_dict(result.ast)
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


def _ir_impl(source: pathlib.Path) -> None:
    result = _run_driver(source, Stage.IR)
    if result.ir is None:
        click.echo("{}")
        return
    click.echo(format_module_ir(result.ir))


def _build_lexer_tables() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    script = root / "scripts" / "build_afd.py"
    subprocess.check_call([sys.executable, str(script)])
    ScriptumLexer._TABLES_CACHE = None
    click.echo("AFD gerado com sucesso.")


@dev_group.command("lex", help="Tokenize a file and emit JSON.")
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def dev_lex_cmd(source: pathlib.Path) -> None:
    _lex_impl(source)


@dev_group.command("ast", help="Emit the AST as JSON.")
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def dev_ast_cmd(source: pathlib.Path) -> None:
    _ast_impl(source)


@dev_group.command("ir", help="Show the structural IR.")
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def dev_ir_cmd(source: pathlib.Path) -> None:
    _ir_impl(source)


@dev_group.command("tokens", help="List supported tokens, operators, and delimiters.")
def dev_tokens_cmd() -> None:
    payload = {
        "keywords": list(tokens.KEYWORDS),
        "operators": list(tokens.OPERATORS),
        "punctuation": list(tokens.PUNCTUATION),
        "delimiters": list(tokens.DELIMITERS),
    }
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@dev_group.command("build-lexer", help="Rebuild lexer tables and DFA diagrams.")
def dev_build_lexer_cmd() -> None:
    _build_lexer_tables()


@dev_group.command("bench", help="Run a simple benchmark across example programs.")
def dev_bench_cmd() -> None:
    examples_root = pathlib.Path("examples") / "ok"
    if not examples_root.exists():
        raise click.ClickException(f"Directory {examples_root} not found.")
    examples = list(examples_root.glob("**/*.stm"))
    driver = CompilerDriver()
    for example in examples:
        driver.run(example, until=Stage.CODEGEN)
    click.echo(f"Bench completed for {len(examples)} files.")


# ---------------------------------------------------------------------------
# Legacy aliases (to be removed in v0.4.0)
# ---------------------------------------------------------------------------


@cli.command("lex", hidden=True)
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def legacy_lex_cmd(source: pathlib.Path) -> None:
    _warn_legacy("scriptum lex", "scriptum dev lex")
    _lex_impl(source)


@cli.command("parse", hidden=True)
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def legacy_parse_cmd(source: pathlib.Path) -> None:
    _warn_legacy("scriptum parse", "scriptum dev ast")
    _ast_impl(source)


@cli.command("sema", hidden=True)
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def legacy_sema_cmd(source: pathlib.Path) -> None:
    _warn_legacy("scriptum sema", "scriptum check")
    _perform_semantic_check(source, json_output=True)


@cli.command("ir", hidden=True)
@click.argument("source", type=SCRIPTUM_FILE, required=True)
def legacy_ir_cmd(source: pathlib.Path) -> None:
    _warn_legacy("scriptum ir", "scriptum dev ir")
    _ir_impl(source)


@cli.command("compile", hidden=True)
@click.argument("source", type=SCRIPTUM_FILE, required=True)
@click.option(
    "--stage",
    type=click.Choice([stage.value for stage in Stage]),
    default=Stage.CODEGEN.value,
    show_default=True,
    help="Pipeline stage to stop after.",
)
def legacy_compile_cmd(source: pathlib.Path, stage: str) -> None:
    _warn_legacy("scriptum compile", "scriptum build")
    _run_driver(source, Stage(stage))


@cli.command("build-lexer", hidden=True)
def legacy_build_lexer_cmd() -> None:
    _warn_legacy("scriptum build-lexer", "scriptum dev build-lexer")
    _build_lexer_tables()


@cli.command("version", help="Show the Scriptum CLI version.")
def version_cmd() -> None:
    click.echo(f"Scriptum CLI version {__version__}")


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
        line, column = line_col(source_text, span)
        payload["position"] = {"line": line, "column": column}
        payload["highlight"] = highlight_span(source_text, span)
    return payload


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
