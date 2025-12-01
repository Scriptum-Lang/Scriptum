from __future__ import annotations

from scriptum.bytecode import BytecodeVM, compile_module
from scriptum.ir import lower_module
from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile


def _run_program(source_text: str):
    parser = ScriptumParser()
    module = parser.parse(SourceFile("<test>", source_text))
    analysis = SemanticAnalyzer().analyze(module)
    ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    program = compile_module(ir_module)
    vm = BytecodeVM(program)
    return vm.run()


def test_bytecode_executes_simple_addition() -> None:
    result = _run_program(
        """
        constans numerus base = 2;

        functio principalis() -> numerus {
            mutabilis numerus outro = 3;
            redde base + outro;
        }
        """
    )
    assert result == 5


def test_bytecode_handles_loops_and_breaks() -> None:
    result = _run_program(
        """
        functio principalis() -> numerus {
            mutabilis numerus total = 0;
            mutabilis numerus idx = 0;
            dum (idx < 5) {
                idx = idx + 1;
                si (idx == 4) {
                    frange;
                } aliter {
                    total = total + idx;
                    perge;
                }
            }
            redde total ?? 0;
        }
        """
    )
    assert result == 6


def test_bytecode_invokes_builtin_summa() -> None:
    result = _run_program(
        """
        functio principalis() -> numerus {
            redde summa([1, 2, 3, 4]);
        }
        """
    )
    assert result == 10
