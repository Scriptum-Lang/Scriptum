from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from .. import errors
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


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.parent = parent
        self.bindings: dict[str, RuntimeBinding] = {}

    def declare(self, name: str, value: Any, mutable: bool) -> None:
        if name in self.bindings:
            raise errors.ExecutionError(f"Name '{name}' already declared in current scope.")
        self.bindings[name] = RuntimeBinding(mutable=mutable, value=value)

    def assign(self, name: str, value: Any) -> None:
        env = self._resolve(name)
        binding = env.bindings[name]
        if not binding.mutable:
            raise errors.ExecutionError(f"Cannot assign to immutable binding '{name}'.")
        binding.value = value

    def get(self, name: str) -> Any:
        env = self._resolve(name)
        return env.bindings[name].value

    def _resolve(self, name: str) -> "Environment":
        env: Optional[Environment] = self
        while env is not None:
            if name in env.bindings:
                return env
            env = env.parent
        raise errors.ExecutionError(f"Name '{name}' is not defined.")


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

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        return interpreter._invoke_function(self, args)


@dataclass(slots=True)
class RuntimeLambda:
    parameters: List[IrParameter]
    body_statements: List[IrStatement]
    body_expression: Optional[IrExpr]
    closure: Environment

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        return interpreter._invoke_lambda(self, args)


class Interpreter:
    def __init__(self, module: ModuleIr) -> None:
        self.module = module
        self.global_env = Environment()

    def execute(self, entry_point: str = "main") -> ExecutionResult:
        self._register_functions()
        self._initialize_globals()
        if entry_point not in self.global_env.bindings:
            raise errors.ExecutionError(f"Entry point '{entry_point}' not found.")
        func = self.global_env.get(entry_point)
        if not hasattr(func, "call"):
            raise errors.ExecutionError(f"Entry point '{entry_point}' is not callable.")
        value = func.call(self, [])
        return ExecutionResult(value=value)

    # Preparation --------------------------------------------------------------

    def _register_functions(self) -> None:
        for func in self.module.functions:
            runtime_fn = RuntimeFunction(ir_function=func, closure=self.global_env)
            self.global_env.declare(func.name, runtime_fn, mutable=False)

    def _initialize_globals(self) -> None:
        for var in self.module.globals:
            value = None
            if var.initializer is not None:
                value = self._evaluate_expression(var.initializer, self.global_env)
            self.global_env.declare(var.name, value, mutable=var.mutable)

    # Function invocation -----------------------------------------------------

    def _invoke_function(self, runtime_fn: RuntimeFunction, args: List[Any]) -> Any:
        func = runtime_fn.ir_function
        call_env = Environment(parent=runtime_fn.closure)
        evaluated_args = self._bind_parameters(func.parameters, args, runtime_fn.closure)
        for (param, value) in evaluated_args:
            call_env.declare(param.name, value, mutable=False)
        try:
            self._execute_statements(func.body, call_env)
        except ReturnSignal as signal:
            return signal.value
        return None

    def _invoke_lambda(self, runtime_lambda: RuntimeLambda, args: List[Any]) -> Any:
        call_env = Environment(parent=runtime_lambda.closure)
        evaluated_args = self._bind_parameters(runtime_lambda.parameters, args, runtime_lambda.closure)
        for (param, value) in evaluated_args:
            call_env.declare(param.name, value, mutable=False)
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
    ) -> List[tuple[IrParameter, Any]]:
        if len(args) > len(parameters):
            raise errors.ExecutionError("Too many arguments supplied.")
        result: List[tuple[IrParameter, Any]] = []
        for idx, param in enumerate(parameters):
            if idx < len(args):
                result.append((param, args[idx]))
            elif param.default_value is not None:
                default_value = self._evaluate_expression(param.default_value, closure)
                result.append((param, default_value))
            else:
                raise errors.ExecutionError(f"Missing argument for parameter '{param.name}'.")
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
            env.declare(stmt.name, value, mutable=stmt.mutable)
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
            elements = list(self._ensure_iterable(iterable_value))
            loop_env = Environment(parent=env)
            loop_env.declare(stmt.target.name, None, mutable=stmt.target.mutable)
            for element in elements:
                loop_env.assign(stmt.target.name, element)
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

        raise errors.ExecutionError(f"Unsupported statement type: {type(stmt).__name__}")

    # Expression evaluation ---------------------------------------------------

    def _evaluate_expression(self, expr: IrExpr, env: Environment) -> Any:
        if isinstance(expr, IrIdentifier):
            return env.get(expr.name)

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
            raise errors.ExecutionError(f"Unknown unary operator '{expr.operator}'.")

        if isinstance(expr, IrBinary):
            return self._evaluate_binary(expr, env)

        if isinstance(expr, IrAssignment):
            if not isinstance(expr.target, IrIdentifier):
                raise errors.ExecutionError("Only identifier assignments are supported.")
            value = self._evaluate_expression(expr.value, env)
            env.assign(expr.target.name, value)
            return value

        if isinstance(expr, IrConditional):
            condition = self._truthy(self._evaluate_expression(expr.condition, env))
            branch = expr.consequent if condition else expr.alternate
            return self._evaluate_expression(branch, env)

        if isinstance(expr, IrCall):
            callee = self._evaluate_expression(expr.callee, env)
            arguments = [self._evaluate_expression(arg, env) for arg in expr.arguments]
            if hasattr(callee, "call"):
                return callee.call(self, arguments)
            raise errors.ExecutionError("Attempted to call a non-callable value.")

        if isinstance(expr, IrMemberAccess):
            obj = self._evaluate_expression(expr.object, env)
            if isinstance(obj, dict):
                return obj.get(expr.property)
            raise errors.ExecutionError("Member access requires an object literal.")

        if isinstance(expr, IrIndex):
            collection = self._evaluate_expression(expr.collection, env)
            index = self._evaluate_expression(expr.index, env)
            try:
                return collection[index]
            except Exception as exc:  # pragma: no cover - safe guard
                raise errors.ExecutionError("Index operation failed.") from exc

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

        raise errors.ExecutionError(f"Unsupported expression type: {type(expr).__name__}")

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
            raise errors.ExecutionError(f"Unsupported binary operator '{op}'.")
        return mapping[op](left, right)

    # Helpers -----------------------------------------------------------------

    def _truthy(self, value: Any) -> bool:
        return bool(value)

    def _ensure_iterable(self, value: Any) -> Iterable[Any]:
        if isinstance(value, (list, tuple)):
            return value
        raise errors.ExecutionError("Value is not iterable for 'pro' loop.")
