"""
Utilities to (re)generate deterministic lexer tables from the regex specification.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable

from . import spec
from ..regex.builder import AutomataBuilder


def _validate_regex(patterns: Iterable[Dict[str, Any]]) -> None:
    for entry in patterns:
        try:
            re.compile(entry["pattern"])
        except re.error as exc:  # pragma: no cover - validation path
            raise ValueError(f"Invalid regex for {entry['name']}: {exc}") from exc


def build_tables() -> Dict[str, Any]:
    """Construct the lexical tables as a serialisable dictionary."""

    payload = spec.to_json()
    _validate_regex(payload["token_patterns"])

    builder = AutomataBuilder()
    result = builder.build(spec.TOKEN_PATTERNS)

    states_payload: list[Dict[str, Any]] = []
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

    payload["dfa"] = {
        "alphabet": sorted(result.dfa.alphabet()),
        "start_state": result.dfa.start_state,
        "states": states_payload,
    }
    return payload


def write_tables(path: Path) -> Dict[str, Any]:
    """Build and persist lexer tables to *path*."""

    tables = build_tables()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tables, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    return tables
