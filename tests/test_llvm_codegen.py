from __future__ import annotations

import textwrap

import pytest

from scriptum.codegen import generate_llvm
from scriptum.ir import lower_module
from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile


def _emit_llvm(source: str) -> str:
    parser = ScriptumParser()
    normalized = textwrap.dedent(source).strip() + "\n"
    module = parser.parse(SourceFile("<test>", normalized))
    analyzer = SemanticAnalyzer()
    analysis = analyzer.analyze(module)
    ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    output = generate_llvm(ir_module)
    return getattr(output, "llvm", str(getattr(output, "text", output)))


def test_simple_function_llvm_codegen() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis numerus x = 1;
            redde x + 2;
        }
        """
    )
    assert "define %scriptum.value @principalis()" in llvm
    assert "@scriptum_value_number" in llvm
    assert "@scriptum_value_as_number" in llvm
    assert "fadd double" in llvm
    assert "ret %scriptum.value" in llvm


def test_while_loop_llvm_codegen() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis numerus total = 0;
            mutabilis numerus atual = 0;
            dum (atual < 3) {
                atual = atual + 1;
                total = total + atual;
            }
            redde total;
        }
        """
    )
    assert "while.cond" in llvm
    assert "while.body" in llvm
    assert "while.end" in llvm
    assert "@scriptum_value_as_number" in llvm


def test_string_literal_codegen() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> textus {
            redde "salve";
        }
        """
    )
    assert "@.str." in llvm
    assert "getelementptr inbounds" in llvm
    assert "@scriptum_text_new" in llvm
    assert "@scriptum_value_text" in llvm


def test_nullish_and_for_in_codegen() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis numerus total = 0;
            pro (mutabilis numerus valor in [1, 2, 3]) {
                total = (total ?? 0) + valor;
            }
            redde total;
        }
        """
    )
    assert "for.cond" in llvm
    assert "@scriptum_array_new" in llvm
    assert "@scriptum_array_get" in llvm
    assert "nullish.rhs" in llvm
    assert "@scriptum_value_number" in llvm


def test_lambda_codegen_emits_runtime_calls() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis numerus base = 1;
            mutabilis quodlibet mapper = functio (x) => x + base;
            redde mapper(2);
        }
        """
    )
    assert "@scriptum_lambda_new" in llvm
    assert "@scriptum_lambda_call" in llvm
    assert "%lambda.capture" in llvm


def test_builtin_call_emits_runtime_bridge() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis array xs = [1, 2];
            redde summa(xs);
        }
        """
    )
    assert "@scriptum_rt_summa" in llvm


ARRAY_METHOD_CASES = [
    ("xs.adde(3);", "scriptum_rt_array_adde"),
    ("mutabilis expulsus = xs.exime();", "scriptum_rt_array_exime"),
    ("xs.extende([4, 5]);", "scriptum_rt_array_extende"),
    ("xs.inserta(1, 99);", "scriptum_rt_array_inserta"),
    ("xs.remove(2);", "scriptum_rt_array_remove"),
    ("xs.purga();", "scriptum_rt_array_purga"),
]


@pytest.mark.parametrize(("statement", "symbol"), ARRAY_METHOD_CASES)
def test_array_methods_emit_runtime_helpers(statement: str, symbol: str) -> None:
    llvm = _emit_llvm(
        f"""
        functio principalis() {{
            mutabilis xs = [1, 2];
            {statement}
        }}
        """
    )
    assert f"@{symbol}" in llvm


TEXT_METHOD_CASES = [
    ("mutabilis partes = base.divide(\",\");", "scriptum_rt_text_divide"),
    ("mutabilis por_defecto = base.divide();", "scriptum_rt_text_divide"),
    ("mutabilis unido = base.coniunge([\"a\", \"b\"]);", "scriptum_rt_text_coniunge"),
    ("mutabilis mutatus = base.substitue(\"a\", \"x\");", "scriptum_rt_text_substitue"),
    ("mutabilis minus = base.ad_minusculas();", "scriptum_rt_text_ad_minusculas"),
    ("mutabilis maius = base.ad_maiusculas();", "scriptum_rt_text_ad_maiusculas"),
    ("mutabilis limpo = base.abscinde();", "scriptum_rt_text_abscinde"),
]


@pytest.mark.parametrize(("statement", "symbol"), TEXT_METHOD_CASES)
def test_text_methods_emit_runtime_helpers(statement: str, symbol: str) -> None:
    llvm = _emit_llvm(
        f"""
        functio principalis() {{
            mutabilis base = "a,b,c";
            {statement}
        }}
        """
    )
    assert f"@{symbol}" in llvm

