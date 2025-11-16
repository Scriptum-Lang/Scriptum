from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from .. import builtins, errors
from ..text import Span
from .ir import (
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
    IrForTarget,
    IrFunction,
    IrIdentifier,
    IrIf,
    IrIndex,
    IrLambda,
    IrLiteral,
    IrMemberAccess,
    IrModule,
    IrObjectLiteral,
    IrObjectProperty,
    IrParameter,
    IrReturn,
    IrStatement,
    IrUnary,
    IrVariable,
    IrVariableDeclaration,
    IrWhile,
    ModuleIr,
)


@dataclass(slots=True)
class ExecutionResult:
    value: Any


@dataclass(slots=True)
class RuntimeBinding:
    mutable: bool
    value: Any
    span: Optional[Span] = None


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self.bindings: dict[str, RuntimeBinding] = {}

    def declare(self, name: str, value: Any, mutable: bool, *, span: Optional[Span] = None) -> None:
        if name in self.bindings:
            raise errors.ExecutionError("IR001", f"Name '{name}' already declared in current scope.", span)
        self.bindings[name] = RuntimeBinding(mutable=mutable, value=value, span=span)

    def assign(self, name: str, value: Any, *, span: Optional[Span] = None) -> None:
        env = self._resolve(name, span=span)
        binding = env.bindings[name]
        if not binding.mutable:
            raise errors.ExecutionError("IR002", f"Cannot assign to immutable binding '{name}'.", span or binding.span)
        binding.value = value

    def get(self, name: str, *, span: Optional[Span] = None) -> Any:
        env = self._resolve(name, span=span)
        return env.bindings[name].value

    def _resolve(self, name: str, *, span: Optional[Span] = None) -> "Environment":
        env: Optional[Environment] = self
        while env is not None:
            if name in env.bindings:
                return env
            env = env.parent
        raise errors.ExecutionError("IR003", f"Name '{name}' is not defined.", span)


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


@dataclass(slots=True)
class RuntimeFunction:
    ir_function: IrFunction
    closure: Environment

    def call(self, interpreter: "Interpreter", args: List[Any], span: Optional[Span] = None) -> Any:
        return interpreter._invoke_function(self, args, span=span)


@dataclass(slots=True)
class RuntimeLambda:
    parameters: List[IrParameter]
    body_statements: List[IrStatement]
    body_expression: Optional[IrExpr]
    closure: Environment

    def call(self, interpreter: "Interpreter", args: List[Any], span: Optional[Span] = None) -> Any:
        return interpreter._invoke_lambda(self, args, span=span)


@dataclass(slots=True)
class RuntimeBuiltinFunction:
    spec: builtins.BuiltinFunctionSpec

    def call(self, interpreter: "Interpreter", args: List[Any], span: Optional[Span] = None) -> Any:
        try:
            normalized = self.spec.prepare_arguments(args)
            return self.spec.implementation(interpreter, normalized)
        except errors.ExecutionError as exc:
            if exc.span is None:
                exc.span = span
            raise


@dataclass(slots=True)
class RuntimeBuiltinMethod:
    spec: builtins.BuiltinMethodSpec
    receiver: Any

    def call(self, interpreter: "Interpreter", args: List[Any], span: Optional[Span] = None) -> Any:
        try:
            normalized = self.spec.prepare_runtime_arguments(args)
            return self.spec.implementation(self.receiver, normalized)
        except errors.ExecutionError as exc:
            if exc.span is None:
                exc.span = span
            raise


class Interpreter:
    def __init__(self, module: ModuleIr) -> None:
        self.module = module
        self.global_env = Environment()

    def execute(self, entry_point: str = "main") -> ExecutionResult:
        self._register_builtins()
        self._register_functions()
        self._initialize_globals()
        if entry_point not in self.global_env.bindings:
            module_span = getattr(self.module, "span", None)
            raise errors.ExecutionError("IR010", f"Entry point '{entry_point}' not found.", module_span)
        binding = self.global_env.bindings[entry_point]
        func = binding.value
        if not hasattr(func, "call"):
            raise errors.ExecutionError("IR011", f"Entry point '{entry_point}' is not callable.", binding.span)
        value = func.call(self, [])
        return ExecutionResult(value=value)

    # Preparation --------------------------------------------------------------

    def _register_builtins(self) -> None:
        for spec in builtins.GLOBAL_FUNCTIONS.values():
            self.global_env.declare(spec.name, RuntimeBuiltinFunction(spec=spec), mutable=False)

    def _register_functions(self) -> None:
        for func in self.module.functions:
            runtime_fn = RuntimeFunction(ir_function=func, closure=self.global_env)
            self.global_env.declare(func.name, runtime_fn, mutable=False, span=func.span)

    def _initialize_globals(self) -> None:
        for var in self.module.globals:
            value = None
            if var.initializer is not None:
                value = self._evaluate_expression(var.initializer, self.global_env)
            self.global_env.declare(var.name, value, mutable=var.mutable, span=var.span)

    # Function invocation -----------------------------------------------------

    def _invoke_function(self, runtime_fn: RuntimeFunction, args: List[Any], span: Optional[Span] = None) -> Any:
        func = runtime_fn.ir_function
        call_env = Environment(parent=runtime_fn.closure)
        evaluated_args = self._bind_parameters(func.parameters, args, runtime_fn.closure, call_span=span)
        for (param, value) in evaluated_args:
            call_env.declare(param.name, value, mutable=False, span=param.span)
        try:
            self._execute_statements(func.body, call_env)
        except ReturnSignal as signal:
            return signal.value
        return None

    def _invoke_lambda(self, runtime_lambda: RuntimeLambda, args: List[Any], span: Optional[Span] = None) -> Any:
        call_env = Environment(parent=runtime_lambda.closure)
        evaluated_args = self._bind_parameters(runtime_lambda.parameters, args, runtime_lambda.closure, call_span=span)
        for (param, value) in evaluated_args:
            call_env.declare(param.name, value, mutable=False, span=param.span)
        try:
            if runtime_lambda.body_expression is not None:
                value = self._evaluate_expression(runtime_lambda.body_expression, call_env)
                raise ReturnSignal(value)
            self._execute_statements(runtime_lambda.body_statements, call_env)
        except ReturnSignal as signal:
            return signal.value
        return None

    def _bind_parameters(
        self,
        parameters: List[IrParameter],
        args: List[Any],
        closure: Environment,
        call_span: Optional[Span] = None,
    ) -> List[tuple[IrParameter, Any]]:
        if len(args) > len(parameters):
            raise errors.ExecutionError("IR020", "Too many arguments supplied.", call_span)
        result: List[tuple[IrParameter, Any]] = []
        for idx, param in enumerate(parameters):
            if idx < len(args):
                result.append((param, args[idx]))
            elif param.default_value is not None:
                default_value = self._evaluate_expression(param.default_value, closure)
                result.append((param, default_value))
            else:
                raise errors.ExecutionError("IR021", f"Missing argument for parameter '{param.name}'.", call_span)
        return result

    # Statement execution -----------------------------------------------------

    def _execute_statements(self, statements: List[IrStatement], env: Environment) -> None:
        for stmt in statements:
            self._execute_statement(stmt, env)

    def _execute_statement(self, stmt: IrStatement, env: Environment) -> None:
        if isinstance(stmt, IrVariableDeclaration):
            value = None
            if stmt.initializer is not None:
                value = self._evaluate_expression(stmt.initializer, env)
            env.declare(stmt.name, value, mutable=stmt.mutable, span=stmt.span)
            return

        if isinstance(stmt, IrExpressionStatement):
            self._evaluate_expression(stmt.expression, env)
            return

        if isinstance(stmt, IrReturn):
            value = None
            if stmt.value is not None:
                value = self._evaluate_expression(stmt.value, env)
            raise ReturnSignal(value)

        if isinstance(stmt, IrIf):
            condition = self._truthy(self._evaluate_expression(stmt.condition, env))
            branch = stmt.then_branch if condition else stmt.else_branch
            branch_env = Environment(parent=env)
            self._execute_statements(branch, branch_env)
            return

        if isinstance(stmt, IrWhile):
            while self._truthy(self._evaluate_expression(stmt.condition, env)):
                loop_env = Environment(parent=env)
                try:
                    self._execute_statements(stmt.body, loop_env)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return

        if isinstance(stmt, IrForIn):
            iterable_value = self._evaluate_expression(stmt.iterable, env)
            elements = list(self._ensure_iterable(iterable_value, span=stmt.iterable.span))
            loop_env = Environment(parent=env)
            loop_env.declare(stmt.target.name, None, mutable=True, span=stmt.target.span)
            for element in elements:
                loop_env.assign(stmt.target.name, element, span=stmt.target.span)
                iteration_env = Environment(parent=loop_env)
                try:
                    self._execute_statements(stmt.body, iteration_env)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return

        if isinstance(stmt, IrBreak):
            raise BreakSignal()

        if isinstance(stmt, IrContinue):
            raise ContinueSignal()

        raise errors.ExecutionError("IR030", f"Unsupported statement type: {type(stmt).__name__}", stmt.span)

    # Expression evaluation ---------------------------------------------------

    def _evaluate_expression(self, expr: IrExpr, env: Environment) -> Any:
        if isinstance(expr, IrIdentifier):
            return env.get(expr.name, span=expr.span)

        if isinstance(expr, IrLiteral):
            return expr.value

        if isinstance(expr, IrUnary):
            operand = self._evaluate_expression(expr.operand, env)
            if expr.operator == "NEGATE" or expr.operator == "-":
                return -operand
            if expr.operator == "POSITIVE" or expr.operator == "+":
                return +operand
            if expr.operator == "NOT" or expr.operator == "!":
                return not self._truthy(operand)
            raise errors.ExecutionError("IR040", f"Unknown unary operator '{expr.operator}'.", expr.span)

        if isinstance(expr, IrBinary):
            return self._evaluate_binary(expr, env)

        if isinstance(expr, IrAssignment):
            if not isinstance(expr.target, IrIdentifier):
                raise errors.ExecutionError("IR041", "Only identifier assignments are supported.", expr.span)
            value = self._evaluate_expression(expr.value, env)
            env.assign(expr.target.name, value, span=expr.span)
            return value

        if isinstance(expr, IrConditional):
            condition = self._truthy(self._evaluate_expression(expr.condition, env))
            branch = expr.consequent if condition else expr.alternate
            return self._evaluate_expression(branch, env)

        if isinstance(expr, IrCall):
            callee = self._evaluate_expression(expr.callee, env)
            arguments = [self._evaluate_expression(arg, env) for arg in expr.arguments]
            try:
                return self.invoke_callable(callee, arguments, span=expr.span)
            except errors.ExecutionError as exc:
                if exc.span is None:
                    exc.span = expr.span
                raise

        if isinstance(expr, IrMemberAccess):
            obj = self._evaluate_expression(expr.object, env)
            if isinstance(obj, dict):
                return obj.get(expr.property)
            bound_method = self._bind_builtin_method(obj, expr.property)
            if bound_method is not None:
                return bound_method
            raise errors.ExecutionError(
                "IR050",
                "Member access requires an object literal or builtin-compatible value.",
                expr.span,
            )

        if isinstance(expr, IrIndex):
            collection = self._evaluate_expression(expr.collection, env)
            index = self._evaluate_expression(expr.index, env)
            try:
                return collection[index]
            except Exception as exc:  # pragma: no cover - safe guard
                raise errors.ExecutionError("IR051", "Index operation failed.", expr.span) from exc

        if isinstance(expr, IrArrayLiteral):
            return [self._evaluate_expression(elem, env) for elem in expr.elements]

        if isinstance(expr, IrObjectLiteral):
            return {
                prop.key: self._evaluate_expression(prop.value, env)
                for prop in expr.properties
            }

        if isinstance(expr, IrLambda):
            return RuntimeLambda(
                parameters=expr.parameters,
                body_statements=expr.body_statements,
                body_expression=expr.body_expression,
                closure=env,
            )

        raise errors.ExecutionError("IR060", f"Unsupported expression type: {type(expr).__name__}", expr.span)

    def invoke_callable(self, callee: Any, args: List[Any], span: Optional[Span] = None) -> Any:
        if hasattr(callee, "call"):
            return callee.call(self, args, span=span)
        raise errors.ExecutionError("IR061", "Attempted to call a non-callable value.", span)

    def _evaluate_binary(self, expr: IrBinary, env: Environment) -> Any:
        op = expr.operator

        if op in {"OR", "||"}:
            left = self._truthy(self._evaluate_expression(expr.left, env))
            if left:
                return True
            return self._truthy(self._evaluate_expression(expr.right, env))

        if op in {"AND", "&&"}:
            left = self._truthy(self._evaluate_expression(expr.left, env))
            if not left:
                return False
            return self._truthy(self._evaluate_expression(expr.right, env))

        if op in {"NULLISH", "??"}:
            left_val = self._evaluate_expression(expr.left, env)
            if left_val is not None:
                return left_val
            return self._evaluate_expression(expr.right, env)

        left = self._evaluate_expression(expr.left, env)
        right = self._evaluate_expression(expr.right, env)

        mapping = {
            "ADD": lambda a, b: a + b,
            "+": lambda a, b: a + b,
            "SUB": lambda a, b: a - b,
            "-": lambda a, b: a - b,
            "MUL": lambda a, b: a * b,
            "*": lambda a, b: a * b,
            "DIV": lambda a, b: a / b,
            "/": lambda a, b: a / b,
            "MOD": lambda a, b: a % b,
            "%": lambda a, b: a % b,
            "POW": lambda a, b: a ** b,
            "**": lambda a, b: a ** b,
            "GT": lambda a, b: a > b,
            ">": lambda a, b: a > b,
            "GE": lambda a, b: a >= b,
            ">=": lambda a, b: a >= b,
            "LT": lambda a, b: a < b,
            "<": lambda a, b: a < b,
            "LE": lambda a, b: a <= b,
            "<=": lambda a, b: a <= b,
            "EQ": lambda a, b: a == b,
            "==": lambda a, b: a == b,
            "NE": lambda a, b: a != b,
            "!=": lambda a, b: a != b,
            "STRICT_EQ": lambda a, b: a == b,
            "===": lambda a, b: a == b,
            "STRICT_NE": lambda a, b: a != b,
            "!==": lambda a, b: a != b,
        }

        if op not in mapping:
            raise errors.ExecutionError("IR070", f"Unsupported binary operator '{op}'.", expr.span)
        return mapping[op](left, right)

    # Helpers -----------------------------------------------------------------

    def _truthy(self, value: Any) -> bool:
        return bool(value)

    def _ensure_iterable(self, value: Any, span: Optional[Span] = None) -> Iterable[Any]:
        if isinstance(value, (list, tuple)):
            return value
        raise errors.ExecutionError("IR080", "Value is not iterable for 'pro' loop.", span)

    def _bind_builtin_method(self, value: Any, property_name: str) -> Optional[RuntimeBuiltinMethod]:
        if isinstance(value, list):
            spec = builtins.ARRAY_METHODS.get(property_name)
            if spec:
                return RuntimeBuiltinMethod(spec=spec, receiver=value)
        if isinstance(value, str):
            spec = builtins.TEXT_METHODS.get(property_name)
            if spec:
                return RuntimeBuiltinMethod(spec=spec, receiver=value)
        return None
