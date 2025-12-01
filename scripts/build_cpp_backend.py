#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _has_llvm() -> bool:
    return shutil.which("llvm-config") is not None or bool(os.environ.get("LLVM_DIR"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure/compile/test the LLVM C++ backend.")
    parser.add_argument(
        "--build-dir",
        default=Path("cpp") / "llvm_codegen" / "build",
        type=Path,
        help="Destino do diretório de build.",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Pular a execução dos testes do GoogleTest.")
    args = parser.parse_args()

    if not _has_llvm():
        print("LLVM_DIR/llvm-config não encontrados. Ignorando build do backend C++.")
        return 0

    cmake = shutil.which("cmake")
    if cmake is None:
        print("cmake não encontrado no PATH.", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    source_dir = repo_root / "cpp" / "llvm_codegen"
    build_dir = (repo_root / args.build_dir).resolve()
    build_dir.mkdir(parents=True, exist_ok=True)

    configure_cmd = [cmake, "-S", str(source_dir), "-B", str(build_dir)]
    build_lib_cmd = [cmake, "--build", str(build_dir), "--target", "scriptum_codegen_llvm_cpp_py"]
    build_tests_cmd = [cmake, "--build", str(build_dir), "--target", "scriptum_codegen_llvm_cpp_tests"]

    print(" ".join(configure_cmd))
    subprocess.run(configure_cmd, check=True)

    print(" ".join(build_lib_cmd))
    subprocess.run(build_lib_cmd, check=True)

    if not args.skip_tests:
        print(" ".join(build_tests_cmd))
        subprocess.run(build_tests_cmd, check=True)
        subprocess.run(["ctest", "--output-on-failure"], cwd=build_dir, check=True)

    print(f"Artefatos gerados em {build_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
