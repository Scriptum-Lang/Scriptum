from __future__ import annotations

import textwrap
from pathlib import Path

from scriptum.ir import format_module_ir, lower_module
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile

FIXTURES_DIR = Path(__file__).resolve().parents[0] / 'fixtures' / 'ir'


def _lower_source(source: str) -> str:
    parser = ScriptumParser()
    normalized = textwrap.dedent(source).strip() + '\n'
    module = parser.parse(SourceFile('<test>', normalized))
    ir_module = lower_module(module)
    return format_module_ir(ir_module)


def test_lowering_with_loops_and_conditionals() -> None:
    result = _lower_source(
        """
        mutabilis numerus contador = 0;

        functio atualizar(numerus limite) -> numerus {
            mutabilis numerus total = 0;
            dum (total < limite) {
                total = total + 1;
                si (total == limite) {
                    frange;
                } aliter {
                    perge;
                }
            }
            redde total ?? 0;
        }
        """
    )
    expected = (FIXTURES_DIR / 'loops.json').read_text(encoding='utf8').strip()
    assert result == expected


def test_lowering_with_collections_and_lambda() -> None:
    result = _lower_source(
        """
        constans numerus base = 10;

        functio transformar(valores) {
            mutabilis numerus soma = 0;
            pro item in valores {
                soma = soma + item;
            }
            mutabilis textus status = structura { texto: "ok" }.texto;
            mutabilis numerus primeiro = [1, 2, 3][0];
            mutabilis quodlibet mapper = functio (x) => x ? x : soma;
            redde mapper(soma);
        }
        """
    )
    expected = (FIXTURES_DIR / 'collections.json').read_text(encoding='utf8').strip()
    assert result == expected
