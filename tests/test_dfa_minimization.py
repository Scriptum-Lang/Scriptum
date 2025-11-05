from __future__ import annotations

from dataclasses import dataclass

from scriptum import tokens
from scriptum.lexer.spec import TokenPattern
from scriptum.regex.builder import AutomataBuilder


def run_dfa_text(dfa_obj, text: str) -> bool:
    state_id = dfa_obj.start_state
    for ch in text:
        symbol = ord(ch)
        state = dfa_obj.states[state_id]
        if symbol not in state.transitions:
            return False
        state_id = state.transitions[symbol]
    accepting = dfa_obj.states[state_id].accepting
    return accepting is not None and not accepting.ignore


def test_identifier_dfa_minimized_states() -> None:
    patterns = [
        TokenPattern(
            name="IDENT",
            kind=tokens.TokenKind.IDENTIFIER,
            pattern=r"[A-Za-z_][A-Za-z0-9_]*",
            priority=10,
        )
    ]
    builder = AutomataBuilder()
    result = builder.build(patterns)
    assert len(result.dfa.states) == 3  # start, accepting, sink
    assert run_dfa_text(result.dfa, "foo")
    assert run_dfa_text(result.dfa, "_bar42")
    assert not run_dfa_text(result.dfa, "1foo")


def test_number_dfa_accepts_valid_literals() -> None:
    patterns = [
        TokenPattern(
            name="NUM",
            kind=tokens.TokenKind.NUMBER_LITERAL,
            pattern=r"-?(?:0|[1-9][0-9_]*)(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?",
            priority=10,
        )
    ]
    builder = AutomataBuilder()
    result = builder.build(patterns)
    assert run_dfa_text(result.dfa, "0")
    assert run_dfa_text(result.dfa, "-10")
    assert run_dfa_text(result.dfa, "3.14")
    assert run_dfa_text(result.dfa, "6.02E23")
    assert not run_dfa_text(result.dfa, "")
    assert not run_dfa_text(result.dfa, "-")
    assert not run_dfa_text(result.dfa, "1.")
