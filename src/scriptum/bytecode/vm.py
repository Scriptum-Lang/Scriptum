from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .. import builtins, errors
from .program import BytecodeFunction, BytecodeInstruction, BytecodeModule


class BytecodeVM:
    """Executes bytecode programs produced by :class:`BytecodeCompiler`."""

    def __init__(self, program: BytecodeModule) -> None:
        self.program = program
        self.globals: Dict[str, Any] = dict(program.globals_init)
        self._register_builtins()
        self._register_functions()

    def run(self, entry_point: str = "principalis") -> Any:
        if entry_point not in self.globals:
            raise errors.ExecutionError("BC200", f"Entry point '{entry_point}' nao encontrado.")
        callee = self.globals[entry_point]
        return self.invoke_callable(callee, [])

    # ------------------------------------------------------------------ registration

    def _register_builtins(self) -> None:
        for spec in builtins.GLOBAL_FUNCTIONS.values():
            self.globals.setdefault(spec.name, _BuiltinFunction(spec))

    def _register_functions(self) -> None:
        for name, function in self.program.functions.items():
            self.globals[name] = _UserFunction(self, function)

    # ------------------------------------------------------------------ execution

    def _execute_function(self, function: BytecodeFunction, args: List[Any]) -> Any:
        frame = _Frame(function=function, args=args)
        while frame.ip < len(function.instructions):
            instr = function.instructions[frame.ip]
            frame.ip += 1
            if self._dispatch(frame, instr):
                break
        return frame.return_value

    def _dispatch(self, frame: "_Frame", instr: BytecodeInstruction) -> bool:
        op = instr.opcode
        if op == "PUSH_CONST":
            frame.stack.append(instr.arg)
        elif op == "LOAD_LOCAL":
            frame.stack.append(frame.locals[instr.arg])
        elif op == "STORE_LOCAL":
            value = frame.stack.pop()
            frame.locals[instr.arg] = value
            frame.stack.append(value)
        elif op == "LOAD_GLOBAL":
            frame.stack.append(self._load_global(instr.arg))
        elif op == "STORE_GLOBAL":
            value = frame.stack.pop()
            self.globals[instr.arg] = value
            frame.stack.append(value)
        elif op == "POP":
            if frame.stack:
                frame.stack.pop()
        elif op == "DUP":
            if not frame.stack:
                raise errors.ExecutionError("BC300", "dup exige valor no topo da pilha.")
            frame.stack.append(frame.stack[-1])
        elif op == "BINARY_ADD":
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(left + right)
        elif op == "BINARY_SUB":
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(left - right)
        elif op == "BINARY_MUL":
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(left * right)
        elif op == "BINARY_DIV":
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(left / right)
        elif op == "BINARY_MOD":
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(left % right)
        elif op == "UNARY_NEGATE":
            frame.stack.append(-frame.stack.pop())
        elif op == "UNARY_POSITIVE":
            frame.stack.append(+frame.stack.pop())
        elif op == "UNARY_NOT":
            frame.stack.append(not self._truthy(frame.stack.pop()))
        elif op == "BUILD_LIST":
            count = instr.arg or 0
            values = [frame.stack.pop() for _ in range(count)]
            values.reverse()
            frame.stack.append(values)
        elif op == "COMPARE":
            right = frame.stack.pop()
            left = frame.stack.pop()
            result = self._compare(instr.arg, left, right)
            frame.stack.append(result)
        elif op == "JUMP":
            frame.ip = instr.arg
        elif op == "JUMP_IF_FALSE":
            value = frame.stack.pop()
            if not self._truthy(value):
                frame.ip = instr.arg
        elif op == "JUMP_IF_TRUE":
            value = frame.stack.pop()
            if self._truthy(value):
                frame.ip = instr.arg
        elif op == "JUMP_IF_NOT_NONE":
            value = frame.stack.pop()
            if value is not None:
                frame.ip = instr.arg
        elif op == "CALL":
            argc = instr.arg or 0
            args = [frame.stack.pop() for _ in range(argc)]
            args.reverse()
            callee = frame.stack.pop()
            result = self.invoke_callable(callee, args)
            frame.stack.append(result)
        elif op == "RETURN":
            frame.return_value = frame.stack.pop() if frame.stack else None
            return True
        else:  # pragma: no cover - defensive default
            raise errors.ExecutionError("BC310", f"Instrucao '{op}' desconhecida.")
        return False

    # ------------------------------------------------------------------ helpers

    def invoke_callable(self, callee: Any, args: List[Any]) -> Any:
        if hasattr(callee, "call"):
            return callee.call(self, args)
        if callable(callee):
            return callee(*args)
        raise errors.ExecutionError("BC400", "Valor nao e invocavel.")

    def _load_global(self, name: str) -> Any:
        if name not in self.globals:
            raise errors.ExecutionError("BC401", f"Simbolo global '{name}' nao encontrado.")
        return self.globals[name]

    def _truthy(self, value: Any) -> bool:
        if value is None:
            return False
        return bool(value)

    def _compare(self, mode: str, left: Any, right: Any) -> bool:
        if mode == "EQ":
            return left == right
        if mode == "NE":
            return left != right
        if mode == "GT":
            return left > right
        if mode == "LT":
            return left < right
        if mode == "GE":
            return left >= right
        if mode == "LE":
            return left <= right
        raise errors.ExecutionError("BC402", f"Comparacao '{mode}' invalida.")


@dataclass
class _Frame:
    function: BytecodeFunction
    args: List[Any]
    stack: List[Any] = None
    locals: List[Any] = None
    ip: int = 0
    return_value: Any = None

    def __post_init__(self) -> None:
        self.stack = []
        self.locals = [None] * max(self.function.locals_count, len(self.args))
        for idx, value in enumerate(self.args):
            if idx < len(self.locals):
                self.locals[idx] = value
            else:
                self.locals.append(value)


class _UserFunction:
    def __init__(self, vm: BytecodeVM, function: BytecodeFunction) -> None:
        self._vm = vm
        self._function = function

    def call(self, vm: BytecodeVM, args: List[Any]) -> Any:
        if vm is not self._vm:
            return self._vm._execute_function(self._function, args)
        return self._vm._execute_function(self._function, args)


class _BuiltinFunction:
    def __init__(self, spec: builtins.BuiltinFunctionSpec) -> None:
        self.spec = spec

    def call(self, vm: BytecodeVM, args: List[Any]) -> Any:
        normalized = self.spec.prepare_arguments(args)
        return self.spec.implementation(vm, normalized)
