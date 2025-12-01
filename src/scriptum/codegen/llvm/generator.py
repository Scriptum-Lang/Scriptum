from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set

from ... import builtins as std_builtins
from ... import errors
from ...ir import (
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
    IrLambda,
    IrLiteral,
    IrMemberAccess,
    IrObjectLiteral,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariable,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
)
from ...sema import types as sema_types
from ...sema.types import type_from_annotation
from .builder import FunctionBuilder, ModuleBuilder, NameGen
from .runtime import runtime_sections
from .types import LLVMTypeInfo, TypeLowerer


SCRIPTUM_VALUE_KIND_UNDEFINED = 0
SCRIPTUM_VALUE_KIND_NUMBER = 1
SCRIPTUM_VALUE_KIND_BOOLEAN = 2
SCRIPTUM_VALUE_KIND_TEXT = 3
SCRIPTUM_VALUE_KIND_ARRAY = 4
SCRIPTUM_VALUE_KIND_OBJECT = 5
SCRIPTUM_VALUE_KIND_LAMBDA = 6
SCRIPTUM_VALUE_KIND_OPTIONAL = 7
SCRIPTUM_VALUE_KIND_NULL = 8

BUILTIN_RUNTIME_MAP: Dict[str, str] = {
    name: f"scriptum_rt_{name}" for name in std_builtins.GLOBAL_FUNCTIONS.keys()
}
ARRAY_METHOD_RUNTIME_MAP: Dict[str, str] = {
    "adde": "scriptum_rt_array_adde",
    "exime": "scriptum_rt_array_exime",
    "extende": "scriptum_rt_array_extende",
    "inserta": "scriptum_rt_array_inserta",
    "remove": "scriptum_rt_array_remove",
    "purga": "scriptum_rt_array_purga",
}
TEXT_METHOD_RUNTIME_MAP: Dict[str, str] = {
    "divide": "scriptum_rt_text_divide",
    "coniunge": "scriptum_rt_text_coniunge",
    "substitue": "scriptum_rt_text_substitue",
    "ad_minusculas": "scriptum_rt_text_ad_minusculas",
    "ad_maiusculas": "scriptum_rt_text_ad_maiusculas",
    "abscinde": "scriptum_rt_text_abscinde",
}


@dataclass(slots=True)
class LLVMOutput:
    ir: ModuleIr
    text: str

    @property
    def llvm(self) -> str:
        return self.text


class LLVMCodegenError(errors.CompilerError):
    code = "LLVM100"

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(slots=True)
class GlobalSlot:
    name: str
    type_info: LLVMTypeInfo
    mutable: bool


@dataclass(slots=True)
class LocalSlot:
    pointer: str
    type_info: LLVMTypeInfo
    mutable: bool


@dataclass(slots=True)
class LambdaCapture:
    name: str
    slot: LocalSlot


@dataclass(slots=True)
class LambdaDescriptor:
    entry_name: str
    capture_struct: Optional[str]
    captures: List[LambdaCapture]


@dataclass(slots=True)
class LoopContext:
    break_label: str
    continue_label: str


class CodegenContext:
    def __init__(self, module: ModuleIr, module_name: str) -> None:
        self.module = module
        self.type_lowerer = TypeLowerer()
        self.module_builder = ModuleBuilder(module_name)
        self.globals: Dict[str, GlobalSlot] = {}
        self.functions: Dict[str, IrFunction] = {func.name: func for func in module.functions}
        self.namegen = NameGen()
        self._string_pool: Dict[str, tuple[str, int]] = {}
        self._string_counter = 0
        self.lambda_counter = 0

    def intern_string(self, literal: str) -> tuple[str, int]:
        cached = self._string_pool.get(literal)
        if cached:
            return cached
        encoded = literal.encode("utf8")
        size = len(encoded) + 1
        name = f"@.str.{self._string_counter}"
        self._string_counter += 1
        escaped = "".join(f"\\{byte:02X}" for byte in encoded)
        descriptor = f"{name} = private unnamed_addr constant [{size} x i8] c\"{escaped}\\00\""
        self.module_builder.add_global(descriptor)
        self._string_pool[literal] = (name, size)
        return name, size

    def next_lambda_index(self) -> int:
        index = self.lambda_counter
        self.lambda_counter += 1
        return index


class LLVMGenerator:
    def __init__(self, module_name: Optional[str] = None) -> None:
        self.module_name = module_name or "scriptum"

    def generate(self, module: ModuleIr, *, verify: bool = False) -> LLVMOutput:
        ctx = CodegenContext(module, self.module_name)
        self._declare_runtime(ctx)
        self._emit_globals(ctx, module.globals)
        self._emit_functions(ctx, module.functions)
        text = ctx.module_builder.render()
        # TODO: optionally run llvm-as for verification when requested (future step).
        return LLVMOutput(ir=module, text=text)

    def _declare_runtime(self, ctx: CodegenContext) -> None:
        for section in runtime_sections():
            ctx.module_builder.append_runtime(section)

    def _emit_globals(self, ctx: CodegenContext, globals_ir: Sequence[IrVariable]) -> None:
        for glob in globals_ir:
            ir_type = self._resolve_type(glob, ctx)
            initializer = self._format_global_value(glob)
            ctx.module_builder.add_global(f"@{glob.name} = internal global {ir_type.ir} {initializer}")
            ctx.globals[glob.name] = GlobalSlot(name=f"@{glob.name}", type_info=ir_type, mutable=glob.mutable)

    def _emit_functions(self, ctx: CodegenContext, functions: Sequence[IrFunction]) -> None:
        for func in functions:
            emitter = _FunctionEmitter(ctx, func)
            ctx.module_builder.add_function(emitter.emit())

    def _resolve_type(self, var: IrVariable, ctx: CodegenContext) -> LLVMTypeInfo:
        annotation = type_from_annotation(var.type_annotation) if var.type_annotation else var.type_info
        scriptum_type = annotation or sema_types.PRIMITIVE_TYPES["numerus"]
        return ctx.type_lowerer.lower(scriptum_type)

    def _format_global_value(self, glob: IrVariable) -> str:
        literal = glob.initializer
        if isinstance(literal, IrLiteral):
            if isinstance(literal.value, (int, float)):
                value = float(literal.value)
                bool_flag = 1 if value != 0.0 else 0
                return (
                    "{ i32 "
                    f"{SCRIPTUM_VALUE_KIND_NUMBER}, double {value:.6f}, i32 {bool_flag}, i32 0, i8* null }}"
                )
            if isinstance(literal.value, bool):
                bool_flag = 1 if literal.value else 0
                number = 1.0 if bool_flag else 0.0
                return (
                    "{ i32 "
                    f"{SCRIPTUM_VALUE_KIND_BOOLEAN}, double {number:.6f}, i32 {bool_flag}, i32 0, i8* null }}"
                )
            if literal.value is None:
                # nullum literal
                return "{ i32 %d, double 0.0, i32 0, i32 0, i8* null }" % SCRIPTUM_VALUE_KIND_NULL
        return "{ i32 %d, double 0.0, i32 0, i32 0, i8* null }" % SCRIPTUM_VALUE_KIND_NULL



class _FunctionEmitter:
    def __init__(self, ctx: CodegenContext, func: IrFunction) -> None:
        self.ctx = ctx
        self.func = func
        self.lowerer = ctx.type_lowerer
        self.locals: List[Dict[str, LocalSlot]] = []
        self.loops: List[LoopContext] = []
        self.value_type = self.lowerer.lower(sema_types.PRIMITIVE_TYPES["quodlibet"])
        self.value_ir = self.value_type.ir
        self.value_ptr_ir = f"{self.value_ir}*"
        self.text_ptr_ir = "%scriptum.text*"
        self.array_ptr_ir = "%scriptum.array*"
        self.object_ptr_ir = "%scriptum.object*"
        self.lambda_entry_type = f"{self.value_ir} (i8*, {self.value_ptr_ir}, i64)*"
        self.builder = self._create_builder()

    def emit(self) -> str:
        self.builder.new_block("entry")
        self._push_scope()
        self._declare_parameters()
        for stmt in self.func.body:
            self._emit_statement(stmt)
        current = self.builder.current_block()
        if not current.terminated:
            default_ret = self._const_null()
            self.builder.emit(f"ret {self.value_ir} {default_ret.name}")
            self.builder.set_terminated()
        if self.locals:
            self.locals.pop()
        return self.builder.render()

    def _create_builder(self) -> FunctionBuilder:
        ret_type = self._function_return_type()
        params = [f"{self._param_type(param).ir} %{param.name}" for param in self.func.parameters]
        header = f"define {ret_type.ir} @{self.func.name}({', '.join(params)}) {{"
        return FunctionBuilder(self.ctx.namegen, header)

    def _function_return_type(self) -> LLVMTypeInfo:
        return self.value_type

    def _param_type(self, _param) -> LLVMTypeInfo:
        return self.value_type

    def _declare_parameters(self) -> None:
        for param in self.func.parameters:
            slot = self._alloca(param.name)
            self.builder.emit(f"store {self.value_ir} %{param.name}, {self.value_ptr_ir} {slot}")
            self._bind(param.name, LocalSlot(pointer=slot, type_info=self.value_type, mutable=False))

    def _new_label(self, base: str) -> str:
        name = self.ctx.namegen.new(base)
        return name[1:] if name.startswith("%") else name

    def _push_scope(self) -> None:
        self.locals.append({})

    def _pop_scope(self) -> None:
        if self.locals:
            self.locals.pop()

    def _bind(self, name: str, slot: LocalSlot) -> None:
        if not self.locals:
            self._push_scope()
        self.locals[-1][name] = slot

    def _lookup(self, name: str) -> Optional[LocalSlot]:
        for scope in reversed(self.locals):
            if name in scope:
                return scope[name]
        return None

    def _snapshot_locals(self) -> Dict[str, LocalSlot]:
        snapshot: Dict[str, LocalSlot] = {}
        for scope in self.locals:
            snapshot.update(scope)
        return snapshot

    def _alloca(self, name: str, type_info: Optional[LLVMTypeInfo] = None) -> str:
        info = type_info or self.value_type
        reg = self.ctx.namegen.new(f"{name}.slot")
        self.builder.emit(f"{reg} = alloca {info.ir}")
        return reg

    def _alloca_raw(self, name: str, ir: str) -> str:
        reg = self.ctx.namegen.new(f"{name}.slot")
        self.builder.emit(f"{reg} = alloca {ir}")
        return reg

    def _store_value(self, pointer: str, value: Value) -> None:
        self.builder.emit(f"store {self.value_ir} {value.name}, {self.value_ptr_ir} {pointer}")

    def _load_value(self, pointer: str) -> Value:
        reg = self.ctx.namegen.new("load")
        self.builder.emit(f"{reg} = load {self.value_ir}, {self.value_ptr_ir} {pointer}")
        return Value(name=reg, type=self.value_type)

    def _emit_statement(self, stmt: IrStatement) -> None:
        if isinstance(stmt, IrVariableDeclaration):
            self._emit_var_decl(stmt)
            return
        if isinstance(stmt, IrExpressionStatement):
            if stmt.expression:
                self._eval_expr(stmt.expression)
            return
        if isinstance(stmt, IrReturn):
            self._emit_return(stmt)
            return
        if isinstance(stmt, IrIf):
            self._emit_if(stmt)
            return
        if isinstance(stmt, IrWhile):
            self._emit_while(stmt)
            return
        if isinstance(stmt, IrForIn):
            self._emit_for_in(stmt)
            return
        if isinstance(stmt, IrBreak):
            self._emit_break()
            return
        if isinstance(stmt, IrContinue):
            self._emit_continue()
            return
        raise LLVMCodegenError(f"Statement '{type(stmt).__name__}' n?o suportado.")

    def _resolve_scriptum_type(self, stmt) -> Optional[sema_types.Type]:
        if getattr(stmt, "type_info", None):
            return stmt.type_info
        annotation = getattr(stmt, "type_annotation", None)
        if annotation:
            return type_from_annotation(annotation)
        return None

    def _emit_var_decl(self, stmt: IrVariableDeclaration) -> None:
        slot = self._alloca(stmt.name)
        target_type = self._resolve_scriptum_type(stmt)
        initial = self._const_default(target_type)
        if stmt.initializer is not None:
            initial = self._eval_expr(stmt.initializer)
        self._store_value(slot, initial)
        self._bind(stmt.name, LocalSlot(pointer=slot, type_info=self.value_type, mutable=stmt.mutable))

    def _const_default(self, scriptum_type: Optional[sema_types.Type]) -> Value:
        if scriptum_type and scriptum_type.kind is sema_types.TypeKind.BOOLEANUM:
            return self._const_bool(False)
        if scriptum_type and scriptum_type.kind is sema_types.TypeKind.NUMERUS:
            return self._const_numeric(0.0)
        return self._const_null()

    def _emit_return(self, stmt: IrReturn) -> None:
        result = self._const_null()
        if stmt.value is not None:
            result = self._eval_expr(stmt.value)
        self.builder.emit(f"ret {self.value_ir} {result.name}")
        self.builder.set_terminated()

    def _emit_if(self, stmt: IrIf) -> None:
        cond_flag = self._truthy_flag(self._eval_expr(stmt.condition))
        then_label = self._new_label("if.then")
        else_label = self._new_label("if.else")
        end_label = self._new_label("if.end")
        self.builder.emit(f"br i1 {cond_flag}, label %{then_label}, label %{else_label}")

        then_block = self.builder.new_block(then_label)
        self._push_scope()
        for inner in stmt.then_branch:
            self._emit_statement(inner)
        self._pop_scope()
        if not then_block.terminated:
            self.builder.emit(f"br label %{end_label}")

        else_block = self.builder.new_block(else_label)
        self._push_scope()
        for inner in stmt.else_branch:
            self._emit_statement(inner)
        self._pop_scope()
        if not else_block.terminated:
            self.builder.emit(f"br label %{end_label}")

        self.builder.new_block(end_label)

    def _emit_while(self, stmt: IrWhile) -> None:
        cond_label = self._new_label("while.cond")
        body_label = self._new_label("while.body")
        end_label = self._new_label("while.end")
        self.builder.emit(f"br label %{cond_label}")

        cond_block = self.builder.new_block(cond_label)
        cond_flag = self._truthy_flag(self._eval_expr(stmt.condition))
        cond_block.emit(f"br i1 {cond_flag}, label %{body_label}, label %{end_label}")

        body_block = self.builder.new_block(body_label)
        self.loops.append(LoopContext(break_label=end_label, continue_label=cond_label))
        self._push_scope()
        for inner in stmt.body:
            self._emit_statement(inner)
        self._pop_scope()
        self.loops.pop()
        if not body_block.terminated:
            body_block.emit(f"br label %{cond_label}")

        self.builder.new_block(end_label)

    def _emit_for_in(self, stmt: IrForIn) -> None:
        iterable = self._eval_expr(stmt.iterable)
        array_ptr = self._value_expect_array(iterable)
        length_reg = self.ctx.namegen.new("for.len")
        self.builder.emit(f"{length_reg} = call i64 @scriptum_array_len({self.array_ptr_ir} {array_ptr})")
        index_slot = self._alloca_raw("for.index", "i64")
        self.builder.emit(f"store i64 0, i64* {index_slot}")

        cond_label = self._new_label("for.cond")
        body_label = self._new_label("for.body")
        end_label = self._new_label("for.end")
        self.builder.emit(f"br label %{cond_label}")

        cond_block = self.builder.new_block(cond_label)
        idx_reg = self.ctx.namegen.new("for.idx")
        cond_block.emit(f"{idx_reg} = load i64, i64* {index_slot}")
        cmp_reg = self.ctx.namegen.new("for.cmp")
        cond_block.emit(f"{cmp_reg} = icmp slt i64 {idx_reg}, {length_reg}")
        cond_block.emit(f"br i1 {cmp_reg}, label %{body_label}, label %{end_label}")

        body_block = self.builder.new_block(body_label)
        self.loops.append(LoopContext(break_label=end_label, continue_label=cond_label))
        self._push_scope()
        target_slot = self._alloca(stmt.target.name)
        self._bind(
            stmt.target.name,
            LocalSlot(pointer=target_slot, type_info=self.value_type, mutable=stmt.target.mutable),
        )
        element_slot = self._alloca(f"{stmt.target.name}.current")
        current_idx = self.ctx.namegen.new("for.body.idx")
        body_block.emit(f"{current_idx} = load i64, i64* {index_slot}")
        self.builder.emit(
            f"call i32 @scriptum_array_get({self.array_ptr_ir} {array_ptr}, i64 {current_idx}, {self.value_ptr_ir} {element_slot})"
        )
        current_value = self._load_value(element_slot)
        self._store_value(target_slot, current_value)
        for inner in stmt.body:
            self._emit_statement(inner)
        self._pop_scope()
        self.loops.pop()
        if not body_block.terminated:
            next_idx = self.ctx.namegen.new("for.next")
            body_block.emit(f"{next_idx} = add i64 {current_idx}, 1")
            body_block.emit(f"store i64 {next_idx}, i64* {index_slot}")
            body_block.emit(f"br label %{cond_label}")
        self.builder.new_block(end_label)

    def _emit_break(self) -> None:
        if not self.loops:
            raise LLVMCodegenError("frange fora de la?o.")
        self.builder.emit(f"br label %{self.loops[-1].break_label}")
        self.builder.set_terminated()

    def _emit_continue(self) -> None:
        if not self.loops:
            raise LLVMCodegenError("perge fora de la?o.")
        self.builder.emit(f"br label %{self.loops[-1].continue_label}")
        self.builder.set_terminated()

    def _eval_expr(self, expr: IrExpr) -> Value:
        if isinstance(expr, IrLiteral):
            literal_type = expr.type_info or sema_types.PRIMITIVE_TYPES["quodlibet"]
            if isinstance(expr.value, (int, float)):
                return self._const_numeric(float(expr.value))
            if isinstance(expr.value, bool):
                return self._const_bool(expr.value)
            if literal_type.kind is sema_types.TypeKind.TEXTUS and isinstance(expr.value, str):
                return self._const_string(expr.value)
            if literal_type.kind in {sema_types.TypeKind.NULLUM, sema_types.TypeKind.INDEFINITUM}:
                return self._const_null()
            raise LLVMCodegenError("Literal n?o suportado.")
        if isinstance(expr, IrIdentifier):
            slot = self._lookup(expr.name)
            if slot:
                return self._load_value(slot.pointer)
            glob = self.ctx.globals.get(expr.name)
            if glob:
                reg = self.ctx.namegen.new("gload")
                self.builder.emit(f"{reg} = load {glob.type_info.ir}, {glob.type_info.ir}* {glob.name}")
                return Value(name=reg, type=self.value_type)
            raise LLVMCodegenError(f"Identificador '{expr.name}' n?o encontrado.")
        if isinstance(expr, IrArrayLiteral):
            return self._emit_array_literal(expr)
        if isinstance(expr, IrObjectLiteral):
            return self._emit_object_literal(expr)
        if isinstance(expr, IrUnary):
            return self._eval_unary(expr)
        if isinstance(expr, IrBinary):
            return self._eval_binary(expr)
        if isinstance(expr, IrAssignment):
            return self._eval_assignment(expr)
        if isinstance(expr, IrConditional):
            return self._eval_conditional(expr)
        if isinstance(expr, IrCall):
            return self._emit_call(expr)
        if isinstance(expr, IrLambda):
            return self._emit_lambda(expr)
        raise LLVMCodegenError(f"Express?o '{type(expr).__name__}' n?o suportada.")

    def _emit_array_literal(self, literal: IrArrayLiteral) -> Value:
        size = len(literal.elements)
        array_reg = self.ctx.namegen.new("array.new")
        self.builder.emit(f"{array_reg} = call {self.array_ptr_ir} @scriptum_array_new(i64 {size})")
        for element in literal.elements:
            value = self._eval_expr(element)
            self.builder.emit(
                f"call void @scriptum_array_push({self.array_ptr_ir} {array_reg}, {self.value_ir} {value.name})"
            )
        wrap = self.ctx.namegen.new("array.wrap")
        self.builder.emit(f"{wrap} = call {self.value_ir} @scriptum_value_array({self.array_ptr_ir} {array_reg})")
        return Value(name=wrap, type=self.value_type)

    def _emit_object_literal(self, literal: IrObjectLiteral) -> Value:
        obj_reg = self.ctx.namegen.new("object.new")
        self.builder.emit(f"{obj_reg} = call {self.object_ptr_ir} @scriptum_object_new()")
        for prop in literal.properties:
            key_ptr = self._text_pointer_from_literal(prop.key)
            value = self._eval_expr(prop.value)
            self.builder.emit(
                f"call void @scriptum_object_set({self.object_ptr_ir} {obj_reg}, {self.text_ptr_ir} {key_ptr}, {self.value_ir} {value.name})"
            )
            self.builder.emit(f"call void @scriptum_text_release({self.text_ptr_ir} {key_ptr})")
        wrap = self.ctx.namegen.new("object.wrap")
        self.builder.emit(f"{wrap} = call {self.value_ir} @scriptum_value_object({self.object_ptr_ir} {obj_reg})")
        return Value(name=wrap, type=self.value_type)

    def _text_pointer_from_literal(self, literal: str) -> str:
        name, size = self.ctx.intern_string(literal)
        data_reg = self.ctx.namegen.new("text.data")
        self.builder.emit(
            f"{data_reg} = getelementptr inbounds [{size} x i8], [{size} x i8]* {name}, i32 0, i32 0"
        )
        text_reg = self.ctx.namegen.new("text.new")
        length = max(size - 1, 0)
        self.builder.emit(f"{text_reg} = call {self.text_ptr_ir} @scriptum_text_new(i8* {data_reg}, i64 {length})")
        return text_reg

    def _eval_unary(self, expr: IrUnary) -> Value:
        operand = self._eval_expr(expr.operand)
        if expr.operator in {"NEGATE", "-"}:
            number_reg = self._as_number(operand)
            reg = self.ctx.namegen.new("neg")
            self.builder.emit(f"{reg} = fsub double 0.0, {number_reg}")
            return self._from_number(reg)
        if expr.operator in {"POSITIVE", "+"}:
            return operand
        if expr.operator in {"NOT", "!"}:
            flag = self._truthy_flag(operand)
            not_reg = self.ctx.namegen.new("not")
            self.builder.emit(f"{not_reg} = xor i1 {flag}, true")
            return self._bool_from_flag(not_reg)
        raise LLVMCodegenError(f"Operador un?rio '{expr.operator}' n?o suportado.")

    def _eval_binary(self, expr: IrBinary) -> Value:
        op = expr.operator
        if op in {"ADD", "+", "SUB", "-", "MUL", "*", "DIV", "/", "MOD", "%"}:
            return self._eval_arithmetic(expr, op)
        if op in {"GT", "GE", "LT", "LE", "EQ", "NE", "STRICT_EQ", "STRICT_NE"}:
            return self._eval_comparison(expr, op)
        if op in {"AND", "&&", "OR", "||"}:
            return self._eval_logical(expr, op)
        if op in {"NULLISH", "??"}:
            return self._eval_nullish(expr)
        raise LLVMCodegenError(f"Operador bin?rio '{op}' n?o suportado.")

    def _eval_arithmetic(self, expr: IrBinary, op: str) -> Value:
        left = self._as_number(self._eval_expr(expr.left))
        right = self._as_number(self._eval_expr(expr.right))
        reg = self.ctx.namegen.new("arith")
        instr = {
            "ADD": "fadd",
            "+": "fadd",
            "SUB": "fsub",
            "-": "fsub",
            "MUL": "fmul",
            "*": "fmul",
            "DIV": "fdiv",
            "/": "fdiv",
            "MOD": "frem",
            "%": "frem",
        }[op]
        self.builder.emit(f"{reg} = {instr} double {left}, {right}")
        return self._from_number(reg)

    def _eval_comparison(self, expr: IrBinary, op: str) -> Value:
        left = self._as_number(self._eval_expr(expr.left))
        right = self._as_number(self._eval_expr(expr.right))
        reg = self.ctx.namegen.new("cmp")
        predicate = {
            "GT": "ogt",
            ">": "ogt",
            "GE": "oge",
            ">=": "oge",
            "LT": "olt",
            "<": "olt",
            "LE": "ole",
            "<=": "ole",
            "EQ": "oeq",
            "==": "oeq",
            "NE": "one",
            "!=": "one",
            "STRICT_EQ": "oeq",
            "STRICT_NE": "one",
        }[op]
        self.builder.emit(f"{reg} = fcmp {predicate} double {left}, {right}")
        return self._bool_from_flag(reg)

    def _eval_logical(self, expr: IrBinary, op: str) -> Value:
        left_flag = self._truthy_flag(self._eval_expr(expr.left))
        head_block = self.builder.current_block().name
        rhs_label = self._new_label("logic.rhs")
        end_label = self._new_label("logic.end")
        if op in {"OR", "||"}:
            self.builder.emit(f"br i1 {left_flag}, label %{end_label}, label %{rhs_label}")
        else:
            self.builder.emit(f"br i1 {left_flag}, label %{rhs_label}, label %{end_label}")
        rhs_block = self.builder.new_block(rhs_label)
        right_flag = self._truthy_flag(self._eval_expr(expr.right))
        rhs_block.emit(f"br label %{end_label}")
        end_block = self.builder.new_block(end_label)
        phi_reg = self.ctx.namegen.new("logic.phi")
        short_val = "true" if op in {"OR", "||"} else "false"
        end_block.emit(f"{phi_reg} = phi i1 [ {short_val}, %{head_block} ], [ {right_flag}, %{rhs_label} ]")
        return self._bool_from_flag(phi_reg)

    def _eval_nullish(self, expr: IrBinary) -> Value:
        left = self._eval_expr(expr.left)
        is_null = self._value_kind_flag(left, SCRIPTUM_VALUE_KIND_NULL)
        rhs_label = self._new_label("nullish.rhs")
        end_label = self._new_label("nullish.end")
        start_block = self.builder.current_block().name
        self.builder.emit(f"br i1 {is_null}, label %{rhs_label}, label %{end_label}")
        rhs_block = self.builder.new_block(rhs_label)
        right = self._eval_expr(expr.right)
        rhs_block.emit(f"br label %{end_label}")
        end_block = self.builder.new_block(end_label)
        phi_reg = self.ctx.namegen.new("nullish")
        end_block.emit(
            f"{phi_reg} = phi {self.value_ir} [ {left.name}, %{start_block} ], [ {right.name}, %{rhs_label} ]"
        )
        return Value(name=phi_reg, type=self.value_type)

    def _eval_assignment(self, expr: IrAssignment) -> Value:
        if not isinstance(expr.target, IrIdentifier):
            raise LLVMCodegenError("Atribui??o suporta apenas identificadores.")
        slot = self._lookup(expr.target.name)
        if slot is None:
            raise LLVMCodegenError(f"Vari?vel '{expr.target.name}' n?o declarada.")
        if not slot.mutable:
            raise LLVMCodegenError(f"Vari?vel '{expr.target.name}' ? imut?vel.")
        value = self._eval_expr(expr.value)
        self._store_value(slot.pointer, value)
        return value

    def _eval_conditional(self, expr: IrConditional) -> Value:
        cond_flag = self._truthy_flag(self._eval_expr(expr.condition))
        then_label = self._new_label("cond.then")
        else_label = self._new_label("cond.else")
        merge_label = self._new_label("cond.merge")
        self.builder.emit(f"br i1 {cond_flag}, label %{then_label}, label %{else_label}")

        then_block = self.builder.new_block(then_label)
        then_value = self._eval_expr(expr.consequent)
        then_block.emit(f"br label %{merge_label}")

        else_block = self.builder.new_block(else_label)
        else_value = self._eval_expr(expr.alternate)
        else_block.emit(f"br label %{merge_label}")

        merge_block = self.builder.new_block(merge_label)
        phi_reg = self.ctx.namegen.new("condphi")
        merge_block.emit(
            f"{phi_reg} = phi {self.value_ir} [ {then_value.name}, %{then_label} ], [ {else_value.name}, %{else_label} ]"
        )
        return Value(name=phi_reg, type=self.value_type)

    def _emit_call(self, expr: IrCall) -> Value:
        if isinstance(expr.callee, IrIdentifier):
            if expr.callee.name in self.ctx.functions:
                arg_values = [self._eval_expr(arg) for arg in expr.arguments]
                return self._emit_direct_call(expr.callee.name, arg_values)
            runtime_symbol = BUILTIN_RUNTIME_MAP.get(expr.callee.name)
            if runtime_symbol:
                arg_values = [self._eval_expr(arg) for arg in expr.arguments]
                return self._emit_builtin_call(runtime_symbol, arg_values, expr.callee.name)
            if expr.callee.name in std_builtins.GLOBAL_FUNCTIONS:
                raise LLVMCodegenError(f"Builtin '{expr.callee.name}' n?o suportado pelo backend LLVM.")
        if isinstance(expr.callee, IrMemberAccess) and expr.callee.binding:
            receiver_value = self._eval_expr(expr.callee.object)
            arg_values = [self._eval_expr(arg) for arg in expr.arguments]
            return self._emit_method_call(receiver_value, expr.callee.binding, arg_values)
        callee_value = self._eval_expr(expr.callee)
        arg_values = [self._eval_expr(arg) for arg in expr.arguments]
        return self._emit_lambda_call(callee_value, arg_values)

    def _emit_direct_call(self, name: str, args: List[Value]) -> Value:
        params = ", ".join(f"{self.value_ir} {arg.name}" for arg in args)
        call_reg = self.ctx.namegen.new("call")
        if params:
            self.builder.emit(f"{call_reg} = call {self.value_ir} @{name}({params})")
        else:
            self.builder.emit(f"{call_reg} = call {self.value_ir} @{name}()")
        return Value(name=call_reg, type=self.value_type)

    def _emit_builtin_call(self, runtime_symbol: str, args: List[Value], name: str) -> Value:
        argc = len(args)
        if argc > 0:
            arg_buffer = self.ctx.namegen.new(f"{name}.args")
            self.builder.emit(f"{arg_buffer} = alloca {self.value_ir}, i64 {argc}")
            for index, arg in enumerate(args):
                slot = self.ctx.namegen.new(f"{name}.arg.slot")
                self.builder.emit(
                    f"{slot} = getelementptr inbounds {self.value_ir}, {self.value_ir}* {arg_buffer}, i64 {index}"
                )
                self.builder.emit(f"store {self.value_ir} {arg.name}, {self.value_ir}* {slot}")
            args_pointer = arg_buffer
        else:
            args_pointer = "null"
        call_reg = self.ctx.namegen.new(f"{name}.builtin")
        self.builder.emit(
            f"{call_reg} = call {self.value_ir} @{runtime_symbol}({self.value_ptr_ir} {args_pointer}, i64 {argc})"
        )
        return Value(name=call_reg, type=self.value_type)

    def _emit_method_call(self, receiver: Value, binding: std_builtins.MethodBinding, args: List[Value]) -> Value:
        spec_name = binding.spec.name
        if binding.spec.receiver_kind is sema_types.TypeKind.ARRAY:
            runtime_symbol = ARRAY_METHOD_RUNTIME_MAP.get(spec_name)
            if runtime_symbol is None:
                raise LLVMCodegenError(f"M�todo de array '{spec_name}' n?o suportado pelo backend LLVM.")
            receiver_ptr = self._value_expect_array(receiver)
            return self._call_method(runtime_symbol, self.array_ptr_ir, receiver_ptr, args, spec_name)
        if binding.spec.receiver_kind is sema_types.TypeKind.TEXTUS:
            runtime_symbol = TEXT_METHOD_RUNTIME_MAP.get(spec_name)
            if runtime_symbol is None:
                raise LLVMCodegenError(f"M�todo de textus '{spec_name}' n?o suportado pelo backend LLVM.")
            receiver_ptr = self._value_expect_text(receiver)
            return self._call_method(runtime_symbol, self.text_ptr_ir, receiver_ptr, args, spec_name)
        raise LLVMCodegenError(f"M�todo builtin '{spec_name}' n?o possui runtime suportado.")

    def _call_method(
        self, runtime_symbol: str, receiver_ptr_ir: str, receiver_ptr: str, args: List[Value], name: str
    ) -> Value:
        argc = len(args)
        if argc > 0:
            arg_buffer = self.ctx.namegen.new(f"{name}.args")
            self.builder.emit(f"{arg_buffer} = alloca {self.value_ir}, i64 {argc}")
            for index, arg in enumerate(args):
                slot = self.ctx.namegen.new(f"{name}.arg.slot")
                self.builder.emit(
                    f"{slot} = getelementptr inbounds {self.value_ir}, {self.value_ir}* {arg_buffer}, i64 {index}"
                )
                self.builder.emit(f"store {self.value_ir} {arg.name}, {self.value_ir}* {slot}")
            args_operand = arg_buffer
        else:
            args_operand = "null"
        call_reg = self.ctx.namegen.new(f"{name}.method")
        self.builder.emit(
            f"{call_reg} = call {self.value_ir} @{runtime_symbol}({receiver_ptr_ir} {receiver_ptr}, {self.value_ptr_ir} {args_operand}, i64 {argc})"
        )
        return Value(name=call_reg, type=self.value_type)

    def _emit_lambda_call(self, callee: Value, args: List[Value]) -> Value:
        spill = self._spill_value(callee)
        lambda_ptr = self.ctx.namegen.new("lambda.ptr")
        self.builder.emit(f"{lambda_ptr} = call %scriptum.lambda* @scriptum_value_expect_lambda({self.value_ptr_ir} {spill})")
        argc = len(args)
        if argc > 0:
            arg_buffer = self.ctx.namegen.new("lambda.args")
            self.builder.emit(f"{arg_buffer} = alloca {self.value_ir}, i64 {argc}")
            for index, arg in enumerate(args):
                slot = self.ctx.namegen.new("lambda.arg.slot")
                self.builder.emit(
                    f"{slot} = getelementptr inbounds {self.value_ir}, {self.value_ir}* {arg_buffer}, i64 {index}"
                )
                self.builder.emit(f"store {self.value_ir} {arg.name}, {self.value_ir}* {slot}")
            args_operand = f"{self.value_ptr_ir} {arg_buffer}"
        else:
            args_operand = f"{self.value_ptr_ir} null"
        call_reg = self.ctx.namegen.new("lambda.call")
        self.builder.emit(
            f"{call_reg} = call {self.value_ir} @scriptum_lambda_call(%scriptum.lambda* {lambda_ptr}, {args_operand}, i64 {argc})"
        )
        return Value(name=call_reg, type=self.value_type)

    def _emit_lambda(self, expr: IrLambda) -> Value:
        captures = self._collect_lambda_captures(expr)
        descriptor = self._declare_lambda(expr, captures)
        closure_ptr = self._instantiate_lambda_closure(descriptor)
        entry_operand = f"{self.lambda_entry_type} @{descriptor.entry_name}"
        lambda_reg = self.ctx.namegen.new("lambda.new")
        self.builder.emit(f"{lambda_reg} = call %scriptum.lambda* @scriptum_lambda_new({entry_operand}, i8* {closure_ptr})")
        wrap = self.ctx.namegen.new("lambda.wrap")
        self.builder.emit(f"{wrap} = call {self.value_ir} @scriptum_value_lambda(%scriptum.lambda* {lambda_reg})")
        return Value(name=wrap, type=self.value_type)

    def _collect_lambda_captures(self, expr: IrLambda) -> List[LambdaCapture]:
        locals_snapshot = self._snapshot_locals()
        collector = _LambdaCaptureCollector(expr, locals_snapshot)
        ordered_names = collector.collect()
        captures: List[LambdaCapture] = []
        for name in ordered_names:
            slot = locals_snapshot.get(name)
            if slot:
                captures.append(LambdaCapture(name=name, slot=slot))
        return captures

    def _declare_lambda(self, expr: IrLambda, captures: List[LambdaCapture]) -> LambdaDescriptor:
        index = self.ctx.next_lambda_index()
        entry_name = f"lambda.{index}.entry"
        capture_struct: Optional[str] = None
        if captures:
            capture_struct = f"%lambda.capture.{index}"
            fields = ", ".join(self.value_ir for _ in captures)
            self.ctx.module_builder.add_struct(f"{capture_struct} = type {{ {fields} }}")
        emitter = _LambdaEmitter(self.ctx, expr, entry_name, capture_struct, captures)
        self.ctx.module_builder.add_function(emitter.emit())
        return LambdaDescriptor(entry_name=entry_name, capture_struct=capture_struct, captures=captures)

    def _instantiate_lambda_closure(self, descriptor: LambdaDescriptor) -> str:
        if not descriptor.capture_struct or not descriptor.captures:
            return "null"
        struct_type = descriptor.capture_struct
        size_ptr = self.ctx.namegen.new("lambda.cap.size.ptr")
        self.builder.emit(f"{size_ptr} = getelementptr inbounds {struct_type}, {struct_type}* null, i32 1")
        size_reg = self.ctx.namegen.new("lambda.cap.size")
        self.builder.emit(f"{size_reg} = ptrtoint {struct_type}* {size_ptr} to i64")
        raw_reg = self.ctx.namegen.new("lambda.cap.raw")
        self.builder.emit(f"{raw_reg} = call i8* @scriptum_alloc(i64 {size_reg})")
        typed_reg = self.ctx.namegen.new("lambda.cap.ptr")
        self.builder.emit(f"{typed_reg} = bitcast i8* {raw_reg} to {struct_type}*")
        for index, capture in enumerate(descriptor.captures):
            field_ptr = self.ctx.namegen.new("lambda.cap.field")
            self.builder.emit(
                f"{field_ptr} = getelementptr inbounds {struct_type}, {struct_type}* {typed_reg}, i32 0, i32 {index}"
            )
            value = self._load_value(capture.slot.pointer)
            self.builder.emit(f"store {self.value_ir} {value.name}, {self.value_ir}* {field_ptr}")
        return raw_reg

    def _const_numeric(self, value: float) -> Value:
        reg = self.ctx.namegen.new("num")
        self.builder.emit(f"{reg} = call {self.value_ir} @scriptum_value_number(double {value})")
        return Value(name=reg, type=self.value_type)

    def _const_bool(self, flag: bool) -> Value:
        reg = self.ctx.namegen.new("bool")
        int_flag = 1 if flag else 0
        self.builder.emit(f"{reg} = call {self.value_ir} @scriptum_value_boolean(i32 {int_flag})")
        return Value(name=reg, type=self.value_type)

    def _const_string(self, literal: str) -> Value:
        text_ptr = self._text_pointer_from_literal(literal)
        reg = self.ctx.namegen.new("str")
        self.builder.emit(f"{reg} = call {self.value_ir} @scriptum_value_text({self.text_ptr_ir} {text_ptr})")
        return Value(name=reg, type=self.value_type)

    def _const_null(self) -> Value:
        reg = self.ctx.namegen.new("null")
        self.builder.emit(f"{reg} = call {self.value_ir} @scriptum_value_null()")
        return Value(name=reg, type=self.value_type)

    def _truthy_flag(self, value: Value) -> str:
        ptr = self._spill_value(value)
        reg = self.ctx.namegen.new("bool32")
        self.builder.emit(f"{reg} = call i32 @scriptum_value_as_boolean({self.value_ptr_ir} {ptr})")
        flag = self.ctx.namegen.new("bool")
        self.builder.emit(f"{flag} = icmp ne i32 {reg}, 0")
        return flag

    def _ensure_bool(self, value: Value) -> Value:
        return self._bool_from_flag(self._truthy_flag(value))

    def _bool_from_flag(self, flag: str) -> Value:
        zext = self.ctx.namegen.new("boolz")
        self.builder.emit(f"{zext} = zext i1 {flag} to i32")
        reg = self.ctx.namegen.new("boolwrap")
        self.builder.emit(f"{reg} = call {self.value_ir} @scriptum_value_boolean(i32 {zext})")
        return Value(name=reg, type=self.value_type)

    def _value_kind_flag(self, value: Value, kind: int) -> str:
        kind_reg = self.ctx.namegen.new("kind")
        self.builder.emit(f"{kind_reg} = extractvalue {self.value_ir} {value.name}, 0")
        flag = self.ctx.namegen.new("kindcmp")
        self.builder.emit(f"{flag} = icmp eq i32 {kind_reg}, {kind}")
        return flag

    def _as_number(self, value: Value) -> str:
        ptr = self._spill_value(value)
        reg = self.ctx.namegen.new("tonum")
        self.builder.emit(f"{reg} = call double @scriptum_value_as_number({self.value_ptr_ir} {ptr})")
        return reg

    def _from_number(self, register: str) -> Value:
        wrap = self.ctx.namegen.new("fromnum")
        self.builder.emit(f"{wrap} = call {self.value_ir} @scriptum_value_number(double {register})")
        return Value(name=wrap, type=self.value_type)

    def _spill_value(self, value: Value) -> str:
        slot = self.ctx.namegen.new("spill")
        self.builder.emit(f"{slot} = alloca {self.value_ir}")
        self.builder.emit(f"store {self.value_ir} {value.name}, {self.value_ptr_ir} {slot}")
        return slot

    def _value_expect_array(self, value: Value) -> str:
        ptr = self._spill_value(value)
        reg = self.ctx.namegen.new("array.ptr")
        self.builder.emit(f"{reg} = call {self.array_ptr_ir} @scriptum_value_expect_array({self.value_ptr_ir} {ptr})")
        return reg

    def _value_expect_text(self, value: Value) -> str:
        ptr = self._spill_value(value)
        reg = self.ctx.namegen.new("text.ptr")
        self.builder.emit(f"{reg} = call {self.text_ptr_ir} @scriptum_value_expect_text({self.value_ptr_ir} {ptr})")
        return reg


class _LambdaEmitter(_FunctionEmitter):
    def __init__(
        self,
        ctx: CodegenContext,
        ir_lambda: IrLambda,
        entry_name: str,
        capture_struct: Optional[str],
        captures: List[LambdaCapture],
    ) -> None:
        body_statements = list(ir_lambda.body_statements)
        if ir_lambda.body_expression is not None:
            body_statements.append(IrReturn(span=ir_lambda.body_expression.span, value=ir_lambda.body_expression))
        func = IrFunction(
            span=ir_lambda.span,
            name=entry_name,
            parameters=ir_lambda.parameters,
            return_annotation=ir_lambda.return_annotation,
            body=body_statements,
        )
        self.capture_struct = capture_struct
        self.captures = captures
        self._closure_param_name = "%lambda.closure.raw"
        self._args_param_name = "%lambda.args.raw"
        self._argc_param_name = "%lambda.argc"
        super().__init__(ctx, func)

    def _create_builder(self) -> FunctionBuilder:
        ret_type = self._function_return_type()
        header = (
            f"define {ret_type.ir} @{self.func.name}("
            f"i8* {self._closure_param_name}, {self.value_ptr_ir} {self._args_param_name}, i64 {self._argc_param_name}) {{"
        )
        return FunctionBuilder(self.ctx.namegen, header)

    def _declare_parameters(self) -> None:
        closure_ptr_reg: Optional[str] = None
        if self.capture_struct and self.captures:
            closure_ptr_reg = self.ctx.namegen.new("lambda.closure.ptr")
            self.builder.emit(
                f"{closure_ptr_reg} = bitcast i8* {self._closure_param_name} to {self.capture_struct}*"
            )
            for index, capture in enumerate(self.captures):
                field_ptr = self.ctx.namegen.new("lambda.capture.ptr")
                self.builder.emit(
                    f"{field_ptr} = getelementptr inbounds {self.capture_struct}, "
                    f"{self.capture_struct}* {closure_ptr_reg}, i32 0, i32 {index}"
                )
                field_value = self.ctx.namegen.new("lambda.capture.load")
                self.builder.emit(f"{field_value} = load {self.value_ir}, {self.value_ir}* {field_ptr}")
                slot = self._alloca(capture.name)
                self.builder.emit(f"store {self.value_ir} {field_value}, {self.value_ptr_ir} {slot}")
                self._bind(
                    capture.name,
                    LocalSlot(pointer=slot, type_info=self.value_type, mutable=capture.slot.mutable),
                )
        for index, param in enumerate(self.func.parameters):
            slot = self._alloca(param.name)
            value = self._lambda_argument_value(index, param)
            self._store_value(slot, value)
            self._bind(param.name, LocalSlot(pointer=slot, type_info=self.value_type, mutable=False))

    def _lambda_argument_value(self, index: int, param: IrParameter) -> Value:
        cmp_reg = self.ctx.namegen.new("lambda.arg.cmp")
        self.builder.emit(f"{cmp_reg} = icmp ugt i64 {self._argc_param_name}, {index}")
        have_label = self._new_label(f"lambda.arg{index}.value")
        default_label = self._new_label(f"lambda.arg{index}.default")
        merge_label = self._new_label(f"lambda.arg{index}.merge")
        self.builder.emit(f"br i1 {cmp_reg}, label %{have_label}, label %{default_label}")

        value_block = self.builder.new_block(have_label)
        provided = self._load_lambda_argument(index)
        value_block.emit(f"br label %{merge_label}")

        default_block = self.builder.new_block(default_label)
        if param.default_value is not None:
            fallback = self._eval_expr(param.default_value)
        else:
            fallback = self._const_null()
        default_block.emit(f"br label %{merge_label}")

        merge_block = self.builder.new_block(merge_label)
        phi_reg = self.ctx.namegen.new("lambda.arg.phi")
        merge_block.emit(
            f"{phi_reg} = phi {self.value_ir} [ {provided.name}, %{have_label} ], [ {fallback.name}, %{default_label} ]"
        )
        return Value(name=phi_reg, type=self.value_type)

    def _load_lambda_argument(self, index: int) -> Value:
        ptr_reg = self.ctx.namegen.new("lambda.arg.ptr")
        self.builder.emit(
            f"{ptr_reg} = getelementptr inbounds {self.value_ir}, {self.value_ir}* {self._args_param_name}, i64 {index}"
        )
        load_reg = self.ctx.namegen.new("lambda.arg.load")
        self.builder.emit(f"{load_reg} = load {self.value_ir}, {self.value_ir}* {ptr_reg}")
        return Value(name=load_reg, type=self.value_type)


class _LambdaCaptureCollector:
    def __init__(
        self,
        expr: IrLambda,
        outer_locals: Dict[str, LocalSlot],
    ) -> None:
        self.expr = expr
        self.outer_locals = outer_locals
        self.captures: List[str] = []
        initial_scope = {param.name for param in expr.parameters}
        self._locals_stack: List[Set[str]] = [initial_scope]
        for param in expr.parameters:
            if param.default_value is not None:
                self._visit_expr(param.default_value)

    def collect(self) -> List[str]:
        for stmt in self.expr.body_statements:
            self._visit_statement(stmt)
        if self.expr.body_expression is not None:
            self._visit_expr(self.expr.body_expression)
        return self.captures

    def _push_scope(self) -> None:
        self._locals_stack.append(set())

    def _pop_scope(self) -> None:
        if len(self._locals_stack) > 1:
            self._locals_stack.pop()

    def _declare_local(self, name: str) -> None:
        self._locals_stack[-1].add(name)

    def _is_local(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self._locals_stack))

    def _maybe_capture(self, name: str) -> None:
        if self._is_local(name):
            return
        if name in self.outer_locals and name not in self.captures:
            self.captures.append(name)

    def _visit_statement(self, stmt: IrStatement) -> None:
        if isinstance(stmt, IrVariableDeclaration):
            self._declare_local(stmt.name)
            if stmt.initializer is not None:
                self._visit_expr(stmt.initializer)
            return
        if isinstance(stmt, IrExpressionStatement):
            self._visit_expr(stmt.expression)
            return
        if isinstance(stmt, IrReturn):
            if stmt.value is not None:
                self._visit_expr(stmt.value)
            return
        if isinstance(stmt, IrIf):
            self._visit_expr(stmt.condition)
            self._push_scope()
            for inner in stmt.then_branch:
                self._visit_statement(inner)
            self._pop_scope()
            self._push_scope()
            for inner in stmt.else_branch:
                self._visit_statement(inner)
            self._pop_scope()
            return
        if isinstance(stmt, IrWhile):
            self._visit_expr(stmt.condition)
            self._push_scope()
            for inner in stmt.body:
                self._visit_statement(inner)
            self._pop_scope()
            return
        if isinstance(stmt, IrForIn):
            self._visit_expr(stmt.iterable)
            self._push_scope()
            self._declare_local(stmt.target.name)
            for inner in stmt.body:
                self._visit_statement(inner)
            self._pop_scope()
            return

    def _visit_expr(self, expr: Optional[IrExpr]) -> None:
        if expr is None:
            return
        if isinstance(expr, IrIdentifier):
            self._maybe_capture(expr.name)
            return
        if isinstance(expr, IrLiteral):
            return
        if isinstance(expr, IrUnary):
            self._visit_expr(expr.operand)
            return
        if isinstance(expr, IrBinary):
            self._visit_expr(expr.left)
            self._visit_expr(expr.right)
            return
        if isinstance(expr, IrAssignment):
            self._visit_expr(expr.target)
            self._visit_expr(expr.value)
            return
        if isinstance(expr, IrConditional):
            self._visit_expr(expr.condition)
            self._visit_expr(expr.consequent)
            self._visit_expr(expr.alternate)
            return
        if isinstance(expr, IrCall):
            self._visit_expr(expr.callee)
            for arg in expr.arguments:
                self._visit_expr(arg)
            return
        if isinstance(expr, IrMemberAccess):
            self._visit_expr(expr.object)
            return
        if isinstance(expr, IrIndex):
            self._visit_expr(expr.collection)
            self._visit_expr(expr.index)
            return
        if isinstance(expr, IrArrayLiteral):
            for element in expr.elements:
                self._visit_expr(element)
            return
        if isinstance(expr, IrObjectLiteral):
            for prop in expr.properties:
                self._visit_expr(prop.value)
            return
        if isinstance(expr, IrLambda):
            self._push_scope()
            for param in expr.parameters:
                self._declare_local(param.name)
                if param.default_value is not None:
                    self._visit_expr(param.default_value)
            for stmt in expr.body_statements:
                self._visit_statement(stmt)
            if expr.body_expression is not None:
                self._visit_expr(expr.body_expression)
            self._pop_scope()
            return

@dataclass(slots=True)
class Value:
    name: str
    type: LLVMTypeInfo
