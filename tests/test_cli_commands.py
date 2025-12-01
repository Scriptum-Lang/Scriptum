from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from scriptum.cli import _ReplSession, cli

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
    payload_text = err_result.output.split("ERRO", 1)[0].strip()
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



def test_inline_execution_without_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["-c", "42"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == 42


def test_inline_execution_accepts_statements() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["-c", "mutabilis numerus a = 1;"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) is None


def test_repl_session_persists_state() -> None:
    session = _ReplSession()
    assert session.execute("mutabilis numerus a = 1;") is None
    assert session.execute("a") == 1
    assert session.execute("a = a + 1;") is None
    assert session.execute("a") == 2


def test_run_without_input_uses_error_schema() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["run"])
    assert result.exit_code != 0
    assert "ERRO [CLI_USAGE]" in result.output


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


def _make_stub_llvm_as(tmp_path: Path, *, success: bool, message: str = "erro sintético") -> Path:
    script_dir = tmp_path / "llvm_stub"
    script_dir.mkdir(exist_ok=True)
    if os.name == "nt":
        suffix = "ok.bat" if success else "fail.bat"
        script = script_dir / f"llvm-as-{suffix}"
        if success:
            script.write_text('@echo off\r\ncopy /Y "%~1" "%~3" >NUL\r\nexit /b 0\r\n', encoding="utf8")
        else:
            script.write_text(f'@echo off\r\necho {message} 1>&2\r\nexit /b 1\r\n', encoding="utf8")
        return script
    script = script_dir / ("llvm-as-ok" if success else "llvm-as-fail")
    if success:
        body = '#!/bin/sh\ncp "$1" "$3"\n'
    else:
        escaped = message.replace('"', '\\"')
        body = f'#!/bin/sh\necho "{escaped}" 1>&2\nexit 1\n'
    script.write_text(body, encoding="utf8")
    script.chmod(0o755)
    return script


def test_build_verify_llvm_with_stub(tmp_path: Path) -> None:
    stub = _make_stub_llvm_as(tmp_path, success=True)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["build", "--emit", "llvm", "--verify-llvm", str(FIXTURES / "basic_valid.stm")],
        env={"LLVM_AS": str(stub)},
    )
    assert result.exit_code == 0, result.output
    assert "define %scriptum.value" in result.output


def test_build_verify_llvm_reports_error(tmp_path: Path) -> None:
    stub = _make_stub_llvm_as(tmp_path, success=False, message="falha proposital")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["build", "--emit", "llvm", "--verify-llvm", str(FIXTURES / "basic_valid.stm")],
        env={"LLVM_AS": str(stub)},
    )
    assert result.exit_code != 0
    assert "CLI_LLVM_VERIFY" in result.output
    assert "falha proposital" in result.output


def test_build_verify_llvm_missing_tool(tmp_path: Path) -> None:
    runner = CliRunner()
    missing = tmp_path / "llvm-as"
    result = runner.invoke(
        cli,
        ["build", "--emit", "llvm", "--verify-llvm", str(FIXTURES / "basic_valid.stm")],
        env={"LLVM_AS": str(missing)},
    )
    assert result.exit_code != 0
    assert "CLI_LLVM_TOOL" in result.output


def test_run_backend_llvm_falls_back_when_lli_missing() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--backend", "llvm", str(FIXTURES / "main_return.stm")],
        env={"LLI": str(Path("missing_lli"))},
    )
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert json.loads(lines[-1]) == 2
    assert "executando com a vm" in result.output.lower()


def test_run_backend_bytecode_executes_program() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--backend", "bytecode", str(FIXTURES / "basic_valid.stm")],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == 3


def test_run_backend_llvm_cpp_falls_back_when_module_missing() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--backend", "llvm-cpp", str(FIXTURES / "main_return.stm")],
    )
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert json.loads(lines[-1]) == 2
    assert "executando com a vm" in result.output.lower()


def test_build_defaults_to_env_backend_when_emit_omitted(tmp_path: Path) -> None:
    stub = _make_stub_llvm_as(tmp_path, success=True)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["build", "--verify-llvm", str(FIXTURES / "basic_valid.stm")],
        env={"SCRIPTUM_BACKEND": "llvm", "LLVM_AS": str(stub)},
    )
    assert result.exit_code == 0, result.output
    assert "define %scriptum.value" in result.output


def test_build_fmt_requires_vm_backend() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["build", "--backend", "llvm", "--emit", "fmt", str(FIXTURES / "basic_valid.stm")],
    )
    assert result.exit_code != 0
    assert "fmt" in result.output.lower()


def test_build_emit_bytecode_outputs_listing() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["build", "--backend", "bytecode", "--emit", "bytecode", str(FIXTURES / "basic_valid.stm")],
    )
    assert result.exit_code == 0, result.output
    assert "functio principalis" in result.output.lower()


def test_run_backend_llvm_uses_env_when_option_omitted() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", str(FIXTURES / "main_return.stm")],
        env={"SCRIPTUM_BACKEND": "llvm", "LLI": str(Path("missing_lli"))},
    )
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert json.loads(lines[-1]) == 2
    assert "executando com a vm" in result.output.lower()


def test_run_backend_strict_flag_reports_error() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--backend", "llvm", "--strict-backend", str(FIXTURES / "main_return.stm")],
        env={"LLI": str(Path("missing_lli"))},
    )
    assert result.exit_code != 0
    assert "CLI_BACKEND" in result.output


def test_run_backend_strict_env_variable_is_respected() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--backend", "llvm", str(FIXTURES / "main_return.stm")],
        env={"LLI": str(Path("missing_lli")), "SCRIPTUM_BACKEND_STRICT": "1"},
    )
    assert result.exit_code != 0
    assert "CLI_BACKEND" in result.output
