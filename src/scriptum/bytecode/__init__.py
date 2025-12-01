"""Stack-based bytecode backend for Scriptum."""

from __future__ import annotations

from typing import Any, Union

from ..ast import nodes
from ..ir import ModuleIr, lower_module
from ..optimizations import LocalOptimizer
from ..sema.analyzer import SemanticAnalyzer
from .compiler import BytecodeCompileError, BytecodeCompiler
from .program import BytecodeModule, format_bytecode
from .vm import BytecodeVM

__all__ = [
    "BytecodeCompileError",
    "BytecodeCompiler",
    "BytecodeModule",
    "BytecodeVM",
    "compile_module",
    "format_bytecode",
    "run_module",
]


def compile_module(module: Union[ModuleIr, nodes.Module]) -> BytecodeModule:
    if isinstance(module, ModuleIr):
        ir_module = module
    else:
        analysis = SemanticAnalyzer().analyze(module)
        ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    ir_module = LocalOptimizer().optimize(ir_module)
    compiler = BytecodeCompiler()
    return compiler.compile(ir_module)


def run_module(module: Union[ModuleIr, nodes.Module], entry_point: str = "principalis") -> Any:
    program = compile_module(module)
    vm = BytecodeVM(program)
    return vm.run(entry_point=entry_point)
