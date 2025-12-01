from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from ..ast import nodes
from ..ir import ModuleIr, lower_module
from ..sema.analyzer import SemanticAnalyzer
from .emitter import CodeEmitter


@dataclass(slots=True)
class CodegenOutput:
    ir: ModuleIr
    formatted: str


def generate(module: Union[nodes.Module, ModuleIr]) -> CodegenOutput:
    """Lower *module* to IR if needed and pretty-print it."""

    if isinstance(module, ModuleIr):
        ir_module = module
    else:
        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(module)
        ir_module = lower_module(
            module,
            type_info=analysis.type_info,
            member_bindings=analysis.member_bindings,
        )
    emitter = CodeEmitter()
    formatted = emitter.emit(ir_module)
    return CodegenOutput(ir=ir_module, formatted=formatted)
