from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def runtime_lib(tmp_path_factory: pytest.TempPathFactory) -> ctypes.CDLL:
    cc = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if cc is None:
        pytest.skip("Compilador C não encontrado (cc/clang/gcc).")

    root = Path(__file__).resolve().parents[1]
    build_dir = tmp_path_factory.mktemp("scriptum_rt")
    lib_name = "libscriptum_rt.so"
    extra_flags: list[str] = ["-shared", "-std=c99", "-O2"]
    system = platform.system().lower()
    if "windows" in system or os.name == "nt":
        lib_name = "scriptum_rt.dll"
    else:
        extra_flags.append("-fPIC")
    lib_path = build_dir / lib_name
    cmd = [
        cc,
        *extra_flags,
        "-I",
        str(root / "src"),
        str(root / "src/scriptum/runtime/llvm_rt.c"),
        "-o",
        str(lib_path),
    ]
    subprocess.run(cmd, check=True, cwd=root)
    return ctypes.CDLL(str(lib_path))


class ScriptumValue(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_int),
        ("number", ctypes.c_double),
        ("boolean", ctypes.c_int32),
        ("_reserved", ctypes.c_uint32),
        ("payload", ctypes.c_void_p),
    ]


class ScriptumText(ctypes.Structure):
    _fields_ = [
        ("ref_count", ctypes.c_uint64),
        ("length", ctypes.c_uint64),
        ("data", ctypes.c_void_p),
    ]


class ScriptumArray(ctypes.Structure):
    _fields_ = [
        ("ref_count", ctypes.c_uint64),
        ("length", ctypes.c_uint64),
        ("capacity", ctypes.c_uint64),
        ("items", ctypes.POINTER(ScriptumValue)),
    ]


@pytest.fixture(scope="session", autouse=True)
def configure_runtime(runtime_lib: ctypes.CDLL) -> None:
    runtime_lib.scriptum_value_number.argtypes = [ctypes.c_double]
    runtime_lib.scriptum_value_number.restype = ScriptumValue

    runtime_lib.scriptum_value_boolean.argtypes = [ctypes.c_int32]
    runtime_lib.scriptum_value_boolean.restype = ScriptumValue

    runtime_lib.scriptum_text_new.argtypes = [ctypes.c_char_p, ctypes.c_uint64]
    runtime_lib.scriptum_text_new.restype = ctypes.POINTER(ScriptumText)

    runtime_lib.scriptum_text_concat.argtypes = [
        ctypes.POINTER(ScriptumText),
        ctypes.POINTER(ScriptumText),
    ]
    runtime_lib.scriptum_text_concat.restype = ctypes.POINTER(ScriptumText)
    runtime_lib.scriptum_text_release.argtypes = [ctypes.POINTER(ScriptumText)]

    runtime_lib.scriptum_array_new.argtypes = [ctypes.c_uint64]
    runtime_lib.scriptum_array_new.restype = ctypes.POINTER(ScriptumArray)
    runtime_lib.scriptum_array_push.argtypes = [
        ctypes.POINTER(ScriptumArray),
        ScriptumValue,
    ]
    runtime_lib.scriptum_array_len.argtypes = [ctypes.POINTER(ScriptumArray)]
    runtime_lib.scriptum_array_len.restype = ctypes.c_uint64
    runtime_lib.scriptum_array_get.argtypes = [
        ctypes.POINTER(ScriptumArray),
        ctypes.c_uint64,
        ctypes.POINTER(ScriptumValue),
    ]
    runtime_lib.scriptum_array_get.restype = ctypes.c_int
    runtime_lib.scriptum_array_release.argtypes = [ctypes.POINTER(ScriptumArray)]


def test_value_constructors(runtime_lib: ctypes.CDLL) -> None:
    val_num = runtime_lib.scriptum_value_number(42.5)
    assert val_num.kind == 1
    assert pytest.approx(val_num.number) == 42.5

    val_bool = runtime_lib.scriptum_value_boolean(1)
    assert val_bool.kind == 2
    assert val_bool.boolean == 1


def test_text_concat(runtime_lib: ctypes.CDLL) -> None:
    hello = runtime_lib.scriptum_text_new(b"salve", 5)
    world = runtime_lib.scriptum_text_new(b" mundo", 6)
    combined = runtime_lib.scriptum_text_concat(hello, world)
    assert combined.contents.length == 11
    data = ctypes.string_at(combined.contents.data, combined.contents.length)
    assert data == b"salve mundo"
    runtime_lib.scriptum_text_release(hello)
    runtime_lib.scriptum_text_release(world)
    runtime_lib.scriptum_text_release(combined)


def test_array_push_and_get(runtime_lib: ctypes.CDLL) -> None:
    array = runtime_lib.scriptum_array_new(0)
    runtime_lib.scriptum_array_push(array, runtime_lib.scriptum_value_number(1.0))
    runtime_lib.scriptum_array_push(array, runtime_lib.scriptum_value_number(2.0))
    runtime_lib.scriptum_array_push(array, runtime_lib.scriptum_value_boolean(0))
    assert runtime_lib.scriptum_array_len(array) == 3

    out = ScriptumValue()
    assert runtime_lib.scriptum_array_get(array, 1, ctypes.byref(out)) == 1
    assert pytest.approx(out.number) == 2.0

    assert runtime_lib.scriptum_array_get(array, 2, ctypes.byref(out)) == 1
    assert out.kind == 2  # boolean stored
    assert out.boolean == 0

    runtime_lib.scriptum_array_release(array)
