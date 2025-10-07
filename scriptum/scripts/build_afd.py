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
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from scriptum.lexer import spec
    from scriptum.regex.builder import AutomataBuilder
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit(f"Failed to import build dependencies: {exc}") from exc


def _validate_regex(patterns: list[dict[str, Any]]) -> None:
    for entry in patterns:
        try:
            re.compile(entry["pattern"])
        except re.error as exc:  # pragma: no cover - invalid regex
            raise SystemExit(f"Invalid regex for {entry['name']}: {exc}") from exc


def build_tables() -> dict[str, Any]:
    base = spec.to_json()
    _validate_regex(base["token_patterns"])

    builder = AutomataBuilder()
    result = builder.build(spec.TOKEN_PATTERNS)

    states_payload: list[dict[str, Any]] = []
    for state_id, state in enumerate(result.dfa.states):
        transitions = {str(symbol): target for symbol, target in sorted(state.transitions.items())}
        accepting = None
        if state.accepting is not None:
            info = state.accepting
            accepting = {
                "token_index": info.index,
                "name": info.name,
                "kind": info.kind,
                "priority": info.priority,
                "ignore": info.ignore,
            }
        states_payload.append(
            {
                "id": state_id,
                "accepting": accepting,
                "transitions": transitions,
            }
        )

    base["dfa"] = {
        "alphabet": sorted(result.dfa.alphabet()),
        "start_state": result.dfa.start_state,
        "states": states_payload,
    }

    return base


def write_tables(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


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

    tables = build_tables()
    write_tables(args.out, tables)

    if args.show:
        json.dump(tables, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
