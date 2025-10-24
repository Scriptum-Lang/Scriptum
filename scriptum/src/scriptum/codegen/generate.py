from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from ..ast import nodes
from ..ir import ModuleIr, lower_module
from .emitter import CodeEmitter


@dataclass(slots=True)
class CodegenOutput:
    ir: ModuleIr
    formatted: str


def generate(module: Union[nodes.Module, ModuleIr]) -> CodegenOutput:
    """Lower *module* to IR if needed and pretty-print it."""

    ir_module = module if isinstance(module, ModuleIr) else lower_module(module)
    emitter = CodeEmitter()
    formatted = emitter.emit(ir_module)
    return CodegenOutput(ir=ir_module, formatted=formatted)
