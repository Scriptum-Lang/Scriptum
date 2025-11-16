"""Registry and runtime implementation of Scriptum builtin functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import errors
from .sema import types

_MISSING = object()

NUM = types.PRIMITIVE_TYPES["numerus"]
TEXT = types.PRIMITIVE_TYPES["textus"]
BOOL = types.PRIMITIVE_TYPES["booleanum"]
VOID = types.PRIMITIVE_TYPES["vacuum"]
ANY = types.PRIMITIVE_TYPES["quodlibet"]
NULL = types.PRIMITIVE_TYPES["nullum"]


def array_of(element: types.Type) -> types.Type:
    return types.Type(types.TypeKind.ARRAY, element=element)


def function_of(params: List[types.Type], return_type: types.Type) -> types.Type:
    return types.function_type(params, return_type)


@dataclass(slots=True)
class BuiltinParameter:
    type: types.Type
    optional: bool = False
    default: Any = _MISSING
    allowed_kinds: Optional[Tuple[types.TypeKind, ...]] = None

    def has_default(self) -> bool:
        return self.default is not _MISSING


@dataclass(slots=True)
class BuiltinFunctionSpec:
    name: str
    parameters: List[BuiltinParameter]
    return_type: types.Type
    implementation: Callable[["RuntimeContext", List[Any]], Any]
    variadic: bool = False
    variadic_type: Optional[types.Type] = None
    doc: str = ""

    def min_arity(self) -> int:
        return sum(1 for param in self.parameters if not param.optional)

    def max_arity(self) -> Optional[int]:
        return None if self.variadic else len(self.parameters)

    def prepare_arguments(self, args: List[Any]) -> List[Any]:
        """Validate arity and append defaults for optional parameters."""

        min_args = self.min_arity()
        max_args = self.max_arity()
        if len(args) < min_args:
            raise errors.ExecutionError(
                "IR200",
                f"{self.name}() expects at least {min_args} argumento(s), recebeu {len(args)}.",
            )
        if max_args is not None and len(args) > max_args:
            raise errors.ExecutionError(
                "IR201",
                f"{self.name}() aceita no máximo {max_args} argumento(s), recebeu {len(args)}.",
            )
        normalized = list(args)
        if not self.variadic:
            for index, param in enumerate(self.parameters):
                if index < len(normalized):
                    continue
                if param.has_default():
                    normalized.append(param.default)
        return normalized


@dataclass(slots=True)
class MethodParameterSpec:
    type_factory: Callable[[types.Type], types.Type]
    optional: bool = False
    default: Any = _MISSING


@dataclass(slots=True)
class BuiltinMethodSpec:
    name: str
    receiver_kind: types.TypeKind
    parameters: List[MethodParameterSpec]
    return_type_factory: Callable[[types.Type], types.Type]
    implementation: Callable[[Any, List[Any]], Any]
    doc: str = ""

    def min_arity(self) -> int:
        return sum(1 for param in self.parameters if not param.optional)

    def prepare_runtime_arguments(self, args: List[Any]) -> List[Any]:
        min_args = self.min_arity()
        max_args = len(self.parameters)
        if len(args) < min_args:
            raise errors.ExecutionError(
                "IR210",
                f"{self.name}() espera ao menos {min_args} argumento(s), recebeu {len(args)}.",
            )
        if len(args) > max_args:
            raise errors.ExecutionError(
                "IR211",
                f"{self.name}() aceita no máximo {max_args} argumento(s), recebeu {len(args)}.",
            )
        normalized = list(args)
        for index, param in enumerate(self.parameters):
            if index < len(normalized):
                continue
            if param.default is not _MISSING:
                normalized.append(param.default)
        return normalized

    def bind(self, receiver_type: types.Type) -> "MethodBinding":
        params = [
            BuiltinParameter(
                type=param.type_factory(receiver_type),
                optional=param.optional,
                default=param.default,
            )
            for param in self.parameters
        ]
        return_type = self.return_type_factory(receiver_type)
        return MethodBinding(spec=self, receiver_type=receiver_type, parameters=params, return_type=return_type)


@dataclass(slots=True)
class MethodBinding:
    spec: BuiltinMethodSpec
    receiver_type: types.Type
    parameters: List[BuiltinParameter]
    return_type: types.Type


RuntimeContext = Any


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "nullum"
    if value is True:
        return "verum"
    if value is False:
        return "falsum"
    return str(value)


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, dict, set)) and not value:
        return False
    if isinstance(value, str):
        return value != ""
    return bool(value)


def _to_number(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text_value = value.strip()
        if not text_value:
            raise errors.ExecutionError("IR220", "textus vazio não pode ser convertido em numerus.")
        try:
            return int(text_value, 10)
        except ValueError as exc:
            raise errors.ExecutionError("IR220", f"'{value}' não é um numerus válido.") from exc
    raise errors.ExecutionError("IR220", "Valor não pode ser convertido para numerus.")


def _ensure_list(value: Any, name: str) -> List[Any]:
    if not isinstance(value, list):
        raise errors.ExecutionError("IR230", f"{name} espera um array.")
    return value


def _ensure_text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise errors.ExecutionError("IR231", f"{name} espera um textus.")
    return value


def _ensure_callable(interpreter: RuntimeContext, value: Any, name: str) -> Any:
    if hasattr(value, "call"):
        return value
    raise errors.ExecutionError("IR232", f"{name} espera uma functio.")


def _builtin_scribe(_: RuntimeContext, args: List[Any]) -> None:
    as_text = [_to_text(value) for value in args]
    print(" ".join(as_text))


def _builtin_longitudo(_: RuntimeContext, args: List[Any]) -> int:
    target = args[0]
    if isinstance(target, str):
        return len(target)
    if isinstance(target, list):
        return len(target)
    raise errors.ExecutionError("IR233", "longitudo aceita apenas textus ou arrays.")


def _builtin_numerus(_: RuntimeContext, args: List[Any]) -> int:
    return _to_number(args[0])


def _builtin_textus(_: RuntimeContext, args: List[Any]) -> str:
    return _to_text(args[0])


def _builtin_booleanum(_: RuntimeContext, args: List[Any]) -> bool:
    return _truthy(args[0])


def _builtin_ambitus(_: RuntimeContext, args: List[Any]) -> List[int]:
    start, end = args[0], args[1]
    step = args[2] if len(args) > 2 else 1
    start_i = _to_number(start)
    end_i = _to_number(end)
    step_i = _to_number(step)
    if step_i == 0:
        raise errors.ExecutionError("IR234", "ambitus requer passus diferente de zero.")
    sequence: List[int] = []
    current = start_i
    if step_i > 0:
        while current < end_i:
            sequence.append(current)
            current += step_i
    else:
        while current > end_i:
            sequence.append(current)
            current += step_i
    return sequence


def _builtin_summa(_: RuntimeContext, args: List[Any]) -> int:
    values = _ensure_list(args[0], "summa")
    total = 0
    for value in values:
        total += _to_number(value)
    return total


def _builtin_minimum(_: RuntimeContext, args: List[Any]) -> int:
    values = _ensure_list(args[0], "minimum")
    if not values:
        raise errors.ExecutionError("IR235", "minimum requer um array não vazio.")
    return min(_to_number(value) for value in values)


def _builtin_maximum(_: RuntimeContext, args: List[Any]) -> int:
    values = _ensure_list(args[0], "maximum")
    if not values:
        raise errors.ExecutionError("IR236", "maximum requer um array não vazio.")
    return max(_to_number(value) for value in values)


def _builtin_absolutum(_: RuntimeContext, args: List[Any]) -> int:
    return abs(_to_number(args[0]))


def _builtin_aliquod(_: RuntimeContext, args: List[Any]) -> bool:
    values = _ensure_list(args[0], "aliquod")
    return any(_truthy(value) for value in values)


def _builtin_omnia(_: RuntimeContext, args: List[Any]) -> bool:
    values = _ensure_list(args[0], "omnia")
    return bool(values) and all(_truthy(value) for value in values)


_input_provider: Callable[[str], str] = input


def set_input_provider(provider: Callable[[str], str]) -> None:
    """Override the input provider used by lege()."""

    global _input_provider
    _input_provider = provider


def reset_input_provider() -> None:
    """Restore the default input provider."""

    global _input_provider
    _input_provider = input


def _builtin_lege(_: RuntimeContext, args: List[Any]) -> str:
    prompt = _ensure_text(args[0], "lege")
    if prompt:
        print(prompt, end="", flush=True)
    line = _input_provider(prompt)
    if line.endswith("\n"):
        return line[:-1]
    return line


def _builtin_enumera(_: RuntimeContext, args: List[Any]) -> List[List[Any]]:
    values = _ensure_list(args[0], "enumera")
    return [[index, value] for index, value in enumerate(values)]


def _builtin_zip(_: RuntimeContext, args: List[Any]) -> List[List[Any]]:
    left = _ensure_list(args[0], "coniunge")
    right = _ensure_list(args[1], "coniunge")
    limit = min(len(left), len(right))
    return [[left[i], right[i]] for i in range(limit)]


def _builtin_applica(interpreter: RuntimeContext, args: List[Any]) -> List[Any]:
    values = _ensure_list(args[0], "applica")
    func = _ensure_callable(interpreter, args[1], "applica")
    result = []
    for value in values:
        result.append(interpreter.invoke_callable(func, [value]))
    return result


def _builtin_filtra(interpreter: RuntimeContext, args: List[Any]) -> List[Any]:
    values = _ensure_list(args[0], "filtra")
    func = _ensure_callable(interpreter, args[1], "filtra")
    result = []
    for value in values:
        decision = interpreter.invoke_callable(func, [value])
        if _truthy(decision):
            result.append(value)
    return result


def _builtin_ordina(interpreter: RuntimeContext, args: List[Any]) -> List[Any]:
    values = list(_ensure_list(args[0], "ordina"))
    key_callable = args[1]
    reverse_flag = bool(args[2])

    if key_callable is None:
        return sorted(values, reverse=reverse_flag)

    func = _ensure_callable(interpreter, key_callable, "ordina")
    decorated: List[Tuple[Any, int, Any]] = []
    for index, value in enumerate(values):
        key = interpreter.invoke_callable(func, [value])
        decorated.append((key, index, value))
    decorated.sort(reverse=reverse_flag)
    return [value for _, _, value in decorated]


def _array_adde(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> None:
    receiver.append(args[0])


def _array_exime(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> Any:
    if not receiver:
        raise errors.ExecutionError("IR237", "exime() em array vazio.")
    return receiver.pop()


def _array_extende(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> None:
    other = _ensure_list(args[0], "extende")
    receiver.extend(other)


def _array_inserta(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> None:
    index = _to_number(args[0])
    value = args[1]
    if index < 0:
        insert_at = 0
    elif index > len(receiver):
        insert_at = len(receiver)
    else:
        insert_at = index
    receiver.insert(insert_at, value)


def _array_remove(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> None:
    value = args[0]
    for idx, current in enumerate(receiver):
        if current == value:
            receiver.pop(idx)
            return
    raise errors.ExecutionError("IR238", "Valor não encontrado em remove().")


def _array_purga(_: RuntimeContext, receiver: List[Any], args: List[Any]) -> None:
    receiver.clear()


def _text_divide(_: RuntimeContext, text_value: str, args: List[Any]) -> List[str]:
    separator = _ensure_text(args[0], "divide")
    if separator == "":
        raise errors.ExecutionError("IR239", "divide() requer separador não vazio.")
    return text_value.split(separator)


def _text_join(_: RuntimeContext, text_value: str, args: List[Any]) -> str:
    parts = _ensure_list(args[0], "coniunge")
    normalized = [_ensure_text(part, "coniunge") for part in parts]
    return text_value.join(normalized)


def _text_replace(_: RuntimeContext, text_value: str, args: List[Any]) -> str:
    old = _ensure_text(args[0], "substitue")
    new = _ensure_text(args[1], "substitue")
    return text_value.replace(old, new)


def _text_lower(_: RuntimeContext, text_value: str, args: List[Any]) -> str:
    return text_value.lower()


def _text_upper(_: RuntimeContext, text_value: str, args: List[Any]) -> str:
    return text_value.upper()


def _text_strip(_: RuntimeContext, text_value: str, args: List[Any]) -> str:
    return text_value.strip()


GLOBAL_FUNCTIONS: Dict[str, BuiltinFunctionSpec] = {
    "scribe": BuiltinFunctionSpec(
        name="scribe",
        parameters=[],
        return_type=VOID,
        implementation=_builtin_scribe,
        variadic=True,
        variadic_type=ANY,
        doc="Imprime os argumentos convertidos para texto separados por espaço.",
    ),
    "longitudo": BuiltinFunctionSpec(
        name="longitudo",
        parameters=[
            BuiltinParameter(
                type=ANY,
                allowed_kinds=(types.TypeKind.TEXTUS, types.TypeKind.ARRAY),
            )
        ],
        return_type=NUM,
        implementation=_builtin_longitudo,
        doc="Retorna o tamanho de um textus ou array.",
    ),
    "numerus": BuiltinFunctionSpec(
        name="numerus",
        parameters=[BuiltinParameter(type=ANY)],
        return_type=NUM,
        implementation=_builtin_numerus,
        doc="Converte valores em numerus.",
    ),
    "textus": BuiltinFunctionSpec(
        name="textus",
        parameters=[BuiltinParameter(type=ANY)],
        return_type=TEXT,
        implementation=_builtin_textus,
        doc="Converte valores em textus.",
    ),
    "booleanum": BuiltinFunctionSpec(
        name="booleanum",
        parameters=[BuiltinParameter(type=ANY)],
        return_type=BOOL,
        implementation=_builtin_booleanum,
        doc="Converte valores para booleanum seguindo a convenção Pythonica.",
    ),
    "ambitus": BuiltinFunctionSpec(
        name="ambitus",
        parameters=[
            BuiltinParameter(type=NUM),
            BuiltinParameter(type=NUM),
            BuiltinParameter(type=NUM, optional=True, default=1),
        ],
        return_type=array_of(NUM),
        implementation=_builtin_ambitus,
        doc="Gera uma sequência de numerus semelhante a range().",
    ),
    "summa": BuiltinFunctionSpec(
        name="summa",
        parameters=[BuiltinParameter(type=array_of(NUM))],
        return_type=NUM,
        implementation=_builtin_summa,
        doc="Soma todos os valores num array numérico.",
    ),
    "minimum": BuiltinFunctionSpec(
        name="minimum",
        parameters=[BuiltinParameter(type=array_of(NUM))],
        return_type=NUM,
        implementation=_builtin_minimum,
        doc="Retorna o menor numerus de um array.",
    ),
    "maximum": BuiltinFunctionSpec(
        name="maximum",
        parameters=[BuiltinParameter(type=array_of(NUM))],
        return_type=NUM,
        implementation=_builtin_maximum,
        doc="Retorna o maior numerus de um array.",
    ),
    "absolutum": BuiltinFunctionSpec(
        name="absolutum",
        parameters=[BuiltinParameter(type=NUM)],
        return_type=NUM,
        implementation=_builtin_absolutum,
        doc="Valor absoluto de numerus.",
    ),
    "aliquod": BuiltinFunctionSpec(
        name="aliquod",
        parameters=[BuiltinParameter(type=array_of(BOOL))],
        return_type=BOOL,
        implementation=_builtin_aliquod,
        doc="Retorna verum se algum valor no array booleano for verum.",
    ),
    "omnia": BuiltinFunctionSpec(
        name="omnia",
        parameters=[BuiltinParameter(type=array_of(BOOL))],
        return_type=BOOL,
        implementation=_builtin_omnia,
        doc="Retorna verum se todos os valores do array forem verum e o array não estiver vazio.",
    ),
    "lege": BuiltinFunctionSpec(
        name="lege",
        parameters=[BuiltinParameter(type=TEXT, optional=True, default="")],
        return_type=TEXT,
        implementation=_builtin_lege,
        doc="Lê uma linha da entrada padrão após exibir opcionalmente um prompt.",
    ),
    "enumera": BuiltinFunctionSpec(
        name="enumera",
        parameters=[BuiltinParameter(type=array_of(ANY))],
        return_type=array_of(array_of(ANY)),
        implementation=_builtin_enumera,
        doc="Retorna pares [indice, valor] para cada elemento.",
    ),
    "coniunge": BuiltinFunctionSpec(
        name="coniunge",
        parameters=[BuiltinParameter(type=array_of(ANY)), BuiltinParameter(type=array_of(ANY))],
        return_type=array_of(array_of(ANY)),
        implementation=_builtin_zip,
        doc="Agrupa dois arrays até o menor tamanho.",
    ),
    "applica": BuiltinFunctionSpec(
        name="applica",
        parameters=[
            BuiltinParameter(type=array_of(ANY)),
            BuiltinParameter(type=function_of([ANY], ANY)),
        ],
        return_type=array_of(ANY),
        implementation=_builtin_applica,
        doc="Aplica uma função a cada elemento de um array.",
    ),
    "filtra": BuiltinFunctionSpec(
        name="filtra",
        parameters=[
            BuiltinParameter(type=array_of(ANY)),
            BuiltinParameter(type=function_of([ANY], BOOL)),
        ],
        return_type=array_of(ANY),
        implementation=_builtin_filtra,
        doc="Filtra elementos cujo predicado retorna verum.",
    ),
    "ordina": BuiltinFunctionSpec(
        name="ordina",
        parameters=[
            BuiltinParameter(type=array_of(ANY)),
            BuiltinParameter(type=types.Type(types.TypeKind.OPTIONAL, element=function_of([ANY], ANY)), optional=True, default=None),
            BuiltinParameter(type=BOOL, optional=True, default=False),
        ],
        return_type=array_of(ANY),
        implementation=_builtin_ordina,
        doc="Ordena uma cópia do array com chave opcional e modo decrescente.",
    ),
}


def _array_element(receiver_type: types.Type) -> types.Type:
    if receiver_type.kind is types.TypeKind.ARRAY and receiver_type.element:
        return receiver_type.element
    return ANY


ARRAY_METHODS: Dict[str, BuiltinMethodSpec] = {
    "adde": BuiltinMethodSpec(
        name="adde",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[
            MethodParameterSpec(type_factory=_array_element),
        ],
        return_type_factory=lambda _: VOID,
        implementation=lambda receiver, args: _array_adde(None, receiver, args),
        doc="Adiciona um elemento ao final do array.",
    ),
    "exime": BuiltinMethodSpec(
        name="exime",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[],
        return_type_factory=lambda receiver: _array_element(receiver),
        implementation=lambda receiver, args: _array_exime(None, receiver, args),
        doc="Remove e retorna o último elemento do array.",
    ),
    "extende": BuiltinMethodSpec(
        name="extende",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[MethodParameterSpec(type_factory=lambda _: array_of(ANY))],
        return_type_factory=lambda _: VOID,
        implementation=lambda receiver, args: _array_extende(None, receiver, args),
        doc="Concatena outro array ao final.",
    ),
    "inserta": BuiltinMethodSpec(
        name="inserta",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[
            MethodParameterSpec(type_factory=lambda _: NUM),
            MethodParameterSpec(type_factory=_array_element),
        ],
        return_type_factory=lambda _: VOID,
        implementation=lambda receiver, args: _array_inserta(None, receiver, args),
        doc="Insere um valor na posição indicada (índices fora do intervalo são ajustados).",
    ),
    "remove": BuiltinMethodSpec(
        name="remove",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[MethodParameterSpec(type_factory=_array_element)],
        return_type_factory=lambda _: VOID,
        implementation=lambda receiver, args: _array_remove(None, receiver, args),
        doc="Remove a primeira ocorrência do valor informado.",
    ),
    "purga": BuiltinMethodSpec(
        name="purga",
        receiver_kind=types.TypeKind.ARRAY,
        parameters=[],
        return_type_factory=lambda _: VOID,
        implementation=lambda receiver, args: _array_purga(None, receiver, args),
        doc="Esvazia o array.",
    ),
}


TEXT_METHODS: Dict[str, BuiltinMethodSpec] = {
    "divide": BuiltinMethodSpec(
        name="divide",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[MethodParameterSpec(type_factory=lambda _: TEXT, optional=True, default=" ")],
        return_type_factory=lambda _: array_of(TEXT),
        implementation=lambda receiver, args: _text_divide(None, receiver, args),
        doc="Divide o textus usando o separador (padrão espaço).",
    ),
    "coniunge": BuiltinMethodSpec(
        name="coniunge",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[MethodParameterSpec(type_factory=lambda _: array_of(TEXT))],
        return_type_factory=lambda _: TEXT,
        implementation=lambda receiver, args: _text_join(None, receiver, args),
        doc="Concatena os textus informados inserindo o receptor como separador.",
    ),
    "substitue": BuiltinMethodSpec(
        name="substitue",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[
            MethodParameterSpec(type_factory=lambda _: TEXT),
            MethodParameterSpec(type_factory=lambda _: TEXT),
        ],
        return_type_factory=lambda _: TEXT,
        implementation=lambda receiver, args: _text_replace(None, receiver, args),
        doc="Substitui todas as ocorrências do textus antigo pelo novo.",
    ),
    "ad_minusculas": BuiltinMethodSpec(
        name="ad_minusculas",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[],
        return_type_factory=lambda _: TEXT,
        implementation=lambda receiver, args: _text_lower(None, receiver, args),
        doc="Retorna o textus em minúsculas.",
    ),
    "ad_maiusculas": BuiltinMethodSpec(
        name="ad_maiusculas",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[],
        return_type_factory=lambda _: TEXT,
        implementation=lambda receiver, args: _text_upper(None, receiver, args),
        doc="Retorna o textus em maiúsculas.",
    ),
    "abscinde": BuiltinMethodSpec(
        name="abscinde",
        receiver_kind=types.TypeKind.TEXTUS,
        parameters=[],
        return_type_factory=lambda _: TEXT,
        implementation=lambda receiver, args: _text_strip(None, receiver, args),
        doc="Remove espaços em branco no início e final do textus.",
    ),
}


def array_method(name: str) -> Optional[BuiltinMethodSpec]:
    return ARRAY_METHODS.get(name)


def text_method(name: str) -> Optional[BuiltinMethodSpec]:
    return TEXT_METHODS.get(name)


__all__ = [
    "GLOBAL_FUNCTIONS",
    "ARRAY_METHODS",
    "TEXT_METHODS",
    "BuiltinFunctionSpec",
    "BuiltinMethodSpec",
    "BuiltinParameter",
    "MethodBinding",
    "array_method",
    "text_method",
    "set_input_provider",
    "reset_input_provider",
]
