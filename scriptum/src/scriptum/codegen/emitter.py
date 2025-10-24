"""
Code generation scaffolding for Scriptum.
"""

from __future__ import annotations

from ..ir import ModuleIr


class CodeEmitter:
    """Produces textual output or bytecode from the lowered IR."""

    def emit(self, module: ModuleIr) -> str:
        raise NotImplementedError("Code generation not yet implemented.")
