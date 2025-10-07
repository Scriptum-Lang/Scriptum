from __future__ import annotations

from pathlib import Path

from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


def _parse_example(relative: str):
    path = EXAMPLES_ROOT / relative
    parser = ScriptumParser()
    module = parser.parse(SourceFile(str(path), path.read_text(encoding="utf8")))
    return module


def test_type_mismatch_in_assignment() -> None:
    module = _parse_example("err/negativos/tipo_incompativel.stm")
    analyzer = SemanticAnalyzer()
    diagnostics = analyzer.analyze(module)
    assert any("Type mismatch" in diag.message for diag in diagnostics)


def test_valid_basico_program() -> None:
    module = _parse_example("ok/basicos/variaveis.stm")
    analyzer = SemanticAnalyzer()
    diagnostics = analyzer.analyze(module)
    assert diagnostics == []
