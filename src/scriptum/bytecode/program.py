from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class BytecodeInstruction:
    opcode: str
    arg: Any = None


@dataclass(slots=True)
class BytecodeFunction:
    name: str
    parameters: List[str]
    instructions: List[BytecodeInstruction] = field(default_factory=list)
    locals_count: int = 0


@dataclass(slots=True)
class BytecodeModule:
    globals_init: Dict[str, Any]
    functions: Dict[str, BytecodeFunction]


def format_bytecode(module: BytecodeModule) -> str:
    lines: List[str] = []
    lines.append("globals:")
    for name in sorted(module.globals_init):
        lines.append(f"  {name} = {module.globals_init[name]!r}")
    for name in sorted(module.functions):
        func = module.functions[name]
        lines.append("")
        header = ", ".join(func.parameters)
        lines.append(f"functio {func.name}({header}) locals={func.locals_count}")
        for index, instr in enumerate(func.instructions):
            arg_repr = "" if instr.arg is None else f" {instr.arg!r}"
            lines.append(f"  {index:04d}: {instr.opcode}{arg_repr}")
    return "\n".join(lines)


__all__ = ["BytecodeInstruction", "BytecodeFunction", "BytecodeModule", "format_bytecode"]
