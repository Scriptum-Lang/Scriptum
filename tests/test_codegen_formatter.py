from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from scriptum.cli import cli
from scriptum.codegen import generate
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile

FIXTURES_DIR = Path(__file__).resolve().parents[0] / "fixtures" / "fmt"


def _load_fixture(name: str) -> tuple[str, str]:
    input_text = (FIXTURES_DIR / f"{name}_input.stm").read_text(encoding="utf8")
    expected_text = (FIXTURES_DIR / f"{name}_expected.stm").read_text(encoding="utf8")
    return input_text, expected_text


def _format_source(text: str) -> str:
    parser = ScriptumParser()
    module = parser.parse(SourceFile("<test>", text))
    return generate(module).formatted


def test_formatter_matches_golden_loops() -> None:
    raw, expected = _load_fixture("loops")
    formatted = _format_source(raw)
    assert formatted == expected


def test_formatter_is_idempotent() -> None:
    _, expected = _load_fixture("loops")
    once = _format_source(expected)
    twice = _format_source(once)
    assert once == expected
    assert twice == expected


def test_cli_fmt_formats_file_in_place(tmp_path: Path) -> None:
    raw, expected = _load_fixture("collections")
    target = tmp_path / "sample.stm"
    target.write_text(raw, encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(cli, ["fmt", str(target)])
    assert result.exit_code == 0
    assert target.read_text(encoding="utf8") == expected

    # Running again should keep the file unchanged.
    result_again = runner.invoke(cli, ["fmt", str(target)])
    assert result_again.exit_code == 0
    assert target.read_text(encoding="utf8") == expected


def test_cli_fmt_from_stdin() -> None:
    raw, expected = _load_fixture("loops")
    runner = CliRunner()
    result = runner.invoke(cli, ["fmt"], input=raw)
    assert result.exit_code == 0
    assert result.output == expected
