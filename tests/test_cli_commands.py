from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scriptum.cli import cli

FIXTURES = Path(__file__).resolve().parents[0] / "fixtures" / "programs"


def test_dev_lex_outputs_tokens_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["dev", "lex", str(FIXTURES / "basic_valid.stm")])
    assert result.exit_code == 0, result.output
    tokens = json.loads(result.output)
    assert tokens[0]["kind"] == "KEYWORD"
    assert tokens[0]["lexeme"] in {"constans", "mutabilis"}


def test_dev_ast_outputs_ast_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["dev", "ast", str(FIXTURES / "basic_valid.stm")])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["__type__"] == "Module"
    assert payload["declarations"]


def test_check_reports_diagnostics_in_json() -> None:
    runner = CliRunner()
    ok_result = runner.invoke(cli, ["check", str(FIXTURES / "basic_valid.stm")])
    assert ok_result.exit_code == 0, ok_result.output
    assert "Semantic analysis completed successfully." in ok_result.output

    err_result = runner.invoke(
        cli,
        ["check", str(FIXTURES / "error_sema.stm"), "--json"],
    )
    assert err_result.exit_code != 0
    payload_text = err_result.output.split("Error:", 1)[0].strip()
    diagnostics = json.loads(payload_text)
    assert diagnostics and diagnostics[0]["code"] == "S100"
    assert diagnostics[0]["position"]["line"] >= 1


def test_dev_ir_and_run_commands() -> None:
    runner = CliRunner()
    ir_result = runner.invoke(cli, ["dev", "ir", str(FIXTURES / "basic_valid.stm")])
    assert ir_result.exit_code == 0, ir_result.output
    assert "ModuleIr" in ir_result.output

    run_result = runner.invoke(cli, ["run", str(FIXTURES / "main_return.stm")])
    assert run_result.exit_code == 0, run_result.output
    assert json.loads(run_result.output) == 2


def test_default_invocation_executes_program() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [str(FIXTURES / "main_return.stm")])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == 2


def test_legacy_lex_still_available_with_warning() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["lex", str(FIXTURES / "basic_valid.stm")])
    assert result.exit_code == 0, result.output
    assert "[warning]" in result.output


def test_inline_execution_without_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["-c", "42"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == 42


@pytest.mark.parametrize(
    "argv",
    [
        ["dev", "lex"],
        ["dev", "ast"],
        ["dev", "ir"],
        ["check"],
        ["fmt"],
        ["build"],
    ],
)
def test_cli_rejects_non_stm_files(argv: list[str]) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("program.txt").write_text("scriptum content")
        result = runner.invoke(cli, argv + ["program.txt"])
    assert result.exit_code != 0
    assert "must use the .stm extension" in result.output
