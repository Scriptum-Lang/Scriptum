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
"$BIN" lex "${SCRIPT_DIR}/../examples/hello.stm"
"$BIN" parse "${SCRIPT_DIR}/../examples/hello.stm"

if "$BIN" --help | grep -q "sema"; then
  "$BIN" sema "${SCRIPT_DIR}/../examples/hello.stm"
fi
