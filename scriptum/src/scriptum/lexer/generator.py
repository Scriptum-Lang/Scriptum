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


def _encode_symbol(codepoint: int) -> str:
    if not 0 <= codepoint <= 0x10FFFF:
        raise ValueError(f"Invalid codepoint for DFA serialization: {codepoint}")
    return chr(codepoint)


def build_tables() -> Dict[str, Any]:
    """Construct the lexical tables as a serialisable dictionary."""

    spec_payload = spec.to_json()
    _validate_regex(spec_payload["token_patterns"])

    builder = AutomataBuilder()
    result = builder.build(spec.TOKEN_PATTERNS)

    alphabet = [_encode_symbol(symbol) for symbol in sorted(result.dfa.alphabet())]
    finals: list[int] = []
    final_labels: Dict[str, str] = {}
    final_priority: Dict[str, int] = {}
    final_ignore: Dict[str, bool] = {}
    final_kind: Dict[str, str] = {}
    final_index: Dict[str, int] = {}
    transitions: Dict[str, Dict[str, int]] = {}

    for state_id, state in enumerate(result.dfa.states):
        state_key = str(state_id)
        encoded_transitions = {
            _encode_symbol(symbol): target for symbol, target in sorted(state.transitions.items())
        }
        if encoded_transitions:
            transitions[state_key] = encoded_transitions

        if state.accepting is None:
            continue

        info = state.accepting
        finals.append(state_id)
        final_labels[state_key] = info.name
        final_priority[state_key] = info.priority
        final_ignore[state_key] = info.ignore
        final_kind[state_key] = info.kind
        final_index[state_key] = info.index

    return {
        "alphabet": alphabet,
        "states": list(range(len(result.dfa.states))),
        "start": result.dfa.start_state,
        "finals": finals,
        "final_token_labels": final_labels,
        "final_token_priority": final_priority,
        "final_token_ignore": final_ignore,
        "final_token_kind": final_kind,
        "final_token_index": final_index,
        "trans": transitions,
    }


def write_tables(path: Path) -> Dict[str, Any]:
    """Build and persist lexer tables to *path*."""

    tables = build_tables()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tables, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    return tables
