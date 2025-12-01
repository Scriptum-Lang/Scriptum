from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from ... import errors
from ...ast import nodes
from ...ir import ModuleIr, lower_module
from ...optimizations import LocalOptimizer
from ...sema.analyzer import SemanticAnalyzer


@dataclass(slots=True)
class LLVMCPPOutput:
    ir: ModuleIr
    text: str


class LLVMCPPBackendUnavailable(errors.CompilerError):
    code = "LLVMCPP001"


class LLVMCPPBackendError(errors.CompilerError):
    code = "LLVMCPP002"


_BINDING_NAME = "scriptum_codegen_llvm_cpp_py"
_BINDING_CACHE = None


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    env_override = os.environ.get("SCRIPTUM_LLVM_CPP_PATH")
    if env_override:
        for entry in env_override.split(os.pathsep):
            if entry:
                candidates.append(Path(entry))
    repo_root = Path(__file__).resolve().parents[4]
    build_root = repo_root / "cpp" / "llvm_codegen" / "build"
    candidates.append(build_root)
    candidates.append(build_root / "Release")
    candidates.append(build_root / "Debug")
    return candidates


def _load_binding():
    global _BINDING_CACHE
    if _BINDING_CACHE is not None:
        return _BINDING_CACHE
    try:
        _BINDING_CACHE = importlib.import_module(_BINDING_NAME)
        return _BINDING_CACHE
    except ModuleNotFoundError:
        pass

    for candidate in _candidate_paths():
        if not candidate.exists():
            continue
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.append(candidate_str)
        try:
            _BINDING_CACHE = importlib.import_module(_BINDING_NAME)
            return _BINDING_CACHE
        except ModuleNotFoundError:
            continue
    raise LLVMCPPBackendUnavailable(
        "Backend LLVM C++ indisponivel. Compile `cpp/llvm_codegen` e defina SCRIPTUM_LLVM_CPP_PATH se necessario."
    )


def generate_llvm_cpp(module: Union[ModuleIr, nodes.Module], *, module_name: str | None = None) -> LLVMCPPOutput:
    if isinstance(module, ModuleIr):
        ir_module = module
    else:
        analysis = SemanticAnalyzer().analyze(module)
        ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    optimizer = LocalOptimizer()
    optimized = optimizer.optimize(ir_module)
    binding = _load_binding()
    try:
        ir_text = binding.emit_module(optimized, module_name or "scriptum")
    except LLVMCPPBackendUnavailable:
        raise
    except Exception as exc:  # pragma: no cover - bridge errors become compiler errors
        raise LLVMCPPBackendError(str(exc)) from exc
    return LLVMCPPOutput(ir=optimized, text=ir_text)


__all__ = ["LLVMCPPOutput", "LLVMCPPBackendUnavailable", "LLVMCPPBackendError", "generate_llvm_cpp"]
