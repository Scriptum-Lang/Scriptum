from __future__ import annotations

import textwrap

from scriptum.codegen import generate_llvm
from scriptum.ir import lower_module
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile


def _emit_llvm(source: str) -> str:
    parser = ScriptumParser()
    normalized = textwrap.dedent(source).strip() + "\n"
    module = parser.parse(SourceFile("<test>", normalized))
    ir_module = lower_module(module)
    output = generate_llvm(ir_module)
    return output.llvm


def test_simple_function_llvm_codegen() -> None:
    llvm = _emit_llvm(
        """
        functio principalis() -> numerus {
            mutabilis numerus x = 1;
            redde x + 2;
        }
        """
    )
    assert "define double @principalis(" in llvm
    assert "alloca double" in llvm
    assert "fadd double" in llvm
    assert "ret double" in llvm


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
    assert "while_cond" in llvm
    assert "while_body" in llvm
    assert "while_end" in llvm
    assert "br i1" in llvm

