from __future__ import annotations

from pathlib import Path

import pytest

from scriptum.ast import nodes
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


def _parse(relative: str) -> nodes.Module:
    path = EXAMPLES_ROOT / relative
    parser = ScriptumParser()
    module = parser.parse(SourceFile(str(path), path.read_text(encoding="utf8")))
    assert isinstance(module, nodes.Module)
    return module


@pytest.mark.parametrize(
    "relative",
    [
        "ok/basicos/variaveis.stm",
        "ok/basicos/condicionais.stm",
        "ok/intermediarios/classes.stm",
        "ok/avancados/sistema_bancario.stm",
    ],
)
def test_parser_smoke(relative: str) -> None:
    module = _parse(relative)
    assert module.declarations  # module must contain at least one declaration


def test_parser_detects_assignments_and_call() -> None:
    module = _parse("ok/avancados/sistema_bancario.stm")
    init_func = next(decl for decl in module.declarations if isinstance(decl, nodes.FunctionDeclaration) and decl.name == "init")
    assign_stmt = next(stmt for stmt in init_func.body.statements if isinstance(stmt, nodes.ExpressionStatement))
    assert isinstance(assign_stmt.expression, nodes.AssignmentExpression)
    assert isinstance(assign_stmt.expression.value, nodes.CallExpression)
