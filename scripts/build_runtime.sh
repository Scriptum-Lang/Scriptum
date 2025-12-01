#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
SRC_FILE="${ROOT_DIR}/src/scriptum/runtime/llvm_rt.c"
INCLUDE_DIR="${ROOT_DIR}/src"

CC_BIN="${CC:-cc}"
CFLAGS_DEFAULT="-O2 -fPIC -std=c99"
CFLAGS="${CFLAGS:-$CFLAGS_DEFAULT}"

mkdir -p "${BUILD_DIR}"

echo "[runtime] Compiling llvm_rt.c with ${CC_BIN}"
"${CC_BIN}" ${CFLAGS} -I"${INCLUDE_DIR}" -c "${SRC_FILE}" -o "${BUILD_DIR}/llvm_rt.o"

echo "[runtime] Building static library"
ar rcs "${BUILD_DIR}/libscriptum_rt.a" "${BUILD_DIR}/llvm_rt.o"

UNAME="$(uname -s 2>/dev/null || echo unknown)"
LIB_EXT="so"
if [[ "${UNAME}" == MINGW* || "${UNAME}" == MSYS* || "${UNAME}" == CYGWIN* || "${UNAME}" == Windows* ]]; then
    LIB_EXT="dll"
fi

echo "[runtime] Building shared library (.${LIB_EXT})"
"${CC_BIN}" ${CFLAGS} -shared "${BUILD_DIR}/llvm_rt.o" -o "${BUILD_DIR}/libscriptum_rt.${LIB_EXT}"

echo "[runtime] Artifacts available under ${BUILD_DIR}"
