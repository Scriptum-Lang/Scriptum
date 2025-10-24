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


def _analyze_snippet(source: str):
    parser = ScriptumParser()
    module = parser.parse(SourceFile("<test>", source))
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(module)


def test_use_before_declaration_reports_s100() -> None:
    diagnostics = _analyze_snippet(
        """
        mutabilis numerus x = y;
        mutabilis numerus y = 1;
        """
    )
    codes = {diag.code for diag in diagnostics}
    assert "S100" in codes


def test_assignment_to_immutable_symbol_reports_s120() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo() {
            constans numerus resposta = 42;
            resposta = 0;
        }
        """
    )
    assert any(diag.code == "S120" for diag in diagnostics)


def test_if_condition_requires_boolean_t020() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo() {
            mutabilis numerus x = 1;
            si (x) {
                mutabilis numerus y = 2;
            }
        }
        """
    )
    assert any(diag.code == "T020" for diag in diagnostics)


def test_break_and_continue_require_loop_context() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo() {
            frange;
            perge;
        }
        """
    )
    codes = {diag.code for diag in diagnostics}
    assert "T040" in codes
    assert "T041" in codes


def test_function_call_checks_arity_and_argument_types() -> None:
    diagnostics = _analyze_snippet(
        """
        functio soma(numerus a, numerus b) -> numerus {
            redde a + b;
        }

        functio demo() {
            mutabilis numerus x = soma(1);
            mutabilis numerus y = soma(1, "dois");
        }
        """
    )
    codes = {diag.code for diag in diagnostics}
    assert "T300" in codes
    assert "T301" in codes


def test_nullish_requires_optional_left_operand() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo() {
            mutabilis numerus valor = 10;
            mutabilis numerus outro = valor ?? 0;
        }
        """
    )
    assert any(diag.code == "T120" for diag in diagnostics)


def test_nullish_with_optional_operand_succeeds() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo(entrada: numerus?) {
            mutabilis numerus resultado = entrada ?? 0;
        }
        """
    )
    assert diagnostics == []


def test_ternary_condition_must_be_boolean() -> None:
    diagnostics = _analyze_snippet(
        """
        functio demo() {
            mutabilis numerus x = 1 ? 2 : 3;
        }
        """
    )
    assert any(diag.code == "T130" for diag in diagnostics)
