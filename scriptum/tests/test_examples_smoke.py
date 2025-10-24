from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scriptum.driver import CompilerDriver, Stage

OK_DIR = Path("examples/ok")
ERR_DIR = Path("examples/err")


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


@pytest.mark.parametrize("program", sorted(ERR_DIR.glob("*.stm")))
def test_examples_err_semantics(program: Path) -> None:
    expected_codes = set(_expect_errors(program))
    driver = CompilerDriver()
    result = driver.run(program, until=Stage.SEMANTIC)
    diagnostics = result.diagnostics or []
    diag_codes = {diag.code for diag in diagnostics}
    assert expected_codes.issubset(diag_codes)
