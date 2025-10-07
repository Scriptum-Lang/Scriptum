#!/usr/bin/env python3
"""Generate lexical tables for the Scriptum lexer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from scriptum.lexer.generator import write_tables
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit(f"Failed to import build dependencies: {exc}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate Scriptum lexer tables")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "src" / "scriptum" / "lexer" / "tables.json",
        help="Destination file for serialized tables",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print tables to stdout as well",
    )
    args = parser.parse_args(argv)

    tables = write_tables(args.out)

    if args.show:
        json.dump(tables, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
