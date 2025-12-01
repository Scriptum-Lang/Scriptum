from __future__ import annotations

from scriptum.ir.ir import IrBinary, IrFunction, IrIf, IrLiteral, IrReturn, IrStatement, ModuleIr
from scriptum.optimizations import LocalOptimizer
from scriptum.text import Span


SPAN = Span(0, 0)


def _literal(value, raw=None):
    raw_value = raw if raw is not None else ("verum" if value is True else "falsum" if value is False else str(value))
    return IrLiteral(span=SPAN, value=value, raw=raw_value)


def _function_with_statement(stmt: IrStatement) -> ModuleIr:
    func = IrFunction(span=SPAN, name="principalis", parameters=[], return_annotation=None, body=[stmt])
    return ModuleIr(span=SPAN, globals=[], functions=[func])


def test_local_optimizer_folds_numeric_binaries() -> None:
    stmt = IrReturn(span=SPAN, value=IrBinary(span=SPAN, operator="+", left=_literal(2), right=_literal(3)))
    module = _function_with_statement(stmt)
    optimized = LocalOptimizer().optimize(module)
    result = optimized.functions[0].body[0].value
    assert isinstance(result, IrLiteral)
    assert result.value == 5


def test_local_optimizer_short_circuits_nullish() -> None:
    stmt = IrReturn(span=SPAN, value=IrBinary(span=SPAN, operator="??", left=_literal(7), right=_literal(42)))
    module = _function_with_statement(stmt)
    optimized = LocalOptimizer().optimize(module)
    result = optimized.functions[0].body[0].value
    assert isinstance(result, IrLiteral)
    assert result.value == 7


def test_local_optimizer_reduces_static_if_branch() -> None:
    then_return = IrReturn(span=SPAN, value=_literal(11))
    else_return = IrReturn(span=SPAN, value=_literal(0))
    ir_if = IrIf(span=SPAN, condition=_literal(True, raw="verum"), then_branch=[then_return], else_branch=[else_return])
    module = _function_with_statement(ir_if)
    optimized = LocalOptimizer().optimize(module)
    assert isinstance(optimized.functions[0].body[0], IrReturn)
    assert optimized.functions[0].body[0].value.value == 11
