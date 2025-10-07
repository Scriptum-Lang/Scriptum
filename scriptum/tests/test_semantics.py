from __future__ import annotations

from pathlib import Path

import pytest

from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


def _analyze(relative: str):
    path = EXAMPLES_ROOT / relative
    parser = ScriptumParser()
    module = parser.parse(SourceFile(str(path), path.read_text(encoding="utf8")))
    analyzer = SemanticAnalyzer()
    diagnostics = analyzer.analyze(module)
    return diagnostics


@pytest.mark.parametrize(
    "relative",
    [
        "ok/basicos/variaveis.stm",
        "ok/basicos/condicionais.stm",
        "ok/intermediarios/classes.stm",
    ],
)
def test_semantics_valid_examples(relative: str) -> None:
    diagnostics = _analyze(relative)
    assert diagnostics == []


def test_semantics_detects_type_mismatch() -> None:
    diagnostics = _analyze("err/negativos/tipo_incompativel.stm")
    assert any("Type mismatch" in diag.message for diag in diagnostics)
