from __future__ import annotations

from typing import Dict, List, Set

from .. import errors
from .. import builtins
from ..ir.ir import (
    IrArrayLiteral,
    IrAssignment,
    IrBinary,
    IrBreak,
    IrCall,
    IrConditional,
    IrContinue,
    IrExpr,
    IrExpressionStatement,
    IrForIn,
    IrFunction,
    IrIdentifier,
    IrIf,
    IrLiteral,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariable,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
)
from .program import BytecodeFunction, BytecodeInstruction, BytecodeModule


class BytecodeCompileError(errors.CompilerError):
    code = "BC100"


class BytecodeCompiler:
    """Lower ModuleIr into a simple stack-based bytecode program."""

    def compile(self, module: ModuleIr) -> BytecodeModule:
        global_names = {var.name for var in module.globals}
        function_names = {func.name for func in module.functions}
        globals_init = {var.name: self._constant_initializer(var) for var in module.globals}
        builtin_names = set(builtins.GLOBAL_FUNCTIONS.keys())
        globals_available = global_names | function_names | builtin_names
        functions: Dict[str, BytecodeFunction] = {}
        for func in module.functions:
            compiler = _FunctionCompiler(func, globals_available)
            functions[func.name] = compiler.compile()
        return BytecodeModule(globals_init=globals_init, functions=functions)

    def _constant_initializer(self, var: IrVariable):
        if var.initializer is None:
            return None
        if isinstance(var.initializer, IrLiteral):
            return var.initializer.value
        raise BytecodeCompileError(f"Variavel global '{var.name}' utiliza inicializador nao suportado pelo bytecode.")


class _LoopContext:
    def __init__(self, continue_target: int) -> None:
        self.continue_target = continue_target
        self.break_jumps: List[int] = []


class _FunctionCompiler:
    _ARITH = {
        "+": "BINARY_ADD",
        "ADD": "BINARY_ADD",
        "-": "BINARY_SUB",
        "SUB": "BINARY_SUB",
        "*": "BINARY_MUL",
        "MUL": "BINARY_MUL",
        "/": "BINARY_DIV",
        "DIV": "BINARY_DIV",
        "%": "BINARY_MOD",
        "MOD": "BINARY_MOD",
    }
    _COMPARE = {
        "==": "EQ",
        "EQ": "EQ",
        "!=": "NE",
        "NE": "NE",
        ">": "GT",
        "GT": "GT",
        "<": "LT",
        "LT": "LT",
        ">=": "GE",
        "GE": "GE",
        "<=": "LE",
        "LE": "LE",
    }

    def __init__(self, func: IrFunction, globals_available: Set[str]) -> None:
        self.func = func
        self.globals = globals_available
        self.instructions: List[BytecodeInstruction] = []
        self.locals: Dict[str, int] = {}
        self.loop_stack: List[_LoopContext] = []
        for param in func.parameters:
            self._declare_local(param.name)

    def compile(self) -> BytecodeFunction:
        for stmt in self.func.body:
            self._emit_statement(stmt)
        if not self.instructions or self.instructions[-1].opcode != "RETURN":
            self._emit_const(None)
            self._emit("RETURN")
        return BytecodeFunction(
            name=self.func.name,
            parameters=[param.name for param in self.func.parameters],
            instructions=self.instructions,
            locals_count=len(self.locals),
        )

    # ------------------------------------------------------------------ statements

    def _emit_statement(self, stmt: IrStatement) -> None:
        if isinstance(stmt, IrVariableDeclaration):
            if stmt.name not in self.locals:
                self._declare_local(stmt.name)
            if stmt.initializer is not None:
                self._emit_expr(stmt.initializer)
            else:
                self._emit_const(None)
            self._emit_store_local(self.locals[stmt.name])
            return

        if isinstance(stmt, IrReturn):
            if stmt.value is not None:
                self._emit_expr(stmt.value)
            else:
                self._emit_const(None)
            self._emit("RETURN")
            return

        if isinstance(stmt, IrIf):
            self._emit_expr(stmt.condition)
            jump_false = self._emit_jump("JUMP_IF_FALSE")
            for inner in stmt.then_branch:
                self._emit_statement(inner)
            jump_end = self._emit_jump("JUMP")
            self._patch(jump_false, self._current_ip())
            for inner in stmt.else_branch:
                self._emit_statement(inner)
            self._patch(jump_end, self._current_ip())
            return

        if isinstance(stmt, IrWhile):
            loop_start = self._current_ip()
            self._emit_expr(stmt.condition)
            jump_exit = self._emit_jump("JUMP_IF_FALSE")
            context = _LoopContext(continue_target=loop_start)
            self.loop_stack.append(context)
            for inner in stmt.body:
                self._emit_statement(inner)
            self.loop_stack.pop()
            self._emit(BytecodeInstruction("JUMP", loop_start))
            self._patch(jump_exit, self._current_ip())
            for idx in context.break_jumps:
                self._patch(idx, self._current_ip())
            return

        if isinstance(stmt, IrExpressionStatement):
            self._emit_expr(stmt.expression)
            self._emit("POP")
            return

        if isinstance(stmt, IrBreak):
            self._emit_break()
            return

        if isinstance(stmt, IrContinue):
            self._emit_continue()
            return

        if isinstance(stmt, IrForIn):
            raise BytecodeCompileError("pro in ainda nao suportado pelo backend de bytecode.")

        raise BytecodeCompileError(f"Statement '{type(stmt).__name__}' nao suportado pelo backend de bytecode.")

    def _emit_break(self) -> None:
        if not self.loop_stack:
            raise BytecodeCompileError("frange fora de laco.")
        idx = self._emit_jump("JUMP")
        self.loop_stack[-1].break_jumps.append(idx)

    def _emit_continue(self) -> None:
        if not self.loop_stack:
            raise BytecodeCompileError("perge fora de laco.")
        target = self.loop_stack[-1].continue_target
        self._emit(BytecodeInstruction("JUMP", target))

    # ------------------------------------------------------------------ expressions

    def _emit_expr(self, expr: IrExpr) -> None:
        if isinstance(expr, IrLiteral):
            self._emit_const(expr.value)
            return
        if isinstance(expr, IrIdentifier):
            self._emit_load_identifier(expr.name)
            return
        if isinstance(expr, IrBinary):
            self._emit_binary(expr)
            return
        if isinstance(expr, IrUnary):
            self._emit_unary(expr)
            return
        if isinstance(expr, IrAssignment):
            if not isinstance(expr.target, IrIdentifier):
                raise BytecodeCompileError("Atribuicoes complexas nao sao suportadas.")
            self._emit_expr(expr.value)
            self._emit_store_identifier(expr.target.name)
            return
        if isinstance(expr, IrConditional):
            self._emit_conditional(expr)
            return
        if isinstance(expr, IrCall):
            self._emit_call(expr)
            return
        if isinstance(expr, IrArrayLiteral):
            for element in expr.elements:
                self._emit_expr(element)
            self._emit(BytecodeInstruction("BUILD_LIST", len(expr.elements)))
            return
        raise BytecodeCompileError(f"Expressao '{type(expr).__name__}' nao suportada no bytecode.")

    def _emit_binary(self, expr: IrBinary) -> None:
        op = expr.operator
        if op in self._ARITH:
            self._emit_expr(expr.left)
            self._emit_expr(expr.right)
            self._emit(self._ARITH[op])
            return
        if op in self._COMPARE:
            self._emit_expr(expr.left)
            self._emit_expr(expr.right)
            self._emit(BytecodeInstruction("COMPARE", self._COMPARE[op]))
            return
        if op in {"OR", "||"}:
            self._emit_or(expr)
            return
        if op in {"AND", "&&"}:
            self._emit_and(expr)
            return
        if op in {"NULLISH", "??"}:
            self._emit_nullish(expr)
            return
        raise BytecodeCompileError(f"Operador '{op}' nao implementado no bytecode.")

    def _emit_unary(self, expr: IrUnary) -> None:
        op = expr.operator
        self._emit_expr(expr.operand)
        if op in {"-", "NEGATE"}:
            self._emit("UNARY_NEGATE")
            return
        if op in {"+", "POSITIVE"}:
            self._emit("UNARY_POSITIVE")
            return
        if op in {"!", "NOT"}:
            self._emit("UNARY_NOT")
            return
        raise BytecodeCompileError(f"Operador unario '{op}' nao suportado.")

    def _emit_conditional(self, expr: IrConditional) -> None:
        self._emit_expr(expr.condition)
        jump_false = self._emit_jump("JUMP_IF_FALSE")
        self._emit_expr(expr.consequent)
        jump_end = self._emit_jump("JUMP")
        self._patch(jump_false, self._current_ip())
        self._emit_expr(expr.alternate)
        self._patch(jump_end, self._current_ip())

    def _emit_call(self, expr: IrCall) -> None:
        self._emit_expr(expr.callee)
        for argument in expr.arguments:
            self._emit_expr(argument)
        self._emit(BytecodeInstruction("CALL", len(expr.arguments)))

    def _emit_or(self, expr: IrBinary) -> None:
        self._emit_expr(expr.left)
        self._emit("DUP")
        jump_true = self._emit_jump("JUMP_IF_TRUE")
        self._emit("POP")
        self._emit_expr(expr.right)
        self._patch(jump_true, self._current_ip())

    def _emit_and(self, expr: IrBinary) -> None:
        self._emit_expr(expr.left)
        self._emit("DUP")
        jump_false = self._emit_jump("JUMP_IF_FALSE")
        self._emit("POP")
        self._emit_expr(expr.right)
        self._patch(jump_false, self._current_ip())

    def _emit_nullish(self, expr: IrBinary) -> None:
        self._emit_expr(expr.left)
        self._emit("DUP")
        jump_has_value = self._emit_jump("JUMP_IF_NOT_NONE")
        self._emit("POP")
        self._emit_expr(expr.right)
        self._patch(jump_has_value, self._current_ip())

    # ------------------------------------------------------------------ helpers

    def _declare_local(self, name: str) -> None:
        if name in self.locals:
            raise BytecodeCompileError(f"Variavel '{name}' ja declarada.")
        self.locals[name] = len(self.locals)

    def _emit_const(self, value) -> None:
        self._emit(BytecodeInstruction("PUSH_CONST", value))

    def _emit(self, instr) -> None:
        if isinstance(instr, str):
            instruction = BytecodeInstruction(instr)
        else:
            instruction = instr
        self.instructions.append(instruction)

    def _emit_jump(self, opcode: str) -> int:
        idx = len(self.instructions)
        self.instructions.append(BytecodeInstruction(opcode, None))
        return idx

    def _patch(self, index: int, target: int) -> None:
        self.instructions[index].arg = target

    def _current_ip(self) -> int:
        return len(self.instructions)

    def _emit_load_identifier(self, name: str) -> None:
        if name in self.locals:
            self._emit(BytecodeInstruction("LOAD_LOCAL", self.locals[name]))
            return
        if name in self.globals:
            self._emit(BytecodeInstruction("LOAD_GLOBAL", name))
            return
        raise BytecodeCompileError(f"Simbolo '{name}' nao resolvido.")

    def _emit_store_identifier(self, name: str) -> None:
        if name in self.locals:
            self._emit_store_local(self.locals[name])
            return
        if name in self.globals:
            self._emit(BytecodeInstruction("STORE_GLOBAL", name))
            return
        raise BytecodeCompileError(f"Destino '{name}' nao resolvido.")

    def _emit_store_local(self, slot: int) -> None:
        self._emit(BytecodeInstruction("STORE_LOCAL", slot))
