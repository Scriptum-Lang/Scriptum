from __future__ import annotations

"""
Experimental LLVM IR backend for Scriptum.

This module translates the structural IR (ModuleIr) into textual LLVM IR.
It intentionally supports apenas um subconjunto da linguagem, focado em:

- variáveis e funções numéricas (`numerus`);
- expressões aritméticas e condicionais básicas;
- `si` / `aliter`, `dum`, `frange`, `perge`;
- chamadas de função diretas.

Outros recursos (arrays, objetos, lambdas, `??`, etc.) ainda não são
suportados e geram NotImplementedError quando encontrados.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from ..ast import nodes
from ..ir import (
    IrAssignment,
    IrBinary,
    IrBreak,
    IrCall,
    IrConditional,
    IrContinue,
    IrExpr,
    IrExpressionStatement,
    IrFunction,
    IrIdentifier,
    IrIf,
    IrLiteral,
    IrModule,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariable,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
    lower_module,
)


@dataclass(slots=True)
class LLVMCodegenOutput:
    ir: ModuleIr
    llvm: str


def generate_llvm(module: Union[nodes.Module, ModuleIr]) -> LLVMCodegenOutput:
    """Lower *module* to IR if needed and emit LLVM IR text."""

    ir_module = module if isinstance(module, ModuleIr) else lower_module(module)
    emitter = _LLVMEmitter()
    llvm_text = emitter.emit(ir_module)
    return LLVMCodegenOutput(ir=ir_module, llvm=llvm_text)


@dataclass(slots=True)
class _LoopContext:
    break_label: str
    continue_label: str


class _FunctionBuilder:
    """Builds LLVM IR for a single Scriptum function."""

    def __init__(self, emitter: "_LLVMEmitter", func: IrFunction) -> None:
        self.emitter = emitter
        self.func = func

        # All Scriptum values are represented as LLVM `double` for now.
        self.return_type = "double"

        self.lines: List[str] = []
        self._tmp_counter = 0
        self._label_counter = 0
        self._current_block_terminated = False

        # Locais mapeados para ponteiros `alloca`.
        self._locals: Dict[str, str] = {}
        self._loop_stack: List[_LoopContext] = []

    # Low-level helpers --------------------------------------------------

    def _new_tmp(self) -> str:
        self._tmp_counter += 1
        return f"%t{self._tmp_counter}"

    def _new_label(self, base: str) -> str:
        self._label_counter += 1
        return f"{base}{self._label_counter}"

    def _emit(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def _emit_label(self, label: str) -> None:
        self.lines.append(f"{label}:")
        self._current_block_terminated = False

    def _as_condition(self, value_reg: str) -> str:
        """Converte um `double` para `i1` (não-zero é verum)."""

        tmp = self._new_tmp()
        self._emit(f"{tmp} = fcmp one double {value_reg}, 0.0")
        return tmp

    # Entry point --------------------------------------------------------

    def build(self) -> str:
        params_sig = ", ".join(f"double %{param.name}" for param in self.func.parameters)
        header = f"define {self.return_type} @{self.func.name}({params_sig}) {{"
        self.lines.append(header)

        # Bloco de entrada.
        self._emit_label("entry")

        # Aloca e inicializa parâmetros como variáveis locais.
        for param in self.func.parameters:
            ptr = self._new_tmp()
            self._emit(f"{ptr} = alloca double")
            self._emit(f"store double %{param.name}, double* {ptr}")
            self._locals[param.name] = ptr

        # Corpo da função.
        for stmt in self.func.body:
            self._gen_statement(stmt)

        # Garante terminador em funções sem `redde`.
        if not self._current_block_terminated:
            self._emit("ret double 0.0")

        self.lines.append("}")
        return "\n".join(self.lines)

    # Statements ---------------------------------------------------------

    def _gen_statement(self, stmt: IrStatement) -> None:
        if self._current_block_terminated:
            return

        if isinstance(stmt, IrVariableDeclaration):
            self._gen_var_decl(stmt)
            return

        if isinstance(stmt, IrExpressionStatement):
            self._gen_expr(stmt.expression)
            return

        if isinstance(stmt, IrReturn):
            self._gen_return(stmt)
            return

        if isinstance(stmt, IrIf):
            self._gen_if(stmt)
            return

        if isinstance(stmt, IrWhile):
            self._gen_while(stmt)
            return

        if isinstance(stmt, IrBreak):
            self._gen_break(stmt)
            return

        if isinstance(stmt, IrContinue):
            self._gen_continue(stmt)
            return

        raise NotImplementedError(f"Unsupported statement in LLVM backend: {type(stmt).__name__}")

    def _gen_var_decl(self, stmt: IrVariableDeclaration) -> None:
        ptr = self._new_tmp()
        self._emit(f"{ptr} = alloca double")
        self._locals[stmt.name] = ptr
        if stmt.initializer is not None:
            value_reg = self._gen_expr(stmt.initializer)
        else:
            value_reg = "0.0"
        self._emit(f"store double {value_reg}, double* {ptr}")

    def _gen_return(self, stmt: IrReturn) -> None:
        if stmt.value is not None:
            value_reg = self._gen_expr(stmt.value)
        else:
            value_reg = "0.0"
        self._emit(f"ret double {value_reg}")
        self._current_block_terminated = True

    def _gen_if(self, stmt: IrIf) -> None:
        cond_reg = self._gen_expr(stmt.condition)
        cond_bool = self._as_condition(cond_reg)

        then_label = self._new_label("if_then")
        else_label = self._new_label("if_else") if stmt.else_branch else None
        end_label = self._new_label("if_end")

        if else_label:
            self._emit(f"br i1 {cond_bool}, label %{then_label}, label %{else_label}")
        else:
            self._emit(f"br i1 {cond_bool}, label %{then_label}, label %{end_label}")

        # then branch
        self._emit_label(then_label)
        for inner in stmt.then_branch:
            self._gen_statement(inner)
        if not self._current_block_terminated:
            self._emit(f"br label %{end_label}")

        # else branch (optional)
        if else_label:
            self._emit_label(else_label)
            for inner in stmt.else_branch:
                self._gen_statement(inner)
            if not self._current_block_terminated:
                self._emit(f"br label %{end_label}")

        # join block
        self._emit_label(end_label)

    def _gen_while(self, stmt: IrWhile) -> None:
        cond_label = self._new_label("while_cond")
        body_label = self._new_label("while_body")
        end_label = self._new_label("while_end")

        # Salta para avaliação da condição.
        self._emit(f"br label %{cond_label}")

        # Condição.
        self._emit_label(cond_label)
        cond_reg = self._gen_expr(stmt.condition)
        cond_bool = self._as_condition(cond_reg)
        self._emit(f"br i1 {cond_bool}, label %{body_label}, label %{end_label}")

        # Corpo do laço.
        self._loop_stack.append(_LoopContext(break_label=end_label, continue_label=cond_label))
        self._emit_label(body_label)
        for inner in stmt.body:
            self._gen_statement(inner)
        if not self._current_block_terminated:
            self._emit(f"br label %{cond_label}")
        self._loop_stack.pop()

        # Bloco após o laço.
        self._emit_label(end_label)

    def _gen_break(self, stmt: IrBreak) -> None:
        if not self._loop_stack:
            raise NotImplementedError("break outside of loop in LLVM backend")
        target = self._loop_stack[-1].break_label
        self._emit(f"br label %{target}")
        self._current_block_terminated = True

    def _gen_continue(self, stmt: IrContinue) -> None:
        if not self._loop_stack:
            raise NotImplementedError("continue outside of loop in LLVM backend")
        target = self._loop_stack[-1].continue_label
        self._emit(f"br label %{target}")
        self._current_block_terminated = True

    # Expressions --------------------------------------------------------

    def _gen_expr(self, expr: IrExpr) -> str:
        if isinstance(expr, IrIdentifier):
            return self._gen_identifier(expr)

        if isinstance(expr, IrLiteral):
            return self._gen_literal(expr)

        if isinstance(expr, IrUnary):
            return self._gen_unary(expr)

        if isinstance(expr, IrBinary):
            return self._gen_binary(expr)

        if isinstance(expr, IrAssignment):
            return self._gen_assignment(expr)

        if isinstance(expr, IrConditional):
            return self._gen_conditional_expr(expr)

        if isinstance(expr, IrCall):
            return self._gen_call(expr)

        raise NotImplementedError(f"Unsupported expression in LLVM backend: {type(expr).__name__}")

    def _gen_identifier(self, expr: IrIdentifier) -> str:
        name = expr.name
        if name in self._locals:
            ptr = self._locals[name]
            tmp = self._new_tmp()
            self._emit(f"{tmp} = load double, double* {ptr}")
            return tmp

        if name in self.emitter.global_vars:
            tmp = self._new_tmp()
            self._emit(f"{tmp} = load double, double* @{name}")
            return tmp

        raise NotImplementedError(f"Unknown identifier in LLVM backend: {name}")

    @staticmethod
    def _format_double_literal(value: float) -> str:
        if isinstance(value, bool):
            return "1.0" if value else "0.0"
        if isinstance(value, int):
            return f"{value}.0"
        return repr(float(value))

    def _gen_literal(self, expr: IrLiteral) -> str:
        value = expr.value
        if isinstance(value, (bool, int, float)):
            return self._format_double_literal(value)
        raise NotImplementedError("Only numeric/boolean literals are supported in LLVM backend.")

    def _gen_unary(self, expr: IrUnary) -> str:
        operand_reg = self._gen_expr(expr.operand)
        op = expr.operator
        if op in {"NEGATE", "-"}:
            tmp = self._new_tmp()
            self._emit(f"{tmp} = fsub double 0.0, {operand_reg}")
            return tmp
        if op in {"POSITIVE", "+"}:
            return operand_reg
        if op in {"NOT", "!"}:
            cond = self._as_condition(operand_reg)
            tmp_bool = self._new_tmp()
            self._emit(f"{tmp_bool} = xor i1 {cond}, true")
            tmp = self._new_tmp()
            self._emit(f"{tmp} = uitofp i1 {tmp_bool} to double")
            return tmp
        raise NotImplementedError(f"Unsupported unary operator in LLVM backend: {op}")

    def _gen_binary(self, expr: IrBinary) -> str:
        op = expr.operator

        # Arithmetic operations -> double.
        arithmetic_ops = {"ADD", "SUB", "MUL", "DIV", "+", "-", "*", "/"}
        if op in arithmetic_ops:
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            tmp = self._new_tmp()
            if op in {"ADD", "+"}:
                self._emit(f"{tmp} = fadd double {left}, {right}")
            elif op in {"SUB", "-"}:
                self._emit(f"{tmp} = fsub double {left}, {right}")
            elif op in {"MUL", "*"}:
                self._emit(f"{tmp} = fmul double {left}, {right}")
            elif op in {"DIV", "/"}:
                self._emit(f"{tmp} = fdiv double {left}, {right}")
            return tmp

        # Comparisons -> i1 -> double.
        comparison_ops = {
            "GT": "ogt",
            "GE": "oge",
            "LT": "olt",
            "LE": "ole",
            "EQ": "oeq",
            "NE": "one",
            "STRICT_EQ": "oeq",
            "STRICT_NE": "one",
            ">": "ogt",
            ">=": "oge",
            "<": "olt",
            "<=": "ole",
            "==": "oeq",
            "!=": "one",
            "===": "oeq",
            "!==": "one",
        }
        if op in comparison_ops:
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            pred = comparison_ops[op]
            tmp_bool = self._new_tmp()
            self._emit(f"{tmp_bool} = fcmp {pred} double {left}, {right}")
            tmp = self._new_tmp()
            self._emit(f"{tmp} = uitofp i1 {tmp_bool} to double")
            return tmp

        # Logical AND/OR (sem curto-circuito) -> i1 -> double.
        if op in {"AND", "OR", "&&", "||"}:
            left_cond = self._as_condition(self._gen_expr(expr.left))
            right_cond = self._as_condition(self._gen_expr(expr.right))
            tmp_bool = self._new_tmp()
            if op in {"AND", "&&"}:
                self._emit(f"{tmp_bool} = and i1 {left_cond}, {right_cond}")
            else:
                self._emit(f"{tmp_bool} = or i1 {left_cond}, {right_cond}")
            tmp = self._new_tmp()
            self._emit(f"{tmp} = uitofp i1 {tmp_bool} to double")
            return tmp

        raise NotImplementedError(f"Unsupported binary operator in LLVM backend: {op}")

    def _gen_assignment(self, expr: IrAssignment) -> str:
        if not isinstance(expr.target, IrIdentifier):
            raise NotImplementedError("Only simple identifier assignments are supported in LLVM backend.")
        value_reg = self._gen_expr(expr.value)
        name = expr.target.name
        if name in self._locals:
            ptr = self._locals[name]
            self._emit(f"store double {value_reg}, double* {ptr}")
            return value_reg
        if name in self.emitter.global_vars:
            self._emit(f"store double {value_reg}, double* @{name}")
            return value_reg
        raise NotImplementedError(f"Assignment to unknown identifier in LLVM backend: {name}")

    def _gen_conditional_expr(self, expr: IrConditional) -> str:
        cond_reg = self._gen_expr(expr.condition)
        cond_bool = self._as_condition(cond_reg)

        then_label = self._new_label("cond_then")
        else_label = self._new_label("cond_else")
        end_label = self._new_label("cond_end")

        self._emit(f"br i1 {cond_bool}, label %{then_label}, label %{else_label}")

        # then branch
        self._emit_label(then_label)
        then_value = self._gen_expr(expr.consequent)
        self._emit(f"br label %{end_label}")

        # else branch
        self._emit_label(else_label)
        else_value = self._gen_expr(expr.alternate)
        self._emit(f"br label %{end_label}")

        # join with phi
        self._emit_label(end_label)
        phi_reg = self._new_tmp()
        self._emit(
            f"{phi_reg} = phi double [{then_value}, %{then_label}], "
            f"[{else_value}, %{else_label}]"
        )
        return phi_reg

    def _gen_call(self, expr: IrCall) -> str:
        if not isinstance(expr.callee, IrIdentifier):
            raise NotImplementedError("Only direct function calls are supported in LLVM backend.")
        fn_name = expr.callee.name

        arg_regs = [self._gen_expr(arg) for arg in expr.arguments]

        # Registra funções externas (builtins, etc.) para gerar `declare` depois.
        if fn_name not in self.emitter.defined_functions:
            self.emitter.register_extern(fn_name, len(arg_regs))

        args_sig = ", ".join(f"double {reg}" for reg in arg_regs)
        tmp = self._new_tmp()
        self._emit(f"{tmp} = call double @{fn_name}({args_sig})")
        return tmp


class _LLVMEmitter:
    """Orquestra a geração de LLVM IR para um módulo completo."""

    def __init__(self) -> None:
        self.global_lines: List[str] = []
        self.global_vars: Dict[str, bool] = {}
        self.defined_functions: set[str] = set()
        self._extern_functions: Dict[str, int] = {}

    # Public API ---------------------------------------------------------

    def emit(self, module: ModuleIr) -> str:
        self._collect_globals(module)
        self._collect_defined_functions(module)

        function_texts: List[str] = []
        for func in module.functions:
            builder = _FunctionBuilder(self, func)
            function_texts.append(builder.build())

        lines: List[str] = []
        lines.append("; Scriptum LLVM IR (experimental)")
        lines.append('source_filename = "scriptum_module"')
        lines.append("")

        # Globais.
        lines.extend(self.global_lines)
        if self.global_lines:
            lines.append("")

        # Declarações de funções externas (builtins, etc.).
        extern_lines = self._emit_extern_declarations()
        if extern_lines:
            lines.extend(extern_lines)
            lines.append("")

        # Definições de funções do módulo.
        for index, text in enumerate(function_texts):
            lines.append(text)
            if index != len(function_texts) - 1:
                lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    # Module helpers -----------------------------------------------------

    def _collect_globals(self, module: ModuleIr) -> None:
        for var in module.globals:
            init = self._global_initializer(var)
            self.global_lines.append(f"@{var.name} = global double {init}")
            self.global_vars[var.name] = True

    @staticmethod
    def _global_initializer(var: IrVariable) -> str:
        if var.initializer and isinstance(var.initializer, IrLiteral):
            value = var.initializer.value
            if isinstance(value, bool):
                return "1.0" if value else "0.0"
            if isinstance(value, int):
                return f"{value}.0"
            if isinstance(value, float):
                return repr(value)
        return "0.0"

    def _collect_defined_functions(self, module: ModuleIr) -> None:
        self.defined_functions = {func.name for func in module.functions}

    def register_extern(self, name: str, arity: int) -> None:
        existing = self._extern_functions.get(name)
        if existing is None:
            self._extern_functions[name] = arity
        elif existing != arity:
            raise ValueError(f"Conflicting declarations for extern function '{name}' in LLVM backend.")

    def _emit_extern_declarations(self) -> List[str]:
        lines: List[str] = []
        for name in sorted(self._extern_functions):
            arity = self._extern_functions[name]
            args_sig = ", ".join("double" for _ in range(arity))
            lines.append(f"declare double @{name}({args_sig})")
        return lines

