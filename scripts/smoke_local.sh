#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/../dist"
BIN="${DIST_DIR}/scriptum"

if [ ! -x "$BIN" ]; then
  echo "Scriptum binary not found at ${BIN}" >&2
  exit 1
fi

"$BIN" --version
"$BIN" --help
"$BIN" "${SCRIPT_DIR}/../examples/hello.stm"
"$BIN" dev lex "${SCRIPT_DIR}/../examples/hello.stm"
"$BIN" dev ast "${SCRIPT_DIR}/../examples/hello.stm"
"$BIN" check "${SCRIPT_DIR}/../examples/err/type_mismatch.stm" --json
