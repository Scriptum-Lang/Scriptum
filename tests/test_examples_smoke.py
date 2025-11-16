from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scriptum import errors
from scriptum.driver import CompilerDriver, Stage
from scriptum.parser.parser import ParseError

OK_DIR = Path("examples/ok")
ERR_DIR = Path("examples/err")
ADVANCED_OK_PROGRAMS = [
    Path("examples/ok/avancados/builtins_collections.stm"),
    Path("examples/ok/avancados/textus_manipulacoes.stm"),
]


def _expect_value(path: Path) -> object:
    for line in path.read_text(encoding="utf8").splitlines():
        stripped = line.strip()
        if stripped.startswith("// EXPECT:"):
            payload = stripped.split(":", 1)[1].strip()
            return ast.literal_eval(payload)
    raise AssertionError(f"Missing // EXPECT: marker in {path}")


def _expect_errors(path: Path) -> list[str]:
    for line in path.read_text(encoding="utf8").splitlines():
        stripped = line.strip()
        if stripped.startswith("// ERROR:"):
            payload = stripped.split(":", 1)[1].strip()
            return [code.strip() for code in payload.split(",") if code.strip()]
    raise AssertionError(f"Missing // ERROR: marker in {path}")


@pytest.mark.parametrize("program", sorted(OK_DIR.glob("*.stm")))
def test_examples_ok_run(program: Path) -> None:
    expected = _expect_value(program)
    driver = CompilerDriver()
    result = driver.run(program, until=Stage.RUN)
    assert result.execution is not None
    assert result.execution.value == expected


def _error_category(codes: list[str]) -> str:
    def classify(code: str) -> str:
        if code.startswith("LEX"):
            return "LEXER"
        if code.startswith("PAR"):
            return "PARSER"
        if code.startswith("IR"):
            return "RUNTIME"
        return "SEMANTIC"

    categories = {classify(code) for code in codes}
    if len(categories) != 1:
        raise AssertionError(f"Examples should focus on um único estágio: {codes}")
    return categories.pop()


@pytest.mark.parametrize("program", sorted(ERR_DIR.glob("*.stm")))
def test_examples_err(program: Path) -> None:
    expected_codes = set(_expect_errors(program))
    category = _error_category(list(expected_codes))
    driver = CompilerDriver()

    if category == "SEMANTIC":
        result = driver.run(program, until=Stage.SEMANTIC)
        diagnostics = result.diagnostics or []
        diag_codes = {diag.code for diag in diagnostics}
        assert expected_codes.issubset(diag_codes)
        return

    if category == "LEXER":
        with pytest.raises(errors.LexerError) as captured:
            driver.run(program, until=Stage.SEMANTIC)
        assert captured.value.code in expected_codes
        return

    if category == "PARSER":
        with pytest.raises(ParseError) as captured:
            driver.run(program, until=Stage.SEMANTIC)
        assert captured.value.code in expected_codes
        return

    if category == "RUNTIME":
        with pytest.raises(errors.ExecutionError) as captured:
            driver.run(program, until=Stage.RUN)
        assert captured.value.code in expected_codes
        return

    raise AssertionError(f"Categoria desconhecida: {category}")


@pytest.mark.parametrize("program", ADVANCED_OK_PROGRAMS)
def test_advanced_examples_run(program: Path) -> None:
    expected = _expect_value(program)
    driver = CompilerDriver()
    result = driver.run(program, until=Stage.RUN)
    assert result.execution is not None
    assert result.execution.value == expected
