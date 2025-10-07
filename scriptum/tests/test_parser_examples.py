from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path

from scriptum.ast import nodes
from scriptum.parser.parser import ScriptumParser
from scriptum.text import SourceFile

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


def _parse(relative: str) -> nodes.Module:
    path = EXAMPLES_ROOT / relative
    parser = ScriptumParser()
    source = SourceFile(str(path), path.read_text(encoding="utf8"))
    module = parser.parse(source)
    assert isinstance(module, nodes.Module)
    return module


def test_parse_classes_example() -> None:
    module = _parse("ok/intermediarios/classes.stm")
    assert len(module.declarations) == 1
    func = module.declarations[0]
    assert isinstance(func, nodes.FunctionDeclaration)
    assert func.name == "init"
    body_stmts = func.body.statements
    assert any(isinstance(stmt, nodes.WhileStatement) for stmt in body_stmts)
    assert any(isinstance(stmt, nodes.ReturnStatement) for stmt in body_stmts)


def test_parse_condicionais_handles_else_branch() -> None:
    module = _parse("ok/basicos/condicionais.stm")
    func = module.declarations[0]
    assert isinstance(func, nodes.FunctionDeclaration)
    if_stmt = next(stmt for stmt in func.body.statements if isinstance(stmt, nodes.IfStatement))
    assert if_stmt.else_branch is not None


def test_parse_sistema_bancario_functions() -> None:
    module = _parse("ok/avancados/sistema_bancario.stm")
    names = [decl.name for decl in module.declarations if isinstance(decl, nodes.FunctionDeclaration)]
    assert names == ["depositum", "init"]
    init_body = module.declarations[1].body.statements  # type: ignore[index]
    assign_stmt = next(stmt for stmt in init_body if isinstance(stmt, nodes.ExpressionStatement))
    expr = assign_stmt.expression
    assert isinstance(expr, nodes.AssignmentExpression)
    assert isinstance(expr.value, nodes.CallExpression)

