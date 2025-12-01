from __future__ import annotations

from typing import Union

from ...ast import nodes
from ...ir import ModuleIr, lower_module
from ...sema.analyzer import SemanticAnalyzer
from .generator import LLVMGenerator, LLVMOutput, LLVMCodegenError

__all__ = ["LLVMGenerator", "LLVMOutput", "LLVMCodegenError", "generate_llvm"]


def generate_llvm(module: Union[ModuleIr, nodes.Module], *, module_name: str | None = None, verify: bool = False) -> LLVMOutput:
    """Convenience API that mirrors the previous backend entrypoint."""

    if isinstance(module, ModuleIr):
        ir_module = module
    else:
        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(module)
        ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    generator = LLVMGenerator(module_name=module_name)
    return generator.generate(ir_module, verify=verify)
