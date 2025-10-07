"""
Code generation scaffolding for Scriptum.
"""

from __future__ import annotations


class CodeEmitter:
    """Produces textual output or bytecode from the lowered IR."""

    def emit(self, module: object) -> str:
        raise NotImplementedError("Code generation not yet implemented.")
