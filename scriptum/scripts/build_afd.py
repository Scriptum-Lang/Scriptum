#!/usr/bin/env python3
"""Generate lexical tables for the Scriptum lexer."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "scriptum" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from scriptum.lexer import spec
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit(f"Failed to import lexer spec: {exc}") from exc


def _validate_regex(payload: dict[str, Any]) -> None:
    for entry in payload["token_patterns"]:
        try:
            re.compile(entry["pattern"])
        except re.error as exc:  # pragma: no cover - invalid regex
            raise SystemExit(f"Invalid regex for {entry['name']}: {exc}") from exc


def build_tables() -> dict[str, Any]:
    data = spec.to_json()
    _validate_regex(data)
    return data


def write_tables(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate Scriptum lexer tables")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "scriptum" / "src" / "scriptum" / "lexer" / "tables.json",
        help="Destination file for serialized tables",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print tables to stdout as well",
    )
    args = parser.parse_args(argv)

    tables = build_tables()
    write_tables(args.out, tables)

    if args.show:
        json.dump(tables, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
