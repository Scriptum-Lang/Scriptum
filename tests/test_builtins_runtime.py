from __future__ import annotations

import textwrap
from typing import Any

import pytest

from scriptum import builtins as std_builtins
from scriptum.ir import lower_module
from scriptum.ir.interpreter import Interpreter
from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile


def _run_program(source: str, entry: str = "principalis") -> Any:
    parser = ScriptumParser()
    normalized = textwrap.dedent(source).strip() + "\n"
    module = parser.parse(SourceFile("<test>", normalized))
    analyzer = SemanticAnalyzer()
    diagnostics = analyzer.analyze(module)
    assert diagnostics == []
    ir_module = lower_module(module)
    interpreter = Interpreter(ir_module)
    return interpreter.execute(entry).value


def test_ambitus_and_summa() -> None:
    result = _run_program(
        """
        functio principalis() -> numerus {
            mutabilis valores = ambitus(0, 5);
            redde summa(valores);
        }
        """
    )
    assert result == 10


def test_minimum_maximum_absolutum() -> None:
    result = _run_program(
        """
        functio principalis() {
            mutabilis valores = [4, 2, 9];
            redde [minimum(valores), maximum(valores), absolutum(-5)];
        }
        """
    )
    assert result == [2, 9, 5]


def test_boolean_helpers() -> None:
    result = _run_program(
        """
        functio principalis() {
            redde [aliquod([falsum, verum, falsum]), omnia([verum, verum]), omnia([])];
        }
        """
    )
    assert result == [True, True, False]


def test_collection_helpers() -> None:
    result = _run_program(
        """
        functio principalis() {
            mutabilis pares = enumera(["a", "b"]);
            mutabilis combinado = coniunge([1, 2], [3, 4]);
            mutabilis dobrado = applica([1, 2, 3], functio (x) => x * 2);
            mutabilis selecionados = filtra(dobrado, functio (x) => x > 2);
                mutabilis ordenado = ordina([3, 1, 2], nullum, falsum);
                redde structura {
                    pares: pares,
                    combinado: combinado,
                    dobrado: dobrado,
                    selecionados: selecionados,
                    ordenado: ordenado
                };
        }
        """
    )
    assert result == {
        "pares": [[0, "a"], [1, "b"]],
        "combinado": [[1, 3], [2, 4]],
        "dobrado": [2, 4, 6],
        "selecionados": [4, 6],
        "ordenado": [1, 2, 3],
    }


def test_array_methods_mutate_collection() -> None:
    result = _run_program(
        """
        functio principalis() {
            mutabilis xs = [1, 2];
            xs.adde(3);
            xs.extende([4, 5]);
            mutabilis numerus ultimo = xs.exime();
            xs.inserta(0, 0);
            xs.remove(2);
            xs.adde(ultimo);
            redde xs;
        }
        """
    )
    assert result == [0, 1, 3, 4, 5]


def test_array_method_purga() -> None:
    result = _run_program(
        """
        functio principalis() -> numerus {
            mutabilis xs = [1, 2];
            xs.purga();
            redde longitudo(xs);
        }
        """
    )
    assert result == 0


def test_string_methods() -> None:
    result = _run_program(
        """
        functio principalis() {
            mutabilis partes = "a,b,c".divide(",");
            mutabilis textus unido = ", ".coniunge(["a", "b", "c"]);
            mutabilis textus trocado = "abcabc".substitue("a", "x");
                redde structura {
                    partes: partes,
                    unido: unido,
                    trocado: trocado,
                    minusculas: "AbC".ad_minusculas(),
                    maiusculas: "AbC".ad_maiusculas(),
                    aparado: "  texto  ".abscinde()
                };
            }
            """
        )
    assert result == {
        "partes": ["a", "b", "c"],
        "unido": "a, b, c",
        "trocado": "xbcxbc",
        "minusculas": "abc",
        "maiusculas": "ABC",
        "aparado": "texto",
    }


def test_scribe_writes_all_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    _run_program(
        """
        functio principalis() {
            scribe("salve", 42, verum);
        }
        """
    )
    captured = capsys.readouterr()
    assert captured.out == "salve 42 verum\n"


def test_lege_uses_custom_input_provider() -> None:
    std_builtins.set_input_provider(lambda prompt: "linha\n")
    try:
        result = _run_program(
            """
            functio principalis() -> textus {
                redde lege(">");
            }
            """
        )
    finally:
        std_builtins.reset_input_provider()
    assert result == "linha"
