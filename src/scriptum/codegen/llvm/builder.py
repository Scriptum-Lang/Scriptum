from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class NameGen:
    prefix: str = "tmp"
    counter: int = 0

    def new(self, base: str | None = None) -> str:
        self.counter += 1
        name = base if base is not None else self.prefix
        if name.startswith("%"):
            return f"{name}.{self.counter}"
        return f"%{name}{self.counter}"


class ModuleBuilder:
    """Collect module-level LLVM IR sections."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self._structs: List[str] = []
        self._globals: List[str] = []
        self._decls: List[str] = []
        self._functions: List[str] = []
        self._runtime: List[str] = []

    def add_struct(self, text: str) -> None:
        self._structs.append(text)

    def add_global(self, text: str) -> None:
        self._globals.append(text)

    def add_declaration(self, text: str) -> None:
        if text not in self._decls:
            self._decls.append(text)

    def add_function(self, text: str) -> None:
        self._functions.append(text)

    def append_runtime(self, text: str) -> None:
        self._runtime.append(text)

    def render(self) -> str:
        sections: List[str] = ["; ModuleID = \"" + self.module_name + "\"", "source_filename = \"" + self.module_name + "\""]
        sections.extend(self._structs)
        sections.extend(self._runtime)
        sections.extend(self._globals)
        sections.extend(self._decls)
        sections.extend(self._functions)
        return "\n".join(section for section in sections if section.strip())


@dataclass(slots=True)
class FunctionBlock:
    name: str
    lines: List[str] = field(default_factory=list)
    terminated: bool = False

    def emit(self, text: str) -> None:
        self.lines.append(f"  {text}")


class FunctionBuilder:
    """Emit textual IR for a single function."""

    def __init__(self, namegen: NameGen, header: str) -> None:
        self.namegen = namegen
        self.header = header
        self.blocks: List[FunctionBlock] = []
        self._current: FunctionBlock | None = None

    def new_block(self, label: str) -> FunctionBlock:
        block = FunctionBlock(name=label)
        self.blocks.append(block)
        self._current = block
        block.terminated = False
        return block

    def switch_block(self, block: FunctionBlock) -> None:
        self._current = block
        block.terminated = False

    def emit(self, text: str) -> None:
        if self._current is None:
            raise RuntimeError("Attempted to emit without active block.")
        self._current.emit(text)

    def set_terminated(self) -> None:
        if self._current is not None:
            self._current.terminated = True

    def current_block(self) -> FunctionBlock:
        if self._current is None:
            raise RuntimeError("FunctionBuilder has no active block.")
        return self._current

    def render(self) -> str:
        lines = [self.header]
        for block in self.blocks:
            lines.append(f"{block.name}:")
            lines.extend(block.lines)
        lines.append("}")
        return "\n".join(lines)
