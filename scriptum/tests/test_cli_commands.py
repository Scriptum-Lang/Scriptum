from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from scriptum.cli import cli

FIXTURES = Path(__file__).resolve().parents[0] / "fixtures" / "programs"


def test_cli_lex_outputs_tokens_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["lex", str(FIXTURES / "basic_valid.stm")])
    assert result.exit_code == 0
    tokens = json.loads(result.output)
    assert tokens[0]["kind"] == "KEYWORD"
    assert tokens[0]["lexeme"] in {"constans", "mutabilis"}


def test_cli_parse_outputs_ast_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["parse", str(FIXTURES / "basic_valid.stm")])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["__type__"] == "Module"
    assert payload["declarations"]


def test_cli_sema_reports_diagnostics() -> None:
    runner = CliRunner()
    ok_result = runner.invoke(cli, ["sema", str(FIXTURES / "basic_valid.stm")])
    assert ok_result.exit_code == 0
    assert json.loads(ok_result.output) == []

    err_result = runner.invoke(cli, ["sema", str(FIXTURES / "error_sema.stm")])
    assert err_result.exit_code == 1
    diagnostics = json.loads(err_result.output)
    assert diagnostics and diagnostics[0]["code"] == "S100"
    assert "position" in diagnostics[0]
    assert diagnostics[0]["position"]["line"] >= 1
    assert "highlight" in diagnostics[0]
    assert "^" in diagnostics[0]["highlight"]


def test_cli_ir_and_run_commands() -> None:
    runner = CliRunner()
    ir_result = runner.invoke(cli, ["ir", str(FIXTURES / "basic_valid.stm")])
    assert ir_result.exit_code == 0
    assert "ModuleIr" in ir_result.output

    run_result = runner.invoke(cli, ["run", str(FIXTURES / "main_return.stm")])
    assert run_result.exit_code == 0
    assert json.loads(run_result.output) == 2
